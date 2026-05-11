# v3/styles.py
# ─────────────────────────────────────────────────────────────────────────────
# UDEC Cyber-Auditor v3 | CSS Modular – Streamlit Cyberpunk Theme
# Cada bloque está separado por responsabilidad para facilitar mantenimiento.
# ─────────────────────────────────────────────────────────────────────────────

# ── 1. Paleta de colores ─────────────────────────────────────────────────────
PALETTE = {
    "bg_void":       "#080a0f",
    "bg_deep":       "#0d1117",
    "bg_panel":      "#111827",
    "bg_card":       "#131a28",
    "bg_card2":      "#0f1420",
    "border_dim":    "#1e2d45",
    "border_active": "#00f2ff44",
    "cyan":          "#00f2ff",
    "magenta":       "#ff00ff",
    "green":         "#00ff41",
    "red":           "#ff0033",
    "yellow":        "#ffb300",
    "amber":         "#ff6b00",
    "purple":        "#cc00ff",
    "text_primary":  "#c8d8f0",
    "text_dim":      "#4a6080",
    "text_muted":    "#243050",
}

# ── 2. Fuentes ───────────────────────────────────────────────────────────────
CSS_FONTS = """
@import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@300;400;500;600;700&family=Share+Tech+Mono&display=swap');
"""

# ── 3. Reset global & fondo ──────────────────────────────────────────────────
CSS_BASE = """
*, *::before, *::after {
    box-sizing: border-box;
}

html, body, [data-testid="stAppViewContainer"],
[data-testid="stApp"] {
    background-color: #080a0f !important;
    color: #c8d8f0 !important;
    font-family: 'Roboto Mono', 'Courier New', monospace !important;
}

/* Quita el fondo blanco del main container */
[data-testid="stMain"], section[data-testid="stSidebar"] > div {
    background-color: #080a0f !important;
}

/* Partículas flotantes azules */
.cyber-particles {
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    overflow: hidden;
    z-index: -1;
    pointer-events: none;
}

.particle {
    position: absolute;
    width: 2px; height: 2px;
    background: #00f2ff;
    border-radius: 50%;
    box-shadow: 0 0 6px #00f2ff, 0 0 12px #00f2ff44;
    animation: float-up 8s linear infinite;
}

.particle:nth-child(odd) {
    animation-duration: 10s;
}

.particle:nth-child(3n) {
    animation-duration: 12s;
}

@keyframes float-up {
    0% {
        transform: translateY(100vh) translateX(0);
        opacity: 0;
    }
    10% {
        opacity: 1;
    }
    90% {
        opacity: 1;
    }
    100% {
        transform: translateY(-100vh) translateX(20px);
        opacity: 0;
    }
}

/* ScrollBar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #00f2ff33; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #00f2ff88; }
"""

