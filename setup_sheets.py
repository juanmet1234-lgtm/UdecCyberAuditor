#!/usr/bin/env python3
"""
Script para inicializar el Google Sheet con estructura y datos de prueba.
Ejecutar ANTES de los agentes.

Uso: python v3/setup_sheets.py

Este script:
1. Crea/limpia hojas para cada biblioteca
2. Agrega headers
3. Carga datos de prueba
"""

import sys
import os
import json
from datetime import datetime, timezone, timedelta
import time

# Agregar path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar configuración
from v3.MonitoreoTiempoReal.sheets_collector import (
    CREDENTIALS_FILE,
    SPREADSHEET_NAME,
    SCOPES,
    SHEET_HEADERS,
    POLL_INTERVAL_SEC,
)

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("ERROR: gspread no instalado. Ejecuta:")
    print("  pip install gspread google-auth")
    sys.exit(1)

# ─────────────────────────────────────────────
#  DATOS DE PRUEBA
# ─────────────────────────────────────────────

LIBRARIES = [
    {
        "name": "Biblioteca Chía",
        "local_ip": "192.168.100.10",
        "status": "STABLE",
        "latency_avg_ms": 45.3,
        "latency_icmp_ms": 32.1,
        "loss_pct": 0.0,
        "packets_sent": 20,
        "packets_lost": 0,
    },
    {
        "name": "Biblioteca Madrid",
        "local_ip": "192.168.101.20",
        "status": "WARNING",
        "latency_avg_ms": 180.5,
        "latency_icmp_ms": 120.3,
        "loss_pct": 5.0,
        "packets_sent": 20,
        "packets_lost": 1,
    },
    {
        "name": "Biblioteca Tabio",
        "local_ip": "192.168.102.30",
        "status": "STABLE",
        "latency_avg_ms": 65.2,
        "latency_icmp_ms": 48.5,
        "loss_pct": 0.0,
        "packets_sent": 20,
        "packets_lost": 0,
    },
]

TARGET_EXAMPLES = {
    "Google DNS": {"ok": True, "lat": 32.1, "code": 200},
    "Cloudflare": {"ok": True, "lat": 28.5, "code": 200},
    "Portal UDEC": {"ok": True, "lat": 85.3, "code": 200},
}


