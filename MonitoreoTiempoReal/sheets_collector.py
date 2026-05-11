"""
UDEC Cyber-Auditor v3 — sheets_collector.py
============================================
Módulo que lee datos de los agentes de biblioteca desde Google Sheets.
Usado internamente por app_streamlit.py para el nuevo tab de Bibliotecas.

INSTALACIÓN:
    pip install gspread google-auth

"""

import json
import time
import threading
import logging
import os
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SheetsCollector")

try:
    import gspread
    from google.oauth2.service_account import Credentials
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False
    logger.warning("gspread o google-auth no instalados")

# ─────────────────────────────────────────────
#  CREDENTIALS HELPER (Streamlit Cloud compatible)
# ─────────────────────────────────────────────

def get_credentials():
    """
    Obtiene credenciales de Google de manera compatible con:
    1. Streamlit Cloud (st.secrets)
    2. Desarrollo local (archivo credentials.json)
    
    Retorna: Credentials object de google-auth
    """
    # Intentar usar st.secrets primero (Streamlit Cloud)
    try:
        import streamlit as st
        if "gcp_service_account" in st.secrets:
            logger.info("Usando credenciales desde st.secrets")
            creds_dict = dict(st.secrets["gcp_service_account"])
            return Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    except ImportError:
        pass  # No estamos en Streamlit, continuar con archivo
    except Exception as e:
        logger.warning(f"Error leyendo st.secrets: {e}")
    
    # Fallback: usar archivo credentials.json (desarrollo local)
    if os.path.exists(CREDENTIALS_FILE):
        logger.info(f"Usando credenciales desde archivo: {CREDENTIALS_FILE}")
        return Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    
    raise FileNotFoundError(
        f"No se encontraron credenciales. "
        f"Streamlit Cloud: configura st.secrets['gcp_service_account']. "
        f"Local: asegúrate de que {CREDENTIALS_FILE} exista."
    )

# ─────────────────────────────────────────────
#  CONFIG (debe coincidir con agent.py)
# ─────────────────────────────────────────────
import os
base_dir = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE  = os.path.join(os.path.dirname(base_dir), "credentials.json") # ../credentials.json
SPREADSHEET_NAME  = "UDEC-Cyber-Auditor"
POLL_INTERVAL_SEC = 30       # Cada cuánto leer el Sheet (para no exceder cuota)
MAX_ROWS_PER_LIB  = 120      # Cuántas filas históricas conservar por biblioteca

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ─────────────────────────────────────────────
#  DATACLASSES
# ─────────────────────────────────────────────

@dataclass
class LibrarySnapshot:
    """Último snapshot conocido de una biblioteca."""
    name:            str   = "Desconocida"
    timestamp:       str   = "—"
    local_ip:        str   = "—"
    status:          str   = "UNKNOWN"       # STABLE | WARNING | CRITICAL | UNKNOWN
    latency_avg_ms:  float = 0.0
    latency_icmp_ms: float = 0.0
    loss_pct:        float = 0.0
    packets_sent:    int   = 0
    packets_lost:    int   = 0
    targets:         dict  = field(default_factory=dict)

    # Historia para gráfico
    latency_history: list  = field(default_factory=list)   # últimos N valores
    timestamps_hist: list  = field(default_factory=list)   # timestamps correspondientes

    # Metadata
    last_seen_sec:   float = 0.0   # time.time() de la última lectura exitosa
    online:          bool  = False


@dataclass
class LibrariesReport:
    """Reporte consolidado de todas las bibliotecas."""
    snapshots:   dict  = field(default_factory=dict)   # {name: LibrarySnapshot}
    last_update: float = 0.0
    error:       Optional[str] = None


# ─────────────────────────────────────────────
#  PARSER DE FILAS
# ─────────────────────────────────────────────

SHEET_HEADERS = [
    "timestamp", "biblioteca", "local_ip", "status",
    "latency_avg_ms", "latency_icmp_ms", "loss_pct",
    "packets_sent", "packets_lost", "targets_json",
]

