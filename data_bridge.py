# v3/data_bridge.py
# ─────────────────────────────────────────────────────────────────────────────
# UDEC Cyber-Auditor v3 | Puente de datos entre core/ y Streamlit
#
# Estrategia: 
#   - Modo LIVE: usa HttpProber real del core/ en un hilo de fondo.
#     Los resultados se almacenan en st.session_state para evitar bloqueos.
#   - Modo SIM:  genera datos sintéticos (idéntica interfaz pública).
#
# IMPORTANTE: Streamlit re-ejecuta el script en cada interacción.
#   Los hilos de captura se guardan en session_state["_prober"] para no
#   reiniciarlos en cada re-render.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import sys
import os
import time
import math
import random
import threading
import logging
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger("DataBridge")

# ── Añade el root del proyecto al sys.path para importar core/ ───────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Importa core con fallback graceful
try:
    from core.http_prober import HttpProber, HttpProbeResult
    from core.analyzer_l7_http import L7HttpAnalyzer, L7HttpSnapshot
    CORE_AVAILABLE = True
except ImportError as e:
    CORE_AVAILABLE = False
    logger.warning(f"core/ no disponible, usando simulación: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Estructuras de salida normalizadas (independientes del modo)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class NetworkNode:
    """Datos de un nodo individual de red."""
    id:               str
    name:             str
    municipio:        str
    lat:              float
    lon:              float
    role:             str           # "PRINCIPAL", "RELAY", "GATEWAY", etc.
    latency_ms:       float = 0.0
    packet_loss:      float = 0.0
    status:           str = "STABLE"  # STABLE | WARNING | CRITICAL
    last_seen:        float = field(default_factory=time.time)
    is_active:        bool = True
    
    def get_color(self) -> list:
        """Retorna color RGB según estado."""
        if self.status == "CRITICAL":
            return [255, 0, 85]    # Rojo cyberpunk
        elif self.status == "WARNING":
            return [255, 230, 0]   # Amarillo
        else:
            return [0, 255, 136]   # Verde cyan


@dataclass
class NetworkSnapshot:
    """Estado de red listo para consumir en la UI."""
    # Latencia
    latency_ms:       float = 0.0
    latency_avg:      float = 0.0
    latency_min:      float = 0.0
    latency_max:      float = 0.0
    latency_history:  list  = field(default_factory=list)

    # Calidad
    packet_loss_pct:  float = 0.0
    error_rate_pct:   float = 0.0
    congestion_score: float = 0.0   # 0-100

    # HTTP
    status_code:      Optional[int] = None
    content_encoding: Optional[str] = None
    content_length:   int           = 0
    resolved_ip:      str           = "—"
    total_probes:     int           = 0

    # Estado
    status:           str           = "STABLE"  # STABLE | WARNING | CRITICAL
    alert_message:    str           = "Inicializando..."
    recommendation:   str           = ""

    # Timestamps para charts
    timestamps:       list = field(default_factory=list)
    latency_points:   list = field(default_factory=list)
    
    # Nodos de red para el mapa
    network_nodes:    list = field(default_factory=list)


@dataclass
class PingResult:
    """Resultado de un ping/HTTP-probe puntual."""
    target:      str
    success:     bool
    latency_ms:  float
    status_code: Optional[int]
    error:       Optional[str]
    timestamp:   float = field(default_factory=time.time)


# ─────────────────────────────────────────────────────────────────────────────
# Simulador (sin dependencias externas)
# ─────────────────────────────────────────────────────────────────────────────

class SimulatedProber:
    """Genera datos sintéticos con patrones realistas."""

    def __init__(self, target: str = "portal.udec.edu.co"):
        self.target    = target
        self._t0       = time.time()
        self._total    = 0
        self._errors   = 0
        self._latencies: list[float] = []
        self._running  = False
        self._thread   = None
        self._lock     = threading.Lock()

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            elapsed = time.time() - self._t0
            base_lat = 55 + 25 * math.sin(elapsed / 8)
            noise    = random.gauss(0, 8)
            is_spike = random.random() < 0.04
            lat      = max(8.0, base_lat + noise + (250 if is_spike else 0))
            is_err   = random.random() < 0.03

            with self._lock:
                self._total += 1
                if is_err:
                    self._errors += 1
                else:
                    self._latencies.append(lat)
                    if len(self._latencies) > 120:
                        self._latencies.pop(0)

            time.sleep(0.5)

    def get_snapshot(self) -> NetworkSnapshot:
        with self._lock:
            lats  = list(self._latencies[-80:])
            total = self._total
            errs  = self._errors

        if not lats:
            return NetworkSnapshot(alert_message="Calentando sensores...")

        avg_lat = sum(lats) / len(lats)
        err_pct = (errs / total * 100) if total else 0.0
        cong    = min(avg_lat / 500, 1.0) * 50 + min(err_pct / 20, 1.0) * 50

        if err_pct > 10 or avg_lat > 500:
            status = "CRITICAL"
            alert  = f"🔴 Latencia crítica: {avg_lat:.0f}ms | Pérdida: {err_pct:.1f}%"
        elif err_pct > 3 or avg_lat > 150:
            status = "WARNING"
            alert  = f"⚠ Degradación: {avg_lat:.0f}ms | Pérdida: {err_pct:.1f}%"
        else:
            status = "STABLE"
            alert  = "✓ Red estable – Sin anomalías"

        return NetworkSnapshot(
            latency_ms        = round(lats[-1], 1) if lats else 0.0,
            latency_avg       = round(avg_lat, 1),
            latency_min       = round(min(lats), 1),
            latency_max       = round(max(lats), 1),
            latency_history   = lats,
            packet_loss_pct   = round(err_pct * 0.7, 2),
            error_rate_pct    = round(err_pct, 2),
            congestion_score  = round(cong, 1),
            status_code       = 200,
            content_encoding  = random.choice(["gzip", "br", None]),
            content_length    = random.randint(15_000, 120_000),
            resolved_ip       = "190.216.132.40",
            total_probes      = total,
            status            = status,
            alert_message     = alert,
            recommendation    = "Habilitar gzip en servidor" if err_pct > 3 else "Sin acciones",
            timestamps        = list(range(len(lats))),
            latency_points    = lats,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Prober LIVE (wrapping core/HttpProber + L7HttpAnalyzer)
# ─────────────────────────────────────────────────────────────────────────────

class LiveProber:
    """Wrapper sobre core/HttpProber para uso en Streamlit."""

    def __init__(self, target: str):
        self.target   = target
        self._prober  = HttpProber(target=target, interval_sec=0.8, num_workers=1)
        self._analyzer = L7HttpAnalyzer(window=80)
        self._running  = False
        self._thread   = None
        self._lock     = threading.Lock()
        self._last_ip  = "resolving..."

    def start(self):
        if self._running:
            return
        self._running = True
        self._prober.start()
        self._thread = threading.Thread(target=self._drain_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        self._prober.stop()

    def _drain_loop(self):
        """Drena la queue del prober y alimenta el analizador."""
        while self._running:
            result = self._prober.get_result(timeout=0.3)
            if result:
                with self._lock:
                    self._analyzer.feed(result)
                    if result.resolved_ip and result.resolved_ip != "?":
                        self._last_ip = result.resolved_ip
            time.sleep(0.05)

    def get_snapshot(self) -> NetworkSnapshot:
        with self._lock:
            snap = self._analyzer.snapshot()
            ip   = self._last_ip

        lats = snap.latency_points[-80:] if snap.latency_points else []

        return NetworkSnapshot(
            latency_ms        = round(lats[-1], 1) if lats else 0.0,
            latency_avg       = round(snap.latency_ms_avg, 1),
            latency_min       = round(snap.latency_ms_min, 1),
            latency_max       = round(snap.latency_ms_max, 1),
            latency_history   = lats,
            packet_loss_pct   = round(snap.error_rate_pct * 0.7, 2),
            error_rate_pct    = round(snap.error_rate_pct, 2),
            congestion_score  = round(snap.congestion_score, 1),
            status_code       = 200 if snap.status_2xx > 0 else (503 if snap.status_5xx > 0 else None),
            content_encoding  = list(snap.encoding_types.keys())[0] if snap.encoding_types else None,
            content_length    = 0,
            resolved_ip       = ip,
            total_probes      = snap.total_probes,
            status            = snap.status,
            alert_message     = snap.alert_message,
            recommendation    = snap.recommendation,
            timestamps        = list(range(len(lats))),
            latency_points    = lats,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Factory y helpers para session_state
# ─────────────────────────────────────────────────────────────────────────────

def get_or_create_prober(state: dict, target: str, mode: str) -> object:
    """
    Recupera el prober activo del session_state o crea uno nuevo.
    Gestiona correctamente el ciclo de vida entre re-renders de Streamlit.
    """
    key     = "_prober_instance"
    key_cfg = "_prober_config"
    cfg     = f"{mode}::{target}"

    # Si la config cambió, destruye el prober anterior
    if state.get(key_cfg) != cfg and state.get(key) is not None:
        try:
            state[key].stop()
        except Exception:
            pass
        state[key]     = None
        state[key_cfg] = None

    if state.get(key) is None:
        if mode == "live" and CORE_AVAILABLE:
            prober = LiveProber(target=target)
        else:
            prober = SimulatedProber(target=target)

        prober.start()
        state[key]     = prober
        state[key_cfg] = cfg

    return state[key]


def run_ping_diagnosis(target: str, timeout: float = 5.0) -> PingResult:
    """
    Ejecuta un probe HTTP puntual y bloquea hasta obtener resultado.
    Usar SOLO en el hilo de diagnóstico (botón manual).
    """
    try:
        import socket
        import requests as req

        t0 = time.time()
        if "://" not in target:
            url = f"https://{target}" if not _looks_like_ip(target) else f"http://{target}"
        else:
            url = target

        resp = req.get(url, timeout=timeout, allow_redirects=True,
                       headers={"User-Agent": "UDEC-Auditor/3.0 (Diag)"})
        lat  = (time.time() - t0) * 1000

        return PingResult(
            target      = target,
            success     = True,
            latency_ms  = round(lat, 1),
            status_code = resp.status_code,
            error       = None,
        )

    except Exception as e:
        return PingResult(
            target      = target,
            success     = False,
            latency_ms  = 0.0,
            status_code = None,
            error       = str(e)[:120],
        )


def _looks_like_ip(s: str) -> bool:
    import socket
    try:
        socket.inet_aton(s.split(":")[0])
        return True
    except socket.error:
        return False
