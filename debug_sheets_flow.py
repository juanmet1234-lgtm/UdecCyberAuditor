#!/usr/bin/env python3
"""
Script de diagnóstico completo para el flujo de Google Sheets.
Identifica exactamente dónde está el problema: envío, recepción o configuración.

Uso: python v3/debug_sheets_flow.py
"""

import sys
import os
import time
import json
from datetime import datetime, timezone

# Agregar path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_credentials():
    """Verifica que las credenciales existan y sean válidas."""
    print("=" * 70)
    print("1. VERIFICANDO CREDENCIALES")
    print("=" * 70)
    
    # Buscar credentials.json en múltiples ubicaciones
    possible_paths = [
        "credentials.json",
        "v3/credentials.json", 
        "v3/MonitoreoTiempoReal/credentials.json",
        os.path.join(os.path.dirname(__file__), "credentials.json"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "credentials.json")
    ]
    
    creds_path = None
    for path in possible_paths:
        if os.path.exists(path):
            creds_path = path
            break
    
    if not creds_path:
        print("❌ ERROR: No se encontró credentials.json")
        print("   Búsquedas en:")
        for path in possible_paths:
            print(f"   - {os.path.abspath(path)}")
        return None
    
    print(f"✅ Credenciales encontradas: {creds_path}")
    
    # Verificar contenido
    try:
        with open(creds_path, 'r') as f:
            creds_data = json.load(f)
        
        print(f"✅ JSON válido")
        print(f"   Project ID: {creds_data.get('project_id', 'N/A')}")
        print(f"   Client Email: {creds_data.get('client_email', 'N/A')}")
        
        # Verificar permisos específicos
        if 'udec-auditor-agent@udec-cyber-auditor.iam.gserviceaccount.com' in creds_data.get('client_email', ''):
            print("✅ Email coincide con la cuenta de servicio mencionada")
        else:
            print(f"⚠️  Email diferente: {creds_data.get('client_email')}")
        
        return creds_path
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON inválido: {e}")
        return None
    except Exception as e:
        print(f"❌ Error leyendo credenciales: {e}")
        return None

def test_connection(creds_path):
    """Prueba la conexión a Google Sheets."""
    print("\n" + "=" * 70)
    print("2. PROBANDO CONEXIÓN A GOOGLE SHEETS")
    print("=" * 70)
    
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError as e:
        print(f"❌ Dependencias faltantes: {e}")
        print("   Ejecuta: pip install gspread google-auth")
        return None
    
    # Configurar scopes
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    
    try:
        print("Autenticando...")
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        gc = gspread.authorize(creds)
        print("✅ Autenticación exitosa")
        
        # Listar spreadsheets disponibles
        print("\nListando spreadsheets accesibles...")
        spreadsheets = gc.list_spreadsheet_files()
        
        target_sheet = "UDEC-Cyber-Auditor"
        target_found = False
        
        for sheet in spreadsheets[:5]:  # Mostrar primeros 5
            sheet_name = sheet.get('name', 'N/A')
            sheet_id = sheet.get('id', 'N/A')
            
            if sheet_name == target_sheet:
                print(f"✅ ENCONTRADO: {sheet_name} (ID: {sheet_id})")
                target_found = True
            else:
                print(f"   Disponible: {sheet_name} (ID: {sheet_id})")
        
        if not target_found:
            print(f"\n❌ ERROR: No se encontró el spreadsheet '{target_sheet}'")
            print("   Soluciones:")
            print("   1. Crea el spreadsheet en Google Drive")
            print("   2. Comparte con la cuenta de servicio:")
            print(f"      udec-auditor-agent@udec-cyber-auditor.iam.gserviceaccount.com")
            print("   3. Con permisos de 'Editor'")
            return None
        
        # Abrir el spreadsheet
        print(f"\nAbriendo spreadsheet '{target_sheet}'...")
        sh = gc.open(target_sheet)
        print(f"✅ Spreadsheet abierto")
        
        # Listar hojas
        worksheets = sh.worksheets()
        print(f"Hojas encontradas: {len(worksheets)}")
        for ws in worksheets:
            print(f"   - {ws.title} ({len(ws.get_all_values())} filas)")
        
        return sh
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

