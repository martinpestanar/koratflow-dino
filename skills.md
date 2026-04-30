# skills.md

## Catálogo de Herramientas Agénticas (Tool Calling)

El Orquestador Central tiene acceso estricto a las siguientes herramientas para interactuar con la infraestructura y los datos:

### 1. `coolprop_thermo_calc`
- **Descripción:** Calcula propiedades termofísicas de fluidos refrigerantes en tiempo real.
- **Inputs:** 
  - `fluid` (string): Nombre del fluido (ej. "Water", "R134a", "R410A").
  - `temp_c` (float): Temperatura de entrada en grados Celsius.
  - `pressure_pa` (float): Presión en Pascales.
- **Outputs:** 
  - `enthalpy_j_kg` (float): Entalpía específica.
  - `density_kg_m3` (float): Densidad del fluido.

### 2. `polars_telemetry_analyzer`
- **Descripción:** Ingiere y procesa millones de filas de series temporales (sensores) para detectar anomalías térmicas en milisegundos.
- **Inputs:** 
  - `data_source` (string): Ruta del archivo parquet o endpoint de la base de datos temporal.
  - `query_window` (string): Ventana de tiempo (ej. "last_15m").
- **Outputs:** 
  - `anomalies` (list[dict]): Picos de temperatura o caídas de presión detectadas con desviación estándar.

### 3. `tespy_digital_twin_sim`
- **Descripción:** Ejecuta una simulación de estado estacionario de la red térmica (gemelo digital) para predecir el impacto de un cambio de hardware.
- **Inputs:** 
  - `component_id` (string): ID del equipo a modificar (ej. "PUMP-02").
  - `new_efficiency` (float): Nuevo valor de eficiencia isentrópica.
- **Outputs:** 
  - `projected_pue` (float): Nuevo PUE estimado.
  - `thermal_margin_c` (float): Margen térmico resultante.

### 4. `n8n_webhook_dispatch`
- **Descripción:** Dispara flujos de trabajo de automatización externa para notificar a los ingenieros de planta o integrar sistemas de tickets.
- **Inputs:** 
  - `severity` (string): Nivel de alerta ("CRITICAL", "WARNING", "INFO").
  - `payload` (dict): Datos técnicos del evento y métricas afectadas.
- **Outputs:** 
  - `dispatch_status` (string): ID de confirmación del CRM/n8n.
