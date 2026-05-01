import streamlit as st
import json
import os
import time
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

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
# UI/UX: CSS Premium & Adaptativo (Light/Dark)
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Variables dinámicas para Light/Dark Mode */
:root {
    --card-bg: #ffffff;
    --card-border: #e2e8f0;
    --text-main: #0f172a;
    --text-muted: #64748b;
    --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
}

@media (prefers-color-scheme: dark) {
    :root {
        --card-bg: #1e293b;
        --card-border: #334155;
        --text-main: #f8fafc;
        --text-muted: #94a3b8;
        --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
}

.metric-card {
    background-color: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 16px;
    padding: 24px;
    box-shadow: var(--shadow);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    display: flex;
    flex-direction: column;
    height: 100%;
}

.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

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

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.6; }
    100% { opacity: 1; }
}

/* Ocultar barra superior de Streamlit para un look más limpio app-like */
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# LECTURA DEL BUS DE DATOS
# ==========================================
FILE_BUS = "telemetria_bus.json"

@st.cache_data(ttl=1)
def obtener_telemetria():
    if os.path.exists(FILE_BUS):
        try:
            with open(FILE_BUS, "r") as f:
                return json.load(f)
        except Exception:
            return None
    return None

if 'historial' not in st.session_state:
    st.session_state.historial = pd.DataFrame(columns=['tiempo', 'potencia_kw', 'temp_c', 'pue'])

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    # Logo SVG Limpio y Moderno
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 24px;">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path>
        </svg>
        <h2 style="margin: 0; font-family: 'Inter', sans-serif; font-weight: 700; font-size: 24px;">Korat Flow</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Observabilidad")
    st.caption("Monitor Térmico en Tiempo Real")
    
    st.divider()
    
    st.markdown("**UNIFIED NAMESPACE**")
    st.code("""
🏢 Empresa (Korat)
 └── 🏭 Planta (DC Alpha)
      └── 🗄️ Fila A
           └── 💻 RACK_DLC_01
    """, language="text")
    
    st.divider()
    
    datos = obtener_telemetria()
    if datos:
        st.success("🟢 Sistema Conectado")
    else:
        st.error("🔴 Sistema Desconectado")
        st.caption("Esperando telemetría...")

# ==========================================
# PANEL PRINCIPAL
# ==========================================
st.title("Monitor de Rendimiento Térmico")
st.markdown("Rack 240kW - Estado Operacional en Tiempo Real")

placeholder = st.empty()

for _ in range(100):
    datos = obtener_telemetria()
    
    if datos:
        nuevo_registro = pd.DataFrame([{
            'tiempo': datetime.now().strftime('%H:%M:%S'),
            'potencia_kw': datos.get('it_load_kw', 0),
            'temp_c': datos.get('coolant_return_c', 0),
            'pue': datos.get('partial_pue', 1.0)
        }])
        st.session_state.historial = pd.concat([st.session_state.historial, nuevo_registro]).tail(60)
        
        with placeholder.container():
            # 1. TARJETAS DE MÉTRICAS (Responsive Columns)
            col1, col2, col3, col4 = st.columns(4)
            
            estado_clase = "value-alert" if datos.get('anomaly_flag', False) else "value-blue"
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Carga IT Actual</div>
                    <div class="metric-value {estado_clase}">{datos.get('it_load_kw', 0):.1f} <span style="font-size:16px;">kW</span></div>
                </div>
                """, unsafe_allow_html=True)
                
            with col2:
                t_out = datos.get('coolant_return_c', 0)
                color_temp = "value-alert" if t_out > 78 else "value-good"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Temp. Retorno</div>
                    <div class="metric-value {color_temp}">{t_out:.1f} <span style="font-size:16px;">°C</span></div>
                </div>
                """, unsafe_allow_html=True)
                
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Caudal DLC</div>
                    <div class="metric-value value-main">{datos.get('flow_rate_lpm', 0):.1f} <span style="font-size:16px;">LPM</span></div>
                </div>
                """, unsafe_allow_html=True)
                
            with col4:
                pue = datos.get('partial_pue', 0)
                color_pue = "value-alert" if pue > 1.05 else "value-good"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">PUE Parcial</div>
                    <div class="metric-value {color_pue}">{pue:.3f}</div>
                </div>
                """, unsafe_allow_html=True)
                
            st.write("") # Espaciador
            
            # 2. GRÁFICO DINÁMICO
            st.subheader("Evolución de Tendencias")
            
            fig = go.Figure()
            
            # Determinar el modo actual (claro/oscuro) para el gráfico no es directo en CSS variables para Plotly,
            # así que usamos transparente para que se adapte al fondo de Streamlit.
            fig.add_trace(go.Scatter(
                x=st.session_state.historial['tiempo'],
                y=st.session_state.historial['potencia_kw'],
                name='Potencia (kW)',
                line=dict(color='#3B82F6', width=3),
                mode='lines'
            ))
            
            fig.add_trace(go.Scatter(
                x=st.session_state.historial['tiempo'],
                y=st.session_state.historial['temp_c'],
                name='Temp (°C)',
                line=dict(color='#10B981', width=3),
                mode='lines'
            ))

            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter, sans-serif"),
                xaxis=dict(showgrid=False, zeroline=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
                hovermode="x unified",
                margin=dict(l=0, r=0, t=20, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            # Envolvemos el gráfico en una tarjeta
            st.markdown('<div class="metric-card" style="padding: 10px;">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.write("") # Espaciador
            
            # 3. ALERTAS
            if datos.get('anomaly_flag', False):
                st.error("⚠️ ALERTA: Pico de carga detectado. Se recomienda inspección térmica.")
            
    time.sleep(1)

