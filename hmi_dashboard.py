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

# Estilos CSS Personalizados para el Dark Mode Industrial
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: #C9D1D9;
    }
    .metric-card {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }
    .metric-value-normal { color: #3FB950; font-size: 28px; font-weight: bold; }
    .metric-value-alert { color: #F85149; font-size: 28px; font-weight: bold; }
    .metric-label { color: #8B949E; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }
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
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/1200px-Python-logo-notext.svg.png", width=50) # Placeholder logo
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
        st.success("🟢 MQTT: Conectado (Unified Namespace)")
        st.info("🔄 Actualización: Tiempo Real")
    else:
        st.error("🔴 MQTT: Desconectado")
        st.warning("Inicia el Simulador Térmico para recibir datos.")

# ==========================================
# PANEL PRINCIPAL (MAIN DASHBOARD)
# ==========================================
st.title("⚡ AI Factory - Telemetría Térmica de Alta Densidad (DLC)")
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
