-- ============================================================================
-- 003_campos_proveedor.sql
-- Agrega campos para HU021 - Carga masiva de productos por proveedores
-- ============================================================================

-- Agregar nuevas columnas a la tabla producto
-- Estos campos son necesarios para la carga masiva de productos por proveedores

ALTER TABLE producto 
ADD COLUMN IF NOT EXISTS certificado_sanitario VARCHAR(255),
ADD COLUMN IF NOT EXISTS tiempo_entrega_dias INTEGER,
ADD COLUMN IF NOT EXISTS proveedor_id VARCHAR(64);

-- Comentarios para documentación
COMMENT ON COLUMN producto.certificado_sanitario IS 'Número o referencia del certificado sanitario del producto';
COMMENT ON COLUMN producto.tiempo_entrega_dias IS 'Tiempo estimado de entrega en días';
COMMENT ON COLUMN producto.proveedor_id IS 'ID del proveedor del producto';

-- Opcional: Crear índice para búsquedas por proveedor
CREATE INDEX IF NOT EXISTS idx_producto_proveedor_id ON producto(proveedor_id);

-- Log de la migración
DO $$
BEGIN
    RAISE NOTICE '✅ Migración 003: Campos de proveedor agregados exitosamente';
END $$;

