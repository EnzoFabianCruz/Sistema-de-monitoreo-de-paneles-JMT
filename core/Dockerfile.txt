FROM python:3.11-slim

# Dependencias base necesarias para agregar el repositorio de Microsoft
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    apt-transport-https \
    unixodbc \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Agrega el repositorio oficial de Microsoft e instala el driver ODBC 17
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia requirements primero (mejor cache de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del proyecto (incluye la carpeta core/)
COPY . .

# Se mueve a donde está manage.py
WORKDIR /app/core

# Recolecta estáticos
RUN python manage.py collectstatic --no-input

EXPOSE 10000

CMD python manage.py migrate && gunicorn core.wsgi:application --bind 0.0.0.0:10000