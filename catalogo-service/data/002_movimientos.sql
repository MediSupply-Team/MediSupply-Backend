-- ===================================================================
-- FASE 1: MIGRACIONES PARA GESTIÓN DE MOVIMIENTOS DE INVENTARIO
-- Script: 002_movimientos.sql
-- Descripción: Agrega tablas para kardex, alertas y campos a producto
-- ===================================================================

-- 1. Agregar campos a la tabla producto para gestión de stock (uno por uno para compatibilidad)
ALTER TABLE producto ADD COLUMN IF NOT EXISTS stock_minimo INT DEFAULT 10;
ALTER TABLE producto ADD COLUMN IF NOT EXISTS stock_critico INT DEFAULT 5;
ALTER TABLE producto ADD COLUMN IF NOT EXISTS requiere_lote BOOLEAN DEFAULT FALSE;
ALTER TABLE producto ADD COLUMN IF NOT EXISTS requiere_vencimiento BOOLEAN DEFAULT TRUE;

-- Actualizar productos existentes con valores razonables
UPDATE producto SET 
    stock_minimo = 50,
    stock_critico = 20,
    requiere_lote = TRUE,
    requiere_vencimiento = TRUE
WHERE categoria_id IN ('ANTIBIOTICS', 'RESPIRATORY');

UPDATE producto SET 
    stock_minimo = 100,
    stock_critico = 30,
    requiere_lote = FALSE,
    requiere_vencimiento = TRUE
WHERE categoria_id IN ('ANALGESICS', 'GASTROINTESTINAL');


-- 2. Tabla de movimientos de inventario (Kardex)
CREATE TABLE IF NOT EXISTS movimiento_inventario (
    id BIGSERIAL PRIMARY KEY,
    
    -- Identificación del producto y ubicación
    producto_id VARCHAR(64) NOT NULL REFERENCES producto(id) ON DELETE RESTRICT,
    bodega_id VARCHAR(64) NOT NULL,
    pais CHAR(2) NOT NULL,
    lote VARCHAR(64),
    
    -- Tipo y motivo del movimiento
    tipo_movimiento VARCHAR(20) NOT NULL CHECK (tipo_movimiento IN (
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
        'TRANSFERENCIA',
        'PRODUCCION',
        'INVENTARIO_INICIAL'
    )),
    
    -- Datos de la transacción
    cantidad INT NOT NULL CHECK (cantidad > 0),
    fecha_vencimiento DATE,
    
    -- Snapshot de saldos
    saldo_anterior INT NOT NULL,
    saldo_nuevo INT NOT NULL,
    
    -- Auditoría y trazabilidad
    usuario_id VARCHAR(64) NOT NULL,
    referencia_documento VARCHAR(128),
    observaciones TEXT,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Estado (para anulación)
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'ANULADO')),
    anulado_por VARCHAR(64),
    anulado_at TIMESTAMP,
    motivo_anulacion TEXT,
    
    -- Relación para transferencias
    movimiento_relacionado_id BIGINT REFERENCES movimiento_inventario(id)
);