# ── 4. Sidebar ───────────────────────────────────────────────────────────────
CSS_SIDEBAR = """
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0d14 0%, #080a0f 100%) !important;
    border-right: 1px solid #00f2ff22 !important;
    padding-top: 0 !important;
}

[data-testid="stSidebar"]::before {
    content: '';
    display: block;
    height: 2px;
    background: linear-gradient(90deg, transparent, #00f2ff, #ff00ff, transparent);
    margin-bottom: 0.5rem;
}

[data-testid="stSidebarNav"] {
    display: none;
}

[data-testid="stSidebarNavItems"] {
    display: none;
}

[data-testid="stSidebarNavSeparator"] {
    display: none;
}

/* Logo / Header del sidebar */
.sb-logo {
    text-align: center;
    padding: 1.5rem 1rem 1rem;
    border-bottom: 1px solid #1e2d4544;
    margin-bottom: 1rem;
}

.sb-logo-title {
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.8rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    color: #00f2ff;
    text-shadow: 0 0 10px #00f2ff88;
    line-height: 1.3;
    transition: all 0.5s ease;
}

.sb-logo-title.active {
    text-shadow: 0 0 10px #00f2ff, 0 0 20px #00f2ff, 0 0 40px #00f2ff;
    animation: title-flicker 5s infinite;
}

@keyframes title-flicker {
    0%, 19%, 21%, 23%, 25%, 54%, 56%, 100% {
        opacity: 1;
        text-shadow: 0 0 10px #00f2ff, 0 0 20px #00f2ff, 0 0 40px #00f2ff;
    }
    20%, 24%, 55% {
        opacity: 0.3;
        text-shadow: none;
    }
}

.sb-logo-sub {
    font-size: 0.68rem;
    color: #4a6080;
    letter-spacing: 0.1em;
    margin-top: 2px;
}

/* Botones de navegación personalizados */
.nav-btn {
    display: block;
    width: 100%;
    padding: 0.7rem 1.2rem;
    margin: 0.25rem 0;
    background: transparent;
    border: 1px solid #1e2d45;
    color: #4a6080;
    font-family: 'Roboto Mono', monospace;
    font-size: 0.8rem;
    letter-spacing: 0.08em;
    cursor: pointer;
    text-align: left;
    transition: all 0.2s ease;
    clip-path: polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px));
    position: relative;
}

.nav-btn:hover {
    border-color: #00f2ff88;
    color: #00f2ff;
    background: #00f2ff0a;
    box-shadow: inset 0 0 15px #00f2ff0a, 0 0 8px #00f2ff22;
}

.nav-btn.active {
    border-color: #00f2ff;
    color: #00f2ff;
    background: #00f2ff11;
    box-shadow: inset 0 0 20px #00f2ff11, 0 0 12px #00f2ff33;
    text-shadow: 0 0 8px #00f2ff;
}

.nav-btn .nav-icon {
    margin-right: 0.6rem;
    opacity: 0.8;
}
"""

# ── 5. Tabs ──────────────────────────────────────────────────────────────────
CSS_TABS = """
/* Tab list container */
[data-testid="stTabs"] [role="tablist"] {
    background: #0d1117 !important;
    border-bottom: 1px solid #00f2ff33 !important;
    gap: 4px;
    padding: 0 4px;
}

[data-testid="stTabs"] *[data-baseweb="tab-highlight"] {
    background-color: #00f2ff !important;
    box-shadow: 0 0 10px #00f2ff, 0 0 20px #00f2ff66 !important;
}

[data-testid="stTabs"] *[data-baseweb="tab-border"] {
    background: transparent !important;
}

/* Cada tab */
[data-testid="stTabs"] [role="tab"] {
    font-family: 'Roboto Mono', monospace !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.1em !important;
    color: #4a6080 !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    border-bottom: none !important;
    padding: 0.6rem 1.2rem !important;
    transition: all 0.25s ease !important;
    clip-path: polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 0 100%) !important;
}

[data-testid="stTabs"] [role="tab"]:hover {
    color: #00f2ff !important;
    background: #00f2ff08 !important;
    border-color: #00f2ff33 !important;
}

[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #00f2ff !important;
    background: #00f2ff11 !important;
    border-color: #00f2ff !important;
    text-shadow: 0 0 10px #00f2ff88 !important;
    box-shadow: 0 0 14px #00f2ff22 !important;
}

/* Contenido de tab */
[data-testid="stTabsContent"] {
    background: transparent !important;
    padding-top: 1.5rem !important;
}
"""

