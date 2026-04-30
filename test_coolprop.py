from CoolProp.CoolProp import PropsSI

def calcular_entalpia_refrigerante(fluido, T_celsius, P_pascales):
    """
    Calcula la entalpía de un fluido industrial para monitoreo térmico.
    """
    try:
        T_kelvin = T_celsius + 273.15
        h = PropsSI('H', 'T', T_kelvin, 'P', P_pascales, fluido)
        return f"La entalpía para {fluido} a {T_celsius}°C y {P_pascales} Pa es {h:.2f} J/kg"
    except Exception as e:
        return f"Error en el cálculo: {str(e)}"

# Prueba rápida con Agua (Water)
if __name__ == "__main__":
    resultado = calcular_entalpia_refrigerante('Water', 25, 101325)
    print(resultado)
