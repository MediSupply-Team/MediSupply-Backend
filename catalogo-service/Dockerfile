FROM python:3.12-slim

WORKDIR /app

# Instalar curl para health checks
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY test-requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r test-requirements.txt

COPY app ./app
COPY tests ./tests
COPY pytest.ini .
COPY data ./data

# Copiar script de entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENV PYTHONUNBUFFERED=1

# Puerto 3000 para coincidir con Terraform
EXPOSE 3000

# Health check para ECS (más tiempo de inicio para población de datos)
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# Usar entrypoint para inicialización
ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]
