import os
import psycopg
from urllib.parse import urlparse

database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("⚠️ DATABASE_URL no configurada")
    exit(0)

parsed = urlparse(database_url)
host = parsed.hostname or "localhost"
port = parsed.port or 5432
user = parsed.username or "postgres"
password = parsed.password or ""
target_db = parsed.path.lstrip('/') if parsed.path else "rutas"

print(f"🔧 Conectando a {host}:{port}")
print(f"📦 Target DB: {target_db}")

admin_dsn = f"host={host} port={port} dbname=postgres user={user} password={password}"

try:
    with psycopg.connect(admin_dsn) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target_db,))
            exists = cur.fetchone() is not None
            
            if not exists:
                print(f"📦 Creando '{target_db}'...")
                cur.execute(f'CREATE DATABASE "{target_db}"')
                print(f"✅ Base de datos '{target_db}' creada")
            else:
                print(f"ℹ️ Base de datos '{target_db}' ya existe")
    exit(0)
except Exception as e:
    print(f"⚠️ Error: {e}")
    exit(0)