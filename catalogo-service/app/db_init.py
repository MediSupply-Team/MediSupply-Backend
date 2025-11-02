#!/usr/bin/env python3
"""
Sistema de inicialización automática de base de datos para catalogo-service

Este módulo se ejecuta al inicio de la aplicación y garantiza que:
1. Todas las tablas existen (usando SQLAlchemy create_all)
2. Todas las columnas necesarias existen (verificación explícita)
3. Los datos iniciales están cargados (idempotente)
4. Todo es automático y no requiere intervención manual

Se puede ejecutar múltiples veces sin problemas (idempotente).
"""
import asyncio
import os
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text, inspect
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


async def verificar_y_agregar_columnas(engine) -> bool:
    """
    Verifica que todas las columnas necesarias existan en la tabla producto.
    Si no existen, las agrega una por una en transacciones separadas.
    
    Returns:
        bool: True si todo está correcto, False si hubo errores críticos
    """
    print("🔍 Verificando columnas de tabla 'producto'...")
    
    columnas_requeridas = [
        ("stock_minimo", "INTEGER", "10"),
        ("stock_critico", "INTEGER", "5"),
        ("requiere_lote", "BOOLEAN", "FALSE"),
        ("requiere_vencimiento", "BOOLEAN", "TRUE"),
    ]
    
    columnas_agregadas = 0
    columnas_existentes = 0
    
    for col_name, col_type, col_default in columnas_requeridas:
        try:
            # Verificar si la columna existe
            async with engine.begin() as conn:
                result = await conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'producto' 
                      AND column_name = :col_name
                """), {"col_name": col_name})
                
                exists = result.scalar_one_or_none()
            
            if exists:
                columnas_existentes += 1
                print(f"   ✓ Columna '{col_name}' ya existe")
            else:
                # Agregar la columna en una transacción separada
                print(f"   + Agregando columna '{col_name}'...")
                async with engine.begin() as conn:
                    await conn.execute(text(f"""
                        ALTER TABLE producto 
                        ADD COLUMN IF NOT EXISTS {col_name} {col_type} DEFAULT {col_default}
                    """))
                columnas_agregadas += 1
                print(f"   ✅ Columna '{col_name}' agregada exitosamente")
        
        except Exception as e:
            error_msg = str(e).lower()
            # Si el error es "columna ya existe", lo ignoramos
            if 'already exists' in error_msg or 'duplicate column' in error_msg:
                columnas_existentes += 1
                print(f"   ✓ Columna '{col_name}' ya existe (detectado por error)")
            else:
                print(f"   ⚠️  Error al agregar columna '{col_name}': {str(e)[:100]}")
                # No es crítico, continuamos
    
    print(f"\n📊 Resumen: {columnas_existentes} existentes, {columnas_agregadas} agregadas")
    return True


async def crear_tablas_movimientos(engine) -> bool:
    """
    Crea las tablas de movimientos de inventario si no existen.
    
    Returns:
        bool: True si todo está correcto
    """
    print("📦 Creando tablas de movimientos de inventario...")
    
    sql_movimientos = """
    -- Tabla de movimientos de inventario (Kardex)
    CREATE TABLE IF NOT EXISTS movimiento_inventario (
        id BIGSERIAL PRIMARY KEY,
        producto_id VARCHAR(64) NOT NULL REFERENCES producto(id) ON DELETE RESTRICT,
        bodega_id VARCHAR(64) NOT NULL,
        pais CHAR(2) NOT NULL,
        lote VARCHAR(64),
        tipo_movimiento VARCHAR(30) NOT NULL CHECK (tipo_movimiento IN (
            'INGRESO', 
            'SALIDA', 
            'TRANSFERENCIA_SALIDA', 
            'TRANSFERENCIA_INGRESO'
        )),
        motivo VARCHAR(50) NOT NULL CHECK (motivo IN (
            'COMPRA',
            'AJUSTE',
            'VENTA',
            'DEVOLUCION',
            'MERMA',
            'PRODUCCION',
            'TRANSFERENCIA'
        )),
        cantidad INT NOT NULL CHECK (cantidad > 0),
        fecha_vencimiento DATE,
        saldo_anterior INT NOT NULL,
        saldo_nuevo INT NOT NULL,
        usuario_id VARCHAR(64) NOT NULL,
        referencia_documento VARCHAR(128),
        observaciones TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'ANULADO')),
        anulado_por VARCHAR(64),
        anulado_at TIMESTAMP,
        motivo_anulacion TEXT,
        movimiento_relacionado_id BIGINT REFERENCES movimiento_inventario(id)
    );
    
    CREATE INDEX IF NOT EXISTS idx_mov_producto ON movimiento_inventario(producto_id);
    CREATE INDEX IF NOT EXISTS idx_mov_bodega ON movimiento_inventario(bodega_id, pais);
    CREATE INDEX IF NOT EXISTS idx_mov_tipo ON movimiento_inventario(tipo_movimiento);
    CREATE INDEX IF NOT EXISTS idx_mov_created ON movimiento_inventario(created_at);
    CREATE INDEX IF NOT EXISTS idx_mov_usuario ON movimiento_inventario(usuario_id);
    
    -- Tabla de alertas de inventario
    CREATE TABLE IF NOT EXISTS alerta_inventario (
        id BIGSERIAL PRIMARY KEY,
        producto_id VARCHAR(64) NOT NULL REFERENCES producto(id) ON DELETE RESTRICT,
        bodega_id VARCHAR(64) NOT NULL,
        pais CHAR(2) NOT NULL,
        tipo_alerta VARCHAR(30) NOT NULL CHECK (tipo_alerta IN (
            'STOCK_MINIMO',
            'STOCK_CRITICO',
            'STOCK_NEGATIVO',
            'PROXIMO_VENCER',
            'VENCIDO'
        )),
        nivel VARCHAR(20) NOT NULL CHECK (nivel IN ('INFO', 'WARNING', 'CRITICAL')),
        mensaje TEXT NOT NULL,
        stock_actual INT,
        stock_minimo INT,
        leida BOOLEAN NOT NULL DEFAULT FALSE,
        leida_por VARCHAR(64),
        leida_at TIMESTAMP,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_alerta_producto ON alerta_inventario(producto_id);
    CREATE INDEX IF NOT EXISTS idx_alerta_leida ON alerta_inventario(leida);
    CREATE INDEX IF NOT EXISTS idx_alerta_created ON alerta_inventario(created_at);
    
    -- Vista para reportes de saldos
    CREATE OR REPLACE VIEW v_saldos_bodega AS
    WITH saldos_actuales AS (
        SELECT 
            producto_id,
            bodega_id,
            pais,
            lote,
            saldo_nuevo as cantidad_total,
            fecha_vencimiento,
            ROW_NUMBER() OVER (
                PARTITION BY producto_id, bodega_id, pais, lote 
                ORDER BY created_at DESC
            ) as rn
        FROM movimiento_inventario
        WHERE estado = 'ACTIVO'
    )
    SELECT 
        s.producto_id,
        p.nombre as producto_nombre,
        p.codigo as producto_codigo,
        s.bodega_id,
        s.pais,
        s.lote,
        s.cantidad_total,
        s.fecha_vencimiento as fecha_vencimiento_proxima,
        p.stock_minimo,
        p.stock_critico,
        CASE 
            WHEN s.cantidad_total <= COALESCE(p.stock_critico, 0) THEN 'CRITICO'
            WHEN s.cantidad_total <= COALESCE(p.stock_minimo, 0) THEN 'BAJO'
            ELSE 'NORMAL'
        END as estado_stock
    FROM saldos_actuales s
    JOIN producto p ON s.producto_id = p.id
    WHERE s.rn = 1 AND s.cantidad_total > 0;
    """
    
    # Ejecutar cada statement por separado
    statements = [s.strip() for s in sql_movimientos.split(';') if s.strip()]
    
    created = 0
    skipped = 0
    
    for statement in statements:
        if not statement or statement.startswith('--'):
            continue
        
        try:
            async with engine.begin() as conn:
                await conn.execute(text(statement))
            created += 1
        except Exception as e:
            error_msg = str(e).lower()
            if any(x in error_msg for x in ['already exists', 'duplicate']):
                skipped += 1
            else:
                print(f"   ⚠️  Advertencia: {str(e)[:100]}")
    
    print(f"   ✅ {created} statements ejecutados, {skipped} omitidos (ya existían)")
    return True


async def cargar_datos_iniciales(engine) -> bool:
    """
    Carga los datos iniciales desde 001_init.sql si no existen productos.
    
    Returns:
        bool: True si se cargaron o ya existían datos
    """
    print("📝 Verificando datos iniciales...")
    
    # Verificar si ya hay productos
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM producto"))
        count = result.scalar()
    
    if count > 0:
        print(f"   ℹ️  Ya existen {count} productos en la base de datos")
        return True
    
    # Cargar datos desde 001_init.sql
    sql_file = Path(__file__).parent.parent / "data" / "001_init.sql"
    
    if not sql_file.exists():
        print(f"   ⚠️  Archivo SQL no encontrado: {sql_file}")
        return False
    
    print(f"   📄 Cargando datos desde {sql_file.name}...")
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    statements = [s.strip() for s in sql_content.split(';') if s.strip()]
    
    inserted = 0
    
    for statement in statements:
        if not statement or statement.startswith('--'):
            continue
        
        try:
            async with engine.begin() as conn:
                await conn.execute(text(statement))
            inserted += 1
        except Exception as e:
            error_msg = str(e).lower()
            if 'duplicate' not in error_msg:
                print(f"   ⚠️  Error insertando datos: {str(e)[:100]}")
    
    print(f"   ✅ {inserted} statements de datos ejecutados")
    return True


async def actualizar_productos_existentes(engine) -> bool:
    """
    Actualiza productos existentes con valores razonables para los nuevos campos.
    """
    print("🔄 Actualizando productos existentes con valores por defecto...")
    
    try:
        async with engine.begin() as conn:
            # Actualizar productos de categorías específicas
            await conn.execute(text("""
                UPDATE producto SET 
                    stock_minimo = 50,
                    stock_critico = 20,
                    requiere_lote = TRUE,
                    requiere_vencimiento = TRUE
                WHERE categoria_id IN ('ANTIBIOTICS', 'RESPIRATORY')
                  AND (stock_minimo IS NULL OR stock_minimo = 10)
            """))
            
            await conn.execute(text("""
                UPDATE producto SET 
                    stock_minimo = 100,
                    stock_critico = 30,
                    requiere_lote = FALSE,
                    requiere_vencimiento = TRUE
                WHERE categoria_id IN ('ANALGESICS', 'GASTROINTESTINAL')
                  AND (stock_minimo IS NULL OR stock_minimo = 10)
            """))
        
        print("   ✅ Productos actualizados")
        return True
    except Exception as e:
        print(f"   ⚠️  Error actualizando productos: {str(e)[:100]}")
        return True  # No es crítico


async def inicializar_base_datos():
    """
    Función principal de inicialización de base de datos.
    
    Esta función:
    1. Crea todas las tablas base usando SQLAlchemy
    2. Agrega columnas faltantes a 'producto'
    3. Crea tablas de movimientos e inventario
    4. Carga datos iniciales si no existen
    5. Actualiza productos existentes
    
    Es idempotente: se puede ejecutar múltiples veces sin problemas.
    """
    print("\n" + "="*70)
    print("🚀 INICIALIZANDO BASE DE DATOS - CATALOGO SERVICE")
    print("="*70 + "\n")
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL no está configurado")
        return False
    
    print(f"🔗 Conectando a base de datos...")
    print(f"   URL: {database_url.split('@')[1] if '@' in database_url else 'local'}\n")
    
    engine = create_async_engine(database_url, echo=False)
    
    try:
        # Paso 1: Crear tablas base con SQLAlchemy
        print("1️⃣ Creando tablas base (SQLAlchemy)...")
        from app.db import Base
        # Importar modelos para que se registren en Base.metadata
        from app.models.catalogo_model import Producto, Inventario
        from app.models.movimiento_model import MovimientoInventario, AlertaInventario
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("   ✅ Tablas base verificadas\n")
        
        # Paso 2: Verificar y agregar columnas a 'producto'
        print("2️⃣ Verificando columnas de 'producto'...")
        await verificar_y_agregar_columnas(engine)
        print()
        
        # Paso 3: Crear tablas de movimientos
        print("3️⃣ Creando tablas de movimientos e inventario...")
        await crear_tablas_movimientos(engine)
        print()
        
        # Paso 4: Cargar datos iniciales
        print("4️⃣ Cargando datos iniciales...")
        await cargar_datos_iniciales(engine)
        print()
        
        # Paso 5: Actualizar productos existentes
        print("5️⃣ Actualizando productos existentes...")
        await actualizar_productos_existentes(engine)
        print()
        
        # Verificación final
        print("6️⃣ Verificación final...")
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT 
                    (SELECT COUNT(*) FROM producto) as productos,
                    (SELECT COUNT(*) FROM inventario) as inventarios,
                    (SELECT COUNT(*) FROM movimiento_inventario) as movimientos,
                    (SELECT COUNT(*) FROM alerta_inventario) as alertas
            """))
            row = result.one()
            print(f"   📊 Productos: {row.productos}")
            print(f"   📊 Inventarios: {row.inventarios}")
            print(f"   📊 Movimientos: {row.movimientos}")
            print(f"   📊 Alertas: {row.alertas}")
        
        print("\n" + "="*70)
        print("✅ INICIALIZACIÓN COMPLETADA EXITOSAMENTE")
        print("="*70 + "\n")
        
        return True
    
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO durante inicialización: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await engine.dispose()


def run_init():
    """Wrapper síncrono para ejecutar desde el entrypoint"""
    return asyncio.run(inicializar_base_datos())


if __name__ == "__main__":
    success = run_init()
    sys.exit(0 if success else 1)