def test_read_data(sh):
    """Prueba leer datos del spreadsheet."""
    print("\n" + "=" * 70)
    print("3. LEYENDO DATOS ACTUALES")
    print("=" * 70)
    
    try:
        worksheets = sh.worksheets()
        
        if not worksheets:
            print("❌ No hay hojas en el spreadsheet")
            return False
        
        total_data = 0
        for ws in worksheets:
            try:
                data = ws.get_all_values()
                print(f"\nHoja: {ws.title}")
                print(f"   Filas totales: {len(data)}")
                
                if len(data) > 1:
                    print(f"   Headers: {data[0][:5]}...")
                    print(f"   Última fila: {data[-1][:3]}...")
                    
                    # Buscar timestamp en última fila
                    if len(data[-1]) > 0:
                        last_timestamp = data[-1][0]
                        print(f"   Último timestamp: {last_timestamp}")
                    
                    total_data += len(data) - 1  # Excluir headers
                else:
                    print("   ⚠️  Hoja vacía (solo headers o sin datos)")
                    
            except Exception as e:
                print(f"   ❌ Error leyendo hoja {ws.title}: {e}")
        
        print(f"\n📊 Total de filas de datos: {total_data}")
        
        if total_data == 0:
            print("❌ PROBLEMA IDENTIFICADO: No hay datos en ninguna hoja")
            print("\n   Posibles causas:")
            print("   1. El agent.py no está corriendo")
            print("   2. El agent.py tiene errores pero no los muestra")
            print("   3. El agent.py está escribiendo en otro spreadsheet")
            print("   4. Problemas de permisos de escritura")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error leyendo datos: {e}")
        return False

def test_write_data(sh):
    """Prueba escribir datos de prueba."""
    print("\n" + "=" * 70)
    print("4. PROBANDO ESCRITURA DE DATOS")
    print("=" * 70)
    
    try:
        # Buscar hoja de prueba o crearla
        test_sheet_name = "DEBUG_TEST"
        
        try:
            ws = sh.worksheet(test_sheet_name)
            print(f"Usando hoja existente: {test_sheet_name}")
        except:
            ws = sh.add_worksheet(title=test_sheet_name, rows=100, cols=10)
            print(f"Creada hoja de prueba: {test_sheet_name}")
        
        # Headers
        headers = ["timestamp", "biblioteca", "local_ip", "status", "latency_avg_ms", "test"]
        ws.append_row(headers)
        print("✅ Headers agregados")
        
        # Escribir fila de prueba
        test_row = [
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "TEST_BIBLIOTECA",
            "192.168.1.100",
            "STABLE",
            "45.5",
            "DEBUG_DATA"
        ]
        
        print("Escribiendo fila de prueba...")
        ws.append_row(test_row, value_input_option="USER_ENTERED")
        print("✅ Fila de prueba escrita")
        
        # Verificar que se escribió
        time.sleep(1)
        data = ws.get_all_values()
        print(f"✅ Verificado: {len(data)} filas totales")
        print(f"   Última fila: {data[-1]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error escribiendo datos: {e}")
        print("   Esto indica un problema de permisos de escritura")
        return False

def main():
    """Función principal de diagnóstico."""
    print("UDEC CYBER-AUDITOR - DIAGNÓSTICO COMPLETO GOOGLE SHEETS")
    print("=" * 70)
    
    # Paso 1: Verificar credenciales
    creds_path = check_credentials()
    if not creds_path:
        return False
    
    # Paso 2: Probar conexión
    sh = test_connection(creds_path)
    if not sh:
        return False
    
    # Paso 3: Leer datos existentes
    has_data = test_read_data(sh)
    
    # Paso 4: Probar escritura
    can_write = test_write_data(sh)
    
    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN DEL DIAGNÓSTICO")
    print("=" * 70)
    
    print(f"✅ Credenciales: VÁLIDAS")
    print(f"✅ Conexión: FUNCIONA")
    print(f"{'✅' if has_data else '❌'} Datos existentes: {'HAY DATOS' if has_data else 'NO HAY DATOS'}")
    print(f"{'✅' if can_write else '❌'} Escritura: {'FUNCIONA' if can_write else 'NO FUNCIONA'}")
    
    if not has_data and can_write:
        print("\n🔍 DIAGNÓSTICO: El problema está en el agent.py")
        print("   - La conexión y permisos funcionan")
        print("   - Pero no hay datos, así que el agent.py no está escribiendo")
        print("\n   Soluciones:")
        print("   1. Verifica que agent.py esté corriendo sin errores")
        print("   2. Revisa el nombre BIBLIOTECA_NAME en agent.py")
        print("   3. Ejecuta agent.py con logging detallado")
        
    elif has_data and not can_write:
        print("\n🔍 DIAGNÓSTICO: Problema de permisos de escritura")
        print("   - Hay datos históricos pero no se puede escribir")
        print("   - Revisa permisos de la cuenta de servicio")
        
    elif not has_data and not can_write:
        print("\n🔍 DIAGNÓSTICO: Problema de permisos general")
        print("   - No hay datos y no se puede escribir")
        print("   - Revisa configuración de compartir el spreadsheet")
        
    else:
        print("\n✅ TODO FUNCIONA CORRECTAMENTE")
    
    return has_data and can_write

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
