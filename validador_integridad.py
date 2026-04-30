import json
import os
import time

# Configuración de Límites Industriales
LIMITES = {
    "it_load_kw": {"min": 0, "max": 310},
    "coolant_return_c": {"min": 40, "max": 78},
    "partial_pue": {"min": 1.0, "max": 1.1}
}

FILE_BUS = "telemetria_bus.json"
FILE_STATE = "shared_state.json"

def validar_lectura(data):
    alertas = []
    # Usamos los nombres de campos de la versión CTO
    pwr = data.get("it_load_kw", 0)
    t_out = data.get("coolant_return_c", 0)
    pue = data.get("partial_pue", 0)
    
    if pwr > LIMITES["it_load_kw"]["max"]:
        alertas.append(f"ALTA CARGA: {pwr}kW")
    
    if t_out > LIMITES["coolant_return_c"]["max"]:
        alertas.append(f"CALOR CRITICO: {t_out}C")
        
    if pue > LIMITES["partial_pue"]["max"]:
        alertas.append(f"PUE INEFICIENTE: {pue}")
    
    return {
        "es_valido": len(alertas) == 0,
        "alertas": alertas,
        "metrics": {"kw": pwr, "temp": t_out, "pue": pue}
    }

def ejecutar_observador():
    print("=== ANALISTA KORAT FLOW: OBSERVANDO INTEGRIDAD ===")
    
    while True:
        if os.path.exists(FILE_BUS):
            try:
                with open(FILE_BUS, "r") as f:
                    lectura = json.load(f)
                
                analisis = validar_lectura(lectura)
                
                # Actualizar Estado Compartido
                estado = {
                    "last_update": lectura["timestamp_iso"],
                    "status": "NOMINAL" if analisis["es_valido"] else "ALERT",
                    "alertas": analisis["alertas"],
                    "reasoning": f"Analizando {analisis['metrics']['kw']}kW y {analisis['metrics']['temp']}C"
                }
                
                with open(FILE_STATE, "w") as f:
                    json.dump(estado, f, indent=4)
                
                # Consola más descriptiva
                icon = "✅" if analisis["es_valido"] else "⚠️"
                msg = "Todo en orden" if analisis["es_valido"] else f"ALERTAS: {', '.join(analisis['alertas'])}"
                print(f"[{time.strftime('%H:%M:%S')}] {icon} {msg} | PUE: {analisis['metrics']['pue']}")
                
            except Exception as e:
                pass # Ignorar errores de lectura parcial si el simulador está escribiendo
        
        time.sleep(1.5)

if __name__ == "__main__":
    ejecutar_observador()
