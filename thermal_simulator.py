import json
import time
import math
import random
import paho.mqtt.client as mqtt
from datetime import datetime
from CoolProp.CoolProp import PropsSI
from pydantic import BaseModel, Field

# ==========================================
# CONFIGURACIÓN DEL ENTORNO Y UNIFIED NAMESPACE
# ==========================================
MQTT_BROKER = "broker.hivemq.com" # Placeholder público para pruebas
MQTT_PORT = 1883
# Unified Namespace: Empresa/Planta/Area/Linea/Celda
UNS_TOPIC = "koratflow/edge/dc_alpha/row_a/rack_dlc_01/telemetry"

# Parámetros del gemelo digital
POTENCIA_BASE_KW = 240.0
AMPLITUD_SINUSOIDAL_KW = 40.0 # Fluctuación entre 200kW y 280kW
TEMP_INLET_NOMINAL_C = 45.0
CAUDAL_NOMINAL_LPM = 120.0
ANOMALIA_INTERVALO_SEG = 60 # 1 minuto (Acelerado para pruebas)

# ==========================================
# MODELO DE DATOS ESTRICTO (PYDANTIC)
# ==========================================
class RackTelemetry(BaseModel):
    timestamp_iso: str
    asset_id: str = "RACK-DLC-01"
    it_load_kw: float = Field(..., description="Carga IT instantánea en kW")
    coolant_supply_c: float = Field(..., description="Temperatura de entrada")
    coolant_return_c: float = Field(..., description="Temperatura de salida")
    flow_rate_lpm: float = Field(..., description="Caudal de refrigerante")
    partial_pue: float = Field(..., description="Power Usage Effectiveness parcial")
    anomaly_flag: bool = Field(False, description="Flag de inyección de anomalía")

# ==========================================
# LÓGICA DEL GEMELO DIGITAL
# ==========================================
def obtener_cp_dinamico(temp_c: float) -> float:
    """Calcula el calor específico real del agua usando CoolProp."""
    try:
        return PropsSI('C', 'T', temp_c + 273.15, 'P', 101325, 'Water') / 1000.0
    except Exception:
        return 4.184

def simular_telemetria(inicio_simulacion: float) -> RackTelemetry:
    tiempo_actual = time.time()
    tiempo_transcurrido = tiempo_actual - inicio_simulacion
    
    # 1. Función Senoidal para la carga IT (simula el ciclo diario, acelerado para la demo)
    # Ciclo completo cada 10 minutos (600 seg) para efectos de demostración
    fase = (tiempo_transcurrido % 600) / 600.0 * 2 * math.pi
    carga_teorica = POTENCIA_BASE_KW + (math.sin(fase) * AMPLITUD_SINUSOIDAL_KW)
    
    # Inyección de Ruido Blanco (Gaussian Noise)
    carga_kw = carga_teorica + random.gauss(0, 2.0)
    temp_in = TEMP_INLET_NOMINAL_C + random.gauss(0, 0.1)
    caudal_lpm = CAUDAL_NOMINAL_LPM + random.gauss(0, 0.5)
    
    # 2. Inyección de Anomalía Térmica (Spike de +5°C cada 5 min)
    es_anomalia = False
    if int(tiempo_transcurrido) % ANOMALIA_INTERVALO_SEG < 5 and tiempo_transcurrido > 10:
        carga_kw += 50.0 # Pico de IA masivo repentino
        es_anomalia = True
    
    # 3. Cálculo Físico Real de Delta T
    cp_dinamico = obtener_cp_dinamico(temp_in)
    flujo_masico = caudal_lpm / 60.0
    delta_t = carga_kw / (flujo_masico * cp_dinamico) if flujo_masico > 0 else 0
    temp_out = temp_in + delta_t
    
    # 4. Cálculo PUE (Simplificado: P_Total / P_IT)
    pue = (carga_kw + 10.0) / carga_kw # Asumiendo 10kW fijos de bombas/cooling
    
    return RackTelemetry(
        timestamp_iso=datetime.utcnow().isoformat() + "Z",
        it_load_kw=round(carga_kw, 2),
        coolant_supply_c=round(temp_in, 2),
        coolant_return_c=round(temp_out, 2),
        flow_rate_lpm=round(caudal_lpm, 2),
        partial_pue=round(pue, 3),
        anomaly_flag=es_anomalia
    )

def iniciar_nodo_edge():
    print("[KORAT FLOW CTO] Iniciando Nodo Edge de Telemetria (Digital Twin)")
    print(f"Conectando al Unified Namespace: {UNS_TOPIC}")
    
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "korat_edge_sim_01")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        print(f"MQTT Conectado ({MQTT_BROKER})")
    except Exception as e:
        print(f"Error MQTT ({e}). Ejecutando en modo consola estricto.")
        
    inicio_simulacion = time.time()
    
    try:
        while True:
            datos = simular_telemetria(inicio_simulacion)
            payload = datos.model_dump_json()
            
            # Formateo visual para la consola
            estado = "ANOMALIA" if datos.anomaly_flag else "NOMINAL"
            print(f"[{estado}] IT Load: {datos.it_load_kw}kW | Return T: {datos.coolant_return_c}°C | PUE: {datos.partial_pue}")
            
            if client.is_connected():
                client.publish(UNS_TOPIC, payload)
            
            # ESCRIBIR AL BUS LOCAL PARA EL VALIDADOR
            with open("telemetria_bus.json", "w") as f:
                f.write(payload)
                
            time.sleep(1) # High frequency data
            
    except KeyboardInterrupt:
        print("\nApagado controlado del Nodo Edge.")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    iniciar_nodo_edge()
