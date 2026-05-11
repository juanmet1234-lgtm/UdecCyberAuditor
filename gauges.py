# v3/gauges.py
# ─────────────────────────────────────────────────────────────────────────────
# UDEC Cyber-Auditor v3 | SVG Cyberpunk Gauges
#
# Genera HTML/SVG puro, inyectable con st.markdown(unsafe_allow_html=True).
# No requiere Plotly ni ninguna librería extra.
#
# Gauges disponibles:
#   render_arc_gauge()        → Medidor de arco semicircular con HUD
#   render_latency_gauge()    → Latencia (0–1000ms) neon cyan/magenta
#   render_signal_gauge()     → Nivel de señal / conexión (0–100) verde neón
#   render_gauge_row()        → Fila con ambos medidores side-by-side
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations
import math


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de geometría SVG
# ─────────────────────────────────────────────────────────────────────────────

def _polar(cx: float, cy: float, r: float, angle_deg: float) -> tuple[float, float]:
    """Convierte ángulo (0°=arriba, sentido horario) a coordenadas cartesianas."""
    rad = math.radians(angle_deg - 90)
    return cx + r * math.cos(rad), cy + r * math.sin(rad)


def _arc_path(cx: float, cy: float, r: float,
              start_deg: float, end_deg: float) -> str:
    """Genera el atributo 'd' de un arco SVG entre start_deg y end_deg."""
    # Normaliza para que el barrido siempre sea ≤ 359.99 grados
    sweep = (end_deg - start_deg) % 360
    if sweep == 0:
        sweep = 0.001

    x1, y1 = _polar(cx, cy, r, start_deg)
    x2, y2 = _polar(cx, cy, r, end_deg)
    large = 1 if sweep > 180 else 0

    return (
        f"M {x1:.3f} {y1:.3f} "
        f"A {r} {r} 0 {large} 1 {x2:.3f} {y2:.3f}"
    )


def _tick_path(cx: float, cy: float, r_outer: float, r_inner: float,
               angle_deg: float) -> str:
    """Genera una línea de graduación radial."""
    x1, y1 = _polar(cx, cy, r_outer, angle_deg)
    x2, y2 = _polar(cx, cy, r_inner, angle_deg)
    return f"M {x1:.2f} {y1:.2f} L {x2:.2f} {y2:.2f}"


# ─────────────────────────────────────────────────────────────────────────────
# Generador de arco base
# ─────────────────────────────────────────────────────────────────────────────

