# UDEC Cyber-Auditor v3 - Guía de Deploy en Streamlit Cloud

## Resumen

Esta guía te ayudará a subir tu dashboard a **Streamlit Cloud** (gratuito) de forma segura, sin exponer tus credenciales de Google.

---

## Arquitectura de Deploy

```
┌─────────────────────────────────────────────────────────────┐
│  AGENTES EN BIBLIOTECAS (PCs locales)                      │
│  └─► Envían datos a Google Sheets (sin cambios)             │
├─────────────────────────────────────────────────────────────┤
│  GOOGLE SHEETS "UDEC-Cyber-Auditor"                         │
│  └─► Backend de datos (sin cambios)                        │
├─────────────────────────────────────────────────────────────┤
│  STREAMLIT CLOUD (Dashboard Web)                            │
│  └─► Lee desde Sheets usando Secrets                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Paso 1: Preparar el Repositorio

### 1.1 Verifica que los archivos estén correctos

Después de las modificaciones automáticas, verifica que estos archivos tengan soporte para `st.secrets`:

- ✅ `v3/MonitoreoTiempoReal/sheets_collector.py` - Función `get_credentials()` agregada
- ✅ `v3/app_streamlit.py` - Usa `st.secrets` como primera opción

### 1.2 Crea un repositorio en GitHub

```bash
# Inicializar repositorio (si no lo tienes)
git init

# Agregar archivos (EXCEPTO credenciales)
git add v3/app_streamlit.py
git add v3/MonitoreoTiempoReal/sheets_collector.py
git add v3/data_bridge.py
git add v3/gauges.py
git add v3/styles.py
git add v3/auth.py
git add v3/requirements.txt
git add .streamlit/secrets.toml  # Este es solo un template, está bien subirlo

# NOTA: NO agregar credentials.json
git add .gitignore  # Asegúrate de ignorar *.json

git commit -m "Preparado para deploy en Streamlit Cloud"

# Conectar con GitHub y subir
git remote add origin https://github.com/TU_USUARIO/udec-cyber-auditor.git
git push -u origin main
```

### 1.3 Verifica tu .gitignore

Asegúrate de tener esto en tu `.gitignore`:

```
# Credenciales
*.json
credentials.json
v3/credentials.json
v3/MonitoreoTiempoReal/credentials.json

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Entornos virtuales
venv/
env/
ENV/

# IDEs
.vscode/
.idea/

# Archivos temporales
*.log
*.tmp
```

---

## Paso 2: Configurar Secrets en Streamlit Cloud

### 2.1 Ir a Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Inicia sesión con tu cuenta de GitHub
3. Click en **"New app"**

### 2.2 Conectar el Repositorio

- **Repository**: `TU_USUARIO/udec-cyber-auditor`
- **Branch**: `main` (o `master`)
- **Main file path**: `v3/app_streamlit.py`

### 2.3 Configurar Secrets (IMPORTANTE)

Antes de hacer deploy, configura los secrets:

1. Ve a la sección **"Settings"** (⚙️) de tu app
2. Click en **"Secrets"**
3. Pega el contenido de tu `credentials.json` en este formato:

```toml
[gcp_service_account]
type = "service_account"
project_id = "udec-cyber-auditor"
private_key_id = "TU_PRIVATE_KEY_ID"
private_key = """
-----BEGIN PRIVATE KEY-----
TU_PRIVATE_KEY_AQUI_MULTILINEA
...
-----END PRIVATE KEY-----
"""
client_email = "udec-auditor-agent@udec-cyber-auditor.iam.gserviceaccount.com"
client_id = "TU_CLIENT_ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/udec-auditor-agent%40udec-cyber-auditor.iam.gserviceaccount.com"
universe_domain = "googleapis.com"
```

**⚠️ IMPORTANTE**: El `private_key` debe estar entre triple comillas `"""` porque es multilinea.

### 2.4 Deploy

Click en **"Deploy"** y espera a que se construya.

---

## Paso 3: Verificar el Funcionamiento

### 3.1 Ver logs

En Streamlit Cloud, ve a **"Manage app"** > **"Logs"** para ver:
- ✅ "Usando credenciales desde st.secrets" (confirma que está leyendo secrets)
- ✅ "Conexión a Google Sheets establecida"
- ✅ "Fetch completado: X bibliotecas actualizadas"

### 3.2 Probar localmente (opcional)

Si quieres probar localmente con secrets:

```bash
# Crear archivo .streamlit/secrets.toml con tus credenciales
# Luego ejecutar:
streamlit run v3/app_streamlit.py
```

O si prefieres usar `credentials.json` local:

```bash
# Solo asegúrate de tener credentials.json en la carpeta v3/
streamlit run v3/app_streamlit.py
```

---

## Troubleshooting

| Problema | Solución |
|----------|----------|
| "No se encontraron credenciales" | Verifica que `st.secrets` esté configurado en Streamlit Cloud |
| "SpreadsheetNotFound" | Verifica que el Sheet esté compartido con el `client_email` de la cuenta de servicio |
| "APIError: 403" | La cuenta de servicio no tiene permisos. Ve al Sheet > Compartir > Agrega el email |
| Datos no aparecen | Verifica que los agentes en bibliotecas estén corriendo y enviando datos |
| App se "duerme" en Streamlit Cloud | Esto es normal en el tier gratuito. Se reactiva automáticamente al recibir tráfico. |

---

## Estructura Final del Proyecto

```
udec-cyber-auditor/
├── .streamlit/
│   └── secrets.toml          # Template (sin credenciales reales)
├── v3/
│   ├── app_streamlit.py      # ✅ Modificado para st.secrets
│   ├── data_bridge.py        # Sin cambios
│   ├── gauges.py             # Sin cambios
│   ├── styles.py             # Sin cambios
│   ├── auth.py               # Sin cambios
│   ├── requirements.txt      # Sin cambios
│   └── MonitoreoTiempoReal/
│       ├── sheets_collector.py  # ✅ Modificado para st.secrets
│       └── agent.py            # Sin cambios (solo corre en PCs locales)
├── .gitignore
└── README_DEPLOY.md          # Este archivo
```

---

## Recursos

- [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-community-cloud)
- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Google Service Account Credentials](https://developers.google.com/workspace/guides/create-credentials#service-account)

---

## Notas de Seguridad

✅ **Seguro**: Las credenciales están en `st.secrets`, encriptadas y nunca expuestas en el código  
✅ **Seguro**: El archivo `credentials.json` NUNCA se sube a GitHub  
✅ **Seguro**: Las credenciales solo se usan server-side, los usuarios nunca las ven  

---

**¿Preguntas?** Revisa los logs de Streamlit Cloud primero — allí está la información más útil para diagnosticar problemas.