# ── 6. Métricas (st.metric) ───────────────────────────────────────────────────
CSS_METRICS = """
[data-testid="stMetric"] {
    background: #111827 !important;
    border: 1px solid #1e2d45 !important;
    border-top: 2px solid #00f2ff !important;
    padding: 1rem !important;
    clip-path: polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px));
    transition: box-shadow 0.3s ease;
}

[data-testid="stMetric"]:hover {
    box-shadow: 0 0 20px #00f2ff1a !important;
}

[data-testid="stMetricLabel"] {
    font-family: 'Roboto Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.12em !important;
    color: #4a6080 !important;
    text-transform: uppercase !important;
}

[data-testid="stMetricValue"] {
    font-family: 'Share Tech Mono', 'Roboto Mono', monospace !important;
    font-size: 1.9rem !important;
    color: #00f2ff !important;
    text-shadow: 0 0 15px #00f2ff88 !important;
    font-weight: 700 !important;
}

[data-testid="stMetricDelta"] {
    font-family: 'Roboto Mono', monospace !important;
    font-size: 0.75rem !important;
}
"""

CSS_BUTTONS = """
/* Botón Principal (Primary) - Escalas de azul neón */
[data-testid="stBaseButton-primary"],
[data-testid="stButton"] > button[kind="primary"],
[data-testid="stButton"] > button[data-baseweb="button"]:not([kind="secondary"]) {
    font-family: 'Share Tech Mono', 'Roboto Mono', monospace !important;
    font-size: 1.1rem !important;
    letter-spacing: 0.13em !important;
    font-weight: 700 !important;
    background: linear-gradient(90deg, #001a33, #004466) !important;
    border: 1px solid #00f2ff !important;
    border-radius: 4px !important;
    color: #00f2ff !important;
    padding: 1.1rem 0.5rem !important;
    margin-bottom: 1.2rem !important;
    width: 100% !important;
    box-shadow: inset 0 0 10px #00f2ff22 !important;
    text-shadow: 0 0 8px #00f2ff66 !important;
    transition: all 0.2s !important;
}
[data-testid="stBaseButton-primary"]:hover,
[data-testid="stButton"] > button[kind="primary"]:hover,
[data-testid="stButton"] > button[data-baseweb="button"]:not([kind="secondary"]):hover {
    background: linear-gradient(90deg, #003366, #006699) !important;
    box-shadow: 0 0 20px #00f2ff55, inset 0 0 15px #00f2ff44 !important;
    color: #ffffff !important;
    text-shadow: 0 0 15px #00f2ff !important;
    border-color: #ffffff !important;
}
[data-testid="stBaseButton-primary"]:active,
[data-testid="stButton"] > button[kind="primary"]:active,
[data-testid="stButton"] > button[data-baseweb="button"]:not([kind="secondary"]):active {
    box-shadow: 0 0 5px #00f2ff44 !important;
    background: #001a33 !important;
}

/* Botón Secundario (Secondary) - Ocasional / Sutil */
[data-testid="stBaseButton-secondary"],
[data-testid="stButton"] > button[kind="secondary"] {
    font-family: 'Roboto Mono', monospace !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.08em !important;
    background: transparent !important;
    border: 1px solid #1e2d45 !important;
    border-radius: 2px !important;
    color: #4a6080 !important;
    padding: 0.4rem 0.8rem !important;
    width: auto !important;
    transition: all 0.2s !important;
}
[data-testid="stBaseButton-secondary"]:hover,
[data-testid="stButton"] > button[kind="secondary"]:hover {
    border-color: #00f2ff44 !important;
    color: #00f2ff !important;
    background: rgba(0, 242, 255, 0.05) !important;
}

/* Botón Danger */
.btn-danger [data-testid="stButton"] > button {
    border-color: #ff0033 !important;
    color: #ff0033 !important;
    text-shadow: 0 0 8px #ff003366 !important;
}
"""