def render_arc_gauge(
    value: float,
    max_value: float,
    label: str,
    unit: str = "",
    # Ángulos del arco: 225° a 315° = 270° de barrido (horseshoe)
    start_deg: float = 225,
    end_deg: float = 315,
    # Colores
    color_low: str = "#00ff41",       # verde neón
    color_mid: str = "#ffb300",       # ámbar
    color_high: str = "#ff0033",      # rojo crítico
    bg_color: str = "#080a0f",
    track_color: str = "#1a2035",
    # Umbrales de color (% del max)
    threshold_mid: float = 0.5,
    threshold_high: float = 0.80,
    # Dimensiones
    size: int = 220,
    stroke_width: float = 14,
    # Opciones visuales
    show_ticks: bool = True,
    num_ticks: int = 10,
    show_glow: bool = True,
    sublabel: str = "",
    invert_colors: bool = False,      # Para latencia: rojo=bajo es bueno
    # ID único para aislar filtros SVG
    uid: str = "g0",
) -> str:
    """
    Retorna HTML completo de un gauge SVG estilo HUD cyberpunk.
    """
    cx = size / 2
    cy = size / 2
    r = (size / 2) - stroke_width - 8

    # Normaliza valor al rango [0, 1]
    ratio = max(0.0, min(1.0, value / max_value if max_value > 0 else 0))

    # Calcula el ángulo de la aguja
    total_sweep = (end_deg - start_deg) % 360  # 270° por defecto
    fill_deg = start_deg + total_sweep * ratio
    # Si ratio == 0, arco vacío → usa un arco invisible ínfimo
    arc_end = fill_deg if ratio > 0.001 else start_deg + 0.01

    # Color dinámico del arco según nivel
    if invert_colors:
        # Latencia: bajo=bueno (verde), alto=malo (rojo)
        if ratio < threshold_mid:
            arc_color = color_low
        elif ratio < threshold_high:
            arc_color = color_mid
        else:
            arc_color = color_high
    else:
        # Señal/calidad: alto=bueno (verde), bajo=malo (rojo)
        if ratio > threshold_mid:
            arc_color = color_low
        elif ratio > (1 - threshold_high):
            arc_color = color_mid
        else:
            arc_color = color_high

    # ── Graduaciones ──────────────────────────────────────────────────────────
    ticks_svg = ""
    if show_ticks:
        for i in range(num_ticks + 1):
            t_ratio = i / num_ticks
            t_angle = start_deg + total_sweep * t_ratio
            is_major = (i % (num_ticks // 5) == 0) if num_ticks >= 5 else True
            r_outer = r + stroke_width * 0.5
            r_inner = r_outer - (stroke_width * 0.6 if is_major else stroke_width * 0.35)
            t_color = arc_color if t_ratio <= ratio else "#2a3550"
            t_width = 2.0 if is_major else 1.0
            path = _tick_path(cx, cy, r_outer, r_inner, t_angle)
            ticks_svg += f'<path d="{path}" stroke="{t_color}" stroke-width="{t_width}" opacity="0.8"/>\n'

    # ── Etiquetas de escala (min / mid / max) ────────────────────────────────
    scale_labels = ""
    for t_ratio, t_val in [(0, 0), (0.5, max_value / 2), (1.0, max_value)]:
        angle = start_deg + total_sweep * t_ratio
        rx, ry = _polar(cx, cy, r - stroke_width * 1.6, angle)
        val_str = f"{int(t_val)}"
        scale_labels += (
            f'<text x="{rx:.1f}" y="{ry:.1f}" '
            f'text-anchor="middle" dominant-baseline="middle" '
            f'fill="#2a3550" font-size="9" font-family="Roboto Mono,monospace">'
            f'{val_str}</text>\n'
        )

    # ── Aguja indicadora ──────────────────────────────────────────────────────
    needle_angle = start_deg + total_sweep * ratio
    nx, ny = _polar(cx, cy, r - stroke_width * 0.5, needle_angle)
    needle_svg = (
        f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{nx:.1f}" y2="{ny:.1f}" '
        f'stroke="{arc_color}" stroke-width="2.5" stroke-linecap="round" '
        f'opacity="0.9"/>\n'
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="{arc_color}" '
        f'opacity="0.9"/>\n'
    )

    # ── Texto central ─────────────────────────────────────────────────────────
    # Formato del valor: entero si >10, 1 decimal si pequeño
    if max_value <= 10:
        val_display = f"{value:.1f}"
    elif value >= 1000:
        val_display = f"{value/1000:.1f}k"
    else:
        val_display = f"{int(round(value))}"

    # ── Filtros de glow ───────────────────────────────────────────────────────
    filters_svg = ""
    if show_glow:
        filters_svg = f"""
        <defs>
            <filter id="glow_{uid}" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="3.5" result="blur1"/>
                <feGaussianBlur stdDeviation="7" result="blur2"/>
                <feMerge>
                    <feMergeNode in="blur2"/>
                    <feMergeNode in="blur1"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>
            <filter id="glow_strong_{uid}" x="-80%" y="-80%" width="260%" height="260%">
                <feGaussianBlur stdDeviation="5" result="b1"/>
                <feGaussianBlur stdDeviation="10" result="b2"/>
                <feMerge>
                    <feMergeNode in="b2"/>
                    <feMergeNode in="b1"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>
            <linearGradient id="arc_grad_{uid}" gradientUnits="userSpaceOnUse"
                x1="{_polar(cx,cy,r,start_deg)[0]:.1f}"
                y1="{_polar(cx,cy,r,start_deg)[1]:.1f}"
                x2="{_polar(cx,cy,r,fill_deg)[0]:.1f}"
                y2="{_polar(cx,cy,r,fill_deg)[1]:.1f}">
                <stop offset="0%" stop-color="{arc_color}" stop-opacity="0.6"/>
                <stop offset="100%" stop-color="{arc_color}" stop-opacity="1.0"/>
            </linearGradient>
        </defs>
        """
        glow_filter = f'filter="url(#glow_{uid})"'
        strong_filter = f'filter="url(#glow_strong_{uid})"'
    else:
        glow_filter = ""
        strong_filter = ""

    # ── Arco de fondo (track) ─────────────────────────────────────────────────
    track_path = _arc_path(cx, cy, r, start_deg, end_deg)

    # ── Arco de valor (fill) ──────────────────────────────────────────────────
    fill_path = _arc_path(cx, cy, r, start_deg, arc_end)
    fill_color_attr = f"url(#arc_grad_{uid})" if show_glow else arc_color

    # ── Decoraciones angulares (esquinas HUD) ─────────────────────────────────
    corner_size = 10
    hud_corners = f"""
    <rect x="0" y="0" width="{corner_size}" height="2" fill="{arc_color}" opacity="0.5"/>
    <rect x="0" y="0" width="2" height="{corner_size}" fill="{arc_color}" opacity="0.5"/>
    <rect x="{size-corner_size}" y="{size-2}" width="{corner_size}" height="2" fill="{arc_color}" opacity="0.3"/>
    <rect x="{size-2}" y="{size-corner_size}" width="2" height="{corner_size}" fill="{arc_color}" opacity="0.3"/>
    """

    # ── Anillo interior decorativo ────────────────────────────────────────────
    inner_r = r - stroke_width * 1.8
    inner_ring = (
        f'<circle cx="{cx}" cy="{cy}" r="{inner_r:.1f}" '
        f'fill="none" stroke="{arc_color}" stroke-width="0.5" '
        f'stroke-dasharray="3 6" opacity="0.25"/>\n'
    )

    # ── Ensamble final (sin comentarios HTML para evitar escape de Streamlit) ──
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}" '
        f'style="display:block;margin:auto;overflow:visible;">'
        + filters_svg
        + f'<rect width="{size}" height="{size}" fill="{bg_color}" rx="4"/>'
        + hud_corners
        + f'<path d="{track_path}" fill="none" stroke="{track_color}" '
          f'stroke-width="{stroke_width}" stroke-linecap="butt"/>'
        + f'<path d="{track_path}" fill="none" stroke="{arc_color}" '
          f'stroke-width="{stroke_width * 0.15:.1f}" stroke-linecap="butt" opacity="0.08"/>'
        + inner_ring
        + ticks_svg
        + scale_labels
        + f'<path d="{fill_path}" fill="none" stroke="{fill_color_attr}" '
          f'stroke-width="{stroke_width}" stroke-linecap="butt" {glow_filter}/>'
        + f'<path d="{fill_path}" fill="none" stroke="white" '
          f'stroke-width="0.8" stroke-linecap="butt" opacity="0.12"/>'
        + needle_svg
        + f'<text x="{cx}" y="{cy - 10}" text-anchor="middle" '
          f'dominant-baseline="middle" fill="{arc_color}" font-size="28" '
          f'font-weight="700" font-family="Share Tech Mono,Roboto Mono,monospace" '
          f'letter-spacing="2" {strong_filter}>{val_display}</text>'
        + f'<text x="{cx}" y="{cy + 20}" text-anchor="middle" '
          f'dominant-baseline="middle" fill="{arc_color}" font-size="10" '
          f'font-family="Roboto Mono,monospace" opacity="0.7">{unit}</text>'
        + f'<text x="{cx}" y="{size - 18}" text-anchor="middle" '
          f'dominant-baseline="middle" fill="#4a6080" font-size="9" '
          f'letter-spacing="3" font-family="Roboto Mono,monospace">{label.upper()}</text>'
        + (f'<text x="{cx}" y="{size - 6}" text-anchor="middle" '
           f'dominant-baseline="middle" fill="{arc_color}" font-size="8" '
           f'letter-spacing="2" font-family="Roboto Mono,monospace" '
           f'opacity="0.85">{sublabel}</text>' if sublabel else '')
        + '</svg>'
    )
    return svg


