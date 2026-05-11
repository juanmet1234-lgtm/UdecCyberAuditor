import sys
import os
import time
import logging

# Agregar path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar logging a DEBUG para ver todo
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')

from v3.MonitoreoTiempoReal.sheets_collector import get_or_create_collector, LibrariesCollector
from datetime import datetime

def test_sheets_connection():
    """Prueba conexión a Google Sheets y muestra datos."""
    
    print("=" * 70)
    print("PRUEBA DE CONEXIÓN A GOOGLE SHEETS - UDEC Cyber-Auditor")
    print("=" * 70)
    print()
    
    # Crear instancia del collector
    print("1. Creando collector...")
    collector = LibrariesCollector()
    
    # Iniciar
    print("2. Iniciando conexión (primer fetch)...")
    collector.start()
    
    # Esperar un poco para que haga el fetch inicial
    time.sleep(3)
    
    # Obtener reporte
    report = collector.get_report()
    
    print()
    print("RESULTADOS:")
    print("-" * 70)
    
    if report.error:
        print(f"❌ ERROR: {report.error}")
        print()
        print("Posibles soluciones:")
        print("1. Verifica que credentials.json esté en el directorio v3/")
        print("2. Verifica que la cuenta de servicio tenga acceso al Sheet:")
        print('   "UDEC-Cyber-Auditor"')
        print("3. Instala las dependencias: pip install gspread google-auth")
        return False
    
    if not report.snapshots:
        print("⚠️  No se encontraron datos en el Sheet")
        print("   - Verifica que agent.py esté escribiendo en el Sheet")
        print("   - Verifica que las hojas del Sheet no estén vacías")
        return False
    
    print(f"✅ Conexión exitosa!")
    print(f"   Última actualización: {datetime.fromtimestamp(report.last_update).strftime('%H:%M:%S')}")
    print()
    print(f"📚 Bibliotecas encontradas: {len(report.snapshots)}")
    print("-" * 70)
    
    for lib_name, snap in report.snapshots.items():
        status_icon = {
            "STABLE": "✓",
            "WARNING": "⚠",
            "CRITICAL": "✗",
            "UNKNOWN": "?"
        }.get(snap.status, "?")
        
        online_status = "EN LÍNEA" if snap.online else "FUERA DE LÍNEA"
        
        print(f"\n  {status_icon} {lib_name}")
        print(f"     Estado: {snap.status} | {online_status}")
        print(f"     Latencia HTTP: {snap.latency_avg_ms:.1f} ms")
        print(f"     Latencia ICMP: {snap.latency_icmp_ms:.1f} ms")
        print(f"     Pérdida: {snap.loss_pct:.1f}%")
        print(f"     IP Local: {snap.local_ip}")
        print(f"     Timestamp: {snap.timestamp}")
        if snap.targets:
            print(f"     Targets: {len(snap.targets)} monitoreados")
    
    print()
    print("=" * 70)
    print("PRUEBA: Esperando 35 segundos para verificar actualización...")
    print("=" * 70)
    
    old_update = report.last_update
    
    for i in range(35):
        time.sleep(1)
        print(f"\r[{i+1}/35 seg] Esperando actualización...", end="", flush=True)
    
    print()
    print()
    
    # Obtener nuevo reporte
    report = collector.get_report()
    new_update = report.last_update
    
    if new_update > old_update:
        print("✅ ¡ACTUALIZACIÓN EXITOSA!")
        print(f"   Tiempo de actualización anterior: {datetime.fromtimestamp(old_update).strftime('%H:%M:%S')}")
        print(f"   Tiempo de actualización actual:   {datetime.fromtimestamp(new_update).strftime('%H:%M:%S')}")
    else:
        print("❌ NO se actualizaron los datos")
        print(f"   Último update: {datetime.fromtimestamp(report.last_update).strftime('%H:%M:%S')}")
        if report.error:
            print(f"   Error: {report.error}")
    
    # Detener
    collector.stop()
    
    print()
    print("=" * 70)
    print("Prueba completada")
    print("=" * 70)
    
    return new_update > old_update


if __name__ == "__main__":
    success = test_sheets_connection()
    sys.exit(0 if success else 1)
