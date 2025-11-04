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


async def execute_sql_file(engine, sql_file_path: Path, description: str):
    """Ejecuta un archivo SQL completo"""
    print(f"📄 Ejecutando {description}...")
    
    if not sql_file_path.exists():
        print(f"⚠️  Archivo SQL no encontrado: {sql_file_path}")
        return False
    
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Dividir en statements individuales
    statements = [s.strip() for s in sql_content.split(';') if s.strip()]
    
    executed = 0
    skipped = 0
    
    for i, statement in enumerate(statements, 1):
        # Saltar comentarios y líneas vacías
        if statement.startswith('--') or not statement:
            continue
        
        try:
            async with engine.begin() as conn:
                await conn.execute(text(statement))
            executed += 1
        except Exception as e:
            error_msg = str(e).lower()
            # Ignorar errores de "ya existe"
            if any(x in error_msg for x in ['already exists', 'duplicate', 'no column changes']):
                skipped += 1
                continue
            # Mostrar otros errores pero continuar
            print(f"⚠️  Advertencia en statement {i}: {str(e)[:100]}...")
    
    print(f"   ✅ {description}: {executed} statements ejecutados, {skipped} omitidos")
    return True


async def populate_database():
    """Poblar la base de datos con datos de ejemplo e inicializar esquema de movimientos"""
    print("🚀 Iniciando población de base de datos...")
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL no está configurado")
        sys.exit(1)
    
    engine = create_async_engine(database_url, echo=False)
    
    try:
        # 1. Ejecutar script de estructura inicial y datos (001_init.sql)
        sql_dir = Path(__file__).parent.parent / 'data'
        init_sql = sql_dir / '001_init.sql'
        
        # Verificar si ya hay datos
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM producto"))
            count = result.scalar()
            
            if count > 0:
                print(f"ℹ️  Base de datos ya tiene {count} productos.")
            else:
                print("📦 Base de datos vacía, ejecutando inicialización...")
                await execute_sql_file(engine, init_sql, "001_init.sql (estructura y datos)")
        
        # 2. Ejecutar script de movimientos de inventario (002_movimientos.sql)
        movimientos_sql = sql_dir / '002_movimientos.sql'
        
        # Verificar si las tablas de movimientos ya existen
        async with engine.begin() as conn:
            result = await conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_name = 'movimiento_inventario'"
            ))
            table_exists = result.scalar() > 0
        
        if table_exists:
            print("ℹ️  Tablas de movimientos ya existen, ejecutando migraciones incrementales...")
        else:
            print("📊 Creando tablas de movimientos de inventario...")
        
        await execute_sql_file(engine, movimientos_sql, "002_movimientos.sql (kardex y alertas)")
        
        # 3. Verificar resultado final
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM producto"))
            prod_count = result.scalar()
            
            result = await conn.execute(text("SELECT COUNT(*) FROM inventario"))
            inv_count = result.scalar()
            
            result = await conn.execute(text("SELECT COUNT(*) FROM movimiento_inventario"))
            mov_count = result.scalar()
            
            result = await conn.execute(text("SELECT COUNT(*) FROM alerta_inventario"))
            alert_count = result.scalar()
        
        print("")
        print("✅ Población completada exitosamente")
        print(f"   📦 Productos: {prod_count}")
        print(f"   🏭 Inventario: {inv_count} registros")
        print(f"   📋 Movimientos: {mov_count}")
        print(f"   🔔 Alertas: {alert_count}")
        print("")
            
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

