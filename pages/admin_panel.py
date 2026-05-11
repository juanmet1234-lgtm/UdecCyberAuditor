from __future__ import annotations

import pandas as pd
import streamlit as st
from streamlit.errors import StreamlitAPIException

from v3.auth import (
    clear_login_history,
    create_user,
    delete_user,
    get_all_users,
    get_login_history,
    load_users,
    update_user,
)
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
    page_title="Panel Admin | CyberAuditor v3",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(get_full_css(), unsafe_allow_html=True)
st.markdown('<div class="scanlines"></div>', unsafe_allow_html=True)

load_users()

if not st.session_state.get("authenticated") or st.session_state.get("role") != "administrador":
    _safe_switch_page("app_streamlit.py", "..\\app_streamlit.py", "../app_streamlit.py")

if st.button("← Volver al dashboard", key="back_dashboard"):
    _safe_switch_page("app_streamlit.py", "..\\app_streamlit.py", "../app_streamlit.py")

st.markdown('<div class="cyber-section-title"><span>//</span> PANEL ADMIN</div>', unsafe_allow_html=True)

tab_users, tab_create, tab_hist = st.tabs([
    "👥 Gestión de Usuarios",
    "➕ Crear Usuario (Admin)",
    "📋 Historial de Accesos",
])

with tab_users:
    users = get_all_users()
    df = pd.DataFrame(users)
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)

    usernames = [u["username"] for u in users]
    selected = st.selectbox("Seleccionar usuario", options=usernames, index=0 if usernames else None)
    selected_row = next((u for u in users if u["username"] == selected), None)

    if selected_row:
        col_a, col_b = st.columns([1, 1])
        with col_a:
            new_name = st.text_input("Nombre", value=str(selected_row.get("display_name") or ""), key="edit_display_name")
            new_role = st.selectbox(
                "Rol",
                options=["usuario_comun", "bibliotecario", "administrador"],
                index=["usuario_comun", "bibliotecario", "administrador"].index(str(selected_row.get("role") or "usuario_comun")),
                key="edit_role",
            )
            new_active = st.checkbox("Activo", value=bool(selected_row.get("active", True)), key="edit_active")

            if st.button("GUARDAR CAMBIOS", key="btn_save_user", type="primary"):
                update_user(selected, role=new_role, display_name=new_name.strip(), active=new_active)
                st.rerun()

        with col_b:
            if st.button("DESACTIVAR/ACTIVAR", key="btn_toggle_active", type="secondary"):
                update_user(selected, active=not bool(selected_row.get("active", True)))
                st.rerun()

            disable_delete = selected == st.session_state.get("username")
            if st.button("ELIMINAR USUARIO", key="btn_delete_user", type="secondary", disabled=disable_delete):
                delete_user(selected)
                st.rerun()

with tab_create:
    with st.form("create_user_form", clear_on_submit=True):
        new_username = st.text_input("Username")
        new_display = st.text_input("Nombre completo")
        new_pwd = st.text_input("Contraseña temporal", type="password")
        new_role = st.selectbox("Rol", options=["usuario_comun", "bibliotecario", "administrador"])
        submit = st.form_submit_button("CREAR")

    if submit:
        u = new_username.strip()
        if not u or any(c.isspace() for c in u):
            st.error("Username inválido.")
        elif len(new_pwd) < 8:
            st.error("La contraseña debe tener mínimo 8 caracteres.")
        elif not new_display.strip():
            st.error("Nombre obligatorio.")
        else:
            try:
                create_user(u, new_pwd, new_role, new_display.strip())
                st.success("Usuario creado.")
            except ValueError as e:
                if str(e) == "username_exists":
                    st.error("Ese username ya existe.")
                else:
                    st.error("No se pudo crear el usuario.")

with tab_hist:
    events = get_login_history()
    usernames = sorted({str(e.get("username")) for e in events if isinstance(e, dict) and e.get("username")})
    user_filter = st.selectbox("Usuario", options=["(Todos)"] + usernames)
    result_filter = st.selectbox("Resultado", options=["(Todos)", "Éxito", "Fallo"])

    filtered = []
    for e in events:
        if not isinstance(e, dict):
            continue
        if user_filter != "(Todos)" and str(e.get("username")) != user_filter:
            continue
        if result_filter == "Éxito" and not bool(e.get("success")):
            continue
        if result_filter == "Fallo" and bool(e.get("success")):
            continue
        filtered.append(e)

    if filtered:
        df = pd.DataFrame(filtered)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No hay registros.")

    confirm = st.checkbox("Confirmar limpieza", value=False, key="confirm_clear_history")
    if st.button("LIMPIAR HISTORIAL", key="btn_clear_history", type="secondary", disabled=not confirm):
        clear_login_history()
        st.rerun()
