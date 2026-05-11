# DOCUMENTACIÓN TÉCNICA - UDEC Cyber-Auditor v3

**Versión:** 3.0 · Streamlit Edition  
**Fecha:** 5 de mayo de 2026  
**Autor:** UDEC · Comunicación de Datos  
**Propósito:** Platform de monitoreo de red con interfaz Cyberpunk en tiempo real

---

## 📋 TABLA DE CONTENIDOS

1. [Descripción General](#descripción-general)
2. [Arquitectura de Sistemas](#arquitectura-de-sistemas)
3. [Dependencias y Frameworks](#dependencias-y-frameworks)
4. [Componentes Técnicos](#componentes-técnicos)
5. [Guía de Código Detallada](#guía-de-código-detallada)
6. [Flujo de Datos](#flujo-de-datos)
7. [Guía de Ejecución](#guía-de-ejecución)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Descripción General

**UDEC Cyber-Auditor v3** es un **Dashboard de Monitoreo de Red** basado en **Streamlit**, diseñado para la **Universidad de Cundinamarca (UDEC)** con una estética **Cyberpunk/Neon**. 

### Características principales:

- ✅ **Monitoreo en Tiempo Real**: Captura de métricas L7 (HTTP) mediante `HttpProber`
- 🎨 **Interfaz Cyberpunk**: CSS personalizado con efectos neon, particles flotantes y animaciones
- 📊 **Gauges SVG Interactivos**: Medidores estilo HUD sin dependencias externas
- 🗺️ **Mapa Regional Interactivo**: Visualización de nodos UDEC usando PyDeck
- 🔄 **Simulación Integrada**: Modo simulación para pruebas sin conexión real
- 🧵 **Concurrencia Thread-Safe**: Manejo de hilos para no bloquear la UI de Streamlit

### Modos de operación:

```
┌─────────────────────────────────────────────┐
│        UDEC Cyber-Auditor v3                │
├─────────────────────────────────────────────┤
│                                             │
│  Modo LIVE:       HttpProber real (core/)  │
│  Modo SIM:        Datos sintéticos         │
│                                             │
│  Targets:         portal.udec.edu.co       │
│                   8.8.8.8 (DNS)            │
│                   1.1.1.1 (Cloudflare)     │
│                   google.com               │
│                                             │
│  Refresh Rate:    0.5s – 3.0s (configurable)│
│                                             │
└─────────────────────────────────────────────┘
```

---

## 🏗️ Arquitectura de Sistemas

### Diagrama de Componentes:

```
┌─────────────────────────────────────────────────────────────────┐
│                     STREAMLIT UI FRONTEND                       │
│  (app_streamlit.py)                                             │
│  • Tabs: Monitor, Mapa Regional, Admin/Diagnóstico            │
│  • Renders: Gauges SVG, Gráficos Plotly, Tablas pandas        │
│  • Estado: session_state (persistent entre re-renders)        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │  data_bridge   │  ◄─── CORE LOGIC
                    │   (v3/)        │
                    └───────┬────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   ┌────▼─────┐    ┌────────▼────────┐   ┌─────▼──────┐
   │LiveProber │    │SimulatedProber │   │ PingResult │
   │(wraps     │    │(synthetic)     │   │ (dataclass)│
   │core/)     │    │                │   │            │
   └────┬─────┘    └────────┬────────┘   └─────┬──────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                    ┌───────▼────────┐
                    │NetworkSnapshot │  ◄─── NORMALIZED OUTPUT
                    │  (dataclass)   │
                    └────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   ┌────▼──────┐     ┌──────▼──────┐    ┌──────▼───────┐
   │ gauges.py │     │ styles.py   │    │  app_streamlit│
   │(SVG gen)  │     │ (CSS inject)│    │  (rendering) │
   └───────────┘     └─────────────┘    └──────────────┘
```

### Capas de la aplicación:

| Capa | Responsabilidad | Archivos |
|------|-----------------|----------|
| **UI / Presentación** | Renderizado Streamlit, CSS, componentes | `app_streamlit.py`, `styles.py` |
| **Visualización** | Generación SVG, gráficos Plotly | `gauges.py`, `app_streamlit.py` |
| **Lógica de Datos** | Probers, normalización, snapshots | `data_bridge.py` |
| **Integración** | Puente con `core/` (HttpProber, L7Analyzer) | `data_bridge.py` |
| **Backend** | Captura HTTP, análisis L7 | `core/http_prober.py`, `core/analyzer_l7_http.py` |

---

## 📦 Dependencias y Frameworks

### archivo `requirements.txt`

```
streamlit>=1.32
pydeck>=0.9
plotly>=5.20
pandas>=2.0
requests>=2.31
```

### Desglose de dependencias:

#### **Streamlit** (≥1.32)
- **Propósito**: Framework principal para UI interactiva
- **Uso en v3**:
  - `st.set_page_config()` → Configuración de página, layout
  - `st.markdown()` → Inyección HTML/CSS con `unsafe_allow_html=True`
  - `st.sidebar` → Panel lateral configurable
  - `st.tabs()` → Navegación por pestañas
  - `st.button()`, `st.text_input()`, `st.slider()` → Controles
  - `st.session_state` → Persistencia entre re-renders (clave para mantener hilos de fondo)
  - `st.spinners()`, `st.progress()` → Feedback visual
  - `st.dataframe()` → Renderizado de tablas pandas
  - `st.pydeck_chart()` → Visualización cartográfica

- **Ciclo de vida**:
  ```
  Usuario interactúa → Streamlit re-ejecuta script completo
  session_state preserva: _prober_instance, last_snapshot, etc.
  ```

#### **PyDeck** (≥0.9)
- **Propósito**: Visualización cartográfica 3D con Mapbox
- **Uso en v3**:
  - `pdk.Layer()` → Capas visuales (ScatterplotLayer, ArcLayer, TextLayer)
  - `pdk.Deck()` → Composición del mapa
  - `pdk.ViewState()` → Posición, zoom, pitch (perspectiva 3D)
  
- **Capas implementadas**:
  - `ScatterplotLayer`: Nodos con glow pulsante
  - `ArcLayer`: Enlaces entre nodos con gradiente cyberpunk
  - `TextLayer`: Etiquetas de municipios y roles

#### **Plotly** (≥5.20)
- **Propósito**: Gráficos interactivos vectoriales
- **Uso en v3**:
  - `go.Figure()` → Gráfico de latencia en tiempo real
  - `go.Scatter()` → Serie de tiempo con relleno de área
  - `fig.add_hline()` → Líneas de umbrales (WARN, CRIT)
  - Customización de layout, colores, tipografía

#### **Pandas** (≥2.0)
- **Propósito**: Manipulación y presentación de datos tabulares
- **Uso en v3**:
  - `pd.DataFrame()` → Creación de tablas desde listas de dicts
  - `st.dataframe()` → Renderizado nativo con scroll

#### **Requests** (≥2.31)
- **Propósito**: Cliente HTTP para probes manuales
- **Uso en v3**:
  - `requests.get()` en `run_ping_diagnosis()`
  - Diagnóstico puntual de latencia/status code

---

## 🔧 Componentes Técnicos

### 1. **app_streamlit.py** – Interfaz Principal

**Líneas de código:** ~600+  
**Propósito:** Orquestación de UI, gestión de estado global, renderizado de tres tabs  

#### Secciones principales:

##### A) **Configuración de página** (líneas 30–45)
```python
st.set_page_config(
    page_title="UDEC Cyber-Auditor v3",
    page_icon="🛡️",
    layout="wide",         # Layout de 2+ columnas
    initial_sidebar_state="expanded",
)
```

**Efecto:** Maximiza el espacio de trabajo, inicia sidebar visible

##### B) **Inyección de CSS y Partículas** (líneas 47–80)
```python
st.markdown(get_full_css(), unsafe_allow_html=True)  # styles.py
st.markdown(particles_html, unsafe_allow_html=True)  # Partículas flotantes
```

**Efecto:** Aplica tema cyberpunk global + animaciones de fondo

##### C) **Sincronización de estado global** (líneas 82–105)
```python
if "monitoring_active" not in st.session_state:
    st.session_state["monitoring_active"] = False

is_active = st.session_state["monitoring_active"]

# Limpieza de hilos zombis
if not is_active and st.session_state.get("_prober_instance"):
    st.session_state["_prober_instance"].stop()
    st.session_state["_prober_instance"] = None
```

**Propósito:** 
- Sincronizar estado del hilo de captura
- Evitar threads fantasmas tras parar monitoreo
- Garantizar que `_prober_instance` esté activo solo si `monitoring_active==True`

##### D) **SIDEBAR** (líneas 107–175)
- **Logo:** "🛡 UDEC CYBER-AUDITOR v3.0"
- **Status del Core:** `🟢 CORE LIVE` o `🟡 SIM MODE`
- **Configuración:**
  - Target (dominio/IP)
  - Modo: Simulación vs Live HTTP
  - Refresh Rate: 0.5s, 1.0s, 2.0s, 3.0s, Pausado
- **Timestamp:** Última actualización HH:MM:SS

**CSS especial:**
```css
.sb-logo-title.active {
    animation: title-flicker 5s infinite;
    text-shadow: 0 0 10px #00f2ff, 0 0 20px #00f2ff;
}
```

##### E) **HEADER PRINCIPAL** (líneas 177–187)
Título centrado con clase dinámica:
```python
header_class = "cyber-header active" if is_active else "cyber-header inactive"
```

**Efecto:** Cambia de color y glow según si está monitoreando

##### F) **TAB 1 – MONITOR USUARIO** (líneas 195–410)

###### Subsecciones:

**Badge de estado** (líneas 226–240):
```python
badge_cls = {
    "STABLE":   "status-healthy",    # Verde
    "WARNING":  "status-warning",    # Ámbar
    "CRITICAL": "status-critical",   # Rojo
}
```

**Métricas rápidas** (5 columnas):
- ◈ LATENCIA (ms)
- ▧ PÉRDIDA PKT (%)
- ▤ CONGESTIÓN (0-100)
- ⎈ PROBES (total)
- ⛬ IP RESUELTA

**Función `render_metric()`:**
```python
def render_metric(label, val_str, delta_str, val, warn_th, crit_th):
    """Renderiza tarjeta con borde coloreado según nivel de alerta"""
    if val <= warn_th:
        color, glow = "#00ff41", "#00ff4166"  # Verde
    elif val <= crit_th:
        color, glow = "#ffb300", "#ffb30066"  # Ámbar
    else:
        color, glow = "#ff0033", "#ff003366"  # Rojo
```

**Gauges SVG** (líneas 270–280):
```python
gauge_html = render_gauge_row(
    latency_ms,
    signal_pct,
    congestion_score,
    gauge_size=200,
)
components.html(gauge_html, height=250, scrolling=False)
```

**Gráfico de latencia en tiempo real** (líneas 295–340):
- Serie Plotly con `go.Scatter()` fill=tozeroy
- Líneas horizontales de umbral (WARN 150ms, CRIT 500ms)
- Fondo dark con grid dim

**Tabla de diagnóstico L7** (líneas 341–390):
- MODO, HTTP CODE, ENCODING, LAT AVG/MIN/MAX, PKT LOSS, SEÑAL, RECOM.
- Renderizada con `st.dataframe()` con paleta cyberpunk

**Botones de control** (líneas 395–410):
- `▶ INICIAR` / `◈ DETENER` (toggle monitoring)
- `[// FORZAR REFRESH ]` (St.rerun())

**Lluvia Matrix decorativa** (líneas 266–269):
```html
<div class="matrix-rain-container matrix-rain-left">
    <div class="matrix-drop">ア<br>イ<br>ウ...</div>
</div>
```

###### Lógica de obtención de datos:

```python
prober = None
if is_active:
    prober = get_or_create_prober(st.session_state, target, mode_key)
    snap = prober.get_snapshot()
    st.session_state["last_snapshot"] = snap
else:
    snap = st.session_state.get("last_snapshot")
    if not snap:
        snap = NetworkSnapshot()  # Default vacío
```

##### G) **TAB 2 – MAPA REGIONAL** (líneas 415–550)

**Nodos definidos:**
```python
NODES = [
    {"id": "chia", "name": "◉ UDEC CHÍA", "lat": 4.8671, "lon": -74.0368, "status": "STABLE", "color": [0, 255, 136]},
    {"id": "cajica", "name": "◉ CAJICÁ", "lat": 4.9389, "lon": -73.9933, "status": "WARNING", "color": [255, 230, 0]},
    # ... más nodos
]
```

**Filtro por municipio:**
```python
if filtro == "all":
    nodos_visibles = NODES
else:
    nodos_visibles = [n for n in NODES if n["id"] == filtro]
```

**Capas PyDeck:**
1. **pulse_layer** (ScatterplotLayer): Glow semi-transparente
2. **arc_layer** (ArcLayer): Enlaces entre nodos con gradiente
3. **scatter_layer** (ScatterplotLayer): Nodos principales
4. **text_layer** (TextLayer): Nombres de nodos
5. **municipio_layer** (TextLayer): Etiquetas de municipios

**ViewState (perspectiva 3D):**
```python
view = pdk.ViewState(
    latitude=4.88,
    longitude=-74.03,
    zoom=10.5,
    pitch=25,  # Perspectiva isométrica
    bearing=0,
)
```

**Tooltip HTML complejo:**
```html
<div style='font-family:Orbitron,Roboto Mono,monospace;
            background:linear-gradient(135deg, #0d1117 0%, #1a1f2e 100%);
            border:2px solid #00f2ff;...'>
    <div style='color:#00f2ff;...'>◉ {name}</div>
    <div style='color:#ffe600;...'>▶ {role}</div>
    ...
</div>
```

**Tabla de nodos:**
```python
display_df = pd.DataFrame([{
    "NODO": n["name"],
    "ROL": n["role"],
    "LATENCIA": f"{n['latency']} ms",
    "ESTADO": n["status"],
} for n in NODES])
```

##### H) **TAB 3 – ADMIN / DIAGNÓSTICO** (líneas 555–720)

**Panel izquierdo (Diagnóstico):**
- Target de diagnóstico (text_input)
- Timeout (slider 2-15s)
- `▶ EJECUTAR PROBE HTTP` (button)
- `⎈ PING GATEWAY LOCAL` (button)

**Panel derecho (Terminal):**
- Terminal simulada con CSS `.terminal-box`
- Log con formato coloreado:
  ```python
  KIND_MAP = {
      "ok":   ("t-ok", "✓"),
      "err":  ("t-err", "✗"),
      "warn": ("t-warn", "⚠"),
      "info": ("t-info", "›"),
  }
  ```

**Benchmark rápido:**
```python
TARGETS_BENCH = [
    ("portal.udec.edu.co", "UDEC Portal"),
    ("8.8.8.8", "Google DNS"),
    ("1.1.1.1", "Cloudflare DNS"),
    ("google.com", "Google"),
]
```

**Info del sistema:**
- OS, Hostname, Python, Core Status, Streamlit version

##### I) **Auto-refresh (Live Loop)** (líneas 725–728)
```python
if is_active and refresh_delay is not None:
    time.sleep(refresh_delay)
    st.rerun()
```

**Propósito:** Re-ejecuta el script cada N segundos para actualizar snapshots

---

### 2. **data_bridge.py** – Puente de Datos

**Líneas de código:** ~400  
**Propósito:** Normalizar interfaz entre `core/` (HttpProber) y Streamlit  

#### Estructura:

##### A) **Dataclasses normalizados**

**NetworkSnapshot:**
```python
@dataclass
class NetworkSnapshot:
    # Latencia (ms)
    latency_ms: float
    latency_avg: float
    latency_min: float
    latency_max: float
    latency_history: list
    
    # Calidad (%)
    packet_loss_pct: float
    error_rate_pct: float
    congestion_score: float  # 0-100
    
    # HTTP
    status_code: Optional[int]
    content_encoding: Optional[str]
    resolved_ip: str
    total_probes: int
    
    # Estado
    status: str  # STABLE | WARNING | CRITICAL
    alert_message: str
    recommendation: str
    
    # Datos para gráficos
    timestamps: list
    latency_points: list
```

**PingResult:**
```python
@dataclass
class PingResult:
    target: str
    success: bool
    latency_ms: float
    status_code: Optional[int]
    error: Optional[str]
    timestamp: float
```

##### B) **SimulatedProber** (línea ~70–170)

**Propósito:** Genera datos sintéticos realistas sin depender de `core/`

**Algoritmo de simulación:**
```python
class SimulatedProber:
    def _loop(self):
        while self._running:
            elapsed = time.time() - self._t0
            
            # Onda sinusoidal base (ciclo 8s)
            base_lat = 55 + 25 * math.sin(elapsed / 8)
            
            # Ruido gaussiano (σ=8)
            noise = random.gauss(0, 8)
            
            # Spike aleatorio (4% probabilidad)
            is_spike = random.random() < 0.04
            lat = max(8.0, base_lat + noise + (250 if is_spike else 0))
            
            # Error aleatorio (3% probabilidad)
            is_err = random.random() < 0.03
            
            with self._lock:
                self._total += 1
                if is_err:
                    self._errors += 1
                else:
                    self._latencies.append(lat)
                    # Mantiene ventana deslizante de 120 puntos
                    if len(self._latencies) > 120:
                        self._latencies.pop(0)
            
            time.sleep(0.5)  # Genera punto cada 500ms
```

**Parámetros realistas:**
- Latencia base: 55ms ± 25ms (onda)
- Ruido: ±8ms (gaussiano)
- Spikes: 4% de probabilidad (+250ms)
- Errores: 3% de probabilidad
- Tasa: 1 punto cada 500ms = 120 puntos = 60s de historia

**get_snapshot():**
```python
# Calcula error_rate_pct
err_pct = (errs / total * 100) if total else 0.0

# Calcula congestión como combinación
cong = min(avg_lat / 500, 1.0) * 50 + min(err_pct / 20, 1.0) * 50

# Determina estado y alerta
if err_pct > 10 or avg_lat > 500:
    status = "CRITICAL"
elif err_pct > 3 or avg_lat > 150:
    status = "WARNING"
else:
    status = "STABLE"
```

##### C) **LiveProber** (línea ~175–250)

**Propósito:** Wrapper sobre `core/HttpProber` y `core/L7HttpAnalyzer`

```python
class LiveProber:
    def __init__(self, target: str):
        self._prober = HttpProber(
            target=target,
            interval_sec=0.8,  # Probe cada 800ms
            num_workers=1      # 1 hilo HTTP
        )
        self._analyzer = L7HttpAnalyzer(window=80)  # Ventana de 80 probes
        self._running = False
        self._thread = None
```

**Hilo de drenado (_drain_loop):**
```python
def _drain_loop(self):
    """Extrae resultados de la queue del prober y alimenta el analizador"""
    while self._running:
        result = self._prober.get_result(timeout=0.3)  # Timeout corto
        if result:
            with self._lock:
                self._analyzer.feed(result)  # Alimenta análisis L7
                if result.resolved_ip and result.resolved_ip != "?":
                    self._last_ip = result.resolved_ip
        time.sleep(0.05)  # Yield CPU
```

**get_snapshot():**
```python
def get_snapshot(self) -> NetworkSnapshot:
    with self._lock:
        snap = self._analyzer.snapshot()  # Obtiene snapshot del analyzer
        ip = self._last_ip
    
    lats = snap.latency_points[-80:] if snap.latency_points else []
    
    return NetworkSnapshot(
        latency_ms = round(lats[-1], 1) if lats else 0.0,
        latency_avg = round(snap.latency_ms_avg, 1),
        # ... más campos normalizados
    )
```

**Thread-safety:**
- Usa `threading.Lock()` para proteger `_analyzer` y `_last_ip`
- El acceso al prober es thread-safe por diseño (queue interna)

##### D) **get_or_create_prober()** (línea ~260–290)

**Propósito:** Factory pattern para gestionar ciclo de vida del prober en session_state

```python
def get_or_create_prober(state: dict, target: str, mode: str) -> object:
    key = "_prober_instance"
    key_cfg = "_prober_config"
    cfg = f"{mode}::{target}"
    
    # Si la config cambió (target o modo), destruye el anterior
    if state.get(key_cfg) != cfg and state.get(key) is not None:
        try:
            state[key].stop()
        except Exception:
            pass
        state[key] = None
        state[key_cfg] = None
    
    # Crea nuevo si no existe
    if state.get(key) is None:
        if mode == "live" and CORE_AVAILABLE:
            prober = LiveProber(target=target)
        else:
            prober = SimulatedProber(target=target)
        
        prober.start()
        state[key] = prober
        state[key_cfg] = cfg
    
    return state[key]
```

**Ventajas:**
- Reutiliza prober entre re-renders de Streamlit
- Detecta cambios de config (target/modo) automáticamente
- Limpia correctamente hilos al cambiar configuración

##### E) **run_ping_diagnosis()** (línea ~300–340)

**Propósito:** Ejecuta probe HTTP puntual y bloqueante (para botones de diagnóstico)

```python
def run_ping_diagnosis(target: str, timeout: float = 5.0) -> PingResult:
    try:
        import requests as req
        
        t0 = time.time()
        url = f"https://{target}" if not _looks_like_ip(target) else f"http://{target}"
        
        resp = req.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": "UDEC-Auditor/3.0 (Diag)"}
        )
        lat = (time.time() - t0) * 1000
        
        return PingResult(
            target=target,
            success=True,
            latency_ms=round(lat, 1),
            status_code=resp.status_code,
            error=None,
        )
    except Exception as e:
        return PingResult(
            target=target,
            success=False,
            latency_ms=0.0,
            status_code=None,
            error=str(e)[:120],
        )
```

**Características:**
- Detecta si es IP o dominio automáticamente
- Sigue redirecciones
- User-Agent identificado como UDEC-Auditor
- Timeout configurable

##### F) **_looks_like_ip()** (línea ~345–355)

```python
def _looks_like_ip(s: str) -> bool:
    import socket
    try:
        socket.inet_aton(s.split(":")[0])  # Maneja "IP:puerto"
        return True
    except socket.error:
        return False
```

---

### 3. **gauges.py** – Generación SVG

**Líneas de código:** ~400  
**Propósito:** Generar medidores/gauges SVG estilo HUD sin librerías gráficas externas

#### Estructura:

##### A) **Funciones de geometría SVG**

**_polar()** → Convierte ángulo polar a coordenadas cartesianas:
```python
def _polar(cx, cy, r, angle_deg):
    rad = math.radians(angle_deg - 90)  # 0° = arriba
    return cx + r * math.cos(rad), cy + r * math.sin(rad)
```

**Ejemplo:**
- angle=0°   → (cx, cy-r) = arriba
- angle=90°  → (cx+r, cy) = derecha
- angle=180° → (cx, cy+r) = abajo
- angle=270° → (cx-r, cy) = izquierda

**_arc_path()** → Genera comando SVG `<path d="...">`para arco:
```python
def _arc_path(cx, cy, r, start_deg, end_deg):
    sweep = (end_deg - start_deg) % 360
    large = 1 if sweep > 180 else 0
    x1, y1 = _polar(cx, cy, r, start_deg)
    x2, y2 = _polar(cx, cy, r, end_deg)
    
    return f"M {x1:.3f} {y1:.3f} A {r} {r} 0 {large} 1 {x2:.3f} {y2:.3f}"
```

**Parámetros SVG Arc:**
- `M x y` = Move to
- `A rx ry x-axis-rotation large-arc-flag sweep-flag x y` = Arc to
- `large-arc-flag` = 1 si barrido > 180°
- `sweep-flag` = 1 para sentido horario

**_tick_path()** → Genera línea de graduación:
```python
def _tick_path(cx, cy, r_outer, r_inner, angle_deg):
    x1, y1 = _polar(cx, cy, r_outer, angle_deg)
    x2, y2 = _polar(cx, cy, r_inner, angle_deg)
    return f"M {x1:.2f} {y1:.2f} L {x2:.2f} {y2:.2f}"
```

##### B) **render_arc_gauge()** – Medidor base

**Firma:**
```python
def render_arc_gauge(
    value: float,
    max_value: float,
    label: str,
    unit: str = "",
    start_deg: float = 225,
    end_deg: float = 315,
    color_low: str = "#00ff41",      # Verde
    color_mid: str = "#ffb300",      # Ámbar
    color_high: str = "#ff0033",     # Rojo
    # ...más opciones
) -> str:
```

**Lógica de color dinámico:**
```python
ratio = max(0.0, min(1.0, value / max_value))

if invert_colors:  # Para latencia (bajo es bueno)
    if ratio < threshold_mid:
        arc_color = color_low        # Verde (bajo)
    elif ratio < threshold_high:
        arc_color = color_mid        # Ámbar (medio)
    else:
        arc_color = color_high       # Rojo (alto)
else:  # Para señal (alto es bueno)
    if ratio > threshold_mid:
        arc_color = color_low        # Verde (alto)
    elif ratio > (1 - threshold_high):
        arc_color = color_mid        # Ámbar (bajo-medio)
    else:
        arc_color = color_high       # Rojo (muy bajo)
```

**Graduaciones:**
```python
for i in range(num_ticks + 1):
    t_ratio = i / num_ticks
    t_angle = start_deg + total_sweep * t_ratio
    is_major = (i % (num_ticks // 5) == 0)
    r_outer = r + stroke_width * 0.5
    r_inner = r_outer - (stroke_width * 0.6 if is_major else stroke_width * 0.35)
    t_color = arc_color if t_ratio <= ratio else "#2a3550"
    path = _tick_path(cx, cy, r_outer, r_inner, t_angle)
```

**Filtros SVG (glow neon):**
```xml
<defs>
    <filter id="glow_{uid}">
        <feGaussianBlur stdDeviation="3.5" result="blur1"/>
        <feGaussianBlur stdDeviation="7" result="blur2"/>
        <feMerge>
            <feMergeNode in="blur2"/>
            <feMergeNode in="blur1"/>
            <feMergeNode in="SourceGraphic"/>
        </feMerge>
    </filter>
    <linearGradient id="arc_grad_{uid}">
        <stop offset="0%" stop-color="{arc_color}" stop-opacity="0.6"/>
        <stop offset="100%" stop-color="{arc_color}" stop-opacity="1.0"/>
    </linearGradient>
</defs>
```

**Decoraciones HUD:**
```python
hud_corners = f"""
<rect x="0" y="0" width="10" height="2" fill="{arc_color}" opacity="0.5"/>
<rect x="0" y="0" width="2" height="10" fill="{arc_color}" opacity="0.5"/>
...esquinas inferiores...
"""
```

**Aguja indicadora:**
```python
needle_angle = start_deg + total_sweep * ratio
nx, ny = _polar(cx, cy, r - stroke_width * 0.5, needle_angle)
needle_svg = f"""
<line x1="{cx}" y1="{cy}" x2="{nx}" y2="{ny}"
      stroke="{arc_color}" stroke-width="2.5"/>
<circle cx="{cx}" cy="{cy}" r="4" fill="{arc_color}"/>
"""
```

##### C) **render_latency_gauge()** – Medidor de latencia

```python
def render_latency_gauge(latency_ms: float, size: int = 220, uid: str = "lat"):
    if latency_ms < 80:
        sublabel = "ÓPTIMO"
    elif latency_ms < 150:
        sublabel = "ESTABLE"
    elif latency_ms < 500:
        sublabel = "DEGRADADO"
    else:
        sublabel = "CRÍTICO"
    
    return render_arc_gauge(
        value=latency_ms,
        max_value=1000,
        label="Latencia",
        unit="ms",
        color_low="#00f2ff",   # Cyan bajo es bueno
        color_high="#ff0033",  # Rojo alto es malo
        invert_colors=True,
        sublabel=sublabel,
        # ...más opciones
    )
```

**Umbrales de color:**
- 0–150ms: Verde (ÓPTIMO)
- 150–500ms: Ámbar (DEGRADADO)
- 500–1000ms: Rojo (CRÍTICO)

##### D) **render_signal_gauge()** – Medidor de señal

```python
def render_signal_gauge(signal_pct: float, size: int = 220, uid: str = "sig"):
    if signal_pct >= 80:
        sublabel = "EXCELENTE"
    elif signal_pct >= 50:
        sublabel = "BUENA"
    elif signal_pct >= 20:
        sublabel = "DÉBIL"
    else:
        sublabel = "CRÍTICA"
    
    return render_arc_gauge(
        value=signal_pct,
        max_value=100,
        label="Señal",
        unit="%",
        color_low="#00ff41",   # Verde alto es bueno
        color_high="#ff0033",  # Rojo bajo es malo
        invert_colors=False,   # Alto es bueno (normal)
        sublabel=sublabel,
    )
```

**Umbrales de color:**
- 80–100%: Verde (EXCELENTE)
- 50–80%: Ámbar (BUENA)
- 20–50%: Naranja (DÉBIL)
- 0–20%: Rojo (CRÍTICA)

##### E) **render_gauge_row()** – Fila de 3 gauges

```python
def render_gauge_row(
    latency_ms: float,
    signal_pct: float,
    congestion_score: float,
    gauge_size: int = 200,
) -> str:
    """Retorna HTML con 3 gauges side-by-side + estilos compartidos"""
```

**Estructura HTML:**
```html
<div style="display:flex; justify-content:space-around; gap:20px;">
    <!-- Gauge de latencia -->
    <div style="flex:1; max-width:250px;">
        <svg>...latency_gauge...</svg>
    </div>
    
    <!-- Gauge de señal -->
    <div style="flex:1; max-width:250px;">
        <svg>...signal_gauge...</svg>
    </div>
    
    <!-- Gauge de congestión -->
    <div style="flex:1; max-width:250px;">
        <svg>...congestion_gauge...</svg>
    </div>
</div>

<!-- Estilos CSS compartidos -->
<style>
    .gauge-container { ... }
    @keyframes needle-swing { ... }
    @keyframes glow-pulse { ... }
</style>
```

**Animaciones:**
```css
@keyframes needle-swing {
    0%, 100% { transform: rotate(0deg); }
    50% { transform: rotate(5deg); }
}

@keyframes glow-pulse {
    0%, 100% { filter: drop-shadow(0 0 8px ...); }
    50% { filter: drop-shadow(0 0 15px ...); }
}
```

---

### 4. **styles.py** – Sistema CSS Modular

**Líneas de código:** ~600+  
**Propósito:** CSS centralizado para tema Cyberpunk global

#### Estructura de módulos CSS:

##### A) **PALETTE** (línea ~4–25)

```python
PALETTE = {
    "bg_void":       "#080a0f",  # Negro profundo
    "bg_deep":       "#0d1117",
    "bg_panel":      "#111827",
    "bg_card":       "#131a28",
    "border_dim":    "#1e2d45",
    "border_active": "#00f2ff44",
    "cyan":          "#00f2ff",
    "magenta":       "#ff00ff",
    "green":         "#00ff41",
    "red":           "#ff0033",
    "yellow":        "#ffb300",
    "text_primary":  "#c8d8f0",
    "text_dim":      "#4a6080",
    "text_muted":    "#243050",
}
```

**Uso en HTML:**
```python
f'<span style="color:{PALETTE["cyan"]};">...'
```

##### B) **CSS_FONTS** (línea ~27–29)

```python
CSS_FONTS = """
@import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@300;400;500;600;700&family=Share+Tech+Mono&display=swap');
"""
```

**Fuentes:**
- **Roboto Mono** (monoespaciada): Código, números, etiquetas
- **Share Tech Mono** (futurista): Títulos, efectos neon

##### C) **CSS_BASE** (línea ~31–100)

**Reset global:**
```css
*, *::before, *::after {
    box-sizing: border-box;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: #080a0f !important;
    font-family: 'Roboto Mono', monospace !important;
}
```

**Partículas flotantes (fondo animado):**
```css
.cyber-particles {
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    z-index: -1;
    pointer-events: none;
}

.particle {
    position: absolute;
    width: 2px; height: 2px;
    background: #00f2ff;
    box-shadow: 0 0 6px #00f2ff;
    animation: float-up 8s linear infinite;
}

@keyframes float-up {
    0% { transform: translateY(100vh); opacity: 0; }
    10% { opacity: 1; }
    90% { opacity: 1; }
    100% { transform: translateY(-100vh); opacity: 0; }
}
```

**ScrollBar personalizada:**
```css
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #00f2ff33; }
::-webkit-scrollbar-thumb:hover { background: #00f2ff88; }
```

##### D) **CSS_SIDEBAR** (línea ~102–200)

**Gradiente de fondo:**
```css
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0d14 0%, #080a0f 100%) !important;
    border-right: 1px solid #00f2ff22 !important;
}
```

**Logo con animación de parpadeo:**
```css
.sb-logo-title.active {
    animation: title-flicker 5s infinite;
}

@keyframes title-flicker {
    0%, 19%, 21%, 23%, 25%, 54%, 56%, 100% {
        opacity: 1;
        text-shadow: 0 0 10px #00f2ff, 0 0 40px #00f2ff;
    }
    20%, 24%, 55% {
        opacity: 0.3;
        text-shadow: none;
    }
}
```

**Botones de navegación:**
```css
.nav-btn {
    border: 1px solid #1e2d45;
    clip-path: polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%);
    transition: all 0.2s ease;
}

.nav-btn:hover {
    border-color: #00f2ff88;
    background: #00f2ff0a;
    box-shadow: 0 0 8px #00f2ff22;
}

.nav-btn.active {
    box-shadow: 0 0 12px #00f2ff33;
    text-shadow: 0 0 8px #00f2ff;
}
```

##### E) **CSS_TABS** (línea ~202–240)

```css
[data-testid="stTabs"] [role="tab"] {
    clip-path: polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%);
    transition: all 0.25s ease !important;
}

[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: #00f2ff11 !important;
    border-color: #00f2ff !important;
    text-shadow: 0 0 10px #00f2ff88 !important;
}
```

##### F) **CSS_METRICS** (línea ~242–270)

```css
[data-testid="stMetric"] {
    border-top: 2px solid #00f2ff !important;
    clip-path: polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%);
}

[data-testid="stMetricValue"] {
    font-size: 1.9rem !important;
    color: #00f2ff !important;
    text-shadow: 0 0 15px #00f2ff88 !important;
}
```

##### G) **CSS_BUTTONS** (línea ~272–350)

```css
/* Botón Primary */
[data-testid="stBaseButton-primary"] {
    background: linear-gradient(90deg, #001a33, #004466) !important;
    border: 1px solid #00f2ff !important;
    box-shadow: inset 0 0 10px #00f2ff22 !important;
}

[data-testid="stBaseButton-primary"]:hover {
    background: linear-gradient(90deg, #003366, #0066aa) !important;
    box-shadow: 0 0 25px #00f2ff44 !important;
}

/* Botón Secondary */
[data-testid="stBaseButton-secondary"] {
    border: 1px dashed #4a6080 !important;
    background: transparent !important;
}
```

##### H) **CSS_CARDS Y CONTAINERS** (línea ~352–450)

```css
.cyber-card {
    background: linear-gradient(135deg, #131a28 0%, #111827 100%);
    border: 1px solid #1e2d45;
    border-radius: 4px;
    padding: 1rem;
    box-shadow: inset 0 0 10px #00f2ff0a;
    transition: all 0.3s ease;
}

.cyber-card:hover {
    border-color: #00f2ff33;
    box-shadow: 0 0 15px #00f2ff1a;
}

.cyber-card-cyan {
    border-left: 3px solid #00f2ff;
}

.cyber-header {
    text-align: center;
    padding: 2rem 0;
    transition: all 0.5s ease;
}

.cyber-header.active {
    text-shadow: 0 0 20px #00f2ff, 0 0 40px #00f2ff;
}

.cyber-header.inactive {
    color: #4a6080;
    text-shadow: 0 0 5px #4a608066;
}
```

##### I) **CSS_TERMINAL** (línea ~452–520)

```css
.terminal-box {
    font-family: 'Share Tech Mono', monospace;
    background: #080a0f;
    border: 1px solid #00f2ff;
    border-radius: 4px;
    padding: 1rem;
    color: #00f2ff;
    text-shadow: 0 0 5px #00f2ff;
    max-height: 400px;
    overflow-y: auto;
    line-height: 1.6;
}

.terminal-cursor {
    display: inline-block;
    width: 8px;
    height: 1em;
    background: #00f2ff;
    margin-left: 4px;
    animation: blink 1s infinite;
}

@keyframes blink {
    0%, 49%, 100% { opacity: 1; }
    50%, 99% { opacity: 0; }
}

.t-ok { color: #00ff41; }
.t-err { color: #ff0033; }
.t-warn { color: #ffb300; }
.t-info { color: #00f2ff; }
.t-muted { color: #243050; }
```

##### J) **CSS_MATRIX_RAIN** (línea ~522–580)

```css
.matrix-rain-container {
    position: fixed;
    top: 0;
    width: 50%;
    height: 100%;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
}

.matrix-rain-left {
    left: 0;
    background: linear-gradient(90deg, #00f2ff11 0%, transparent 100%);
}

.matrix-rain-right {
    right: 0;
    background: linear-gradient(90deg, transparent 0%, #ff00ff11 100%);
}

.matrix-drop {
    position: absolute;
    font-family: monospace;
    font-size: 0.8rem;
    color: #00f2ff33;
    animation: rain 20s linear infinite;
}

@keyframes rain {
    0% { transform: translateY(-100%); opacity: 0; }
    10% { opacity: 0.5; }
    90% { opacity: 0.5; }
    100% { transform: translateY(100vh); opacity: 0; }
}
```

##### K) **Función get_full_css()** (final del archivo)

```python
def get_full_css() -> str:
    return f"""
    <style>
        {CSS_FONTS}
        {CSS_BASE}
        {CSS_SIDEBAR}
        {CSS_TABS}
        {CSS_METRICS}
        {CSS_BUTTONS}
        {CSS_CARDS}
        {CSS_TERMINAL}
        {CSS_MATRIX_RAIN}
        {CSS_SCANLINES}
        {CSS_GLITCH_EFFECT}
        {CSS_NEON_PULSE}
    </style>
    """
```

**Inyección en app_streamlit.py:**
```python
st.markdown(get_full_css(), unsafe_allow_html=True)
```

---

## 🔄 Flujo de Datos

### Ciclo de operación (1 re-render de Streamlit):

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USUARIO INTERACTÚA (click botón, cambio slider, etc.)        │
└───────────────────────┬─────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│ 2. STREAMLIT RE-EJECUTA SCRIPT COMPLETO (app_streamlit.py)      │
│    • Lee session_state (persistente)                            │
│    • Re-calcula variables, layouts                              │
└───────────────────────┬─────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│ 3. SINCRONIZACIÓN DE ESTADO GLOBAL (líneas 82–105)             │
│    • Verifica si monitoring_active == True                      │
│    • Si no, limpia threads zombis                               │
└───────────────────────┬─────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│ 4. SIDEBAR: Lee configuración de usuario                        │
│    • target = text_input                                        │
│    • mode = selectbox (Simulación / Live)                       │
│    • refresh_delay = selectbox (0.5s–Pausado)                   │
└───────────────────────┬─────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│ 5. TAB 1 (MONITOR): get_or_create_prober()                      │
│                                             │                   │
│   Si is_active == True:                     │                   │
│   • Llama: get_or_create_prober(state, target, mode)            │
│   • Factory crea LiveProber o SimulatedProber                   │
│   • Prober.start() inicia hilo de captura (si no está)          │
│   • Retorna instancia guardada en session_state                 │
│                                             │                   │
│   Luego:                                    │                   │
│   • snap = prober.get_snapshot()            │                   │
│   • snapshot normaliza datos (NetworkSnapshot dataclass)        │
│   • Guarda en session_state["last_snapshot"]                    │
│                                             │                   │
│   Si is_active == False:                    │                   │
│   • snap = session_state.get("last_snapshot")                   │
│   • Usa último snapshot disponible          │                   │
└───────────────────────┬─────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│ 6. RENDERIZADO DE COMPONENTES                                   │
│                                             │                   │
│   a) Badge de estado (color dinámico)       │                   │
│   b) 5 Métricas (color dinámico)            │                   │
│   c) Gauges SVG (render_gauge_row)          │                   │
│   d) Gráfico Plotly (latency_points)        │                   │
│   e) Tabla diagnóstico (pandas DataFrame)   │                   │
│                                             │                   │
│   • Todos leen datos de 'snap'              │                   │
│   • HTML/SVG inyectado con st.markdown()    │                   │
└───────────────────────┬─────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│ 7. AUTO-REFRESH (líneas 725–728)                                │
│                                             │                   │
│   if is_active and refresh_delay is not None:                   │
│   • time.sleep(refresh_delay)  [0.5s–3.0s] │                   │
│   • st.rerun()  ◄─── Vuelve al paso 1      │                   │
│                                             │                   │
│   Else:                                     │                   │
│   • Se detiene (usuario debe interactuar)   │                   │
└─────────────────────────────────────────────────────────────────┘
```

### Thread de captura en LiveProber (paralelo al main):

```
┌─────────────────────────────────────────────────────────────────┐
│ LiveProber Thread (daemon=True)                                  │
│ • Inicializa: HttpProber + L7HttpAnalyzer                       │
│ • Inicia: prober.start()                                        │
│ • Loop (_drain_loop):                                           │
│   - Cada 50ms: Drena queue de HttpProber                        │
│   - Alimenta L7HttpAnalyzer con HttpProbeResult                │
│   - Actualiza _last_ip si se resuelve nuevo IP                 │
│   - Thread-safe con lock                                        │
│                                             │                   │
│ • get_snapshot() (sincronizado):            │                   │
│   - Copia datos thread-safe                 │                   │
│   - Normaliza a NetworkSnapshot            │                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Guía de Ejecución

### Requisitos:

```
Python ≥ 3.9
Streamlit ≥ 1.32
PyDeck ≥ 0.9
Plotly ≥ 5.20
Pandas ≥ 2.0
Requests ≥ 2.31
```

### Instalación:

```bash
# Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r v3/requirements.txt

# Opcional: instalar core/ si está disponible
# pip install -e .
```

### Ejecución:

```bash
# Modo 1: Directo desde v3/
cd v3
streamlit run app_streamlit.py

# Modo 2: Desde raíz del proyecto
streamlit run v3/app_streamlit.py

# Modo 3: Con configuración personalizada
streamlit run v3/app_streamlit.py --logger.level=debug
```

**URL por defecto:** http://localhost:8501

### Primeros pasos:

1. **Abre la app** → http://localhost:8501
2. **Sidebar → Configura:**
   - Target: `portal.udec.edu.co` (por defecto)
   - Modo: `Simulación` (para pruebas rápidas)
   - Refresh: `1.0s`
3. **Tab 1 (Monitor):**
   - Click en `▶ INICIAR`
   - Observa métricas actualizarse cada 1s
4. **Tab 2 (Mapa):**
   - Visualiza nodos UDEC en mapa interactivo
   - Zoom/pan/rotate con mouse
5. **Tab 3 (Admin):**
   - Click en `▶ EJECUTAR PROBE HTTP`
   - O `⎈ PING GATEWAY LOCAL`

---

## 🐛 Troubleshooting

### Error: `ModuleNotFoundError: No module named 'streamlit'`

**Causa:** Entorno virtual no activado o dependencias no instaladas  
**Solución:**
```bash
.venv\Scripts\activate
pip install -r v3/requirements.txt
```

### Error: `Cannot import HttpProber from core/`

**Causa:** `core/` no disponible (v2 mode Live necesita core/)  
**Solución:**
- Usar modo Simulación (por defecto cuando core/ no existe)
- O copiar archivos de `core/` al proyecto

**En data_bridge.py:**
```python
try:
    from core.http_prober import HttpProber
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False  # ← Modo Simulación automático
```

### Dashboard muy lento / UI congelada

**Causas posibles:**
1. `refresh_delay` muy bajo (< 0.5s)
2. Gauges muy grandes (`gauge_size > 300`)
3. Demasiados puntos de latencia (`latency_points > 500`)

**Soluciones:**
1. Aumentar refresh_delay a 2.0s–3.0s
2. Reducir `gauge_size` a 180–200
3. En data_bridge.py, reducir ventana de puntos:
   ```python
   self._latencies = self._latencies[-80:]  # Máx 80 puntos
   ```

### Mapa PyDeck no aparece

**Causa:** PyDeck no instalado o versión vieja  
**Solución:**
```bash
pip install --upgrade pydeck>=0.9 mapbox-api
```

### Terminal de diagnóstico no responde

**Causa:** Probe HTTP bloqueado en target inalcanzable  
**Solución:**
- Verificar conectividad: `ping 8.8.8.8`
- Aumentar timeout en slider (TAB 3)
- Cambiar target a `8.8.8.8` (Google DNS, más confiable)

### Botones no funcionan

**Causa:** session_state no inicializado correctamente  
**Solución:**
- Borrar caché de Streamlit:
  ```bash
  streamlit cache clear
  ```
- O forzar refresh: `Ctrl+R` en navegador

### CSS no se aplica (tema no cyberpunk)

**Causa:** `unsafe_allow_html=True` no permitido en app  
**Solución:**
- Streamlit requiere desactivar protección en local:
  ```bash
  streamlit run app_streamlit.py --client.toolbarMode=minimal
  ```

### Gauges no renderizan (solo HTML en blanco)

**Causa:** SVG inválido o UID duplicado  
**Solución:**
- Verificar en browser console (F12 → Console)
- Asegurarse de pasar `uid` único a render_gauge_row()
- Verificar que `latency_ms`, `signal_pct`, `congestion_score` sean números válidos

---

## 📊 Estadísticas del Proyecto

| Métrica | Valor |
|---------|-------|
| **Total de archivos** | 4 |
| **Líneas de código** | ~1,200 |
| **Dependencias externas** | 5 |
| **Frameworks principales** | Streamlit, PyDeck, Plotly |
| **Temas visuales** | Cyberpunk/Neon |
| **Modos de operación** | 2 (Live + Simulación) |
| **Tabs en UI** | 3 |
| **Métricas en tiempo real** | 9 |
| **Gauges SVG** | 3 |
| **Nodos en mapa** | 6 |

---

## 🎓 Referencias

### Documentación oficial:

- **Streamlit:** https://docs.streamlit.io/
- **PyDeck:** https://deckgl.readthedocs.io/
- **Plotly:** https://plotly.com/python/
- **Pandas:** https://pandas.pydata.org/docs/

### Conceptos clave:

- **Thread-safety en Streamlit:** Usar `session_state` para compartir entre threads
- **SVG Geometry:** Coordenadas polares para medidores circulares
- **CSS Injection:** `st.markdown(..., unsafe_allow_html=True)`
- **Network Metrics:** L7 (HTTP), latencia, pérdida de paquetes, congestión

---

**Documento generado:** 5 de mayo de 2026  
**Versión:** 1.0  
**Responsable:** UDEC · Semestre 7 · Comunicación de Datos
