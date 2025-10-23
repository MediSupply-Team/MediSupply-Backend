# ===========================
#   BASE COMÚN (Build stage)
# ===========================
FROM python:3.11-slim-bookworm AS base

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PYTHONHASHSEED=0

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd -r -m -g appuser appuser

COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

# ===========================
#   ENTORNO DE DESARROLLO
# ===========================
FROM base AS dev
ENV ENVIRONMENT=development \
    LOG_LEVEL=debug \
    PORT=3000 \
    RUN_DDL_ON_STARTUP=true
EXPOSE 3000
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000", "--reload", "--log-level", "debug"]

# ===========================
#   ENTORNO DE PRODUCCIÓN
# ===========================
FROM base AS prod
RUN pip install --no-cache-dir gunicorn

ENV ENVIRONMENT=production \
    LOG_LEVEL=info \
    WORKERS=2 \
    TIMEOUT=60 \
    KEEPALIVE=5 \
    PORT=3000 \
    RUN_DDL_ON_STARTUP=false

EXPOSE 3000
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python - <<'PY' || exit 1
import sys, urllib.request
try:
    with urllib.request.urlopen("http://127.0.0.1:3000/health", timeout=3) as r:
        sys.exit(0 if r.status == 200 else 1)
except Exception:
    sys.exit(1)
PY

CMD ["bash", "-lc", "gunicorn -k uvicorn.workers.UvicornWorker -w ${WORKERS:-2} -b 0.0.0.0:${PORT} app.main:app --timeout ${TIMEOUT:-60} --keep-alive ${KEEPALIVE:-5} --access-logfile - --error-logfile -"]
