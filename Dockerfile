# Usa una imagen de Python oficial
FROM python:3.11-slim

# Instalar dependencias del sistema y el Driver de Microsoft para SQL Server
# Instalar dependencias del sistema y el Driver de Microsoft para SQL Server
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/keyrings/microsoft.gpg \
    && echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
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