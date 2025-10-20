FROM python:3.11-slim

WORKDIR /app

# ✅ Instalar wget para health checks
RUN apt-get update && \
    apt-get install -y --no-install-recommends wget && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

# ✅ Puerto fijo en 8001 (debe coincidir con bff_app_port en Terraform)
EXPOSE 8001

# ✅ CMD simplificado con puerto fijo
CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:8001", "--workers", "2", "--threads", "4", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "--capture-output"]