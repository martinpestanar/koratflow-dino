import streamlit as st
import json
import os
import time
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA (Cyber-Industrial)
# ==========================================
st.set_page_config(
    page_title="Korat Flow | HMI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS Personalizados Premium
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at 50% 0%, #1a1e29 0%, #0a0e17 100%);
        color: #E2E8F0;
    }
    
    /* Efecto Glassmorphism para las tarjetas */
    .metric-card {
        background: rgba(22, 27, 34, 0.4);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px 20px;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 40px rgba(0, 240, 255, 0.1);
        border: 1px solid rgba(0, 240, 255, 0.3);
    }
    
    /* Títulos y valores premium */
    .metric-label { 
        color: #94A3B8; 
        font-size: 13px; 
        text-transform: uppercase; 
        letter-spacing: 1.5px; 
        font-weight: 600;
        margin-bottom: 10px;
    }
    
    .metric-value-normal { 
        color: #10B981; 
        font-size: 36px; 
        font-weight: 700; 
        text-shadow: 0 0 20px rgba(16, 185, 129, 0.4);
    }
    
    .metric-value-alert { 
        color: #EF4444; 
        font-size: 36px; 
        font-weight: 700; 
        text-shadow: 0 0 20px rgba(239, 68, 68, 0.4);
        animation: pulse-alert 2s infinite;
    }
    
    @keyframes pulse-alert {
        0% { text-shadow: 0 0 20px rgba(239, 68, 68, 0.4); }
        50% { text-shadow: 0 0 40px rgba(239, 68, 68, 0.8); }
        100% { text-shadow: 0 0 20px rgba(239, 68, 68, 0.4); }
    }
    
    /* Gradiente para el título principal */
    h1 {
        background: linear-gradient(90deg, #00F0FF 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        letter-spacing: -1px;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# LECTURA DEL BUS DE DATOS (Simula la conexión MQTT/Local)
# ==========================================
FILE_BUS = "telemetria_bus.json"

@st.cache_data(ttl=1) # Cache corto para sensación de tiempo real
def obtener_telemetria():
    if os.path.exists(FILE_BUS):
        try:
            with open(FILE_BUS, "r") as f:
                return json.load(f)
        except Exception:
            return None
    return None

# Inicializar estado para el historial del gráfico
if 'historial' not in st.session_state:
    st.session_state.historial = pd.DataFrame(columns=['tiempo', 'potencia_kw', 'temp_c', 'pue'])

# ==========================================
# SIDEBAR: Unified Namespace & Contexto
# ==========================================
with st.sidebar:
    st.image("logo.png", width=150) # Logo Premium de Korat Flow
    st.title("Korat Flow")
    st.markdown("### Observabilidad Industrial")
    
    st.markdown("---")
    st.markdown("**UNIFIED NAMESPACE**")
    st.code("""
🏢 Empresa (Korat)
 └── 🏭 Planta (DC Alpha)
      └── 🗄️ Fila A
           └── 💻 RACK_DLC_01
    """, language="text")
    
    st.markdown("---")
    st.markdown("**ESTADO DE CONEXIÓN**")
    
    datos = obtener_telemetria()
    if datos:
        st.success("🟢 MQTT: Conectado")
        st.info("🔄 Estado: Operacional | v1.1")
    else:
        st.error("🔴 MQTT: Desconectado")
        st.warning("Inicia el Simulador Térmico para recibir datos.")

# ==========================================
# PANEL PRINCIPAL (MAIN DASHBOARD)
# ==========================================
st.title("⚡ Korat Flow HMI | v1.1 - LIVE")
st.markdown("Monitor de Rendimiento Térmico en Tiempo Real - **Rack 240kW**")

# Contenedor principal que se actualizará
placeholder = st.empty()

# Bucle principal de actualización (Simulando Reactividad)
for _ in range(100): # Limitado a 100 iteraciones para evitar infinite loop en Streamlit, el usuario puede refrescar
    datos = obtener_telemetria()
    
    if datos:
        # Actualizar Historial
        nuevo_registro = pd.DataFrame([{
            'tiempo': datetime.now().strftime('%H:%M:%S'),
            'potencia_kw': datos.get('it_load_kw', 0),
            'temp_c': datos.get('coolant_return_c', 0),
            'pue': datos.get('partial_pue', 1.0)
        }])
        st.session_state.historial = pd.concat([st.session_state.historial, nuevo_registro]).tail(60) # Mantener últimos 60 segundos
        
        with placeholder.container():
            # 1. TARJETAS DE MÉTRICAS (KPIs)
            col1, col2, col3, col4 = st.columns(4)
            
            estado_clase = "metric-value-alert" if datos.get('anomaly_flag', False) else "metric-value-normal"
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Carga IT Actual</div>
                    <div class="{estado_clase}">{datos.get('it_load_kw', 0):.1f} kW</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col2:
                t_out = datos.get('coolant_return_c', 0)
                color_temp = "metric-value-alert" if t_out > 78 else "metric-value-normal"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Temp. de Retorno (T_out)</div>
                    <div class="{color_temp}">{t_out:.1f} °C</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Caudal DLC</div>
                    <div class="metric-value-normal">{datos.get('flow_rate_lpm', 0):.1f} LPM</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col4:
                pue = datos.get('partial_pue', 0)
                color_pue = "metric-value-alert" if pue > 1.05 else "metric-value-normal"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">PUE Parcial</div>
                    <div class="{color_pue}">{pue:.3f}</div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 2. GRÁFICO DINÁMICO (Plotly)
            st.subheader("📈 Evolución de Carga y Temperatura")
            
            fig = go.Figure()
            
            # Línea de Potencia
            fig.add_trace(go.Scatter(
                x=st.session_state.historial['tiempo'],
                y=st.session_state.historial['potencia_kw'],
                name='Potencia IT (kW)',
                line=dict(color='#00F0FF', width=2),
                mode='lines+markers'
            ))
            
            # Línea de Temperatura en Eje Secundario (Simulado visualmente ajustando la escala)
            fig.add_trace(go.Scatter(
                x=st.session_state.historial['tiempo'],
                y=st.session_state.historial['temp_c'],
                name='Temp. Retorno (°C)',
                line=dict(color='#FF3E3E', width=2),
                mode='lines'
            ))

            fig.update_layout(
                paper_bgcolor='#0E1117',
                plot_bgcolor='#161B22',
                font=dict(color='#C9D1D9'),
                xaxis=dict(showgrid=False, zeroline=False),
                yaxis=dict(showgrid=True, gridcolor='#30363D', title="kW / °C"),
                hovermode="x unified",
                margin=dict(l=20, r=20, t=30, b=20)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 3. CONSOLA DE ALERTAS
            if datos.get('anomaly_flag', False):
                st.error("🔥 ALERTA TÉRMICA: Pico de carga detectado. Delta T superando umbrales de seguridad.")
            else:
                st.success("✅ Sistema operando dentro del margen de seguridad termodinámico.")
            
    time.sleep(1) # Refresco de la interfaz cada segundo