def _parse_row(row: list) -> Optional[dict]:
    """Convierte una fila del sheet en dict. Retorna None si está incompleta."""
    if len(row) < len(SHEET_HEADERS):
        row = row + [""] * (len(SHEET_HEADERS) - len(row))
    d = dict(zip(SHEET_HEADERS, row))
    try:
        d["latency_avg_ms"]  = float(d.get("latency_avg_ms")  or 0)
        d["latency_icmp_ms"] = float(d.get("latency_icmp_ms") or 0)
        d["loss_pct"]        = float(d.get("loss_pct")        or 0)
        d["packets_sent"]    = int(float(d.get("packets_sent")  or 0))
        d["packets_lost"]    = int(float(d.get("packets_lost")  or 0))
        d["targets"] = json.loads(d.get("targets_json") or "{}")
    except (ValueError, json.JSONDecodeError):
        return None
    return d


def _seconds_since(timestamp_str: str) -> float:
    """Cuántos segundos han pasado desde el timestamp del agente."""
    try:
        ts = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S UTC")
        ts = ts.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - ts).total_seconds()
    except Exception:
        return 9999.0


# ─────────────────────────────────────────────
#  COLLECTOR PRINCIPAL
# ─────────────────────────────────────────────

class LibrariesCollector:
    """
    Lector periódico de Google Sheets en hilo de fondo.
    Compatible con session_state de Streamlit.

    Uso:
        collector = LibrariesCollector()
        collector.start()
        report = collector.get_report()
        collector.stop()
    """

    def __init__(self):
        self._lock    = threading.Lock()
        self._running = False
        self._thread  = None
        self._report  = LibrariesReport()
        self._gc      = None          # cliente gspread reutilizable

    # ── Ciclo de vida ──────────────────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="LibCollector")
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)

    # ── Acceso thread-safe ─────────────────────────────────────────────────

    def get_report(self) -> LibrariesReport:
        with self._lock:
            return self._report

    # ── Loop interno ───────────────────────────────────────────────────────

    def _loop(self):
        logger.info("LibrariesCollector iniciado. POLL_INTERVAL: %d seg", POLL_INTERVAL_SEC)
        retry_count = 0
        max_retries = 3
        
        # Primer fetch inmediato al arrancar (no esperar 30s)
        try:
            logger.info("Fetch inicial...")
            report = self._fetch()
            with self._lock:
                self._report = report
            logger.info("Fetch inicial exitoso. Snapshots encontrados: %d", len(report.snapshots))
            retry_count = 0
        except Exception as e:
            logger.error("Error en fetch inicial: %s", str(e)[:150])
            with self._lock:
                self._report.error = f"Init error: {str(e)[:100]}"
            retry_count += 1
            
        # Luego ciclo normal
        while self._running:
            time.sleep(POLL_INTERVAL_SEC)
            try:
                logger.debug("Ejecutando fetch periódico...")
                report = self._fetch()
                with self._lock:
                    self._report = report
                logger.debug("Fetch periódico exitoso. Snapshots: %d, Última actualización: %s", 
                            len(report.snapshots), 
                            datetime.fromtimestamp(report.last_update).strftime("%H:%M:%S"))
                retry_count = 0  # Reset de reintentos en caso de éxito
            except Exception as e:
                retry_count += 1
                error_msg = str(e)[:150]
                logger.error("Fetch periódico falló (intento %d/%d): %s", retry_count, max_retries, error_msg)
                with self._lock:
                    self._report.error = f"Fetch error: {error_msg}"
                
                # Si fallan demasiadas veces seguidas, reintentar conectar
                if retry_count >= max_retries:
                    logger.warning("Máximo de reintentos alcanzado. Reseteando conexión...")
                    self._gc = None
                    retry_count = 0

    def _fetch(self) -> LibrariesReport:
        if not SHEETS_AVAILABLE:
            raise RuntimeError("gspread no instalado. Ejecuta: pip install gspread google-auth")

        try:
            # Conectar (reutiliza cliente si ya existe)
            if self._gc is None:
                logger.info("Creando nueva conexión a Google Sheets...")
                creds = get_credentials()
                self._gc = gspread.authorize(creds)
                logger.info("Conexión a Google Sheets establecida")

            sh        = self._gc.open(SPREADSHEET_NAME)
            worksheets = sh.worksheets()
            logger.info("Hojas encontradas en Spreadsheet: %s", [ws.title for ws in worksheets])

            snapshots = {}

            for ws in worksheets:
                # Saltar hojas de índice/instrucciones (en español e inglés)
                skip_sheets = ("instrucciones", "index", "índice", "readme", "hoja 1", "sheet1")
                if ws.title.lower() in skip_sheets:
                    logger.debug("Saltando hoja de índice: %s", ws.title)
                    continue

                logger.info("Procesando hoja: %s", ws.title)
                
                try:
                    all_rows = ws.get_all_values()
                    logger.debug("  Hoja %s tiene %d filas", ws.title, len(all_rows))
                except Exception as e:
                    logger.warning("Error leyendo hoja %s: %s", ws.title, str(e)[:80])
                    continue

                if len(all_rows) < 2:
                    logger.warning("  Hoja %s vacía o solo headers (%d filas)", ws.title, len(all_rows))
                    continue

                # Primera fila = headers (ignorar), resto = datos
                data_rows = all_rows[1:]
                logger.debug("  Hoja %s tiene %d filas de datos", ws.title, len(data_rows))

                # Parsear todas las filas válidas
                parsed = [_parse_row(r) for r in data_rows]
                valid_parsed = [p for p in parsed if p and p.get("biblioteca")]
                logger.debug("  Hoja %s: %d/%d filas parseadas correctamente", ws.title, len(valid_parsed), len(parsed))

                if not valid_parsed:
                    logger.warning("  Hoja %s sin registros válidos", ws.title)
                    continue

                name = ws.title

                # Historia: últimas MAX_ROWS filas
                history_rows = valid_parsed[-MAX_ROWS_PER_LIB:]
                lat_hist  = [r["latency_avg_ms"]  for r in history_rows]
                time_hist = [r["timestamp"]        for r in history_rows]

                # Último snapshot
                last = valid_parsed[-1]
                age  = _seconds_since(last["timestamp"])

                snap = LibrarySnapshot(
                    name            = name,
                    timestamp       = last["timestamp"],
                    local_ip        = last.get("local_ip", "—"),
                    status          = last.get("status", "UNKNOWN"),
                    latency_avg_ms  = last["latency_avg_ms"],
                    latency_icmp_ms = last["latency_icmp_ms"],
                    loss_pct        = last["loss_pct"],
                    packets_sent    = last["packets_sent"],
                    packets_lost    = last["packets_lost"],
                    targets         = last["targets"],
                    latency_history = lat_hist,
                    timestamps_hist = time_hist,
                    last_seen_sec   = time.time(),
                    # Online si el dato tiene menos de 10 minutos (tolerancia amplia a timezones y delays)
                    online          = age < 600,
                )

                snapshots[name] = snap
                logger.info("✅ Biblioteca %s: latencia=%.1f ms, estado=%s, antigüedad=%.0f seg", 
                           name, last["latency_avg_ms"], last.get("status"), age)

            logger.info("Fetch completado: %d bibliotecas actualizadas", len(snapshots))
            return LibrariesReport(
                snapshots   = snapshots,
                last_update = time.time(),
                error       = None,
            )
        except Exception as e:
            logger.error("Error en _fetch: %s", str(e), exc_info=True)
            raise


