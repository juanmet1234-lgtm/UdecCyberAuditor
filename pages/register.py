from __future__ import annotations

import streamlit as st
from streamlit.errors import StreamlitAPIException
import sys
import os

# Detectar estructura (raíz para Streamlit Cloud o v3/ para desarrollo local)
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if _CURRENT_DIR.endswith('pages'):
    _ROOT = os.path.dirname(_CURRENT_DIR)
else:
    _ROOT = _CURRENT_DIR

if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Importar según estructura
try:
    from auth import create_user, load_users
    from styles import get_full_css
except ImportError:
    from v3.auth import create_user, load_users
    from v3.styles import get_full_css


def _safe_switch_page(*candidates: str) -> None:
    last_err: Exception | None = None
    for p in candidates:
        try:
            st.switch_page(p)
            return
        except StreamlitAPIException as e:
            last_err = e
        except Exception as e:
            last_err = e
    if last_err:
        st.error("No se encontró la página solicitada. Reinicia Streamlit si cambiaste pages/.")


st.set_page_config(
    page_title="Registro | CyberAuditor v3",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(get_full_css(), unsafe_allow_html=True)
st.markdown('<div class="scanlines"></div>', unsafe_allow_html=True)

load_users()

if st.button("← Volver al login", key="back_login"):
    _safe_switch_page("app_streamlit.py", "..\\app_streamlit.py", "../app_streamlit.py")

st.markdown('<div class="cyber-section-title"><span>//</span> CREAR CUENTA</div>', unsafe_allow_html=True)

with st.form("register_form", clear_on_submit=False):
    username = st.text_input("Username")
    display_name = st.text_input("Nombre completo")
    pwd1 = st.text_input("Contraseña", type="password")
    pwd2 = st.text_input("Confirmar contraseña", type="password")
    submit = st.form_submit_button("REGISTRAR")

if submit:
    u = username.strip()
    if not u:
        st.error("Username obligatorio.")
    elif any(c.isspace() for c in u):
        st.error("El username no puede contener espacios.")
    elif len(pwd1) < 8:
        st.error("La contraseña debe tener mínimo 8 caracteres.")
    elif pwd1 != pwd2:
        st.error("Las contraseñas no coinciden.")
    elif not display_name.strip():
        st.error("El nombre completo es obligatorio.")
    else:
        try:
            create_user(u, pwd1, "usuario_comun", display_name.strip())
            st.success("Cuenta creada correctamente.")
            if st.button("[ VOLVER AL LOGIN ]", key="btn_return_login"):
                _safe_switch_page("app_streamlit.py", "..\\app_streamlit.py", "../app_streamlit.py")
        except ValueError as e:
            if str(e) == "username_exists":
                st.error("Ese username ya existe.")
            else:
                st.error("No se pudo crear la cuenta.")