# ── 8. Inputs / Selectbox ─────────────────────────────────────────────────────
CSS_INPUTS = """
[data-testid="stSelectbox"] > div > div,
[data-testid="stTextInput"] > div > div > input,
[data-testid="stNumberInput"] input {
    background: rgba(0, 242, 255, 0.03) !important;
    border: 1px solid rgba(0, 242, 255, 0.3) !important;
    border-radius: 4px !important;
    color: #00f2ff !important;
    text-shadow: 0 0 5px rgba(0, 242, 255, 0.5) !important;
    box-shadow: 0 0 8px rgba(0, 242, 255, 0.1), inset 0 0 5px rgba(0, 242, 255, 0.05) !important;
    backdrop-filter: blur(2px) !important;
    font-family: 'Share Tech Mono', 'Roboto Mono', monospace !important;
    font-size: 0.85rem !important;
    transition: all 0.3s ease;
    animation: holo-flicker 6s infinite;
}

[data-testid="stSelectbox"] > div > div:focus-within,
[data-testid="stTextInput"] > div > div:focus-within,
[data-testid="stNumberInput"] input:focus {
    border-color: #cc00ff !important;
    box-shadow: 0 0 15px rgba(204, 0, 255, 0.45), inset 0 0 10px rgba(204, 0, 255, 0.25) !important;
    color: #cc00ff !important;
    text-shadow: 0 0 8px rgba(204, 0, 255, 0.85) !important;
}

[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    outline: none !important;
}

[data-testid="stSelectbox"] label,
[data-testid="stTextInput"] label,
[data-testid="stNumberInput"] label {
    font-family: 'Share Tech Mono', 'Roboto Mono', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.15em !important;
    color: #00f2ff !important;
    text-shadow: 0 0 5px rgba(0, 242, 255, 0.6) !important;
    text-transform: uppercase !important;
}

/* Holographic effect for Streamlit Top Bars and 3 dots */
[data-testid="stHeader"] {
    background: transparent !important;
}
[data-testid="stHeader"] button,
[data-testid="stSidebarCollapsedControl"] {
    background: rgba(0, 242, 255, 0.05) !important;
    border: 1px solid rgba(0, 242, 255, 0.4) !important;
    box-shadow: 0 0 8px rgba(0, 242, 255, 0.2), inset 0 0 5px rgba(0, 242, 255, 0.1) !important;
    backdrop-filter: blur(2px) !important;
    color: #00f2ff !important;
    border-radius: 4px !important;
    transition: all 0.3s ease !important;
    animation: holo-flicker 5s infinite;
}
[data-testid="stHeader"] button:hover,
[data-testid="stSidebarCollapsedControl"]:hover {
    background: rgba(0, 242, 255, 0.15) !important;
    box-shadow: 0 0 15px rgba(0, 242, 255, 0.5), inset 0 0 10px rgba(0, 242, 255, 0.3) !important;
}

/* Holographic styling for the 3-dots Menu Popover */
div[data-baseweb="popover"] > div,
div[data-testid="stPopoverBody"] {
    background-color: rgba(13, 17, 23, 0.85) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(0, 242, 255, 0.5) !important;
    box-shadow: 0 0 20px rgba(0, 242, 255, 0.2), inset 0 0 10px rgba(0, 242, 255, 0.1) !important;
    border-radius: 4px !important;
}

ul[data-testid="main-menu-list"],
div[data-baseweb="popover"] ul {
    background-color: transparent !important;
}

ul[data-testid="main-menu-list"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 6px !important;
    padding: 0.35rem 0 !important;
}

ul[data-testid="main-menu-list"] li,
div[data-baseweb="popover"] li {
    margin: 0 !important;
}

ul[data-testid="main-menu-list"] li > div,
div[data-baseweb="popover"] li > div {
    display: flex !important;
    align-items: center !important;
    padding: 0.55rem 0.95rem !important;
    border-radius: 6px !important;
    min-height: 38px !important;
}

ul[data-testid="main-menu-list"] span,
div[data-baseweb="popover"] li span {
    font-family: 'Share Tech Mono', 'Roboto Mono', monospace !important;
    color: #c8d8f0 !important;
    transition: all 0.2s ease;
}

ul[data-testid="main-menu-list"] li:hover span,
div[data-baseweb="popover"] li:hover span {
    color: #00f2ff !important;
    text-shadow: 0 0 8px #00f2ff !important;
}

ul[data-testid="main-menu-list"] li:hover,
div[data-baseweb="popover"] li:hover {
    background-color: rgba(0, 242, 255, 0.15) !important;
}
"""

