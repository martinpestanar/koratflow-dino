# Usar Python 3.11 (Garantiza compatibilidad de binarios precompilados para CoolProp en Linux)
FROM python:3.11

# Evitar archivos .pyc y habilitar logs (formato actualizado)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema extra por si acaso
RUN apt-get update && apt-get install -y \
    cmake \
    gfortran \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar requerimientos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Streamlit y Plotly (que no estaban en el requirements original)
RUN pip install --no-cache-dir streamlit plotly

COPY . .

EXPOSE 8501

CMD ["python", "thermal_simulator.py"]
