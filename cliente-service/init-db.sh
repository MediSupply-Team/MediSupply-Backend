#!/bin/bash
set -e

echo "🔄 Cliente Service - Inicializando base de datos..."

# Esperar a que la aplicación esté lista (el DATABASE_URL esté disponible)
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL no está configurado"
    exit 1
fi

echo "✅ DATABASE_URL configurado"

# Ejecutar el script de población de datos
python3 /app/app/populate_db.py

echo "✅ Inicialización de base de datos completada"

