import streamlit as st
import json
import os
import time
import pandas as pd
import plotly.graph_objects as go
import math
import random
from datetime import datetime
from CoolProp.CoolProp import PropsSI

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Korat Flow | HMI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# LÓGICA DEL GEMELO DIGITAL (SIMULADOR INTEGRADO)
# ==========================================
def obtener_cp_dinamico(temp_c: float) -> float:
    try:
        return PropsSI('C', 'T', temp_c + 273.15, 'P', 101325, 'Water') / 1000.0
    except:
        return 4.184

def generar_dato_simulado():
    """Genera un punto de telemetría realista basado en física térmica."""
    t_transcurrido = time.time() % 600
    fase = (t_transcurrido / 600.0) * 2 * math.pi
    
    # Carga IT base 240kW + fluctuación
    carga_kw = 240.0 + (math.sin(fase) * 40.0) + random.gauss(0, 2.0)
    temp_in = 45.0 + random.gauss(0, 0.1)
    caudal_lpm = 120.0 + random.gauss(0, 0.5)
    
    # Inyección aleatoria de anomalía para la demo
    es_anomalia = (int(time.time()) % 60) < 5
    if es_anomalia: carga_kw += 50.0
    
    # Cálculo Delta T real
    cp = obtener_cp_dinamico(temp_in)
    flujo_masico = caudal_lpm / 60.0
    delta_t = carga_kw / (flujo_masico * cp) if flujo_masico > 0 else 0
    temp_out = temp_in + delta_t
    
    return {
        "timestamp_iso": datetime.now().isoformat(),
        "it_load_kw": round(carga_kw, 2),
        "coolant_return_c": round(temp_out, 2),
        "flow_rate_lpm": round(caudal_lpm, 2),
        "partial_pue": round((carga_kw + 10) / carga_kw, 3),
        "anomaly_flag": es_anomalia
    }

# ==========================================
# UI/UX: CSS Premium & Adaptativo
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

:root {
    --card-bg: #ffffff;
    --card-border: #e2e8f0;
    --text-main: #0f172a;
    --text-muted: #64748b;
}

@media (prefers-color-scheme: dark) {
    :root {
        --card-bg: #1e293b;
        --card-border: #334155;
        --text-main: #f8fafc;
        --text-muted: #94a3b8;
    }
}

.metric-card {
    background-color: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 16px;
    padding: 24px;
    transition: transform 0.2s ease;
}

.metric-card:hover { transform: translateY(-4px); }

.metric-title {
    color: var(--text-muted);
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}

.metric-value {
    color: var(--text-main);
    font-size: 36px;
    font-weight: 700;
    line-height: 1.1;
}

.value-alert { color: #ef4444 !important; animation: pulse 2s infinite; }
.value-good { color: #10b981 !important; }
.value-blue { color: #3b82f6 !important; }

@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.6; } 100% { opacity: 1; } }
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# LECTURA DE DATOS
# ==========================================
FILE_BUS = "telemetria_bus.json"

def obtener_datos(modo_demo):
    if modo_demo:
        return generar_dato_simulado()
    
    if os.path.exists(FILE_BUS):
        try:
            with open(FILE_BUS, "r") as f:
                return json.load(f)
        except:
            return None
    return None

if 'historial' not in st.session_state:
    st.session_state.historial = pd.DataFrame(columns=['tiempo', 'potencia_kw', 'temp_c', 'pue'])

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 24px;">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path>
        </svg>
        <h2 style="margin: 0; font-family: 'Inter', sans-serif; font-weight: 700; font-size: 24px;">Korat Flow</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Control de Datos")
    modo_demo = st.toggle("🚀 Modo Simulación (Demo)", value=False)
    
    if modo_demo:
        st.info("Simulando Digital Twin en tiempo real.")
    
    st.divider()
    st.markdown("**UNIFIED NAMESPACE**")
    st.code("🏢 Empresa (Korat)\n └── 🏭 Planta (DC Alpha)\n      └── 🗄️ Fila A\n           └── 💻 RACK_DLC_01", language="text")

# ==========================================
# PANEL PRINCIPAL
# ==========================================
st.title("Monitor de Rendimiento Térmico")
st.markdown("Rack 240kW - Estado Operacional")

placeholder = st.empty()

while True: # Bucle infinito para tiempo real fluido
    datos = obtener_datos(modo_demo)
    
    if datos:
        nuevo_registro = pd.DataFrame([{
            'tiempo': datetime.now().strftime('%H:%M:%S'),
            'potencia_kw': datos.get('it_load_kw', 0),
            'temp_c': datos.get('coolant_return_c', 0),
            'pue': datos.get('partial_pue', 1.0)
        }])
        st.session_state.historial = pd.concat([st.session_state.historial, nuevo_registro]).tail(60)
        
        with placeholder.container():
            col1, col2, col3, col4 = st.columns(4)
            estado_clase = "value-alert" if datos.get('anomaly_flag', False) else "value-blue"
            
            with col1:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Carga IT Actual</div><div class="metric-value {estado_clase}">{datos.get("it_load_kw", 0):.1f} <span style="font-size:16px;">kW</span></div></div>', unsafe_allow_html=True)
            with col2:
                t_out = datos.get('coolant_return_c', 0)
                color_temp = "value-alert" if t_out > 78 else "value-good"
                st.markdown(f'<div class="metric-card"><div class="metric-title">Temp. Retorno</div><div class="metric-value {color_temp}">{t_out:.1f} <span style="font-size:16px;">°C</span></div></div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Caudal DLC</div><div class="metric-value">{datos.get("flow_rate_lpm", 0):.1f} <span style="font-size:16px;">LPM</span></div></div>', unsafe_allow_html=True)
            with col4:
                pue = datos.get('partial_pue', 0)
                color_pue = "value-alert" if pue > 1.05 else "value-good"
                st.markdown(f'<div class="metric-card"><div class="metric-title">PUE Parcial</div><div class="metric-value {color_pue}">{pue:.3f}</div></div>', unsafe_allow_html=True)
                
            st.write("")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=st.session_state.historial['tiempo'], y=st.session_state.historial['potencia_kw'], name='Potencia (kW)', line=dict(color='#3B82F6', width=3), mode='lines'))
            fig.add_trace(go.Scatter(x=st.session_state.historial['tiempo'], y=st.session_state.historial['temp_c'], name='Temp (°C)', line=dict(color='#10B981', width=3), mode='lines'))
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter, sans-serif", size=12),
                xaxis=dict(
                    showgrid=False, 
                    zeroline=False,
                    nticks=10, 
                    tickangle=0 
                ),
                yaxis=dict(
                    showgrid=True, 
                    gridcolor='rgba(128,128,128,0.1)',
                    title="kW / °C",
                    range=[0, 350] 
                ),
                hovermode="x unified",
                margin=dict(l=0, r=0, t=40, b=80), 
                legend=dict(
                    orientation="h", 
                    yanchor="top", 
                    y=-0.2, 
                    xanchor="center", 
                    x=0.5
                )
            )
            st.markdown('<div class="metric-card" style="padding: 10px;">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            if datos.get('anomaly_flag', False):
                st.error("⚠️ ALERTA: Pico de carga detectado.")
            
    time.sleep(1)

