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
    page_title="Korat Flow | NVIDIA Blackwell Node",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed" # Sidebar cerrado por defecto para el post
)

# ==========================================
# LÓGICA DEL GEMELO DIGITAL (NVIDIA GB200 NVL72)
# ==========================================
def obtener_cp_dinamico(temp_c: float) -> float:
    try:
        return PropsSI('C', 'T', temp_c + 273.15, 'P', 101325, 'Water') / 1000.0
    except:
        return 4.184

def generar_dato_simulado():
    """Genera telemetría real para un cluster NVIDIA GB200 NVL72."""
    t_transcurrido = time.time() % 600
    fase = (t_transcurrido / 600.0) * 2 * math.pi
    
    # Carga IT base 142kW (Standard Blackwell) x 2 (Dual Cluster) = 284kW
    carga_kw = 284.0 + (math.sin(fase) * 20.0) + random.gauss(0, 1.0)
    temp_in = 45.0 + random.gauss(0, 0.1)
    caudal_lpm = 135.0 + random.gauss(0, 0.5)
    
    es_anomalia = (int(time.time()) % 60) < 5
    if es_anomalia: carga_kw += 40.0
    
    cp = obtener_cp_dinamico(temp_in)
    flujo_masico = caudal_lpm / 60.0
    delta_t = carga_kw / (flujo_masico * cp) if flujo_masico > 0 else 0
    temp_out = temp_in + delta_t
    
    return {
        "timestamp_iso": datetime.now().isoformat(),
        "it_load_kw": round(carga_kw, 2),
        "coolant_return_c": round(temp_out, 2),
        "flow_rate_lpm": round(caudal_lpm, 2),
        "partial_pue": round((carga_kw + 12) / carga_kw, 3), # 12kW overhead para CDU
        "anomaly_flag": es_anomalia
    }

# ==========================================
# UI/UX: CSS Blackwell Style
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
def obtener_datos(modo_demo):
    if modo_demo:
        return generar_dato_simulado()
    
    FILE_BUS = "telemetria_bus.json"
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
# SIDEBAR (Panel de Control Oculto)
# ==========================================
with st.sidebar:
    st.markdown("### Control Maestro")
    modo_demo = st.toggle("🚀 Activar Telemetría Live", value=False)
    
    st.divider()
    st.caption("Configuración de Nodo: NVIDIA Blackwell NVL72")
    st.caption("CDU Status: Vertiv XDU1350 Operational")

# ==========================================
# PANEL PRINCIPAL
# ==========================================
st.title("Digital Twin: NVIDIA GB200 NVL72")
st.markdown("Cluster de Alta Densidad (Blackwell Architecture) - **Telemetría en Tiempo Real**")

placeholder = st.empty()

while True:
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
            # Distribución: Rack SVG + Métricas
            col_left, col_right = st.columns([1, 3])
            
            with col_left:
                # El Rack Realista (Blackwell Style)
                st.markdown(f"""
                <div class="metric-card" style="text-align: center;">
                    <div class="metric-title">Esquema del Rack</div>
                    <svg width="140" height="220" viewBox="0 0 220 320" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <rect x="40" y="10" width="140" height="300" rx="2" fill="#0F172A" stroke="#334155" stroke-width="2"/>
                      <rect x="35" y="20" width="5" height="280" fill="#3B82F6" opacity="0.8"/>
                      <rect x="180" y="20" width="5" height="280" fill="#EF4444" opacity="0.8"/>
                      <g>
                        <rect x="45" y="30" width="130" height="8" fill="#1E293B" rx="1"/>
                        <rect x="45" y="45" width="130" height="8" fill="#1E293B" rx="1"/>
                        <rect x="45" y="140" width="130" height="40" fill="#334155" rx="2" stroke="#475569"/>
                        <text x="75" y="165" fill="#94A3B8" font-family="Inter" font-size="10" font-weight="bold">NVLINK</text>
                        <rect x="45" y="250" width="130" height="8" fill="#1E293B" rx="1"/>
                      </g>
                      <circle cx="37.5" cy="50" r="2" fill="white">
                        <animate attributeName="cy" values="20;300" dur="3s" repeatCount="indefinite" />
                      </circle>
                    </svg>
                    <div style="font-size: 10px; color: var(--text-muted); margin-top: 10px;">ID: GB200-NVL72-B1</div>
                </div>
                """, unsafe_allow_html=True)

            with col_right:
                m_col1, m_col2 = st.columns(2)
                estado_clase = "value-alert" if datos.get('anomaly_flag', False) else "value-blue"
                
                with m_col1:
                    st.markdown(f'<div class="metric-card"><div class="metric-title">Carga IT (Pico)</div><div class="metric-value {estado_clase}">{datos.get("it_load_kw", 0):.1f} <span style="font-size:16px;">kW</span></div></div>', unsafe_allow_html=True)
                with m_col2:
                    t_out = datos.get('coolant_return_c', 0)
                    color_temp = "value-alert" if t_out > 78 else "value-good"
                    st.markdown(f'<div class="metric-card"><div class="metric-title">Return Temp (T_out)</div><div class="metric-value {color_temp}">{t_out:.1f} <span style="font-size:16px;">°C</span></div></div>', unsafe_allow_html=True)
                
                st.write("")
                m_col3, m_col4 = st.columns(2)
                with m_col3:
                    st.markdown(f'<div class="metric-card"><div class="metric-title">DLC Flow Rate</div><div class="metric-value">{datos.get("flow_rate_lpm", 0):.1f} <span style="font-size:16px;">LPM</span></div></div>', unsafe_allow_html=True)
                with m_col4:
                    pue = datos.get('partial_pue', 0)
                    st.markdown(f'<div class="metric-card"><div class="metric-title">Partial PUE</div><div class="metric-value value-good">{pue:.3f}</div></div>', unsafe_allow_html=True)

            st.write("")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=st.session_state.historial['tiempo'], y=st.session_state.historial['potencia_kw'], name='Power (kW)', line=dict(color='#3B82F6', width=3), mode='lines'))
            fig.add_trace(go.Scatter(x=st.session_state.historial['tiempo'], y=st.session_state.historial['temp_c'], name='Temp (°C)', line=dict(color='#10B981', width=3), mode='lines'))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family="Inter, sans-serif"), xaxis=dict(showgrid=False, zeroline=False, nticks=10), yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)', range=[0, 350]), hovermode="x unified", margin=dict(l=0, r=0, t=20, b=80), legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5))
            st.markdown('<div class="metric-card" style="padding: 10px;">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
    time.sleep(1)

