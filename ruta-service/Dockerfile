# -------- Base común --------
FROM python:3.11-slim-bookworm AS base
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PYTHONHASHSEED=0

WORKDIR /app

# Sistema mínimo: certificados
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Usuario no root
RUN groupadd -r appuser && useradd -r -m -g appuser appuser

# Instalar dependencias
COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt

# Copiar código con ownership correcto
COPY --chown=appuser:appuser . .

# -------- Desarrollo --------
FROM base AS dev
ENV ENV=dev \
    PORT=8000
EXPOSE 8000
USER appuser
CMD ["bash", "-c", "python create_rutas_db.py && python seed.py && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"]

# -------- Producción --------
FROM base AS prod
ENV ENV=production \
    PORT=8000 \
    WORKERS=2
EXPOSE 8000
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=3).raise_for_status()" || exit 1

# Comando: crear DB → cargar seed → iniciar con workers
CMD ["bash", "-c", "python create_rutas_db.py && python seed.py && uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers ${WORKERS}"]