#!/bin/bash
set -e

echo "🚀 Starting Auth Service..."

# Intentar conectar a DB pero con timeout
if [ ! -z "$DATABASE_URL" ]; then
    echo "⏳ Waiting for database..."
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    echo "🔌 Connecting to: ${DB_HOST}:${DB_PORT}"
    
    # Esperar máximo 30 segundos
    TIMEOUT=30
    ELAPSED=0
    while ! pg_isready -h ${DB_HOST} -p ${DB_PORT} -U orders_user 2>/dev/null; do
        sleep 1
        ELAPSED=$((ELAPSED + 1))
        if [ $ELAPSED -ge $TIMEOUT ]; then
            echo "⚠️  Database not ready after ${TIMEOUT}s, starting service anyway..."
            echo "⚠️  Database operations will fail until connection is established"
            break
        fi
    done
    
    if [ $ELAPSED -lt $TIMEOUT ]; then
        echo "✅ Database is ready!"
        echo "📋 Creating database tables..."
        python run_once_create_tables.py || echo "⚠️  Could not create tables"
        echo "🌱 Seeding initial data..."
        python seed_data.py || echo "ℹ️  Seed data already exists or failed"
    fi
fi

echo "🎯 Starting Auth Service on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}