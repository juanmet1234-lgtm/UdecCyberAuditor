# v3/app_streamlit.py
# ─────────────────────────────────────────────────────────────────────────────
# UDEC Cyber-Auditor v3 | Streamlit Dashboard – Cyberpunk Edition
# Ejecutar: streamlit run v3/app_streamlit.py
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations
import sys, os, time, math, random
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from streamlit.errors import StreamlitAPIException

# ── Path ─────────────────────────────────────────────────────────────────────
# Detectar si estamos en desarrollo local (carpeta v3/) o en Streamlit Cloud (raíz)
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if _CURRENT_DIR.endswith('v3'):
    # Desarrollo local: subir un nivel
    _ROOT = os.path.dirname(_CURRENT_DIR)
else:
    # Streamlit Cloud: ya estamos en la raíz
    _ROOT = _CURRENT_DIR

if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Importar según estructura
try:
    from styles import get_full_css
    from auth import authenticate, load_users
    from data_bridge import (
        get_or_create_prober,
        run_ping_diagnosis,
        CORE_AVAILABLE,
    )
    from gauges import render_gauge_row
    from MonitoreoTiempoReal.sheets_collector import (
        get_or_create_collector,
        status_color,
        status_icon,
        overall_status,
        POLL_INTERVAL_SEC,
        SPREADSHEET_NAME,
    )
except ImportError:
    # Fallback para desarrollo local con estructura v3/
    from v3.styles import get_full_css
    from v3.auth import authenticate, load_users
    from v3.data_bridge import (
        get_or_create_prober,
        run_ping_diagnosis,
        CORE_AVAILABLE,
    )
    from v3.gauges import render_gauge_row
    from v3.MonitoreoTiempoReal.sheets_collector import (
        get_or_create_collector,
        status_color,
        status_icon,
        overall_status,
        POLL_INTERVAL_SEC,
        SPREADSHEET_NAME,
    )

# ── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="UDEC Cyber-Auditor v3",
    page_icon=" 🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inyección CSS completa ────────────────────────────────────────────────────
st.markdown(get_full_css(), unsafe_allow_html=True)

# ── Efecto scanlines ──────────────────────────────────────────────────────────
st.markdown('<div class="scanlines"></div>', unsafe_allow_html=True)

# ── Partículas flotantes azules ────────────────────────────────────────────────
particles_html = """
<div class="cyber-particles">
    <div class="particle" style="left: 10%; animation-delay: 0s;"></div>
    <div class="particle" style="left: 20%; animation-delay: 1s;"></div>
    <div class="particle" style="left: 30%; animation-delay: 2s;"></div>
    <div class="particle" style="left: 40%; animation-delay: 3s;"></div>
    <div class="particle" style="left: 50%; animation-delay: 4s;"></div>
    <div class="particle" style="left: 60%; animation-delay: 5s;"></div>
    <div class="particle" style="left: 70%; animation-delay: 6s;"></div>
    <div class="particle" style="left: 80%; animation-delay: 7s;"></div>
    <div class="particle" style="left: 90%; animation-delay: 8s;"></div>
    <div class="particle" style="left: 15%; animation-delay: 2.5s;"></div>
    <div class="particle" style="left: 25%; animation-delay: 3.5s;"></div>
    <div class="particle" style="left: 35%; animation-delay: 4.5s;"></div>
    <div class="particle" style="left: 45%; animation-delay: 5.5s;"></div>
    <div class="particle" style="left: 55%; animation-delay: 6.5s;"></div>
    <div class="particle" style="left: 65%; animation-delay: 7.5s;"></div>
    <div class="particle" style="left: 75%; animation-delay: 8.5s;"></div>
    <div class="particle" style="left: 85%; animation-delay: 9.5s;"></div>
    <div class="particle" style="left: 5%; animation-delay: 1.5s;"></div>
    <div class="particle" style="left: 95%; animation-delay: 0.5s;"></div>
</div>
"""
st.markdown(particles_html, unsafe_allow_html=True)

