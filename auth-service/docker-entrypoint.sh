#!/bin/bash
set -e

echo "Waiting for database..."
while ! pg_isready -h db -p 5432 -U user; do
  sleep 1
done
echo "Database is ready!"

echo "Creating database tables..."
python run_once_create_tables.py

echo "Seeding initial data..."
python seed_data.py || echo "Seed data already exists"

echo "Starting Auth Service..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload