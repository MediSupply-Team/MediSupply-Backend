#!/usr/bin/env python3
"""
Script para poblar la base de datos del catálogo con datos iniciales
"""
import asyncio
import os
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text


async def populate_database():
    """Poblar la base de datos con datos de ejemplo del archivo SQL"""
    print("🔄 Poblando base de datos de catálogo...")
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL no está configurado")
        sys.exit(1)
    
    engine = create_async_engine(database_url, echo=False)
    
    try:
        # Verificar si ya hay datos
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM producto"))
            count = result.scalar()
            
            if count > 0:
                print(f"ℹ️  Base de datos ya tiene {count} productos. Saltando población de datos.")
                return
        
        print("📄 Cargando datos desde 001_init.sql...")
        
        # Leer el archivo SQL
        sql_file = Path(__file__).parent.parent / 'data' / '001_init.sql'
        
        if not sql_file.exists():
            print(f"⚠️  Archivo SQL no encontrado: {sql_file}")
            print("   Continuando sin poblar datos...")
            return
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Dividir en statements individuales y ejecutar cada uno en su propia transacción
        statements = [s.strip() for s in sql_content.split(';') if s.strip()]
        
        for i, statement in enumerate(statements, 1):
            # Saltar comentarios y líneas vacías
            if statement.startswith('--') or not statement:
                continue
            
            try:
                # Cada statement en su propia transacción
                async with engine.begin() as conn:
                    await conn.execute(text(statement))
            except Exception as e:
                # Ignorar errores de "ya existe"
                if 'already exists' in str(e).lower() or 'duplicate key' in str(e).lower():
                    continue
                # Mostrar otros errores pero continuar
                print(f"⚠️  Advertencia en statement {i}: {str(e)[:100]}...")
        
        # Verificar resultado
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM producto"))
            prod_count = result.scalar()
            
            result = await conn.execute(text("SELECT COUNT(*) FROM inventario"))
            inv_count = result.scalar()
        
        print("🎉 Base de datos poblada exitosamente")
        print(f"   📦 Productos: {prod_count}")
        print(f"   🏭 Registros de inventario: {inv_count}")
            
    except Exception as e:
        print(f"❌ Error al poblar base de datos: {e}")
        # No fallar el inicio de la aplicación por esto
        print("⚠️  Continuando sin datos iniciales...")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(populate_database())
    except Exception as e:
        print(f"❌ Error durante la población: {e}")
        # No fallar con exit code != 0 para no impedir el inicio del contenedor
        sys.exit(0)

