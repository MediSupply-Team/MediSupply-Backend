-- ============================================================================
-- 003_cliente_uuid_rol.sql
-- Actualizar cliente a UUID y agregar campo rol
-- ============================================================================

-- Cambiar id de cliente a UUID
DO $$ 
BEGIN
    -- Si la columna id es VARCHAR, convertir a UUID
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'cliente' 
        AND column_name = 'id'
        AND data_type = 'character varying'
    ) THEN
        RAISE NOTICE 'Convirtiendo cliente.id de VARCHAR a UUID...';
        
        -- Primero, eliminar constraints que dependen de id
        -- (No hay FKs hacia cliente en este momento, solo vendedor_id sale de cliente)
        
        -- Cambiar tipo a UUID (si los valores actuales son UUID strings válidos)
        -- Si no, la tabla debe estar vacía o con datos UUID compatibles
        ALTER TABLE cliente ALTER COLUMN id TYPE UUID USING id::uuid;
        
        RAISE NOTICE '✅ cliente.id convertido a UUID';
    END IF;
END $$;

-- Agregar columna rol si no existe
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'cliente' AND column_name = 'rol'
    ) THEN
        ALTER TABLE cliente ADD COLUMN rol VARCHAR(32) DEFAULT 'cliente' NOT NULL;
        RAISE NOTICE '✅ Columna rol agregada a cliente';
    END IF;
END $$;

-- Actualizar todos los clientes existentes para que tengan rol='cliente' si es NULL
UPDATE cliente SET rol = 'cliente' WHERE rol IS NULL OR rol = '';

-- Comentarios
COMMENT ON COLUMN cliente.id IS 'ID único del cliente (UUID autogenerado)';
COMMENT ON COLUMN cliente.rol IS 'Rol del cliente (cliente por defecto)';

-- Log de la migración
DO $$
BEGIN
    RAISE NOTICE '✅ Migración 003: Cliente actualizado a UUID y rol agregado';
END $$;

