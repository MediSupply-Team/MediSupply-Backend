"""
Script de migración para agregar nuevas columnas a la tabla visita
"""
from sqlalchemy import create_engine, text
from database import engine as db_engine
import os

def migrate_visita_table():
    """
    Agrega las nuevas columnas a la tabla visita si no existen
    """
    print("🔄 Ejecutando migración de base de datos...")
    
    # Usar el engine de la aplicación
    engine = db_engine
    
    with engine.connect() as conn:
        # Verificar si las columnas ya existen
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'visita' 
            AND column_name IN ('cliente_id', 'ciudad', 'estado', 'observaciones')
        """)
        
        existing_columns = conn.execute(check_query).fetchall()
        existing_column_names = [col[0] for col in existing_columns]
        
        print(f"📊 Columnas existentes: {existing_column_names}")
        
        # Agregar columnas faltantes
        migrations = []
        
        if 'cliente_id' not in existing_column_names:
            migrations.append("ALTER TABLE visita ADD COLUMN cliente_id VARCHAR")
            print("  ➕ Agregando columna: cliente_id")
        
        if 'ciudad' not in existing_column_names:
            migrations.append("ALTER TABLE visita ADD COLUMN ciudad VARCHAR")
            print("  ➕ Agregando columna: ciudad")
        
        if 'estado' not in existing_column_names:
            migrations.append("ALTER TABLE visita ADD COLUMN estado VARCHAR DEFAULT 'pendiente'")
            print("  ➕ Agregando columna: estado")
        
        if 'observaciones' not in existing_column_names:
            migrations.append("ALTER TABLE visita ADD COLUMN observaciones TEXT")
            print("  ➕ Agregando columna: observaciones")
        
        # Ejecutar migraciones
        if migrations:
            for migration in migrations:
                conn.execute(text(migration))
            conn.commit()
            print(f"✅ Migración completada: {len(migrations)} columnas agregadas")
        else:
            print("✅ Base de datos ya está actualizada, no se requieren migraciones")
    
    print("🎉 Migración finalizada")


if __name__ == "__main__":
    migrate_visita_table()