# ─────────────────────────────────────────────────────────────────────────────
# Gauge de Latencia (0–1000ms)
# ─────────────────────────────────────────────────────────────────────────────

def render_latency_gauge(latency_ms: float, size: int = 220, uid: str = "lat") -> str:
    """
    Medidor de latencia:
      0–150ms   → Verde neón (ÓPTIMO)
      150–500ms → Ámbar      (ADVERTENCIA)
      500–1000ms→ Rojo neón  (CRÍTICO)
    """
    # Determina sublabel
    if latency_ms < 80:
        sublabel = "ÓPTIMO"
    elif latency_ms < 150:
        sublabel = "ESTABLE"
    elif latency_ms < 500:
        sublabel = "DEGRADADO"
    else:
        sublabel = "CRÍTICO"

    return render_arc_gauge(
        value          = latency_ms,
        max_value      = 1000,
        label          = "Latencia",
        unit           = "ms",
        color_low      = "#00f2ff",   # cyan  → latencia baja
        color_mid      = "#ffb300",   # ámbar → media
        color_high     = "#ff0033",   # rojo  → alta
        track_color    = "#0f1a2e",
        threshold_mid  = 0.15,        # 150ms / 1000ms
        threshold_high = 0.50,        # 500ms / 1000ms
        invert_colors  = True,
        size           = size,
        show_ticks     = True,
        num_ticks      = 10,
        sublabel       = sublabel,
        uid            = uid,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Gauge de Nivel de Conexión / Señal (0–100)
# ─────────────────────────────────────────────────────────────────────────────

def render_signal_gauge(
    signal_pct: float,
    size: int = 220,
    uid: str = "sig",
) -> str:
    """
    Medidor de calidad de conexión (100 = perfecta, 0 = sin señal).
    Derivado del error_rate y congestion_score.
    """
    if signal_pct >= 90:
        sublabel = "EXCELENTE"
    elif signal_pct >= 70:
        sublabel = "BUENA"
    elif signal_pct >= 40:
        sublabel = "DÉBIL"
    else:
        sublabel = "SIN SEÑAL"

    return render_arc_gauge(
        value          = signal_pct,
        max_value      = 100,
        label          = "Señal / Calidad",
        unit           = "%",
        color_low      = "#00ff41",   # verde neón  → señal alta (buena)
        color_mid      = "#ffb300",   # ámbar       → media
        color_high     = "#ff0033",   # rojo        → baja (mala)
        track_color    = "#0f1a2e",
        threshold_mid  = 0.70,        # >70% bueno
        threshold_high = 0.40,        # >40% medio
        invert_colors  = False,       # Alto = bueno
        size           = size,
        show_ticks     = True,
        num_ticks      = 10,
        sublabel       = sublabel,
        uid            = uid,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Gauge de Congestión (0–100, donde 0 = sin congestión)
# ─────────────────────────────────────────────────────────────────────────────

def render_congestion_gauge(
    congestion_score: float,
    size: int = 220,
    uid: str = "cong",
) -> str:
    """
    Medidor de congestión de red.
    0  = red libre (verde)
    100= red saturada (rojo)
    """
    if congestion_score < 20:
        sublabel = "LIBRE"
    elif congestion_score < 50:
        sublabel = "MODERADA"
    elif congestion_score < 80:
        sublabel = "ALTA"
    else:
        sublabel = "SATURADA"

    return render_arc_gauge(
        value          = congestion_score,
        max_value      = 100,
        label          = "Congestión",
        unit           = "/100",
        color_low      = "#cc00ff",   # magenta → poco indica baja cong.
        color_mid      = "#ffb300",
        color_high     = "#ff0033",
        track_color    = "#0f1a2e",
        threshold_mid  = 0.50,
        threshold_high = 0.80,
        invert_colors  = True,        # Alto = malo
        size           = size,
        show_ticks     = True,
        num_ticks      = 10,
        sublabel       = sublabel,
        uid            = uid,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Fila completa de 3 medidores (HTML envolvente)
# ─────────────────────────────────────────────────────────────────────────────

def render_gauge_row(
    latency_ms: float,
    signal_pct: float,
    congestion_score: float,
    gauge_size: int = 200,
) -> str:
    """
    Retorna HTML con los 3 gauges lado a lado, con contenedor cyberpunk.
    Listo para st.markdown(unsafe_allow_html=True).
    """
    lat_svg  = render_latency_gauge(latency_ms,      size=gauge_size, uid="lat_r")
    sig_svg  = render_signal_gauge(signal_pct,        size=gauge_size, uid="sig_r")
    cong_svg = render_congestion_gauge(congestion_score, size=gauge_size, uid="cong_r")

    sep_cyan = (
        '<div style="width:1px;height:160px;'
        'background:linear-gradient(180deg,transparent,rgba(0,242,255,0.27),transparent);">'
        '</div>'
    )
    sep_mag = (
        '<div style="width:1px;height:160px;'
        'background:linear-gradient(180deg,transparent,rgba(255,0,255,0.27),transparent);">'
        '</div>'
    )
    glow_top = (
        '<div style="position:absolute;top:0;left:0;right:0;height:2px;'
        'background:linear-gradient(90deg,transparent,#00f2ff,#ff00ff,transparent);'
        'opacity:0.7;"></div>'
    )
    glow_bot = (
        '<div style="position:absolute;bottom:0;left:0;right:0;height:1px;'
        'background:linear-gradient(90deg,transparent,#ff00ff,#00f2ff,transparent);'
        'opacity:0.4;"></div>'
    )

    html = (
        '<div style="display:flex;justify-content:space-around;align-items:center;'
        'gap:1rem;padding:1.2rem 0.5rem;background:#080a0f;'
        'border:1px solid rgba(0,242,255,0.15);border-top:2px solid #00f2ff;'
        'position:relative;overflow:hidden;">'
        + glow_top
        + f'<div style="text-align:center;flex:1;">{lat_svg}</div>'
        + sep_cyan
        + f'<div style="text-align:center;flex:1;">{sig_svg}</div>'
        + sep_mag
        + f'<div style="text-align:center;flex:1;">{cong_svg}</div>'
        + glow_bot
        + '</div>'
    )
    return html
