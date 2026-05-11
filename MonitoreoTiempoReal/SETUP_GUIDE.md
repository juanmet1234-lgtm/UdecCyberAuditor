# UDEC Cyber-Auditor v3 — Guía de Configuración Google Sheets
## Para el módulo de Monitoreo de Bibliotecas

---

## PASO 1 — Crear proyecto en Google Cloud Console

1. Ve a https://console.cloud.google.com/
2. Crea un nuevo proyecto: `udec-cyber-auditor`
3. En el menú lateral: **APIs y servicios → Biblioteca**
4. Busca y activa:
   - ✅ **Google Sheets API**
   - ✅ **Google Drive API**

---

## PASO 2 — Crear cuenta de servicio

1. Ve a **APIs y servicios → Credenciales**
2. Click en **+ Crear credenciales → Cuenta de servicio**
3. Nombre: `udec-auditor-agent`
4. Rol: **Editor** (o "Usuario de Hojas de cálculo de Google")
5. Click en la cuenta creada → pestaña **Claves**
6. **Agregar clave → Crear clave nueva → JSON**
7. Se descarga `credentials.json` → **cópialo a la carpeta del proyecto**

---

## PASO 3 — Crear el Google Sheet

1. Ve a https://sheets.google.com
2. Crea una hoja nueva llamada exactamente: `UDEC-Cyber-Auditor`
3. Abre el archivo `credentials.json` y copia el campo `client_email`
   - Ejemplo: `udec-auditor-agent@udec-cyber-auditor.iam.gserviceaccount.com`
4. En el Sheet: **Compartir** → pega ese email → rol **Editor** → Listo

---

## PASO 4 — Instalar dependencias

En la PC donde corre Streamlit y en cada PC de biblioteca:

```bash
pip install gspread google-auth requests
```

---

## PASO 5 — Configurar agent.py en cada biblioteca

Edita estas líneas en `agent.py`:

```python
BIBLIOTECA_NAME  = "Biblioteca Chía"      # ← Nombre único por sede
CREDENTIALS_FILE = "credentials.json"     # ← Ruta al archivo descargado
SPREADSHEET_NAME = "UDEC-Cyber-Auditor"   # ← Debe coincidir con el Sheet
INTERVAL_SEC     = 15                     # ← Cada cuántos segundos enviar
```

Para la segunda biblioteca, cambia solo:
```python
BIBLIOTECA_NAME = "Biblioteca Cajicá"
```

---

## PASO 6 — Correr el agente

```bash
# En cada PC de biblioteca
python agent.py
```

Deberías ver:
```
╔══════════════════════════════════════════╗
║   UDEC Cyber-Auditor — Agente v3.0       ║
║   Biblioteca : Biblioteca Chía           ║
╚══════════════════════════════════════════╝
[INIT] Conectando a Google Sheets...
[OK]   Hoja 'Biblioteca Chía' lista.
[OK]   Iniciando ciclo de medición...

[14:32:01] Ciclo #1 — midiendo red...
  ▶ Estado    : STABLE
  ▶ Latencia  : 45.2 ms (HTTP) | 12.0 ms (ICMP)
  ▶ Pérdida   : 0.0%
  ✓ Datos enviados al Sheet
```

---

## PASO 7 — Integrar en app_streamlit.py

1. Copia `sheets_collector.py` a la carpeta `v3/`
2. Agrega el import al inicio de `app_streamlit.py`:
   ```python
   from sheets_collector import get_or_create_collector, stop_collector, \
       status_color, status_icon, overall_status, POLL_INTERVAL_SEC, SPREADSHEET_NAME
   ```
3. Agrega `"📚 Bibliotecas"` a tu lista de `st.tabs()`
4. Copia el bloque `with tab4:` desde `tab_bibliotecas.py`

---

## Estructura final del proyecto

```
v3/
├── app_streamlit.py       ← Modificado (nuevo tab)
├── data_bridge.py         ← Sin cambios
├── gauges.py              ← Sin cambios
├── styles.py              ← Sin cambios
├── sheets_collector.py    ← NUEVO
├── credentials.json       ← NUEVO (no subir a git)
└── requirements.txt       ← Agregar: gspread>=5.0 google-auth>=2.0
```

## .gitignore — Importante

Agrega esto para no subir credenciales:
```
credentials.json
*.json
```

---

## Troubleshooting

| Error | Causa | Solución |
|-------|-------|----------|
| `FileNotFoundError: credentials.json` | Archivo no está en la carpeta | Cópialo junto a agent.py |
| `gspread.exceptions.SpreadsheetNotFound` | Nombre del Sheet incorrecto | Verifica que sea exactamente `UDEC-Cyber-Auditor` |
| `gspread.exceptions.APIError: 403` | Sheet no compartido | Compártelo con el `client_email` de credentials.json |
| `ModuleNotFoundError: gspread` | Dependencias no instaladas | `pip install gspread google-auth` |
| Datos no aparecen en Streamlit | Agente no corre | Verifica que `agent.py` esté corriendo en la biblioteca |
