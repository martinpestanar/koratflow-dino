# Usar una imagen de Python 3.12
FROM python:3.12-slim

# Evitar archivos .pyc y habilitar logs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instalar dependencias del sistema necesarias para compilar CoolProp y otras libs científicas
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    gfortran \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar requerimientos
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Instalar Streamlit y Plotly (que no estaban en el requirements original)
RUN pip install --no-cache-dir streamlit plotly

COPY . .

EXPOSE 8501

CMD ["python", "thermal_simulator.py"]
