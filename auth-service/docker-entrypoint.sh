#!/bin/bash
set -e

echo "Waiting for database..."

# Extraer host y port del DATABASE_URL
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

echo "Connecting to: ${DB_HOST}:${DB_PORT}"

while ! pg_isready -h ${DB_HOST} -p ${DB_PORT} -U orders_user; do
  sleep 1
done

echo "Database is ready!"

echo "Creating database tables..."
python run_once_create_tables.py

echo "Seeding initial data..."
python seed_data.py || echo "Seed data already exists"

echo "Starting Auth Service..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --reload