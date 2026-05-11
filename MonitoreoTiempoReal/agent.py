# UDEC Cyber-Auditor v3 — Agente de Biblioteca
# Corre este script en cada PC de biblioteca.
# Mide latencia y pérdida de paquetes, y envía los datos a Google Sheets.
#
# INSTALACIÓN:
#     pip install gspread google-auth requests
#
# CONFIGURACIÓN:
#     1. Edita las variables de la sección CONFIG más abajo
#     2. Descarga tu credentials.json de Google Cloud Console
#     3. Ejecuta: python agent.py

import time
import socket
import statistics
import platform
import subprocess
import requests
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone

# ---------------------------------------------
#  CONFIG - Edita esto antes de correr
# ---------------------------------------------

BIBLIOTECA_NAME = "Biblioteca Ch\u00eda"          # Nombre unico de esta sede (debe coincidir con la hoja en Google Sheets)
import os
base_dir = os.path.dirname(os.path.abspath(__file__))
# Busca credenciales en la misma carpeta (para cuando copies al celular) o en la carpeta padre (estructura original)
_local_creds = os.path.join(base_dir, "credentials.json")
_parent_creds = os.path.join(os.path.dirname(base_dir), "credentials.json")
CREDENTIALS_FILE = _local_creds if os.path.exists(_local_creds) else _parent_creds
SPREADSHEET_NAME = "UDEC-Cyber-Auditor"       # Nombre del Google Sheet (debe existir)

# Targets que se van a sondear (host, descripción)
PROBE_TARGETS = [
    ("8.8.8.8",          "Google DNS"),
    ("1.1.1.1",          "Cloudflare DNS"),
    ("portal.udec.edu.co", "Portal UDEC"),
]

INTERVAL_SEC   = 30       # Cada cuántos segundos enviar datos
PROBE_COUNT    = 5        # Cuántos pings por ciclo para calcular pérdida
HTTP_TIMEOUT   = 5.0      # Timeout para probes HTTP (segundos)

# ─────────────────────────────────────────────
#  SCOPES GOOGLE SHEETS
# ─────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ─────────────────────────────────────────────
#  MEDICIÓN DE RED
# ─────────────────────────────────────────────

def probe_http(host: str, timeout: float = HTTP_TIMEOUT) -> dict:
    """Mide latencia HTTP hacia un host. Retorna dict con métricas."""
    url = f"http://{host}" if _is_ip(host) else f"https://{host}"
    try:
        t0 = time.time()
        resp = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": f"UDEC-Auditor/3.0-Agent ({BIBLIOTECA_NAME})"},
        )
        latency = (time.time() - t0) * 1000
        return {
            "success": True,
            "latency_ms": round(latency, 1),
            "status_code": resp.status_code,
            "error": None,
        }
    except requests.exceptions.Timeout:
        return {"success": False, "latency_ms": 0.0, "status_code": None, "error": "TIMEOUT"}
    except Exception as e:
        return {"success": False, "latency_ms": 0.0, "status_code": None, "error": str(e)[:80]}


def probe_icmp_ping(host: str, count: int = PROBE_COUNT) -> dict:
    """
    Envía N pings ICMP y retorna latencia promedio y pérdida de paquetes.
    Funciona en Windows y Linux/Mac.
    """
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", str(count), host]
    else:
        cmd = ["ping", "-c", str(count), "-W", "2", host]

    latencies = []
    errors = 0

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=count * 3 + 5,
        )
        output = result.stdout

        # Parsear latencias individuales
        import re
        if system == "windows":
            matches = re.findall(r"tiempo[=<](\d+)ms|time[=<](\d+)ms", output, re.IGNORECASE)
            for m in matches:
                val = m[0] or m[1]
                latencies.append(float(val))
        else:
            matches = re.findall(r"time[=<](\d+\.?\d*)\s*ms", output, re.IGNORECASE)
            latencies = [float(m) for m in matches]

        errors = count - len(latencies)

    except subprocess.TimeoutExpired:
        errors = count
    except Exception:
        errors = count

    loss_pct = (errors / count) * 100 if count > 0 else 100.0
    avg_lat  = statistics.mean(latencies) if latencies else 0.0
    min_lat  = min(latencies) if latencies else 0.0
    max_lat  = max(latencies) if latencies else 0.0

    return {
        "loss_pct":   round(loss_pct, 1),
        "latency_avg": round(avg_lat, 1),
        "latency_min": round(min_lat, 1),
        "latency_max": round(max_lat, 1),
        "packets_sent": count,
        "packets_lost": errors,
    }


