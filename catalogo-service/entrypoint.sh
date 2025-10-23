#!/bin/bash
set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║          📦 CATALOGO SERVICE - INICIALIZANDO                 ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

# Verificar que DATABASE_URL esté configurado
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL no está configurado"
    exit 1
fi

echo "✅ DATABASE_URL configurado"
echo ""

# Ejecutar script de población de datos (idempotente - solo inserta si no hay datos)
echo "🔄 Verificando e inicializando datos..."
cd /app && python3 -m app.populate_db

if [ $? -eq 0 ]; then
    echo "✅ Inicialización de base de datos completada"
else
    echo "⚠️  Advertencia: Hubo un problema en la inicialización, pero continuamos..."
fi

echo ""
echo "🚀 Iniciando aplicación..."
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Ejecutar el comando original (uvicorn)
exec "$@"

