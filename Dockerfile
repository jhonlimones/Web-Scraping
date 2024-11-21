# Usar una imagen base oficial de Python
FROM python:3.9-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo requirements.txt e instalar las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de la aplicación al contenedor
COPY . .

# Exponer el puerto donde Flask correrá (si fuera necesario)
EXPOSE 5000

# Establecer la variable de entorno para evitar buffering
ENV PYTHONUNBUFFERED=1

# Comando por defecto al ejecutar el contenedor
CMD ["python", "scraper.py"]
