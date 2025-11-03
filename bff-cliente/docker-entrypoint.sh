#!/bin/bash
set -e

# Usar PORT de variable de entorno o default a 8001
PORT=${PORT:-8001}

echo "Starting Gunicorn on port $PORT..."

exec gunicorn wsgi:app \
  --bind "0.0.0.0:$PORT" \
  --workers 2 \
  --threads 4 \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  --capture-output