MATRIX_RAIN_HTML = """
<div class="matrix-rain-container matrix-rain-left">
    <div class="matrix-drop">ア<br>イ<br>ウ<br>エ<br>オ<br>カ<br>キ<br>ク<br>ケ<br>コ</div>
    <div class="matrix-drop">サ<br>シ<br>ス<br>セ<br>ソ<br>タ<br>チ<br>ツ<br>テ<br>ト</div>
    <div class="matrix-drop">ナ<br>ニ<br>ヌ<br>ネ<br>ノ<br>ハ<br>ヒ<br>フ<br>ヘ<br>ホ</div>
</div>
<div class="matrix-rain-container matrix-rain-right">
    <div class="matrix-drop">マ<br>ミ<br>ム<br>メ<br>モ<br>ヤ<br>ユ<br>ヨ<br>ラ<br>リ</div>
    <div class="matrix-drop">ル<br>レ<br>ロ<br>ワ<br>ヲ<br>ン<br>ガ<br>ギ<br>グ<br>ゲ</div>
    <div class="matrix-drop">ゴ<br>ザ<br>ジ<br>ズ<br>ゼ<br>ゾ<br>ダ<br>ヂ<br>ヅ<br>デ</div>
</div>
"""

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
        st.error(
            "No se encontró la página solicitada. Si acabas de crear/editar archivos en pages/, reinicia Streamlit."
        )

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state.get("authenticated"):
    load_users()
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
        [data-testid="stForm"] {
            max-width: 440px;
            margin: 0 auto;
            padding: 1.6rem 1.4rem;
            background: linear-gradient(135deg, rgba(13, 17, 23, 0.85) 0%, rgba(17, 24, 39, 0.75) 100%);
            border: 1px solid rgba(0, 242, 255, 0.35);
            border-top: 3px solid #00f2ff;
            border-radius: 10px;
            box-shadow: 0 0 45px rgba(0, 242, 255, 0.12), inset 0 0 18px rgba(0, 242, 255, 0.05);
            backdrop-filter: blur(8px);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, col_login, _ = st.columns([1, 1.25, 1])
    with col_login:
        st.markdown(
            """
            <div style="text-align:center;margin:2.2rem 0 1.1rem;">
                <div class="sb-logo-title active">🛡 UDEC<br>CYBER-AUDITOR</div>
                <div class="sb-logo-sub" style="margin-top:0.5rem;letter-spacing:0.18em;">v3.0 · STREAMLIT EDITION</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="cyber-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="cyber-section-title"><span>//</span> INICIAR SESIÓN</div>',
            unsafe_allow_html=True,
        )

        with st.form("login_form", clear_on_submit=False):
            u = st.text_input("Usuario", key="login_username")
            p = st.text_input("Contraseña", type="password", key="login_password")
            ok = st.form_submit_button("INICIAR SESIÓN")

        if ok:
            user = authenticate(u.strip(), p)
            if user:
                st.session_state["authenticated"] = True
                st.session_state["username"] = user["username"]
                st.session_state["role"] = user["role"]
                st.session_state["display_name"] = user["display_name"]
                st.rerun()
            else:
                st.error("Credenciales incorrectas.")

        if st.button(
            "CREAR CUENTA",
            key="btn_create_account",
            type="secondary",
            use_container_width=True,
        ):
            _safe_switch_page("pages/register.py", "pages\\register.py")

    st.stop()

if "cfg_target" not in st.session_state:
    st.session_state["cfg_target"] = "portal.udec.edu.co"

if "cfg_mode" not in st.session_state:
    st.session_state["cfg_mode"] = "Simulación"

if "cfg_refresh_rate" not in st.session_state:
    st.session_state["cfg_refresh_rate"] = "1.0s"

interval_opts = {"0.5s": 0.5, "1.0s": 1.0, "2.0s": 2.0, "3.0s": 3.0, "Pausado": None}
target = str(st.session_state.get("cfg_target") or "portal.udec.edu.co")
mode = str(st.session_state.get("cfg_mode") or "Simulación")
mode_key = "sim" if mode == "Simulación" else "live"
selected_interval = str(st.session_state.get("cfg_refresh_rate") or "1.0s")
refresh_delay = interval_opts.get(selected_interval, 1.0)

# ─────────────────────────────────────────────────────────────────────────────
# ESTADO GLOBAL Y SINCRONIZACIÓN
# ─────────────────────────────────────────────────────────────────────────────
if "_prober_instance" in st.session_state and st.session_state["_prober_instance"] is not None:
    # Consulta el estado REAL del hilo en el backend
    actual_running = getattr(st.session_state["_prober_instance"], "_running", False)
    st.session_state["monitoring_active"] = actual_running

if "monitoring_active" not in st.session_state:
    st.session_state["monitoring_active"] = False

is_active = st.session_state["monitoring_active"]

# Limpieza de hilos zombis si el estado es inactivo
if not is_active and st.session_state.get("_prober_instance") is not None:
    try:
        st.session_state["_prober_instance"].stop()
    except Exception:
        pass
    st.session_state["_prober_instance"] = None
    st.session_state["_prober_config"] = None

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    logo_class = "sb-logo-title active" if is_active else "sb-logo-title"
    st.markdown(f"""
    <div class="sb-logo">
        <div class="{logo_class}">🛡 UDEC<br>CYBER-AUDITOR</div>
        <div class="sb-logo-sub">v3.0 · STREAMLIT EDITION</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    sb_display_name = st.session_state.get("display_name", "")
    sb_role = str(st.session_state.get("role", "")).upper()
    sb_username = st.session_state.get("username", "")
    st.markdown(f"""
    <div style="border:1px solid rgba(0,242,255,0.25);background:rgba(0,242,255,0.04);
                border-radius:6px;padding:0.7rem;margin-bottom:0.8rem;">
        <div style="font-family:'Share Tech Mono',monospace;color:#00f2ff;letter-spacing:0.12em;">
            👤 {sb_display_name}
        </div>
        <div style="font-family:'Roboto Mono',monospace;font-size:0.72rem;color:#4a6080;letter-spacing:0.1em;margin-top:4px;">
            ROL: <span style="color:#00f2ff;">{sb_role}</span><br>
            USER: <span style="color:#00f2ff;">{sb_username}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.get("role") == "administrador":
        if st.button("⚙ PANEL ADMIN", key="btn_open_admin_panel", type="primary"):
            _safe_switch_page("pages/admin_panel.py", "pages\\admin_panel.py")

    if st.button("⏻ CERRAR SESIÓN", key="btn_logout", type="secondary"):
        for k in ("authenticated", "username", "role", "display_name"):
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

    # Estado del núcleo
    core_status = "🟢 CORE LIVE" if CORE_AVAILABLE else "🟡 SIM MODE"
    st.markdown(f"""
    <div style="text-align:center;font-family:'Roboto Mono',monospace;
                font-size:0.72rem;letter-spacing:0.12em;
                color:{'#00ff41' if CORE_AVAILABLE else '#ffb300'};
                text-shadow:0 0 8px {'#00ff4188' if CORE_AVAILABLE else '#ffb30088'};
                margin-bottom:1rem;">
        {core_status}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Timestamp
    ts = time.strftime("%H:%M:%S")
    st.markdown(f"""
    <div style="font-family:'Roboto Mono',monospace;font-size:0.68rem;
                color:#243050;text-align:center;letter-spacing:0.1em;">
        LAST UPDATE<br>
        <span style="color:rgba(0,242,255,0.2);">{ts}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<p style="font-family:Roboto Mono,monospace;font-size:0.65rem;color:#243050;text-align:center;letter-spacing:0.08em;">UNIVERSIDAD DE CUNDINAMARCA<br>REDES DE COMUNICACIONES</p>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
header_class = "cyber-header active" if is_active else "cyber-header inactive"
st.markdown(f"""
<div class="{header_class}">
    <h1>CYBER-AUDITOR</h1>
    <div class="sub">UDEC · SABANA CENTRO · NETWORK INTELLIGENCE PLATFORM</div>
</div>
<div class="cyber-divider"></div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TABS PRINCIPALES
# ─────────────────────────────────────────────────────────────────────────────
role = st.session_state.get("role")
if role in ("administrador", "bibliotecario"):
    tab1, tab2, tab3, tab4 = st.tabs([
        "◧  MONITOR USUARIO",
        "◈  MAPA REGIONAL",
        "⎔  ADMIN · DIAGNÓSTICO",
        "📚 BIBLIOTECAS"
    ])
else:
    tab1, tab4 = st.tabs([
        "◧  MONITOR USUARIO",
        "📚 BIBLIOTECAS"
    ])
    tab2 = None
    tab3 = None

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 – MONITOR USUARIO
# ═════════════════════════════════════════════════════════════════════════════
with tab1:
    # ── Obtiene snapshot ──────────────────────────────────────────────────────

    col_cfg_1, col_cfg_2, col_cfg_3 = st.columns([2.6, 1.7, 1.3])
    with col_cfg_1:
        st.markdown('<p style="font-family:Roboto Mono,monospace;font-size:0.72rem;letter-spacing:0.1em;color:#4a6080;text-transform:uppercase;margin:0 0 4px 0;">TARGET</p>', unsafe_allow_html=True)
        st.text_input("Target", key="cfg_target", label_visibility="collapsed")

    with col_cfg_2:
        st.markdown('<p style="font-family:Roboto Mono,monospace;font-size:0.72rem;letter-spacing:0.1em;color:#4a6080;text-transform:uppercase;margin:0 0 4px 0;">MODO</p>', unsafe_allow_html=True)
        st.selectbox("Modo", ["Simulación", "Live (HTTP Probe)"], key="cfg_mode", label_visibility="collapsed")

    with col_cfg_3:
        st.markdown('<p style="font-family:Roboto Mono,monospace;font-size:0.72rem;letter-spacing:0.1em;color:#4a6080;text-transform:uppercase;margin:0 0 4px 0;">REFRESH</p>', unsafe_allow_html=True)
        st.selectbox("Refresh", options=list(interval_opts.keys()), key="cfg_refresh_rate", label_visibility="collapsed")

    st.markdown('<div style="height:0.75rem;"></div>', unsafe_allow_html=True)

    target = str(st.session_state.get("cfg_target") or "portal.udec.edu.co")
    mode = str(st.session_state.get("cfg_mode") or "Simulación")
    mode_key = "sim" if mode == "Simulación" else "live"
    selected_interval = str(st.session_state.get("cfg_refresh_rate") or "1.0s")
    refresh_delay = interval_opts.get(selected_interval, 1.0)

    # Solo crear/consultar prober si está activo
    prober = None
    snap = None
    
    if is_active:
        st.markdown("""
        <div style="background: rgba(0, 255, 65, 0.08); border: 1px solid #00ff41; border-radius: 4px; padding: 0.6rem; display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 1rem; box-shadow: 0 0 15px rgba(0,255,65,0.2), inset 0 0 10px rgba(0,255,65,0.1);">
            <div style="width: 12px; height: 12px; background-color: #00ff41; border-radius: 50%; box-shadow: 0 0 10px #00ff41, 0 0 20px #00ff41; animation: blink-critical 1s infinite;"></div>
            <span style="font-family: 'Share Tech Mono', monospace; font-size: 1rem; font-weight: bold; color: #00ff41; letter-spacing: 0.2em; text-shadow: 0 0 8px #00ff41;">LIVE MONITORING ACTIVE</span>
        </div>
        """, unsafe_allow_html=True)
        
        prober = get_or_create_prober(st.session_state, target, mode_key)
        snap   = prober.get_snapshot()
        st.session_state["last_snapshot"] = snap
    else:
        st.markdown("""
        <div style="background: rgba(255, 179, 0, 0.05); border: 1px dashed #ffb300; border-radius: 4px; padding: 0.5rem; display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 1rem;">
            <div style="width: 10px; height: 10px; background-color: transparent; border: 2px solid #ffb300; border-radius: 50%;"></div>
            <span style="font-family: 'Share Tech Mono', monospace; font-size: 0.9rem; font-weight: bold; color: #ffb300; letter-spacing: 0.2em;">MONITORING PAUSED</span>
        </div>
        """, unsafe_allow_html=True)
        
        snap = st.session_state.get("last_snapshot")
        if not snap:
            from v3.data_bridge import NetworkSnapshot
            snap = NetworkSnapshot()
            st.session_state["last_snapshot"] = snap

    # Lluvia digital Matrix en el fondo
    st.markdown(MATRIX_RAIN_HTML, unsafe_allow_html=True)

    col_btn_start, col_btn_refresh, col_btn_dummy = st.columns([1.2, 0.9, 6.2])
    with col_btn_start:
        btn_label = "◈ DETENER" if is_active else "▶ INICIAR"
        if st.button(btn_label, key="btn_toggle_monitor", help="Inicia o detiene el monitoreo de red", use_container_width=True, type="primary"):
            st.session_state["monitoring_active"] = not is_active
            if "_prober_instance" in st.session_state and st.session_state["_prober_instance"] is not None:
                try:
                    st.session_state["_prober_instance"].stop()
                except Exception:
                    pass
                st.session_state["_prober_instance"] = None
                st.session_state["_prober_config"] = None
            st.rerun()

    with col_btn_refresh:
        if st.button("⟳", key="btn_refresh", type="secondary", use_container_width=True):
            st.rerun()

    st.markdown('<div style="height:0.75rem;"></div>', unsafe_allow_html=True)

    # Calcula señal (0–100): inverso del error_rate + congestión
    signal_pct = max(0.0, 100.0 - snap.error_rate_pct * 3 - snap.congestion_score * 0.3)

    # ── Badge de estado ───────────────────────────────────────────────────────
    badge_cls = {
        "STABLE":   "status-healthy",
        "HEALTHY":  "status-healthy",
        "WARNING":  "status-warning",
        "CRITICAL": "status-critical",
    }.get(snap.status, "status-healthy")

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem;">
        <span class="status-badge {badge_cls}">{snap.status}</span>
        <span style="font-family:'Roboto Mono',monospace;font-size:0.8rem;
                     color:#4a6080;">{snap.alert_message}</span>
        <span style="margin-left:auto;font-family:'Roboto Mono',monospace;
                     font-size:0.7rem;color:rgba(0,242,255,0.4);">
            TARGET: {target} &nbsp;|&nbsp; PROBES: {snap.total_probes:,}
            &nbsp;|&nbsp; IP: {snap.resolved_ip}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # ── Métricas rápidas ──────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    
    def render_metric(label, val_str, delta_str, val, warn_th, crit_th):
        if val <= warn_th:
            color, glow, glitch = "#00ff41", "#00ff4166", ""
        elif val <= crit_th:
            color, glow, glitch = "#ffb300", "#ffb30066", ""
        else:
            color, glow, glitch = "#ff0033", "#ff003366", "glitch-critical"
            
        # Atributo data-text para efectos glitch mejorados
        data_text = f'data-text="{val_str}"' if glitch else ""
        
        return f"""
        <div class="cyber-card" style="padding:0.6rem; border-top: 2px solid {color}; box-shadow: inset 0 0 10px {glow}; margin-bottom: 0;">
            <div style="font-family:'Share Tech Mono', monospace; font-size:0.65rem; color:#c8d8f0; opacity:0.8;">{label}</div>
            <div class="{glitch}" {data_text} style="font-family:'Roboto Mono', monospace; font-size:1.4rem; font-weight:bold; color:{color}; text-shadow: 0 0 8px {glow}; line-height:1.2;">{val_str}</div>
            <div style="font-family:'Roboto Mono', monospace; font-size:0.65rem; color:#4a6080;">{delta_str}</div>
        </div>
        """

    def render_neutral_metric(label, val_str):
        return f"""
        <div class="cyber-card" style="padding:0.6rem; border-top: 2px solid #00f2ff; box-shadow: inset 0 0 10px #00f2ff44; margin-bottom: 0;">
            <div style="font-family:'Share Tech Mono', monospace; font-size:0.65rem; color:#c8d8f0; opacity:0.8;">{label}</div>
            <div style="font-family:'Roboto Mono', monospace; font-size:1.1rem; font-weight:bold; color:#00f2ff; text-shadow: 0 0 8px #00f2ff66; line-height:1.4; word-break: break-all;">{val_str}</div>
            <div style="height:0.65rem;"></div>
        </div>
        """

    with c1:
        st.markdown(render_metric("◈ LATENCIA", f"{snap.latency_ms:.1f} ms", f"avg {snap.latency_avg:.0f}ms", snap.latency_ms, 50, 150), unsafe_allow_html=True)
    with c2:
        st.markdown(render_metric("▧ PÉRDIDA PKT", f"{snap.packet_loss_pct:.1f}%", f"err {snap.error_rate_pct:.1f}%", snap.packet_loss_pct, 1.0, 5.0), unsafe_allow_html=True)
    with c3:
        st.markdown(render_metric("▤ CONGESTIÓN", f"{snap.congestion_score:.0f}/100", "carga actual", snap.congestion_score, 35, 65), unsafe_allow_html=True)
    with c4:
        st.markdown(render_neutral_metric("⎈ PROBES", f"{snap.total_probes:,}"), unsafe_allow_html=True)
    with c5:
        st.markdown(render_neutral_metric("⛬ IP RESUELTA", snap.resolved_ip), unsafe_allow_html=True)

    # ── FILA DE GAUGES SVG ────────────────────────────────────────────────────
    st.markdown('<div class="cyber-section-title"><span>//</span> INSTRUMENTACIÓN EN TIEMPO REAL</div>',
                unsafe_allow_html=True)

    gauge_html = render_gauge_row(
        latency_ms        = snap.latency_ms,
        signal_pct        = signal_pct,
        congestion_score  = snap.congestion_score,
        gauge_size        = 200,
    )
    # components.html renderiza SVG complejo sin sanitización de Streamlit
    components.html(gauge_html, height=250, scrolling=False)

    st.markdown('<div style="height:1.2rem;"></div>', unsafe_allow_html=True)

    # ── Segunda fila: Gráfico + Info table ───────────────────────────────────
    col_chart, col_info = st.columns([2, 1])

    with col_chart:
        st.markdown('<div class="cyber-section-title"><span>//</span> LATENCIA EN TIEMPO REAL</div>',
                    unsafe_allow_html=True)

        lats = snap.latency_points
        if lats:
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=list(range(len(lats))),
                y=lats,
                fill='tozeroy',
                fillcolor='rgba(0,242,255,0.06)',
                line=dict(color='#00f2ff', width=2),
                mode='lines',
                name='Latencia ms',
                hovertemplate='<b>%{y:.1f} ms</b><extra></extra>',
            ))

            fig.add_hline(y=150, line=dict(color='#ffb300', width=1, dash='dot'),
                          annotation_text="WARN 150ms",
                          annotation_font_color='#ffb300', annotation_font_size=9)
            fig.add_hline(y=500, line=dict(color='#ff0033', width=1, dash='dot'),
                          annotation_text="CRIT 500ms",
                          annotation_font_color='#ff0033', annotation_font_size=9)

            fig.update_layout(
                height=220,
                paper_bgcolor='#080a0f',
                plot_bgcolor='#0a0d14',
                font=dict(family='Roboto Mono', color='#4a6080', size=10),
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=False,
                xaxis=dict(
                    showgrid=True, gridcolor='rgba(30,45,69,0.4)',
                    zeroline=False, showticklabels=False,
                ),
                yaxis=dict(
                    showgrid=True, gridcolor='rgba(30,45,69,0.4)',
                    zeroline=False, ticksuffix=' ms', tickfont=dict(size=9),
                ),
            )
            st.plotly_chart(fig, use_container_width=True,
                            config={'displayModeBar': False})
        else:
            st.markdown(
                '<div class="terminal-box">Esperando datos...'
                '<span class="terminal-cursor"></span></div>',
                unsafe_allow_html=True,
            )

        # ── Easter Eggs pulsantes ─────────────────────────────────────────────────────
        st.markdown("""
        <div style="display:flex;flex-direction:column;align-items:flex-start;margin:1.5rem 0;">
            <div class="pulse-neon-text">ニクス、愛してる <3。</div>
            <div class="pulse-neon-text">トゥタ、愛してる <3。</div>
            <div class="pulse-neon-text">ウリベはクソ野郎だ</div>
            <div class="pulse-neon-text">自由なコードのみ</div>
            <div class="pulse-neon-text">UDECに感謝</div>
        </div>
        """, unsafe_allow_html=True)

    with col_info:
        st.markdown('<div class="cyber-section-title"><span>//</span> DIAGNÓSTICO L7</div>',
                    unsafe_allow_html=True)

        info_rows = [
            ("MODO",      mode),
            ("HTTP CODE", str(snap.status_code or "—")),
            ("ENCODING",  snap.content_encoding or "sin comp."),
            ("LAT AVG",   f"{snap.latency_avg:.1f} ms"),
            ("LAT MIN",   f"{snap.latency_min:.1f} ms"),
            ("LAT MAX",   f"{snap.latency_max:.1f} ms"),
            ("PKT LOSS",  f"{snap.packet_loss_pct:.2f}%"),
            ("SEÑAL",     f"{signal_pct:.0f}%"),
            ("RECOM.",    (snap.recommendation[:28] if snap.recommendation else "OK")),
        ]

        # Crear DataFrame para mostrar con estética cyberpunk
        import pandas as pd
        df_data = []
        
        for k, v in info_rows:
            df_data.append([k, v])
        
        df = pd.DataFrame(df_data, columns=["MÉTRICA", "VALOR"])
        
        # Contenedor cyberpunk
        st.markdown("""
        <div style="background:linear-gradient(135deg, #0d1117 0%, #111827 100%);border:2px solid #00f2ff;border-radius:8px;padding:1rem;box-shadow:0 0 20px rgba(0,242,255,0.3),inset 0 0 20px rgba(0,242,255,0.1);position:relative;overflow:hidden;margin-bottom:1rem;">
            <div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg, #00f2ff, #ff00ff, #00f2ff);animation:scan 3s linear infinite;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar tabla nativa de Streamlit
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "MÉTRICA": st.column_config.Column(
                    width=200,
                    help="Métrica de diagnóstico de red"
                ),
                "VALOR": st.column_config.Column(
                    width=250,
                    help="Valor actual medido"
                )
            }
        )

# ═════════════════════════════════════════════════════════════════════════════
# Función reutilizable para mostrar datos de biblioteca
def mostrar_datos_biblioteca(nombre_hoja, nombre_biblioteca):
    """Muestra los datos de una biblioteca desde Google Sheets"""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        import os
        from datetime import datetime
        import time
        import pandas as pd
        
        # Verificar caché específica para esta biblioteca
        cache_key = f'cached_sheets_data_{nombre_hoja}'
        cache_time_key = f'cache_time_{nombre_hoja}'
        
        if cache_key not in st.session_state:
            st.session_state[cache_key] = None
            st.session_state[cache_time_key] = 0
        
        current_time = time.time()
        cache_age = current_time - st.session_state[cache_time_key]
        
        # Verificar si tenemos datos en caché y son recientes (menos de 60 segundos)
        if (st.session_state[cache_key] is not None and cache_age < 30):
            data = st.session_state[cache_key]
            st.markdown(f"""
            <div style='background:rgba(0,150,255,0.1);border:1px solid #0096ff;border-radius:6px;padding:8px;margin-bottom:1rem;'>
                <span style='color:#0096ff;font-family:Orbitron,monospace;font-size:0.8em;'>
                     Usando datos cacheados · Edad: {cache_age:.0f}s
                </span>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Obtener datos frescos de Google Sheets
            st.markdown("""
            <div style='background:rgba(255,150,0,0.1);border:1px solid #ff9600;border-radius:6px;padding:8px;margin-bottom:1rem;'>
                <span style='color:#ff9600;font-family:Orbitron,monospace;font-size:0.8em;'>
                     Obteniendo datos frescos de Google Sheets...
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            # Obtener credenciales (Streamlit Cloud o local)
            SCOPES = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            
            # Intentar usar st.secrets primero (Streamlit Cloud)
            if "gcp_service_account" in st.secrets:
                creds_dict = dict(st.secrets["gcp_service_account"])
                creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
                gc = gspread.authorize(creds)
            else:
                # Fallback: usar archivo local (desarrollo)
                creds_path = os.path.join(os.path.dirname(__file__), "credentials.json")
                if not os.path.exists(creds_path):
                    creds_path = "credentials.json"
                creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
                gc = gspread.authorize(creds)
            
            # Abrir spreadsheet
            sh = gc.open("UDEC-Cyber-Auditor")
            
            # Buscar hoja específica
            ws = sh.worksheet(nombre_hoja)
            
            # Obtener todos los datos
            data = ws.get_all_values()
            
            # Guardar en caché
            st.session_state[cache_key] = data
            st.session_state[cache_time_key] = current_time
        
        # Procesar datos obtenidos (de caché o frescos)
        try:
            if len(data) <= 1:
                st.markdown(f"""
                <div style='background:rgba(255,0,85,0.1);border:2px solid #ff0055;border-radius:8px;padding:20px;text-align:center;margin:2rem 0;'>
                    <div style='color:#ff0055;font-family:Orbitron,monospace;font-size:1.2em;margin-bottom:10px;'>
                        ⚠️ HOJA VACÍA
                    </div>
                    <div style='color:#ccc;font-family:Orbitron,monospace;'>
                        La hoja "{nombre_hoja}" existe pero no tiene datos.<br>
                        Asegúrate de que el script del celular esté enviando datos.
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Mostrar última actualización
                last_row = data[-1]
                if last_row:
                    timestamp = last_row[0] if len(last_row) > 0 else "N/A"
                    biblioteca = last_row[1] if len(last_row) > 1 else "N/A"
                    local_ip = last_row[2] if len(last_row) > 2 else "N/A"
                    status = last_row[3] if len(last_row) > 3 else "N/A"
                    latency_avg = last_row[4] if len(last_row) > 4 else "N/A"
                    latency_icmp = last_row[5] if len(last_row) > 5 else "N/A"
                    loss_pct = last_row[6] if len(last_row) > 6 else "N/A"
                    
                    # Definir color según estado
                    status_color = {
                        "STABLE": "#00ff88",
                        "WARNING": "#ffb300",
                        "CRITICAL": "#ff0055"
                    }.get(status, "#ccc")
                    
                    # Indicador de datos recibidos
                    st.markdown(f"""
                    <div style='background:linear-gradient(135deg, rgba(0,242,255,0.1) 0%, rgba(255,0,255,0.1) 100%);
                                border:1px solid #00f2ff;border-radius:8px;padding:12px;margin-bottom:1rem;
                                display:flex;align-items:center;gap:10px;'>
                        <div style='width:8px;height:8px;background:#00ff88;border-radius:50%;animation:pulse 2s infinite;'></div>
                        <span style='color:#00f2ff;font-family:Orbitron,monospace;font-size:0.9em;'>
                            ◈ DATOS RECIBIDOS · Última actualización: {timestamp}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Letras japonesas animadas
                    st.markdown(f"""
                    <div id='japanese-text-{nombre_hoja}' style='color:{status_color};font-family:"MS Gothic","Yu Gothic",sans-serif;font-size:3em;text-shadow:0 0 10px {status_color},0 0 20px {status_color},0 0 30px {status_color};text-align:center;padding:30px;animation:neon-damaged 2s infinite alternate;' data-status='{status}'>
                        オープンソース万歳
                    </div>
                    <script>
                        const japaneseTexts{nombre_hoja.replace(' ', '')} = [
                            "オープンソース万歳",
                            "人工知能は未来",
                            "クリティカルは最高の学習",
                            "コードは自由"
                        ];
                        let currentIndex{nombre_hoja.replace(' ', '')} = 0;
                        const textElement{nombre_hoja.replace(' ', '')} = document.getElementById('japanese-text-{nombre_hoja}');
                        
                        const statusColors{nombre_hoja.replace(' ', '')} = {{
                            "STABLE": ["#00ff88", "#00ff99", "#00ffaa", "#00ffbb", "#00ffcc", "#00ffdd", "#00ffee"],
                            "WARNING": ["#ffb300", "#ffcc00", "#ffdd00", "#ffee00", "#ffff00", "#ffcc33", "#ffdd44"],
                            "CRITICAL": ["#ff0033", "#ff0044", "#ff0055", "#ff0066", "#ff0077", "#ff0088", "#ff0099"]
                        }};
                        
                        if (textElement{nombre_hoja.replace(' ', '')}) {{
                            setInterval(() => {{
                                currentIndex{nombre_hoja.replace(' ', '')} = (currentIndex{nombre_hoja.replace(' ', '')} + 1) % japaneseTexts{nombre_hoja.replace(' ', '')}.length;
                                textElement{nombre_hoja.replace(' ', '')}.textContent = japaneseTexts{nombre_hoja.replace(' ', '')}[currentIndex{nombre_hoja.replace(' ', '')}];
                            }}, 3000);
                            
                            setInterval(() => {{
                                const currentStatus = textElement{nombre_hoja.replace(' ', '')}.getAttribute('data-status');
                                const colorVariations = statusColors{nombre_hoja.replace(' ', '')}[currentStatus] || statusColors{nombre_hoja.replace(' ', '')}["STABLE"];
                                const randomColor = colorVariations[Math.floor(Math.random() * colorVariations.length)];
                                textElement{nombre_hoja.replace(' ', '')}.style.color = randomColor;
                                textElement{nombre_hoja.replace(' ', '')}.style.textShadow = `0 0 10px ${{randomColor}}, 0 0 20px ${{randomColor}}, 0 0 30px ${{randomColor}}`;
                            }}, 1500);
                        }}
                    </script>
                    <style>
                        @keyframes neon-damaged {{
                            0% {{ opacity: 1; filter: brightness(1); }}
                            25% {{ opacity: 0.9; filter: brightness(1.1); }}
                            50% {{ opacity: 0.8; filter: brightness(0.95); }}
                            75% {{ opacity: 0.95; filter: brightness(1.05); }}
                            100% {{ opacity: 0.85; filter: brightness(0.98); }}
                        }}
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Encabezado
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown(f"""
                        <div style='color:#00f2ff;font-family:Orbitron,monospace;font-size:1.5em;font-weight:700;text-shadow:0 0 15px #00f2ff;'>
                            ◉ UDEC {nombre_biblioteca.upper()}
                        </div>
                        <div style='color:#ffe600;font-family:Orbitron,monospace;font-size:1em;margin-top:5px;'>
                            NODO PRINCIPAL
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div style='color:{status_color};font-family:Orbitron,monospace;font-size:1.3em;font-weight:700;text-shadow:0 0 10px {status_color},0 0 20px {status_color},0 0 30px {status_color};text-align:right;'>
                            ● {status}
                        </div>
                        <div style='color:{status_color};font-family:Orbitron,monospace;font-size:0.9em;margin-top:5px;text-align:right;text-shadow:0 0 5px {status_color},0 0 10px {status_color};'>
                            {local_ip}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("""
                    <div style='border:1px solid #1e2d45;margin:15px 0;'></div>
                    """, unsafe_allow_html=True)
                    
                    # Métricas con línea de separación mejorada
                    st.markdown(f"""
                    <div style='border:1px solid {status_color}66;margin:20px 0;position:relative;'>
                        <div style='position:absolute;top:-1px;left:0;width:100%;height:1px;background:linear-gradient(90deg, transparent, {status_color}, transparent);'></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"""
                        <div style='background:linear-gradient(135deg, rgba(255,0,255,0.1) 0%, rgba(0,242,255,0.1) 100%);
                                    border:1px solid #ff00ff;border-radius:12px;padding:16px;margin:10px 0;
                                    box-shadow:0 0 20px rgba(255,0,255,0.3),inset 0 0 15px rgba(255,0,255,0.1);'>
                            <div style='color:#ff00ff;font-family:Orbitron,monospace;font-size:0.85em;margin-bottom:8px;text-transform:uppercase;letter-spacing:2px;'>
                                ⚛ LATENCIA HTTP
                            </div>
                            <div style='color:#fff;font-family:Orbitron,monospace;font-size:2em;font-weight:700;text-shadow:0 0 10px #ff00ff;'>
                                {latency_avg} <span style='font-size:0.6em;color:#ff00ff;'>MS</span>
                            </div>
                            <div style='margin-top:8px;height:4px;background:#1a1a2a;border-radius:2px;overflow:hidden;'>
                                <div style='height:100%;background:linear-gradient(90deg, #ff00ff, #00ffff);width:{min(100, float(latency_avg.replace(",", "."))/10)}%;animation:pulse 2s infinite;'></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div style='background:linear-gradient(135deg, rgba(0,242,255,0.1) 0%, rgba(255,0,255,0.1) 100%);
                                    border:1px solid #00f2ff;border-radius:12px;padding:16px;margin:10px 0;
                                    box-shadow:0 0 20px rgba(0,242,255,0.3),inset 0 0 15px rgba(0,242,255,0.1);'>
                            <div style='color:#00f2ff;font-family:Orbitron,monospace;font-size:0.85em;margin-bottom:8px;text-transform:uppercase;letter-spacing:2px;'>
                                ⌬ LATENCIA ICMP
                            </div>
                            <div style='color:#fff;font-family:Orbitron,monospace;font-size:2em;font-weight:700;text-shadow:0 0 10px #00f2ff;'>
                                {latency_icmp} <span style='font-size:0.6em;color:#00f2ff;'>MS</span>
                            </div>
                            <div style='margin-top:8px;height:4px;background:#1a1a2a;border-radius:2px;overflow:hidden;'>
                                <div style='height:100%;background:linear-gradient(90deg, #00f2ff, #ff00ff);width:{min(100, float(latency_icmp.replace(",", "."))/5)}%;animation:pulse 2s infinite;'></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Pérdida de paquetes con efecto cyberpunk
                    loss_color = "#ff0055" if float(loss_pct.replace(",", ".")) > 20 else "#ffb300" if float(loss_pct.replace(",", ".")) > 5 else "#00ff88"
                    st.markdown(f"""
                    <div style='background:linear-gradient(135deg, rgba(255,0,85,0.1) 0%, rgba(255,0,255,0.1) 100%);
                                border:1px solid {loss_color};border-radius:12px;padding:16px;margin:10px 0;
                                box-shadow:0 0 20px {loss_color}44,inset 0 0 15px {loss_color}22;'>
                        <div style='color:{loss_color};font-family:Orbitron,monospace;font-size:0.85em;margin-bottom:8px;text-transform:uppercase;letter-spacing:2px;'>
                            ▼ PÉRDIDA DE PAQUETES
                        </div>
                        <div style='color:#fff;font-family:Orbitron,monospace;font-size:1.8em;font-weight:700;text-shadow:0 0 10px {loss_color};'>
                            {loss_pct} <span style='font-size:0.6em;color:{loss_color};'>%</span>
                        </div>
                        <div style='margin-top:8px;height:6px;background:#1a1a2a;border-radius:3px;overflow:hidden;'>
                            <div style='height:100%;background:linear-gradient(90deg, {loss_color}, #ff00ff);width:{loss_pct}%;animation:pulse 1.5s infinite;'></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Gráfica cyberpunk de latencia HTTP
                    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
                    st.markdown('<div class="cyber-section-title"><span>//</span> HISTORIAL DE LATENCIA HTTP</div>', unsafe_allow_html=True)
                    
                    # Preparar datos para la gráfica (últimos 20 registros)
                    graph_data = data[-21:-1] if len(data) > 1 else []
                    if graph_data:
                        timestamps = []
                        latencies = []
                        for row in graph_data:
                            if len(row) >= 5:
                                timestamps.append(row[0])
                                try:
                                    lat_val = float(row[4].replace(",", "."))
                                    latencies.append(lat_val)
                                except:
                                    latencies.append(0)
                        
                        if latencies:
                            import plotly.graph_objects as go
                            
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(
                                x=list(range(len(latencies))),
                                y=latencies,
                                mode='lines+markers',
                                name='Latencia HTTP',
                                line=dict(
                                    color='#00f2ff',
                                    width=2,
                                    shape='spline'
                                ),
                                marker=dict(
                                    color='#ff00ff',
                                    size=6,
                                    symbol='circle',
                                    line=dict(color='#00f2ff', width=1)
                                ),
                                fill='tozeroy',
                                fillcolor='rgba(0,242,255,0.1)'
                            ))
                            
                            fig.update_layout(
                                title=dict(
                                    text=f'Latencia HTTP - {nombre_biblioteca}',
                                    font=dict(color='#00f2ff', family='Orbitron, monospace', size=16),
                                    x=0.5
                                ),
                                xaxis=dict(
                                    title='Muestras',
                                    showgrid=True,
                                    gridcolor='rgba(0,242,255,0.1)',
                                    gridwidth=1,
                                    tickfont=dict(color='#00f2ff', family='Orbitron, monospace'),
                                    title_font=dict(color='#00f2ff', family='Orbitron, monospace')
                                ),
                                yaxis=dict(
                                    title='Latencia (ms)',
                                    showgrid=True,
                                    gridcolor='rgba(255,0,255,0.1)',
                                    gridwidth=1,
                                    tickfont=dict(color='#ff00ff', family='Orbitron, monospace'),
                                    title_font=dict(color='#ff00ff', family='Orbitron, monospace')
                                ),
                                plot_bgcolor='rgba(10,10,26,0.8)',
                                paper_bgcolor='rgba(10,10,26,0.8)',
                                font=dict(family='Orbitron, monospace'),
                                margin=dict(l=50, r=50, t=50, b=50),
                                height=300
                            )
                            
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                    
                    # Tabla con historial reciente
                    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
                    st.markdown('<div class="cyber-section-title"><span>//</span> HISTORIAL RECIENTE</div>', unsafe_allow_html=True)
                    
                    # Preparar datos para la tabla (últimos 10 registros)
                    recent_data = data[-11:-1] if len(data) > 1 else []
                    if recent_data:
                        df_data = []
                        for row in reversed(recent_data):
                            if len(row) >= 7:
                                df_data.append({
                                    "TIMESTAMP": row[0],
                                    "BIBLIOTECA": row[1],
                                    "IP LOCAL": row[2],
                                    "ESTADO": row[3],
                                    "LATENCIA HTTP": f"{row[4]} ms",
                                    "LATENCIA ICMP": f"{row[5]} ms",
                                    "PÉRDIDA": f"{row[6]}%"
                                })
                        
                        df = pd.DataFrame(df_data)
                        st.dataframe(
                            df,
                            use_container_width=True,
                            hide_index=True,
                        )
                    else:
                        st.info("No hay datos históricos disponibles")
        
        except gspread.WorksheetNotFound:
            st.markdown(f"""
            <div style='background:rgba(255,0,85,0.1);border:2px solid #ff0055;border-radius:8px;padding:20px;text-align:center;margin:2rem 0;'>
                <div style='color:#ff0055;font-family:Orbitron,monospace;font-size:1.2em;margin-bottom:10px;'>
                    ❌ HOJA NO ENCONTRADA
                </div>
                <div style='color:#ccc;font-family:Orbitron,monospace;'>
                    No se encontró la hoja "{nombre_hoja}" en el spreadsheet.<br>
                    Verifica que el script del celular esté creando la hoja correcta.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Error conectando a Google Sheets: {e}")
        st.markdown("""
        <div style='background:rgba(255,0,85,0.1);border:2px solid #ff0055;border-radius:8px;padding:20px;text-align:center;margin:2rem 0;'>
            <div style='color:#ff0055;font-family:Orbitron,monospace;font-size:1.2em;margin-bottom:10px;'>
                ❌ ERROR DE CONEXIÓN
            </div>
            <div style='color:#ccc;font-family:Orbitron,monospace;'>
                No se pueden obtener los datos de Google Sheets.<br>
                Verifica las credenciales y la conexión.
            </div>
        </div>
        """, unsafe_allow_html=True)

if tab2 is not None:
    # TAB 2 – MAPA REGIONAL CYBERPUNK
    # ═════════════════════════════════════════════════════════════════════════════
    with tab2:
        # Título cyberpunk simple sin líneas animadas
        st.markdown('<div class="cyber-section-title"><span>//</span> MAPA REGIONAL · CYBERPUNK INTERFACE</div>', unsafe_allow_html=True)
        
        # Efectos de partículas y grid cyberpunk
        st.markdown("""
        <div style='position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:-1;overflow:hidden;'>
            <div style='position:absolute;width:100%;height:100%;background-image:
                radial-gradient(circle at 20% 50%, rgba(255,0,255,0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(0,255,255,0.1) 0%, transparent 50%),
                linear-gradient(0deg, transparent 24%, rgba(0,255,255,0.03) 25%, rgba(0,255,255,0.03) 26%, transparent 27%, transparent 74%, rgba(0,255,255,0.03) 75%, rgba(0,255,255,0.03) 76%, transparent 77%, transparent),
                linear-gradient(90deg, transparent 24%, rgba(255,0,255,0.03) 25%, rgba(255,0,255,0.03) 26%, transparent 27%, transparent 74%, rgba(255,0,255,0.03) 75%, rgba(255,0,255,0.03) 76%, transparent 77%, transparent);
                background-size:50px 50px, 50px 50px, 50px 50px, 50px 50px;
                animation:grid-move 10s linear infinite;'></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(MATRIX_RAIN_HTML, unsafe_allow_html=True)
        
        # Crear sub-pestañas para cada biblioteca
        tab_chia, tab_sopo, tab_cajica = st.tabs(["CHÍA", "SOPO", "CAJICÁ"])
        
        # Auto-refresh cada 30 segundos para el Mapa Regional
        try:
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=30000, key="mapa_regional_refresh")
        except ImportError:
            pass
        
        with tab_chia:
            mostrar_datos_biblioteca("Biblioteca Chía", "Chía")
        
        with tab_sopo:
            mostrar_datos_biblioteca("Biblioteca Sopo", "Sopo")
        
        with tab_cajica:
            mostrar_datos_biblioteca("Biblioteca Cajica", "Cajica")


if tab3 is not None:
    # ═════════════════════════════════════════════════════════════════════════════
    # TAB 3 – ADMIN DIAGNÓSTICO
    # ═════════════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown('<div class="cyber-section-title"><span>//</span> CONSOLA DE DIAGNÓSTICO · AISLAMIENTO DE FALLAS</div>', unsafe_allow_html=True)

        col_diag_a, col_diag_b = st.columns([1, 1])

        with col_diag_a:
            st.markdown("""
            <div class="cyber-card cyber-card-cyan">
                <div class="cyber-section-title"><span>//</span> PROBE HTTP · GATEWAY / UDEC</div>
            </div>
            """, unsafe_allow_html=True)

            diag_target = st.text_input(
                "TARGET DE DIAGNÓSTICO",
                value="portal.udec.edu.co",
                key="diag_target",
            )
            diag_timeout = st.slider("Timeout (seg)", 2, 15, 5, key="diag_timeout")

            run_probe = st.button("▶ EJECUTAR PROBE HTTP", key="btn_probe", type="primary")
            ping_gw   = st.button("⎈ PING GATEWAY LOCAL", key="btn_gw", type="primary")

            if "diag_log" not in st.session_state:
                st.session_state["diag_log"] = []

            def add_log(msg: str, kind: str = "info"):
                ts_ = time.strftime("%H:%M:%S")
                st.session_state["diag_log"].append((ts_, kind, msg))
                if len(st.session_state["diag_log"]) > 40:
                    st.session_state["diag_log"].pop(0)

            if run_probe:
                with st.spinner("Enviando probe HTTP..."):
                    add_log(f"[PROBE] → {diag_target}", "info")
                    result = run_ping_diagnosis(diag_target, timeout=float(diag_timeout))
                    if result.success:
                        add_log(f"[OK]    HTTP {result.status_code} · {result.latency_ms:.1f}ms", "ok")
                    else:
                        add_log(f"[ERR]   {result.error}", "err")

            if ping_gw:
                add_log("[PING] Detectando gateway local...", "info")
                import subprocess, socket
                try:
                    hostname = socket.gethostname()
                    local_ip = socket.gethostbyname(hostname)
                    parts = local_ip.split(".")
                    gw_ip = ".".join(parts[:3] + ["1"])
                    add_log(f"[INFO]  Host={hostname} | IP={local_ip} | GW estimado={gw_ip}", "info")

                    proc = subprocess.run(
                        ["ping", "-n", "3", gw_ip],
                        capture_output=True, text=True, timeout=10,
                    )
                    lines = [l.strip() for l in proc.stdout.splitlines() if l.strip()]
                    for line in lines[-5:]:
                        add_log(f"  {line}", "ok" if "TTL" in line else "muted")

                except Exception as exc:
                    add_log(f"[ERR]   {exc}", "err")

        with col_diag_b:
            st.markdown("""
            <div class="cyber-card">
                <div class="cyber-section-title"><span>//</span> TERMINAL DE SALIDA</div>
            </div>
            """, unsafe_allow_html=True)

            KIND_MAP = {
                "ok":   ("t-ok",   "✓"),
                "err":  ("t-err",  "✗"),
                "warn": ("t-warn", "⚠"),
                "info": ("t-info", "›"),
                "muted":("t-muted","·"),
            }

            log_html = ""
            for (ts_, kind, msg) in reversed(st.session_state.get("diag_log", [])):
                css_cls, icon = KIND_MAP.get(kind, ("t-info", "›"))
                log_html += f'<span class="{css_cls}">[{ts_}] {icon} {msg}</span>\n'

            if not log_html:
                log_html = '<span class="t-muted">// Esperando comandos...\n// Usa los botones del panel izquierdo.</span>'

            st.markdown(f'<div class="terminal-box">{log_html}<span class="terminal-cursor"></span></div>',
                        unsafe_allow_html=True)

            st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
            if st.button("[// LIMPIAR TERMINAL ]", key="btn_clear", type="secondary"):
                st.session_state["diag_log"] = []
                st.rerun()

        st.markdown('<div style="height:1.5rem;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="cyber-section-title"><span>//</span> COMPARATIVA MULTI-OBJETIVO</div>', unsafe_allow_html=True)

        TARGETS_BENCH = [
            ("portal.udec.edu.co",  "UDEC Portal"),
            ("8.8.8.8",             "Google DNS"),
            ("1.1.1.1",             "Cloudflare DNS"),
            ("google.com",          "Google"),
        ]

        if st.button("◈ BENCHMARK RÁPIDO (TODOS LOS TARGETS)", key="btn_bench", type="primary"):
            results = []
            progress = st.progress(0)
            for i, (t, label) in enumerate(TARGETS_BENCH):
                with st.spinner(f"Probando {label}..."):
                    r = run_ping_diagnosis(t, timeout=4.0)
                    results.append({
                        "TARGET":    label,
                        "IP":        t,
                        "LATENCIA":  f"{r.latency_ms:.1f} ms" if r.success else "—",
                        "HTTP CODE": str(r.status_code or "—"),
                        "ESTADO":    "✓ OK" if r.success else f"✗ {r.error[:40] if r.error else 'Error'}",
                    })
                    progress.progress((i + 1) / len(TARGETS_BENCH))

            st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)

        st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
        with st.expander("⎔ Información del sistema"):
            import platform, socket as sock
            sys_info = {
                "OS":           platform.system() + " " + platform.release(),
                "Hostname":     sock.gethostname(),
                "Python":       platform.python_version(),
                "Core LIVE":    str(CORE_AVAILABLE),
                "Streamlit":    st.__version__,
                "Target":       target,
                "Modo":         mode,
            }
            for k, v in sys_info.items():
                st.markdown(f"""
                <div style="font-family:'Roboto Mono',monospace;font-size:0.78rem;
                            padding:2px 0;border-bottom:1px solid rgba(30,45,69,0.13);">
                    <span style="color:#4a6080;min-width:120px;display:inline-block;">{k}</span>
                    <span style="color:#c8d8f0;">{v}</span>
                </div>
                """, unsafe_allow_html=True)

# =============================================================================
# TAB 4 - MONITOREO DE BIBLIOTECAS
# =============================================================================
with tab4:

    # Auto-refresh cada 30s (preserva la pestana activa gracias a st_autorefresh)
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=30000, key="lib_autorefresh")
        has_autorefresh = True
    except ImportError:
        has_autorefresh = False
        st.warning("⚠️ streamlit-autorefresh no instalado. Ejecuta: pip install streamlit-autorefresh")

    collector = get_or_create_collector(st.session_state)
    report    = collector.get_report()

    overall  = overall_status(report)
    ov_icon  = status_icon(overall)

    # Header con timestamp de actualización
    col_header, col_refresh_info = st.columns([4, 1])
    with col_header:
        st.subheader(ov_icon + " ESTADO GLOBAL: " + overall)
    with col_refresh_info:
        last_upd = report.last_update
        last_str = datetime.fromtimestamp(last_upd).strftime("%H:%M:%S") if last_upd else "-"
        if has_autorefresh:
            st.caption(f"🔄 Actualizado: {last_str}")
        else:
            st.caption(f"⏸️ {last_str}")

    if report.error:
        st.error(
            "ERROR SHEETS: " + report.error + "\n\n"
            "Verifica que credentials.json este en el directorio y que el Sheet "
            "'" + SPREADSHEET_NAME + "' este compartido con la cuenta de servicio."
        )

    if not report.snapshots:
        st.info("Esperando datos de los agentes...\n\nAsegurate de que agent.py este corriendo en las PCs de biblioteca.")
    else:
        cols = st.columns(min(len(report.snapshots), 3))
        for idx, (lib_name, snap) in enumerate(report.snapshots.items()):
            col = cols[idx % len(cols)]
            online_str = "EN LINEA" if snap.online else "FUERA DE LINEA"
            with col:
                st.markdown("**" + status_icon(snap.status) + " " + lib_name + "**")
                st.caption(online_str + " | " + snap.timestamp)
                m1, m2 = st.columns(2)
                m1.metric("HTTP ms", str(round(snap.latency_avg_ms)))
                m2.metric("ICMP ms", str(round(snap.latency_icmp_ms)))
                m3, m4 = st.columns(2)
                m3.metric("Perdida", str(round(snap.loss_pct, 1)) + "%")
                m4.metric("IP", snap.local_ip)
                st.divider()

        st.caption("HISTORIAL DE LATENCIA HTTP")
        fig = go.Figure()
        for lib_name, snap in report.snapshots.items():
            if snap.latency_history:
                # Definir colores directamente
                status_color_map = {
                    "STABLE": "#00ff41",
                    "WARNING": "#ffb300",
                    "CRITICAL": "#ff0033",
                    "UNKNOWN": "#4a6080",
                }
                color_hex = status_color_map.get(snap.status, "#4a6080")
                r_val = int(color_hex[1:3], 16)
                g_val = int(color_hex[3:5], 16)
                b_val = int(color_hex[5:7], 16)
                fig.add_trace(go.Scatter(
                    x=list(range(len(snap.latency_history))),
                    y=snap.latency_history,
                    name=lib_name,
                    mode="lines",
                    line=dict(color=color_hex, width=2),
                    fill="tozeroy",
                    fillcolor="rgba(" + str(r_val) + "," + str(g_val) + "," + str(b_val) + ",0.07)",
                ))
        fig.add_hline(y=150, line_dash="dot", line_color="#ffb300",
                      annotation_text="WARN 150ms", annotation_font_color="#ffb300",
                      annotation_font_size=10)
        fig.add_hline(y=500, line_dash="dot", line_color="#ff0033",
                      annotation_text="CRIT 500ms", annotation_font_color="#ff0033",
                      annotation_font_size=10)
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0d1117",
            font=dict(family="Roboto Mono", color="#4a6080", size=10),
            height=220, margin=dict(l=40, r=20, t=10, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        font=dict(size=10, color="#c8d8f0")),
            xaxis=dict(showgrid=False, color="#243050", title=""),
            yaxis=dict(gridcolor="#1e2d45", color="#243050",
                       title="ms", title_font=dict(color="#4a6080")),
        )
        st.plotly_chart(fig, use_container_width=True)

        rows = []
        for lib_name, snap in report.snapshots.items():
            for target_label, t_data in snap.targets.items():
                rows.append({
                    "BIBLIOTECA": lib_name,
                    "TARGET":     target_label,
                    "ESTADO":     "OK" if t_data.get("ok") else "FAIL",
                    "LATENCIA":   str(round(t_data.get("lat", 0), 1)) + " ms",
                    "HTTP CODE":  str(t_data.get("code") or "-"),
                })
        if rows:
            st.caption("DETALLE DE TARGETS")
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    last_upd = report.last_update
    last_str = datetime.fromtimestamp(last_upd).strftime("%H:%M:%S") if last_upd else "-"
    st.caption("Última lectura del Sheet: " + last_str + " - Intervalo: " + str(POLL_INTERVAL_SEC) + "s")

# -- Ciclo de Auto-Refresh (Live Monitor - Tab 1) ------------------------------
if is_active and refresh_delay is not None:
    time.sleep(refresh_delay)
    st.rerun()
