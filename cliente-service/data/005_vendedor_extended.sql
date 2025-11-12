-- ============================================================================
-- 005_vendedor_extended.sql
-- Extiende la tabla vendedor con nuevos campos para Fase 2
-- HU: Registrar Vendedor - Campos extendidos con catálogos y jerarquía
-- ============================================================================

DO $$
BEGIN
    -- Agregar columna username (único, para login)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendedor' AND column_name = 'username'
    ) THEN
        ALTER TABLE vendedor ADD COLUMN username VARCHAR(64) UNIQUE;
        CREATE INDEX idx_vendedor_username ON vendedor(username) WHERE username IS NOT NULL;
        RAISE NOTICE '  ✅ Columna username agregada';
    ELSE
        RAISE NOTICE '  ℹ️  Columna username ya existe';
    END IF;

    -- Agregar columna rol_vendedor_id (FK a tipo_rol_vendedor)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendedor' AND column_name = 'rol_vendedor_id'
    ) THEN
        ALTER TABLE vendedor ADD COLUMN rol_vendedor_id UUID;
        CREATE INDEX idx_vendedor_rol_vendedor ON vendedor(rol_vendedor_id) WHERE rol_vendedor_id IS NOT NULL;
        RAISE NOTICE '  ✅ Columna rol_vendedor_id agregada';
    ELSE
        RAISE NOTICE '  ℹ️  Columna rol_vendedor_id ya existe';
    END IF;

    -- Agregar columna territorio_id (FK a territorio)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendedor' AND column_name = 'territorio_id'
    ) THEN
        ALTER TABLE vendedor ADD COLUMN territorio_id UUID;
        CREATE INDEX idx_vendedor_territorio ON vendedor(territorio_id) WHERE territorio_id IS NOT NULL;
        RAISE NOTICE '  ✅ Columna territorio_id agregada';
    ELSE
        RAISE NOTICE '  ℹ️  Columna territorio_id ya existe';
    END IF;

    -- Agregar columna supervisor_id (FK a vendedor - auto-referencia)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendedor' AND column_name = 'supervisor_id'
    ) THEN
        ALTER TABLE vendedor ADD COLUMN supervisor_id UUID;
        CREATE INDEX idx_vendedor_supervisor ON vendedor(supervisor_id) WHERE supervisor_id IS NOT NULL;
        RAISE NOTICE '  ✅ Columna supervisor_id agregada';
    ELSE
        RAISE NOTICE '  ℹ️  Columna supervisor_id ya existe';
    END IF;

    -- Agregar columna fecha_ingreso
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendedor' AND column_name = 'fecha_ingreso'
    ) THEN
        ALTER TABLE vendedor ADD COLUMN fecha_ingreso DATE;
        RAISE NOTICE '  ✅ Columna fecha_ingreso agregada';
    ELSE
        RAISE NOTICE '  ℹ️  Columna fecha_ingreso ya existe';
    END IF;

    -- Agregar columna observaciones
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendedor' AND column_name = 'observaciones'
    ) THEN
        ALTER TABLE vendedor ADD COLUMN observaciones TEXT;
        RAISE NOTICE '  ✅ Columna observaciones agregada';
    ELSE
        RAISE NOTICE '  ℹ️  Columna observaciones ya existe';
    END IF;

END $$;


-- ============================================================================
-- AGREGAR CONSTRAINTS DE FOREIGN KEY (idempotente)
-- ============================================================================

DO $$
BEGIN
    -- FK: rol_vendedor_id → tipo_rol_vendedor(id)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_vendedor_rol_vendedor' AND table_name = 'vendedor'
    ) THEN
        ALTER TABLE vendedor 
        ADD CONSTRAINT fk_vendedor_rol_vendedor 
        FOREIGN KEY (rol_vendedor_id) REFERENCES tipo_rol_vendedor(id) ON DELETE SET NULL;
        RAISE NOTICE '  ✅ FK fk_vendedor_rol_vendedor creada';
    ELSE
        RAISE NOTICE '  ℹ️  FK fk_vendedor_rol_vendedor ya existe';
    END IF;

    -- FK: territorio_id → territorio(id)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_vendedor_territorio' AND table_name = 'vendedor'
    ) THEN
        ALTER TABLE vendedor 
        ADD CONSTRAINT fk_vendedor_territorio 
        FOREIGN KEY (territorio_id) REFERENCES territorio(id) ON DELETE SET NULL;
        RAISE NOTICE '  ✅ FK fk_vendedor_territorio creada';
    ELSE
        RAISE NOTICE '  ℹ️  FK fk_vendedor_territorio ya existe';
    END IF;

    -- FK: supervisor_id → vendedor(id) (auto-referencia)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_vendedor_supervisor' AND table_name = 'vendedor'
    ) THEN
        ALTER TABLE vendedor 
        ADD CONSTRAINT fk_vendedor_supervisor 
        FOREIGN KEY (supervisor_id) REFERENCES vendedor(id) ON DELETE SET NULL;
        RAISE NOTICE '  ✅ FK fk_vendedor_supervisor creada (auto-referencia)';
    ELSE
        RAISE NOTICE '  ℹ️  FK fk_vendedor_supervisor ya existe';
    END IF;

