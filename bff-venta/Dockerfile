FROM python:3.11-slim

WORKDIR /app

# Instalar curl para health checks
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV PYTHONUNBUFFERED=1

# Puerto 8000
EXPOSE 8000

# Gunicorn en producción
CMD ["gunicorn","wsgi:app","--bind", "0.0.0.0:8000","--workers", "2","--threads", "4","--access-logfile", "-","--error-logfile", "-","--log-level", "info","--capture-output"]