# ── 9. Cards / Containers personalizados ──────────────────────────────────────
CSS_CARDS = """
.cyber-card {
    background: #111827;
    border: 1px solid #1e2d45;
    border-top: 2px solid #ff00ff;
    padding: 1.2rem;
    margin-bottom: 1rem;
    clip-path: polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px));
    position: relative;
}

.cyber-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #ff00ff, #00f2ff, #ff00ff);
    opacity: 0.6;
}

.cyber-card-cyan {
    border-top-color: #00f2ff;
}

.cyber-card-green {
    border-top-color: #00ff41;
}

.cyber-card-red {
    border-top-color: #ff0033;
}

.cyber-section-title {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.2em;
    color: #4a6080;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid #1e2d45;
}

.cyber-section-title span {
    color: #ff00ff;
    text-shadow: 0 0 8px #ff00ff66;
}

.status-badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    font-size: 0.7rem;
    letter-spacing: 0.15em;
    font-family: 'Roboto Mono', monospace;
    font-weight: 600;
    clip-path: polygon(0 0, calc(100% - 5px) 0, 100% 5px, 100% 100%, 5px 100%, 0 calc(100% - 5px));
}

.status-healthy  { background: #00ff411a; color: #00ff41; border: 1px solid #00ff4166; text-shadow: 0 0 8px #00ff4188; }
.status-warning  { background: #ffb3001a; color: #ffb300; border: 1px solid #ffb30066; text-shadow: 0 0 8px #ffb30088; }
.status-critical { background: #ff00331a; color: #ff0033; border: 1px solid #ff003366; text-shadow: 0 0 8px #ff003388; animation: blink-critical 1s ease infinite; }

@keyframes blink-critical {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* Scanline overlay (terminal effect) */
.scanlines {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(0, 242, 255, 0.015) 2px,
        rgba(0, 242, 255, 0.015) 4px
    );
    pointer-events: none;
    z-index: 9999;
}
"""

# ── 10. Header animado ────────────────────────────────────────────────────────
CSS_HEADER = """
.cyber-header {
    text-align: center;
    padding: 2rem 0 1rem;
    position: relative;
}

.cyber-header.inactive h1 {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 3.2rem !important;
    font-weight: 900 !important;
    letter-spacing: 0.25em !important;
    color: #4a6080 !important;
    text-shadow: none !important;
    animation: none !important;
    margin: 0 !important;
    position: relative;
}

.cyber-header.active h1 {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 3.2rem !important;
    font-weight: 900 !important;
    letter-spacing: 0.25em !important;
    color: #e0ffff !important;
    text-shadow: 
        0 0 10px #00f2ff, 
        0 0 20px #00f2ff, 
        0 0 40px #00f2ff,
        0 0 80px #00f2ff,
        3px 3px 0px rgba(255, 0, 255, 0.5),
        -3px -3px 0px rgba(0, 242, 255, 0.5) !important;
    animation: holo-flicker 4s infinite !important;
    margin: 0 !important;
    position: relative;
}

.cyber-header.inactive .sub {
    font-family: 'Roboto Mono', monospace;
    font-size: 0.8rem;
    letter-spacing: 0.4em;
    color: #4a6080;
    text-shadow: none;
    margin-top: 0.4rem;
    text-transform: uppercase;
}

.cyber-header.active .sub {
    font-family: 'Roboto Mono', monospace;
    font-size: 0.8rem;
    letter-spacing: 0.4em;
    color: #00f2ff;
    text-shadow: 0 0 8px #00f2ff88;
    margin-top: 0.4rem;
    text-transform: uppercase;
}

@keyframes holo-flicker {
    0%, 19%, 21%, 23%, 25%, 54%, 56%, 100% {
        opacity: 1;
        transform: skew(0deg) translate(0);
        filter: blur(0px);
    }
    20% {
        opacity: 0.5;
        transform: skew(-10deg) translate(-2px, 1px);
        filter: blur(1px);
    }
    24% {
        opacity: 0.3;
        transform: skew(15deg) translate(2px, -1px);
    }
    55% {
        opacity: 0.8;
        transform: skew(0deg) translate(1px, 1px);
        filter: blur(0px);
    }
}

/* Línea decorativa debajo del header */
.cyber-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #00f2ff, #ff00ff, transparent);
    margin: 0.8rem 0 1.5rem;
    opacity: 0.7;
}
"""

