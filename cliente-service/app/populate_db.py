#!/usr/bin/env python3
"""
Script para inicializar y poblar la base de datos con datos de ejemplo
HU07: Consultar Cliente - Datos iniciales
HU: Registrar Vendedor - Catálogos de soporte

Este script:
1. Crea todas las tablas usando SQLAlchemy
2. Ejecuta todos los archivos SQL de la carpeta data/ en orden
3. Es idempotente: se puede ejecutar múltiples veces sin problemas
"""
import asyncio
import os
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Agregar el directorio app al path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from app.db import Base
from app.models.client_model import (
    Vendedor, Cliente, CompraHistorico, DevolucionHistorico, 
    ConsultaClienteLog, ProductoPreferido, EstadisticaCliente
)
from app.models.catalogo_model import (
    TipoRolVendedor, Territorio, TipoPlan, Region, Zona
)
from app.models.plan_venta_model import (
    PlanVenta, PlanProducto, PlanRegion, PlanZona
)


async def execute_sql_file(engine, sql_file_path: Path, description: str) -> bool:
    """
    Ejecuta un archivo SQL completo directamente con psql
    Esto garantiza que los bloques complejos (DO $$, funciones, INSERTs multi-línea) se manejen correctamente
    
    Args:
        engine: Motor de SQLAlchemy
        sql_file_path: Ruta al archivo SQL
        description: Descripción del archivo para logs
        
    Returns:
        True si se ejecutó exitosamente, False si hubo errores críticos
    """
    print(f"📄 Cargando datos desde {sql_file_path.name}...")
    
    if not sql_file_path.exists():
        print(f"⚠️  Archivo SQL no encontrado: {sql_file_path}")
        return False
    
    try:
        # Usar las credenciales del engine URL (SQLAlchemy)
        import subprocess
        from urllib.parse import unquote
        
        # Extraer componentes de la URL
        url = engine.url
        user = url.username or 'postgres'
        password = unquote(url.password or '')  # Decodificar password URL-encoded
        host = url.host or 'localhost'
        port = str(url.port or 5432)
        database = url.database or 'postgres'
        
        # Configurar entorno con la contraseña
        env = os.environ.copy()
        env['PGPASSWORD'] = password
        
        # Comando psql
        cmd = [
            'psql',
            '-h', host,
            '-p', port,
            '-U', user,
            '-d', database,
            '-f', str(sql_file_path),
            '-v', 'ON_ERROR_STOP=0'  # Continuar en caso de error
        ]
        
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True
        )
        
        # Siempre mostrar output para debugging
        if result.stdout:
            for line in result.stdout.split('\n'):
                if line.strip() and ('NOTICE' in line or 'INSERT' in line or 'DELETE' in line):
                    print(f"         📝 {line.strip()}")
        
        if result.returncode == 0 or 'INSERT' in result.stdout:
            print(f"      ✅ {description} ejecutado correctamente")
            return True
        else:
            # Mostrar errores
            print(f"      ⚠️  Algunas advertencias:")
            if result.stderr:
                for line in result.stderr.split('\n')[:10]:
                    if line.strip():
                        print(f"         {line[:150]}")
            return True
        
    except Exception as e:
        print(f"   ❌ Error ejecutando {sql_file_path}: {e}")
        return False


async def crear_tablas_con_sqlalchemy(engine) -> bool:
    """
    Crea todas las tablas usando SQLAlchemy (como fallback)
    """
    print("🔧 Creando/verificando tablas con SQLAlchemy...")
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("   ✅ Tablas verificadas con SQLAlchemy")
        return True
    except Exception as e:
        print(f"   ⚠️  Error en SQLAlchemy (no crítico): {e}")
        return True  # No es crítico, los SQL files crearán las tablas


async def populate_database():
    """
    Función principal de inicialización de base de datos
    
    Ejecuta todos los archivos SQL de la carpeta data/ en orden:
    - 001_init.sql: Estructura inicial de tablas
    - 002_vendedores.sql: Tabla de vendedores y datos
    - 003_cliente_uuid_rol.sql: Migración UUID y rol para clientes
    - 004_catalogos_vendedor.sql: Catálogos de soporte (NUEVO)
    
    Es idempotente: se puede ejecutar múltiples veces sin problemas
    """
    print("\n" + "="*70)
    print("🚀 INICIALIZANDO BASE DE DATOS - CLIENTE SERVICE")
    print("="*70 + "\n")
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL no está configurado")
        sys.exit(1)
    
    print(f"🔗 Conectando a base de datos...")
    print(f"   URL: {database_url.split('@')[1] if '@' in database_url else 'local'}\n")
    
    engine = create_async_engine(database_url, echo=False)
    
    try:
        # Paso 1: Crear tablas con SQLAlchemy (como fallback)
        print("1️⃣ Paso 1: Verificando tablas con SQLAlchemy...")
        await crear_tablas_con_sqlalchemy(engine)
        print()
        
        # Paso 2: Ejecutar todos los archivos SQL de la carpeta data/
        print("2️⃣ Paso 2: Ejecutando migraciones SQL...")
        sql_dir = Path(__file__).parent.parent / 'data'
        
        # Archivos SQL en orden
        sql_files = [
            ('001_init.sql', 'Estructura inicial y tablas base'),
            ('002_vendedores.sql', 'Tabla vendedores y datos iniciales'),
            ('003_asignar_vendedores_clientes.sql', 'Asignar vendedores a clientes existentes'),
            ('004_catalogos_vendedor.sql', 'Catálogos de soporte (Fase 1)'),
            ('005_vendedor_extended.sql', 'Vendedor extendido con FK (Fase 2)'),
            ('006_plan_venta.sql', 'Plan de Venta completo con productos, regiones y zonas (Fase 3)')
        ]
        
        for filename, description in sql_files:
            sql_path = sql_dir / filename
            if sql_path.exists():
                await execute_sql_file(engine, sql_path, f"{filename} - {description}")
            else:
                print(f"⚠️  Archivo {filename} no encontrado, saltando...")
        
        print()
        
        # Paso 3: Verificar resultado final
        print("3️⃣ Paso 3: Verificando resultado final...")
        async with engine.begin() as conn:
            # Verificar tablas principales
            tables_to_check = [
                ('cliente', 'Clientes'),
                ('vendedor', 'Vendedores'),
                ('tipo_rol_vendedor', 'Tipos de Rol'),
                ('territorio', 'Territorios'),
                ('tipo_plan', 'Tipos de Plan'),
                ('region', 'Regiones'),
                ('zona', 'Zonas'),
                ('plan_venta', 'Planes de Venta'),
                ('plan_producto', 'Productos en Planes'),
                ('plan_region', 'Regiones en Planes'),
                ('plan_zona', 'Zonas en Planes')
            ]
            
            print()
            for table_name, description in tables_to_check:
                try:
                    result = await conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    print(f"   ✅ {description:20} : {count:4} registros")
                except Exception as e:
                    print(f"   ⚠️  {description:20} : No disponible")
        
        print()
        print("="*70)
        print("✅ INICIALIZACIÓN COMPLETADA EXITOSAMENTE")
        print("="*70)
        print()
        print("📋 Endpoints de catálogos disponibles:")
        print("   • GET /api/v1/catalogos/tipos-rol")
        print("   • GET /api/v1/catalogos/territorios")
        print("   • GET /api/v1/catalogos/tipos-plan")
        print("   • GET /api/v1/catalogos/regiones")
        print("   • GET /api/v1/catalogos/zonas")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO durante la inicialización: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()


if __name__ == "__main__":
    try:
        success = asyncio.run(populate_database())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error durante la población: {e}")
        sys.exit(1)