-- Índices para consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_mov_producto ON movimiento_inventario(producto_id);
CREATE INDEX IF NOT EXISTS idx_mov_bodega ON movimiento_inventario(bodega_id);
CREATE INDEX IF NOT EXISTS idx_mov_pais ON movimiento_inventario(pais);
CREATE INDEX IF NOT EXISTS idx_mov_fecha ON movimiento_inventario(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_mov_tipo ON movimiento_inventario(tipo_movimiento);
CREATE INDEX IF NOT EXISTS idx_mov_usuario ON movimiento_inventario(usuario_id);
CREATE INDEX IF NOT EXISTS idx_mov_estado ON movimiento_inventario(estado);
CREATE INDEX IF NOT EXISTS idx_mov_ref_doc ON movimiento_inventario(referencia_documento) WHERE referencia_documento IS NOT NULL;

-- Índice compuesto para consultas de kardex
CREATE INDEX IF NOT EXISTS idx_mov_kardex ON movimiento_inventario(producto_id, bodega_id, created_at DESC);


-- 3. Tabla de alertas de inventario
CREATE TABLE IF NOT EXISTS alerta_inventario (
    id BIGSERIAL PRIMARY KEY,
    
    -- Identificación
    producto_id VARCHAR(64) NOT NULL REFERENCES producto(id) ON DELETE CASCADE,
    bodega_id VARCHAR(64) NOT NULL,
    pais CHAR(2) NOT NULL,
    
    -- Tipo y nivel de alerta
    tipo_alerta VARCHAR(30) NOT NULL CHECK (tipo_alerta IN (
        'STOCK_MINIMO',
        'STOCK_CRITICO',
        'PROXIMO_VENCER',
        'VENCIDO',
        'STOCK_NEGATIVO'
    )),
    nivel VARCHAR(20) NOT NULL CHECK (nivel IN ('INFO', 'WARNING', 'CRITICAL')),
    
    -- Información de la alerta
    mensaje TEXT NOT NULL,
    stock_actual INT,
    stock_minimo INT,
    
    -- Control de lectura
    leida BOOLEAN NOT NULL DEFAULT FALSE,
    leida_por VARCHAR(64),
    leida_at TIMESTAMP,
    
    -- Timestamp
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Índices para alertas
CREATE INDEX IF NOT EXISTS idx_alerta_producto ON alerta_inventario(producto_id);
CREATE INDEX IF NOT EXISTS idx_alerta_bodega ON alerta_inventario(bodega_id);
CREATE INDEX IF NOT EXISTS idx_alerta_leida ON alerta_inventario(leida) WHERE leida = FALSE;
CREATE INDEX IF NOT EXISTS idx_alerta_nivel ON alerta_inventario(nivel);
CREATE INDEX IF NOT EXISTS idx_alerta_fecha ON alerta_inventario(created_at DESC);

-- Índice compuesto para consultas de alertas no leídas
CREATE INDEX IF NOT EXISTS idx_alerta_activas ON alerta_inventario(leida, nivel, created_at DESC) WHERE leida = FALSE;


-- 4. Vista para consultar saldos actuales por bodega
CREATE OR REPLACE VIEW v_saldos_bodega AS
SELECT 
    i.producto_id,
    p.nombre AS producto_nombre,
    p.codigo AS producto_codigo,
    i.bodega_id,
    i.pais,
    i.lote,
    SUM(i.cantidad) AS cantidad_total,
    MIN(i.vence) AS fecha_vencimiento_proxima,
    p.stock_minimo,
    p.stock_critico,
    CASE 
        WHEN SUM(i.cantidad) <= p.stock_critico THEN 'CRITICO'
        WHEN SUM(i.cantidad) <= p.stock_minimo THEN 'BAJO'
        ELSE 'NORMAL'
    END AS estado_stock
FROM inventario i
INNER JOIN producto p ON i.producto_id = p.id
GROUP BY i.producto_id, p.nombre, p.codigo, i.bodega_id, i.pais, i.lote, p.stock_minimo, p.stock_critico;


-- 5. Función para obtener saldo actual de un producto en una bodega
CREATE OR REPLACE FUNCTION obtener_saldo_actual(
    p_producto_id VARCHAR(64),
    p_bodega_id VARCHAR(64),
    p_pais CHAR(2),
    p_lote VARCHAR(64) DEFAULT NULL
)
RETURNS INT AS $$
DECLARE
    v_saldo INT;
BEGIN
    IF p_lote IS NOT NULL THEN
        SELECT COALESCE(SUM(cantidad), 0) INTO v_saldo
        FROM inventario
        WHERE producto_id = p_producto_id
          AND bodega_id = p_bodega_id
          AND pais = p_pais
          AND lote = p_lote;
    ELSE
        SELECT COALESCE(SUM(cantidad), 0) INTO v_saldo
        FROM inventario
        WHERE producto_id = p_producto_id
          AND bodega_id = p_bodega_id
          AND pais = p_pais;
    END IF;
    
    RETURN v_saldo;
END;
$$ LANGUAGE plpgsql;


-- 6. Comentarios para documentación
COMMENT ON TABLE movimiento_inventario IS 'Registro completo de todos los movimientos de inventario (kardex)';
COMMENT ON TABLE alerta_inventario IS 'Alertas generadas automáticamente por condiciones de stock';
COMMENT ON COLUMN producto.stock_minimo IS 'Cantidad mínima antes de generar alerta WARNING';
COMMENT ON COLUMN producto.stock_critico IS 'Cantidad crítica antes de generar alerta CRITICAL';
COMMENT ON COLUMN producto.requiere_lote IS 'Indica si el producto debe tener número de lote';
COMMENT ON COLUMN producto.requiere_vencimiento IS 'Indica si el producto debe tener fecha de vencimiento';
COMMENT ON COLUMN movimiento_inventario.saldo_anterior IS 'Snapshot del saldo antes del movimiento';
COMMENT ON COLUMN movimiento_inventario.saldo_nuevo IS 'Snapshot del saldo después del movimiento';
COMMENT ON COLUMN movimiento_inventario.movimiento_relacionado_id IS 'ID del movimiento relacionado (para transferencias)';


-- 7. Datos de prueba: Insertar algunos movimientos iniciales
-- (Para que el kardex tenga datos históricos)
INSERT INTO movimiento_inventario (
    producto_id, bodega_id, pais, lote, tipo_movimiento, motivo,
    cantidad, fecha_vencimiento, saldo_anterior, saldo_nuevo,
    usuario_id, referencia_documento, observaciones
) VALUES
-- Movimiento inicial de Amoxicilina en BOG_CENTRAL
('PROD001', 'BOG_CENTRAL', 'CO', 'AMX001_2024', 'INGRESO', 'INVENTARIO_INICIAL', 
 500, '2025-12-31', 0, 500, 'ADMIN001', 'INV-INICIAL-001', 'Inventario inicial al implementar sistema'),

-- Compra de Ibuprofeno
('PROD006', 'BOG_CENTRAL', 'CO', 'IBU001_2024', 'INGRESO', 'COMPRA', 
 1000, '2026-06-30', 0, 1000, 'COMPRADOR001', 'PO-2024-001', 'Compra proveedor XYZ'),

-- Venta de Acetaminofén
('PROD007', 'BOG_CENTRAL', 'CO', 'ACE001_2024', 'SALIDA', 'VENTA', 
 50, NULL, 1500, 1450, 'VENDEDOR001', 'ORD-2024-100', 'Venta cliente CLI001'),

-- Ajuste por conteo físico
('PROD011', 'BOG_CENTRAL', 'CO', 'ENL001_2024', 'SALIDA', 'AJUSTE', 
 10, NULL, 300, 290, 'ADMIN001', 'AJ-2024-005', 'Ajuste por diferencia en conteo físico');


-- 8. Insertar algunas alertas de ejemplo
INSERT INTO alerta_inventario (
    producto_id, bodega_id, pais, tipo_alerta, nivel, mensaje, stock_actual, stock_minimo
) VALUES
('PROD016', 'LIM_CALLAO', 'PE', 'STOCK_MINIMO', 'WARNING', 
 'Stock bajo para Salbutamol 100mcg en Lima Callao: 100 unidades (mínimo: 50)', 100, 50),
 
('PROD003', 'BOG_CENTRAL', 'CO', 'STOCK_CRITICO', 'CRITICAL', 
 'Stock crítico para Azitromicina 500mg en Bogotá Central: 15 unidades (crítico: 20)', 15, 50);


-- ===================================================================
-- FIN DEL SCRIPT DE MIGRACIÓN
-- ===================================================================

-- Verificar que todo se creó correctamente
DO $$
BEGIN
    RAISE NOTICE '✅ Script 002_movimientos.sql ejecutado correctamente';
    RAISE NOTICE '📊 Tablas creadas: movimiento_inventario, alerta_inventario';
    RAISE NOTICE '📊 Campos agregados a producto: stock_minimo, stock_critico, requiere_lote, requiere_vencimiento';
    RAISE NOTICE '📊 Vista creada: v_saldos_bodega';
    RAISE NOTICE '📊 Función creada: obtener_saldo_actual()';
END $$;