def setup_sheets():
    """Inicializa el Google Sheet con estructura y datos de prueba."""
    
    print("=" * 80)
    print("INICIALIZACIÓN DE GOOGLE SHEETS - UDEC Cyber-Auditor")
    print("=" * 80)
    print()
    
    # Validar credenciales
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ ERROR: {CREDENTIALS_FILE} no encontrado")
        print()
        print("Pasos para resolver:")
        print("1. Ve a Google Cloud Console: https://console.cloud.google.com")
        print("2. Crea una cuenta de servicio")
        print("3. Descarga el JSON de credenciales")
        print(f"4. Guárdalo en: {CREDENTIALS_FILE}")
        return False
    
    print("✅ credentials.json encontrado")
    
    # Conectar
    print("Conectando a Google Sheets...")
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        gc = gspread.authorize(creds)
        print("✅ Autenticación exitosa")
    except Exception as e:
        print(f"❌ Error de autenticación: {e}")
        return False
    
    # Abrir/crear spreadsheet
    try:
        sh = gc.open(SPREADSHEET_NAME)
        print(f"✅ Spreadsheet '{SPREADSHEET_NAME}' abierto")
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"❌ El spreadsheet '{SPREADSHEET_NAME}' no existe")
        print("   Créalo manualmente en Google Drive y comparte con la cuenta de servicio")
        return False
    except Exception as e:
        print(f"❌ Error abriendo spreadsheet: {e}")
        return False
    
    print()
    print("=" * 80)
    print("CONFIGURANDO HOJAS Y DATOS")
    print("=" * 80)
    print()
    
    # Limpiar hojas existentes (excepto la primera)
    worksheets = sh.worksheets()
    print(f"Hojas actuales: {len(worksheets)}")
    
    for ws in worksheets[1:]:
        print(f"  Eliminando hoja: {ws.title}")
        sh.del_worksheet(ws)
        time.sleep(0.5)
    
    # Renombrar/limpiar primera hoja
    if worksheets:
        ws_main = worksheets[0]
        if ws_main.title != "Índice":
            ws_main.update_title("Índice")
        ws_main.clear()
        print("✅ Hoja 'Índice' limpiada")
    
    # Crear hojas para cada biblioteca
    print()
    for idx, lib_data in enumerate(LIBRARIES, 1):
        lib_name = lib_data["name"]
        print(f"\n[{idx}/{len(LIBRARIES)}] Creando hoja para: {lib_name}...")
        
        # Crear hoja
        ws = sh.add_worksheet(title=lib_name, rows=200, cols=10)
        print(f"  ✅ Hoja creada")
        time.sleep(1)  # Esperar a que se sincronice
        
        # Headers
        ws.append_row(SHEET_HEADERS, table_range="A1")
        print(f"  ✅ Headers agregados: {SHEET_HEADERS}")
        time.sleep(1)
        
        # Generar 10 filas de datos de prueba (con timestamps variados)
        rows_to_add = []
        now = datetime.now(timezone.utc)
        
        for i in range(10, 0, -1):
            ts = (now - timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M:%S UTC")
            
            # Variar un poco las métricas para simular cambios
            lat_var = 1.0 + (i % 3) * 0.15
            icmp_var = 1.0 + ((i + 1) % 3) * 0.1
            loss_var = max(0, lib_data["loss_pct"] - (i % 2) * 2)
            
            row = [
                ts,                                                # timestamp
                lib_name,                                          # biblioteca
                lib_data["local_ip"],                              # local_ip
                lib_data["status"],                                # status
                str(lib_data["latency_avg_ms"] * lat_var),         # latency_avg_ms
                str(lib_data["latency_icmp_ms"] * icmp_var),       # latency_icmp_ms
                str(loss_var),                                     # loss_pct
                str(lib_data["packets_sent"]),                     # packets_sent
                str(lib_data["packets_lost"]),                     # packets_lost
                json.dumps(TARGET_EXAMPLES),                       # targets_json
            ]
            rows_to_add.append(row)
        
        # Agregar filas
        print(f"  Agregando {len(rows_to_add)} filas de datos...")
        ws.append_rows(rows_to_add, table_range="A2")
        print(f"  ✅ {len(rows_to_add)} filas de prueba agregadas")
        
        # Esperar para que Google Sheets sincronice
        print(f"  ⏳ Esperando sincronización (5 segundos)...")
        time.sleep(5)
        
        # Validar que los datos se escribieron
        print(f"  Validando datos...")
        try:
            all_data = ws.get_all_values()
            print(f"  ✅ Hoja confirmada: {len(all_data)} filas totales (headers + {len(all_data)-1} datos)")
            if len(all_data) > 1:
                print(f"     Primer dato: {all_data[1][:3]}...")
                print(f"     Último dato: {all_data[-1][:3]}...")
        except Exception as e:
            print(f"  ❌ Error validando: {e}")
    
    print()
    
    print()
    print("=" * 80)
    print("✅ INICIALIZACIÓN COMPLETADA")
    print("=" * 80)
    print()
    print("Próximos pasos:")
    print()
    print("1. Verifica que funciona:")
    print("   python v3/test_sheets_connection.py")
    print()
    print("2. Prueba el dashboard:")
    print("   streamlit run v3/app_streamlit.py")
    print()
    print("3. Para datos reales, corre agent.py en cada PC de biblioteca:")
    print("   python v3/MonitoreoTiempoReal/agent.py")
    print()
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    success = setup_sheets()
    sys.exit(0 if success else 1)
