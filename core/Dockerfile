
FROM python:3.11-slim-bookworm

# Dependencias base necesarias para instalar el paquete de Microsoft
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    unixodbc \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala el driver ODBC 17 de Microsoft usando el paquete oficial .deb (método moderno, sin apt-key)
RUN curl -sSL -O https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .


RUN python manage.py collectstatic --no-input

EXPOSE 10000

CMD python manage.py migrate && gunicorn core.wsgi:application --bind 0.0.0.0:10000