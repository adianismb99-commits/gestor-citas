FROM python:3.11-slim

# ============================================
# INSTALAR CHROME Y DEPENDENCIAS
# ============================================
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# INSTALAR DEPENDENCIAS DE PYTHON
# ============================================
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# COPIAR EL RESTO DEL CÓDIGO
# ============================================
COPY . .

# ============================================
# EXPONER PUERTO Y EJECUTAR
# ============================================
EXPOSE 10000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]