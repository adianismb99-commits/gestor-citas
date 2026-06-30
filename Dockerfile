# Usar la imagen oficial de Playwright con Python
FROM mcr.microsoft.com/playwright/python:v1.40.0-focal

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de dependencias y luego instalarlas
# Esto se hace en dos pasos para aprovechar la caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación
COPY . .

# Descargar los navegadores de Playwright
RUN playwright install

# Exponer el puerto que Render usará (10000 por defecto)
EXPOSE 10000

# Comando para iniciar la aplicación con Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]