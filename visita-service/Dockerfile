FROM python:3.11-slim-bookworm AS base
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PYTHONHASHSEED=0

WORKDIR /app

# Instalar curl para health check
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
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
    PORT=8003
EXPOSE 8003
USER appuser
# Aumentar límite de tamaño de body a 100MB para uploads de fotos/videos
CMD ["bash", "-c", "python seed.py && uvicorn main:app --host 0.0.0.0 --port 8003 --reload --limit-max-requests 1000 --timeout-keep-alive 120 --limit-concurrency 100"]

# -------- Producción --------
FROM base AS prod
ENV ENV=production \
    PORT=8003 \
    WORKERS=2
EXPOSE 8003
USER appuser

# Health check usando curl
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8003/health || exit 1

# Aumentar límite de tamaño de body a 100MB para uploads de fotos/videos
CMD ["bash", "-c", "python seed.py && uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers ${WORKERS} --limit-max-requests 1000 --timeout-keep-alive 120 --limit-concurrency 100"]
