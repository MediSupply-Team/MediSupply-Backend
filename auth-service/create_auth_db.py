# auth-service/create_auth_db.py
import os
import psycopg

host = os.getenv("PGHOST", "localhost")
user = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD", "postgres")
target_db = os.getenv("TARGET_DB", "auth_db")

admin_dsn = f"host={host} dbname=postgres user={user} password={password}"

try:
    with psycopg.connect(admin_dsn) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target_db,))
            exists = cur.fetchone() is not None
            
            if not exists:
                cur.execute(f'CREATE DATABASE "{target_db}"')
                print(f"✅ Database {target_db} creada exitosamente.")
            else:
                print(f"ℹ️  Database {target_db} ya existe.")
                
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)