# ─────────────────────────────────────────────
#  FACTORY para session_state (igual a get_or_create_prober)
# ─────────────────────────────────────────────

def get_or_create_collector(state: dict) -> LibrariesCollector:
    """
    Retorna el LibrariesCollector activo desde session_state.
    Lo crea y arranca si no existe.
    """
    key = "_libraries_collector"
    if state.get(key) is None:
        collector = LibrariesCollector()
        collector.start()
        state[key] = collector
    return state[key]


def stop_collector(state: dict):
    """Detiene y elimina el collector del session_state."""
    key = "_libraries_collector"
    if state.get(key):
        state[key].stop()
        state[key] = None


# ─────────────────────────────────────────────
#  HELPERS DE DIAGNÓSTICO
# ─────────────────────────────────────────────

def status_color(status: str) -> str:
    """Retorna color hex según status."""
    return {
        "STABLE":   "#00ff41",
        "WARNING":  "#ffb300",
        "CRITICAL": "#ff0033",
        "UNKNOWN":  "#4a6080",
    }.get(status, "#4a6080")


def status_icon(status: str) -> str:
    return {
        "STABLE":   "✓",
        "WARNING":  "⚠",
        "CRITICAL": "✗",
        "UNKNOWN":  "?",
    }.get(status, "?")


def overall_status(report: LibrariesReport) -> str:
    """Estado global consolidado de todas las bibliotecas."""
    statuses = [s.status for s in report.snapshots.values()]
    if not statuses:
        return "UNKNOWN"
    if "CRITICAL" in statuses:
        return "CRITICAL"
    if "WARNING" in statuses:
        return "WARNING"
    return "STABLE"
