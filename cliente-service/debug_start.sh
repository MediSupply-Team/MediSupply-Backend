#!/bin/bash
echo "=== DEBUG: Environment Variables ==="
echo "DATABASE_URL: $DATABASE_URL"
echo "ENV: $ENV"
echo "====================================="

# Si DATABASE_URL está vacía, falla
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL is not set!"
    exit 1
fi

# Iniciar la aplicación
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1