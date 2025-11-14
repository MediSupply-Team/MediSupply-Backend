#!/bin/bash
set -e

echo "⏳ Esperando a que la base de datos esté lista..."
# Retry con Python (intenta conectar cada 1s)
python - <<'EOF'
import os, time
from sqlalchemy import create_engine
url = os.getenv("DATABASE_URL")
assert url, "DATABASE_URL no definida"
while True:
    try:
        create_engine(url).connect().close()
        break
    except Exception as e:
        print("DB no lista:", e)
        time.sleep(1)
print("✅ DB lista")
EOF

echo "🔄 Ejecutando migración de base de datos..."
python migrate_db.py

echo "🌱 Generando visitas dinámicas desde cliente-service..."
python seed.py

echo "🚀 Iniciando FastAPI..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
