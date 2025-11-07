#!/bin/bash

# Script para iniciar catalogo-service localmente

echo "🚀 Iniciando Catalogo-Service"
echo "=============================="
echo ""

# Ir al directorio
cd "$(dirname "$0")/catalogo-service"

# Activar entorno virtual
source venv/bin/activate

# Configurar variables de entorno
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5433/catalogo"
export API_PREFIX="/api"

# Mostrar configuración
echo "📋 Configuración:"
echo "   DATABASE_URL: postgresql+asyncpg://user:***@localhost:5433/catalogo"
echo "   API_PREFIX: /api"
echo "   SQS: Deshabilitado (normal para local)"
echo ""

# Iniciar servicio
echo "⏳ Iniciando servidor en http://localhost:8000"
echo ""
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

