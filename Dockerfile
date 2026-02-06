# Usa una imagen de Python oficial
FROM python:3.11-slim

# Instalar dependencias del sistema y el Driver de Microsoft para SQL Server
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev \
    && apt-get clean

# Directorio de trabajo
WORKDIR /app

# Copiar el archivo de requerimientos e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Comando para arrancar la app (Render ignorará el comando de la interfaz y usará este)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]