# ── 11. Terminal output (logs / diagnósticos) ─────────────────────────────────
CSS_TERMINAL = """
.terminal-box {
    background: #030508;
    border: 1px solid #00f2ff33;
    border-left: 3px solid #00f2ff;
    padding: 1rem 1.2rem;
    font-family: 'Share Tech Mono', 'Roboto Mono', monospace;
    font-size: 0.8rem;
    line-height: 1.8;
    color: #00f2ff;
    min-height: 120px;
    max-height: 320px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-all;
}

.terminal-box .t-ok    { color: #00ff41; }
.terminal-box .t-warn  { color: #ffb300; }
.terminal-box .t-err   { color: #ff0033; }
.terminal-box .t-info  { color: #00f2ff; }
.terminal-box .t-muted { color: #4a6080; }

.terminal-cursor::after {
    content: '_';
    animation: blink-cursor 1s step-end infinite;
}

@keyframes blink-cursor {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
}
"""

# ── 12. Progress / Gauge ──────────────────────────────────────────────────────
CSS_PROGRESS = """
.cyber-gauge-label {
    font-family: 'Roboto Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.1em;
    color: #4a6080;
    text-transform: uppercase;
    margin-bottom: 4px;
}

.cyber-gauge-value {
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.1rem;
    color: #00f2ff;
    text-shadow: 0 0 10px #00f2ff88;
}

[data-testid="stProgress"] > div > div {
    background: #1e2d45 !important;
    border-radius: 0 !important;
}

[data-testid="stProgress"] > div > div > div {
    background: linear-gradient(90deg, #00f2ff, #ff00ff) !important;
    border-radius: 0 !important;
    box-shadow: 0 0 10px #00f2ff88 !important;
}
"""

# ── 13. Dataframe ─────────────────────────────────────────────────────────────
CSS_DATAFRAME = """
[data-testid="stDataFrame"] table {
    font-family: 'Roboto Mono', monospace !important;
    font-size: 0.78rem !important;
    background: #0d1117 !important;
}

[data-testid="stDataFrame"] th {
    background: #111827 !important;
    color: #ff00ff !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    border-bottom: 1px solid #ff00ff44 !important;
}

[data-testid="stDataFrame"] td {
    color: #c8d8f0 !important;
    border-bottom: 1px solid #1e2d4544 !important;
}

[data-testid="stDataFrame"] tr:hover td {
    background: #00f2ff08 !important;
}
"""

