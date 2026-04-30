import json
import time
import random
import paho.mqtt.client as mqtt
from CoolProp.CoolProp import PropsSI
import polars as pl
from pydantic import BaseModel, Field

# Configuración MQTT
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "koratflow/planta_01/racks/dlc_240k_01/telemetria"

# Modelo de Datos Estricto (Validación Industrial)
class TelemetriaRack(BaseModel):
    timestamp_ms: int
    asset_id: str = "RACK-DLC-01"
    power_kw: float = Field(..., ge=0, le=500)
    coolant_inlet_c: float
    coolant_outlet_c: float
    flow_rate_lpm: float
    pue_instantaneo: float
    status_flag: str

def obtener_cp_real(temp_c, presion_pa=101325):
    """Calcula el Cp real del agua usando CoolProp para mayor rigor físico"""
    try:
        return PropsSI('C', 'T', temp_c + 273.15, 'P', presion_pa, 'Water') / 1000.0
    except Exception:
        return 4.184 # Fallback seguro

def generar_lectura_v2() -> TelemetriaRack:
    carga_kw = 240.0 + random.gauss(0, 5)
    temp_in = 45.0 + random.gauss(0, 0.2)
    caudal_lpm = 120.0 + random.gauss(0, 1)
    
    # 1. Obtener CP dinámico basado en la física real
    cp_dinamico = obtener_cp_real(temp_in)
    
    # 2. Cálculo térmico preciso
    m_dot = (caudal_lpm / 60.0) # kg/s aprox
    delta_t = carga_kw / (m_dot * cp_dinamico) if m_dot > 0 else 0
    temp_out = temp_in + delta_t
    
    # 3. Cálculo de PUE (Simulado: Energía total / Energía IT)
    pue = (carga_kw * 1.05) / carga_kw 
    
    estado = "CRITICAL" if temp_out > 70.0 or caudal_lpm < 80.0 else ("WARNING" if temp_out > 65.0 else "NOMINAL")
    
    return TelemetriaRack(
        timestamp_ms=int(time.time() * 1000),
        power_kw=round(carga_kw, 2),
        coolant_inlet_c=round(temp_in, 2),
        coolant_outlet_c=round(temp_out, 2),
        flow_rate_lpm=round(caudal_lpm, 2),
        pue_instantaneo=round(pue, 3),
        status_flag=estado
    )

def iniciar_gemelo_digital():
    print("=== INICIANDO GEMELO DIGITAL KORAT FLOW V2 ===")
    print("Rigor Físico: Activado (CoolProp)")
    print("Validación de Datos: Estricta (Pydantic)")
    print("--------------------------------------------------")
    
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "simulador_dlc_v2")
    conexion_activa = False
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        conexion_activa = True
        print(f"Conectado a MQTT -> {MQTT_BROKER}:{MQTT_PORT}")
    except Exception as e:
        print(f"Advertencia MQTT ({e}). Modo Local activo.")
    
    try:
        while True:
            # Generación y validación garantizada por Pydantic
            telemetria = generar_lectura_v2()
            json_str = telemetria.model_dump_json()
            
            print(f"[{telemetria.status_flag}] Q:{telemetria.power_kw}kW | T_in:{telemetria.coolant_inlet_c}°C | T_out:{telemetria.coolant_outlet_c}°C | Flujo:{telemetria.flow_rate_lpm}LPM | PUE:{telemetria.pue_instantaneo}")
            
            # Publicar si el broker está activo
            if conexion_activa:
                client.publish(MQTT_TOPIC, json_str)
            
            # ESCRIBIR AL BUS LOCAL (Para el Validador de Integridad)
            with open("telemetria_bus.json", "w") as f:
                f.write(json_str)
                
            time.sleep(2.0)
            
    except KeyboardInterrupt:
        print("\nSimulación V2 detenida.")
    finally:
        if conexion_activa:
            client.loop_stop()
            client.disconnect()

if __name__ == "__main__":
    iniciar_gemelo_digital()
