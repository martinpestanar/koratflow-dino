from mcp.server.fastmcp import FastMCP
from CoolProp.CoolProp import PropsSI
import json

# Instanciar el servidor MCP
mcp = FastMCP("Korat Flow - Thermal Skills")

@mcp.tool()
def coolprop_thermo_calc(fluid: str, temp_c: float, pressure_pa: float) -> str:
    """
    Calcula propiedades termofísicas de fluidos refrigerantes en tiempo real.
    
    Args:
        fluid: Nombre del fluido (ej. "Water", "R134a", "R410A").
        temp_c: Temperatura de entrada en grados Celsius.
        pressure_pa: Presión en Pascales.
    """
    try:
        temp_k = temp_c + 273.15
        enthalpy = PropsSI('H', 'T', temp_k, 'P', pressure_pa, fluid)
        density = PropsSI('D', 'T', temp_k, 'P', pressure_pa, fluid)
        
        return json.dumps({
            "status": "success",
            "fluid": fluid,
            "enthalpy_j_kg": round(enthalpy, 2),
            "density_kg_m3": round(density, 2)
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

@mcp.tool()
def polars_telemetry_analyzer(data_source: str, query_window: str) -> str:
    """
    Simula el análisis rápido de telemetría usando Polars.
    
    Args:
        data_source: Ruta o endpoint de datos.
        query_window: Ventana de tiempo (ej. "last_15m").
    """
    return json.dumps({
        "status": "simulated_success",
        "message": f"Análisis rápido ejecutado sobre {data_source} para la ventana {query_window}.",
        "anomalies_detected": 0
    })

if __name__ == "__main__":
    print("Iniciando Servidor MCP 'Korat Flow - Thermal Skills' en modo stdio...")
    # FastMCP por defecto usa stdio para comunicarse con clientes MCP locales
    mcp.run()