# ── 14. Animaciones y Easter Eggs ───────────────────────────────────────────
CSS_ANIMATIONS = """
/* Glitch Effect mejorado */
@keyframes glitch-anim {
    0% { 
        transform: translate(0) skew(0deg);
        filter: hue-rotate(0deg);
    }
    20% { 
        transform: translate(-2px, 1px) skew(-2deg);
        filter: hue-rotate(90deg);
    }
    40% { 
        transform: translate(-1px, -1px) skew(1deg);
        filter: hue-rotate(180deg);
    }
    60% { 
        transform: translate(2px, 1px) skew(-1deg);
        filter: hue-rotate(270deg);
    }
    80% { 
        transform: translate(1px, -1px) skew(2deg);
        filter: hue-rotate(360deg);
    }
    100% { 
        transform: translate(0) skew(0deg);
        filter: hue-rotate(0deg);
    }
}

.glitch-critical {
    animation: glitch-anim 0.2s infinite;
    text-shadow: 
        -2px 0 #ff00ff, 
        2px 0 #00f2ff,
        0 0 10px #ff00ff,
        0 0 20px #ff0033;
    position: relative;
}

.glitch-critical::before,
.glitch-critical::after {
    content: attr(data-text);
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: transparent;
    overflow: hidden;
}

.glitch-critical::before {
    left: 2px;
    text-shadow: -1px 0 #ff00ff;
    animation: glitch-anim 0.3s infinite reverse;
    clip-path: polygon(0 0, 100% 0, 100% 45%, 0 45%);
}

.glitch-critical::after {
    left: -2px;
    text-shadow: -1px 0 #00f2ff;
    animation: glitch-anim 0.25s infinite;
    clip-path: polygon(0 55%, 100% 55%, 100% 100%, 0 100%);
}

.glitch-warning {
    animation: glitch-anim 1s infinite;
    text-shadow: -1px 0 #ffb300, 1px 0 #00f2ff;
}

/* Glitch realista para tabla DIAGNÓSTICO L7 */
.glitch-diagnostic {
    position: relative;
    animation: diagnostic-glitch 0.15s infinite;
    filter: url(#svg-glitch-filter);
}

@keyframes diagnostic-glitch {
    0% {
        transform: translate(0);
        filter: hue-rotate(0deg) saturate(1);
    }
    5% {
        transform: translate(-1px, 1px);
        filter: hue-rotate(90deg) saturate(2);
    }
    10% {
        transform: translate(1px, -1px);
        filter: hue-rotate(180deg) saturate(0.5);
    }
    15% {
        transform: translate(-2px, 0);
        filter: hue-rotate(270deg) saturate(3);
    }
    20% {
        transform: translate(0, 2px);
        filter: hue-rotate(360deg) saturate(1.5);
    }
    25% {
        transform: translate(1px, 1px);
        filter: hue-rotate(45deg) saturate(0.8);
    }
    30% {
        transform: translate(-1px, -2px);
        filter: hue-rotate(135deg) saturate(2.5);
    }
    35% {
        transform: translate(2px, -1px);
        filter: hue-rotate(225deg) saturate(1.2);
    }
    40% {
        transform: translate(-2px, 2px);
        filter: hue-rotate(315deg) saturate(0.6);
    }
    45% {
        transform: translate(1px, 0);
        filter: hue-rotate(60deg) saturate(1.8);
    }
    50% {
        transform: translate(0, -1px);
        filter: hue-rotate(150deg) saturate(2.2);
    }
    55% {
        transform: translate(-1px, 1px);
        filter: hue-rotate(240deg) saturate(0.9);
    }
    60% {
        transform: translate(2px, 1px);
        filter: hue-rotate(300deg) saturate(1.6);
    }
    65% {
        transform: translate(-1px, -1px);
        filter: hue-rotate(30deg) saturate(2.8);
    }
    70% {
        transform: translate(1px, 2px);
        filter: hue-rotate(120deg) saturate(0.7);
    }
    75% {
        transform: translate(-2px, -2px);
        filter: hue-rotate(210deg) saturate(1.4);
    }
    80% {
        transform: translate(2px, 0);
        filter: hue-rotate(300deg) saturate(2.1);
    }
    85% {
        transform: translate(0, 1px);
        filter: hue-rotate(30deg) saturate(0.5);
    }
    90% {
        transform: translate(-1px, -1px);
        filter: hue-rotate(120deg) saturate(1.9);
    }
    95% {
        transform: translate(1px, 1px);
        filter: hue-rotate(240deg) saturate(1.3);
    }
    100% {
        transform: translate(0);
        filter: hue-rotate(0deg) saturate(1);
    }
}

.glitch-diagnostic::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(
        90deg,
        transparent 0%,
        rgba(255, 0, 51, 0.1) 20%,
        transparent 40%,
        rgba(0, 242, 255, 0.1) 60%,
        transparent 80%,
        rgba(255, 0, 255, 0.1) 100%
    );
    animation: diagnostic-scan 0.5s linear infinite;
    pointer-events: none;
}

@keyframes diagnostic-scan {
    0% {
        transform: translateX(-100%);
    }
    100% {
        transform: translateX(100%);
    }
}

.glitch-diagnostic tr:nth-child(even) {
    animation: diagnostic-row-glitch 0.2s infinite alternate;
}

@keyframes diagnostic-row-glitch {
    0% {
        opacity: 1;
        transform: translateX(0);
    }
    100% {
        opacity: 0.3;
        transform: translateX(2px);
    }
}

/* Efecto de corrupción de texto */
.glitch-diagnostic td {
    position: relative;
}

.glitch-diagnostic td::after {
    content: attr(data-corrupted);
    position: absolute;
    top: 0; left: 0;
    color: #ff0033;
    opacity: 0;
    animation: text-corruption 3s infinite;
    pointer-events: none;
}

@keyframes text-corruption {
    0%, 85%, 100% {
        opacity: 0;
    }
    86%, 88%, 90%, 92%, 94% {
        opacity: 0.8;
    }
    87%, 89%, 91%, 93% {
        opacity: 0.2;
    }
}

@keyframes scan {
    0% {
        transform: translateX(-100%);
    }
    100% {
        transform: translateX(100%);
    }
}


/* Pulso Neón para textos especiales */
@keyframes pulse-neon {
    0%, 100% {
        color: #ff0033;
        text-shadow: 0 0 5px #ff0033, 0 0 10px #ff0033, 0 0 20px #ff0033;
    }
    50% {
        color: #00f2ff;
        text-shadow: 0 0 5px #00f2ff, 0 0 10px #00f2ff, 0 0 20px #00f2ff;
    }
}
.pulse-neon-text {
    animation: pulse-neon 4s ease-in-out infinite;
    font-family: 'Share Tech Mono', 'Roboto Mono', monospace;
    font-size: 0.8rem;
    font-weight: bold;
    letter-spacing: 0.15em;
    text-align: left;
    margin: 0.2rem 0;
}

/* Matrix Rain Containers */
.matrix-rain-container {
    position: fixed;
    top: 0;
    height: 100vh;
    width: 60px;
    overflow: hidden;
    z-index: 999999;
    opacity: 0.5;
    pointer-events: none;
    font-family: 'Share Tech Mono', 'Roboto Mono', monospace;
    font-size: 1.2rem;
    line-height: 1.2;
    color: #00f2ff;
    text-align: center;
}
.matrix-rain-left { left: 0; }
.matrix-rain-right { right: 0; }

@keyframes fall {
    0% { transform: translateY(-100vh); }
    100% { transform: translateY(100vh); }
}
.matrix-drop {
    position: absolute;
    width: 20px;
    animation: fall linear infinite;
    text-shadow: 0 0 8px #00f2ff, 0 0 15px #00f2ff;
}
.matrix-drop:nth-child(1) { animation-duration: 5s; animation-delay: 0s; left: 0px; }
.matrix-drop:nth-child(2) { animation-duration: 8s; animation-delay: 2s; left: 20px; }
.matrix-drop:nth-child(3) { animation-duration: 6s; animation-delay: 4s; left: 40px; }
"""

# ── Función ensambladora ──────────────────────────────────────────────────────
def get_full_css() -> str:
    """Retorna el bloque CSS completo listo para inyectar con st.markdown."""
    return f"""
<style>
{CSS_FONTS}
{CSS_BASE}
{CSS_SIDEBAR}
{CSS_TABS}
{CSS_METRICS}
{CSS_BUTTONS}
{CSS_INPUTS}
{CSS_CARDS}
{CSS_HEADER}
{CSS_TERMINAL}
{CSS_PROGRESS}
{CSS_DATAFRAME}
{CSS_ANIMATIONS}
</style>
"""