def _is_ip(s: str) -> bool:
    try:
        socket.inet_aton(s.split(":")[0])
        return True
    except socket.error:
        return False


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "desconocida"


def collect_snapshot() -> dict:
    """Recolecta todas las métricas del ciclo actual."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Probe ICMP al primer target (gateway/DNS)
    icmp = probe_icmp_ping("8.8.8.8", count=PROBE_COUNT)

    # Probe HTTP a cada target
    http_results = {}
    for host, label in PROBE_TARGETS:
        http_results[label] = probe_http(host)

    # Latencia HTTP promedio entre targets exitosos
    successful = [r["latency_ms"] for r in http_results.values() if r["success"]]
    avg_http_latency = round(statistics.mean(successful), 1) if successful else 0.0

    # Estado general (ajustado para Android donde ICMP está bloqueado)
    loss = icmp["loss_pct"]
    lat  = avg_http_latency
    
    # Si ICMP está bloqueado (pérdida > 50%), ignorarlo para el estado
    icmp_blocked = loss > 50
    
    # Depuración: imprimir valores que determinan el estado
    print(f"  [DEBUG] Pérdida ICMP: {loss}% (umbral CRITICAL: 10%, WARNING: 3%)")
    print(f"  [DEBUG] Latencia HTTP: {lat}ms (umbral CRITICAL: 1000ms, WARNING: 500ms)")
    print(f"  [DEBUG] ICMP bloqueado: {icmp_blocked}")
    
    if icmp_blocked:
        # Solo usar latencia HTTP para determinar estado (ICMP bloqueado en Android)
        if lat > 1000:
            status = "CRITICAL"
            print(f"  [DEBUG] Motivo CRITICAL (ICMP bloqueado): lat={lat} > 1000")
        elif lat > 500:
            status = "WARNING"
            print(f"  [DEBUG] Motivo WARNING (ICMP bloqueado): lat={lat} > 500")
        else:
            status = "STABLE"
            print(f"  [DEBUG] Motivo STABLE (ICMP bloqueado): lat={lat} <= 500")
    else:
        # Usar ambos ICMP y latencia HTTP (redes normales)
        if loss > 10 or lat > 1000:
            status = "CRITICAL"
            print(f"  [DEBUG] Motivo CRITICAL: loss={loss} > 10 OR lat={lat} > 1000")
        elif loss > 3 or lat > 500:
            status = "WARNING"
            print(f"  [DEBUG] Motivo WARNING: loss={loss} > 3 OR lat={lat} > 500")
        else:
            status = "STABLE"
            print(f"  [DEBUG] Motivo STABLE: loss={loss} <= 3 AND lat={lat} <= 500")

    return {
        "timestamp":       timestamp,
        "biblioteca":      BIBLIOTECA_NAME,
        "local_ip":        get_local_ip(),
        "status":          status,
        "latency_avg_ms":  avg_http_latency,
        "latency_icmp_ms": icmp["latency_avg"],
        "loss_pct":        icmp["loss_pct"],
        "packets_sent":    icmp["packets_sent"],
        "packets_lost":    icmp["packets_lost"],
        # Resultados por target (serializado como JSON)
        "targets_json":    json.dumps({
            label: {"ok": r["success"], "lat": r["latency_ms"], "code": r["status_code"]}
            for label, r in http_results.items()
        }),
    }


# ---------------------------------------------
#  GOOGLE SHEETS
# ---------------------------------------------

SHEET_HEADERS = [
    "timestamp", "biblioteca", "local_ip", "status",
    "latency_avg_ms", "latency_icmp_ms", "loss_pct",
    "packets_sent", "packets_lost", "targets_json",
]

def connect_sheet():
    """Conecta a Google Sheets y retorna la hoja de trabajo."""
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    gc    = gspread.authorize(creds)
    sh    = gc.open(SPREADSHEET_NAME)

    # Buscar o crear hoja con nombre de la biblioteca
    try:
        ws = sh.worksheet(BIBLIOTECA_NAME)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=BIBLIOTECA_NAME, rows=5000, cols=len(SHEET_HEADERS))
        ws.append_row(SHEET_HEADERS)
        print(f"[INFO] Hoja '{BIBLIOTECA_NAME}' creada en el Sheet.")

    return ws


def push_snapshot(ws, snap: dict, cycle: int):
    """Escribe una fila con el snapshot actual al Sheet."""
    # Cada 50 ciclos (~25 minutos) verifica el tamaño para evitar crecimiento infinito
    if cycle % 50 == 0:
        try:
            num_rows = len(ws.col_values(1))
            if num_rows > 2000:
                print(f"  [INFO] Límite de filas alcanzado ({num_rows}). Purgando las más antiguas...")
                ws.delete_rows(2, 500)
        except Exception as e:
            print(f"  [WARN] No se pudo purgar filas: {e}")

    row = [snap.get(col, "") for col in SHEET_HEADERS]
    ws.append_row(row, value_input_option="USER_ENTERED")


# ─────────────────────────────────────────────
#  LOOP PRINCIPAL
# ─────────────────────────────────────────────

def main():
    print(f"+------------------------------------------+")
    print(f"|   UDEC Cyber-Auditor — Agente v3.0       |")
    print(f"|   Biblioteca : {BIBLIOTECA_NAME:<26}|")
    print(f"|   Intervalo  : {INTERVAL_SEC}s                          |")
    print(f"+------------------------------------------+")
    print()

    print("[INIT] Conectando a Google Sheets...")
    try:
        ws = connect_sheet()
        print(f"[OK]   Hoja '{BIBLIOTECA_NAME}' lista.")
    except FileNotFoundError:
        print(f"[ERR]  No se encontró '{CREDENTIALS_FILE}'. Descárgalo de Google Cloud Console.")
        return
    except Exception as e:
        print(f"[ERR]  No se pudo conectar al Sheet: {e}")
        return

    print("[OK]   Iniciando ciclo de medición...\n")

    cycle = 0
    while True:
        cycle += 1
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Ciclo #{cycle} - midiendo red...")
            snap = collect_snapshot()

            print(f"  > Estado    : {snap['status']}")
            print(f"  > Latencia  : {snap['latency_avg_ms']} ms (HTTP) | {snap['latency_icmp_ms']} ms (ICMP)")
            print(f"  > Perdida   : {snap['loss_pct']}%")
            print(f"  > IP local  : {snap['local_ip']}")

        except Exception as e:
            print(f"  [WARN] Error midiendo red: {type(e).__name__}: {str(e)[:80]}")

        # Escribir al Sheet en bloque separado para ver errores especificos
        try:
            push_snapshot(ws, snap, cycle)
            print(f"  OK Datos enviados al Sheet (ciclo #{cycle})\n")
        except Exception as e:
            print(f"  [ERROR] Fallo al escribir en Sheet: {type(e).__name__}: {str(e)[:120]}")
            print(f"  [INFO]  Reintentando reconexion al Sheet...")
            try:
                ws = connect_sheet()
                push_snapshot(ws, snap, cycle)
                print(f"  OK Reconexion exitosa y datos enviados\n")
            except Exception as e2:
                print(f"  [CRITICAL] No se pudo escribir: {str(e2)[:80]}\n")




if __name__ == "__main__":
    main()
