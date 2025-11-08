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

# Ejecutar sistema de inicialización automática de base de datos
echo "🔄 Ejecutando inicialización automática de base de datos..."
cd /app && python3 -m app.db_init

if [ $? -eq 0 ]; then
    echo "✅ Inicialización de base de datos completada exitosamente"
else
    echo "❌ ERROR: La inicialización de base de datos falló"
    echo "   Revise los logs arriba para más detalles"
    exit 1
fi

echo ""
echo "🚀 Iniciando aplicación y worker SQS..."
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Iniciar el worker SQS en background
echo "🔄 Iniciando SQS Consumer Worker..."
python3 -m app.worker.sqs_consumer &
WORKER_PID=$!
echo "✅ Worker SQS iniciado (PID: $WORKER_PID)"

# Función para cleanup al salir
cleanup() {
    echo "🛑 Deteniendo worker SQS..."
    kill $WORKER_PID 2>/dev/null
    wait $WORKER_PID 2>/dev/null
}
trap cleanup EXIT INT TERM

# Ejecutar el comando original (uvicorn)
exec "$@"