END $$;


-- ============================================================================
-- COMENTARIOS PARA DOCUMENTACIÓN
-- ============================================================================

COMMENT ON COLUMN vendedor.username IS 'Nombre de usuario para login (único)';
COMMENT ON COLUMN vendedor.rol_vendedor_id IS 'FK a tipo_rol_vendedor - Define el rol jerárquico del vendedor';
COMMENT ON COLUMN vendedor.territorio_id IS 'FK a territorio - Territorio geográfico asignado al vendedor';
COMMENT ON COLUMN vendedor.supervisor_id IS 'FK a vendedor - Supervisor directo (jerarquía)';
COMMENT ON COLUMN vendedor.fecha_ingreso IS 'Fecha de ingreso del vendedor al equipo';
COMMENT ON COLUMN vendedor.observaciones IS 'Observaciones adicionales sobre el vendedor';


-- ============================================================================
-- ACTUALIZAR VENDEDORES EXISTENTES (OPCIONAL)
-- ============================================================================

-- Si existen vendedores precargados en 002_vendedores.sql, se pueden actualizar aquí
-- Ejemplo: Asignar un tipo de rol por defecto a vendedores existentes

DO $$
DECLARE
    vendedor_count INTEGER;
    tipo_rol_default_id UUID;
BEGIN
    -- Contar vendedores existentes
    SELECT COUNT(*) INTO vendedor_count FROM vendedor;
    
    IF vendedor_count > 0 THEN
        RAISE NOTICE '📝 Actualizando % vendedores existentes...', vendedor_count;
        
        -- Obtener el ID del tipo de rol "Vendedor Senior" (si existe)
        SELECT id INTO tipo_rol_default_id 
        FROM tipo_rol_vendedor 
        WHERE codigo = 'VENDEDOR_SR' AND activo = true 
        LIMIT 1;
        
        IF tipo_rol_default_id IS NOT NULL THEN
            -- Asignar tipo de rol por defecto a vendedores sin rol
            UPDATE vendedor 
            SET rol_vendedor_id = tipo_rol_default_id
            WHERE rol_vendedor_id IS NULL;
            
            RAISE NOTICE '  ✅ Vendedores actualizados con tipo de rol por defecto';
        END IF;
    END IF;
END $$;


-- ============================================================================
-- VERIFICACIÓN Y RESUMEN
-- ============================================================================

DO $$
DECLARE
    vendedor_count INTEGER;
    vendedores_con_username INTEGER;
    vendedores_con_territorio INTEGER;
    vendedores_con_supervisor INTEGER;
BEGIN
    -- Contar registros
    SELECT COUNT(*) INTO vendedor_count FROM vendedor;
    SELECT COUNT(*) INTO vendedores_con_username FROM vendedor WHERE username IS NOT NULL;
    SELECT COUNT(*) INTO vendedores_con_territorio FROM vendedor WHERE territorio_id IS NOT NULL;
    SELECT COUNT(*) INTO vendedores_con_supervisor FROM vendedor WHERE supervisor_id IS NOT NULL;
    
    -- Mostrar resumen
    RAISE NOTICE '======================================';
    RAISE NOTICE '✅ Migración 005: Vendedor Extendido';
    RAISE NOTICE '======================================';
    RAISE NOTICE 'Total vendedores: %', vendedor_count;
    RAISE NOTICE 'Con username: %', vendedores_con_username;
    RAISE NOTICE 'Con territorio: %', vendedores_con_territorio;
    RAISE NOTICE 'Con supervisor: %', vendedores_con_supervisor;
    RAISE NOTICE '======================================';
    RAISE NOTICE '';
    RAISE NOTICE '📋 Nuevos campos disponibles:';
    RAISE NOTICE '   • username (login)';
    RAISE NOTICE '   • rol_vendedor_id (FK)';
    RAISE NOTICE '   • territorio_id (FK)';
    RAISE NOTICE '   • supervisor_id (FK auto-referencia)';
    RAISE NOTICE '   • fecha_ingreso';
    RAISE NOTICE '   • observaciones';
    RAISE NOTICE '======================================';
END $$;

