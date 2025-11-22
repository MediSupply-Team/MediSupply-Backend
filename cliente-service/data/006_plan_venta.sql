-- ============================================================================
-- 006_plan_venta.sql
-- Creación de tablas para Plan de Venta (Fase 3)
--   - plan_venta (1:1 con vendedor)
--   - plan_producto (productos asignados al plan)
--   - plan_region (regiones asignadas al plan)
--   - plan_zona (zonas asignadas al plan)
-- ============================================================================

-- Habilitar extensión pgcrypto para gen_random_uuid() si no está ya
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Función para actualizar 'updated_at' (si no existe)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- Tabla: plan_venta
-- Relación 1:1 con vendedor (un vendedor tiene un plan activo)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS plan_venta (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendedor_id UUID NOT NULL UNIQUE, -- 1:1 con vendedor
    tipo_plan_id UUID, -- FK a tipo_plan (opcional)
    nombre_plan VARCHAR(255) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    meta_ventas NUMERIC(15,2) NOT NULL DEFAULT 0, -- Meta en dinero
    comision_base NUMERIC(5,2) NOT NULL DEFAULT 5.0, -- Porcentaje base
    estructura_bonificaciones JSONB, -- Ejemplo: {"70": 2, "90": 5, "100": 10}
    observaciones TEXT,
    activo BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by_user_id VARCHAR(64),
    
    -- Constraints
    CONSTRAINT fk_plan_venta_vendedor FOREIGN KEY (vendedor_id) REFERENCES vendedor(id) ON DELETE CASCADE,
    CONSTRAINT fk_plan_venta_tipo_plan FOREIGN KEY (tipo_plan_id) REFERENCES tipo_plan(id) ON DELETE SET NULL,
    CONSTRAINT chk_plan_venta_fechas CHECK (fecha_fin >= fecha_inicio),
    CONSTRAINT chk_plan_venta_meta_ventas CHECK (meta_ventas >= 0),
    CONSTRAINT chk_plan_venta_comision_base CHECK (comision_base >= 0 AND comision_base <= 100)
);

-- Índices para plan_venta
CREATE INDEX IF NOT EXISTS idx_plan_venta_vendedor_id ON plan_venta(vendedor_id);
CREATE INDEX IF NOT EXISTS idx_plan_venta_tipo_plan_id ON plan_venta(tipo_plan_id);
CREATE INDEX IF NOT EXISTS idx_plan_venta_nombre ON plan_venta(nombre_plan);
CREATE INDEX IF NOT EXISTS idx_plan_venta_activo ON plan_venta(activo);
CREATE INDEX IF NOT EXISTS idx_plan_venta_fechas ON plan_venta(fecha_inicio, fecha_fin);

-- Trigger para actualizar updated_at
CREATE TRIGGER update_plan_venta_updated_at
BEFORE UPDATE ON plan_venta
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Asegurar que los DEFAULTs estén configurados
ALTER TABLE plan_venta ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE plan_venta ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE plan_venta ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;

COMMENT ON TABLE plan_venta IS 'Planes de venta asignados a vendedores (1:1)';
COMMENT ON COLUMN plan_venta.estructura_bonificaciones IS 'JSON con bonificaciones por cumplimiento: {70: 2, 90: 5, 100: 10}';

-- ----------------------------------------------------------------------------
-- Tabla: plan_producto
-- Productos asignados a un plan de venta con sus metas
-- SOLO guarda producto_id, el frontend consulta catalogo-service para detalles
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS plan_producto (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_venta_id UUID NOT NULL,
    producto_id VARCHAR(64) NOT NULL, -- ID del producto desde catalogo-service (solo ID)
    meta_cantidad INTEGER NOT NULL DEFAULT 0, -- Cantidad a vender
    precio_unitario NUMERIC(12,2) NOT NULL DEFAULT 0, -- Precio en el plan
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Constraints
    CONSTRAINT fk_plan_producto_plan_venta FOREIGN KEY (plan_venta_id) REFERENCES plan_venta(id) ON DELETE CASCADE,
    CONSTRAINT chk_plan_producto_meta_cantidad CHECK (meta_cantidad >= 0),
    CONSTRAINT chk_plan_producto_precio_unitario CHECK (precio_unitario >= 0),
    CONSTRAINT uq_plan_producto_plan_producto UNIQUE (plan_venta_id, producto_id) -- Un producto no puede estar duplicado en el mismo plan
);

-- Índices para plan_producto
CREATE INDEX IF NOT EXISTS idx_plan_producto_plan_venta_id ON plan_producto(plan_venta_id);
CREATE INDEX IF NOT EXISTS idx_plan_producto_producto_id ON plan_producto(producto_id);

-- Asegurar que los DEFAULTs estén configurados
ALTER TABLE plan_producto ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE plan_producto ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;

COMMENT ON TABLE plan_producto IS 'Productos asignados a un plan de venta con sus metas (solo IDs)';
COMMENT ON COLUMN plan_producto.producto_id IS 'ID del producto desde catalogo-service (frontend obtiene detalles)';

-- ----------------------------------------------------------------------------
-- Tabla: plan_region
-- Regiones asignadas a un plan de venta
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS plan_region (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_venta_id UUID NOT NULL,
    region_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Constraints
    CONSTRAINT fk_plan_region_plan_venta FOREIGN KEY (plan_venta_id) REFERENCES plan_venta(id) ON DELETE CASCADE,
    CONSTRAINT fk_plan_region_region FOREIGN KEY (region_id) REFERENCES region(id) ON DELETE CASCADE,
    CONSTRAINT uq_plan_region_plan_region UNIQUE (plan_venta_id, region_id) -- Una región no puede estar duplicada en el mismo plan
);

-- Índices para plan_region
CREATE INDEX IF NOT EXISTS idx_plan_region_plan_venta_id ON plan_region(plan_venta_id);
CREATE INDEX IF NOT EXISTS idx_plan_region_region_id ON plan_region(region_id);

-- Asegurar que los DEFAULTs estén configurados
ALTER TABLE plan_region ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE plan_region ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;

COMMENT ON TABLE plan_region IS 'Regiones principales asignadas a un plan de venta';

-- ----------------------------------------------------------------------------
-- Tabla: plan_zona
-- Zonas asignadas a un plan de venta
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS plan_zona (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_venta_id UUID NOT NULL,
    zona_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Constraints
    CONSTRAINT fk_plan_zona_plan_venta FOREIGN KEY (plan_venta_id) REFERENCES plan_venta(id) ON DELETE CASCADE,
    CONSTRAINT fk_plan_zona_zona FOREIGN KEY (zona_id) REFERENCES zona(id) ON DELETE CASCADE,
    CONSTRAINT uq_plan_zona_plan_zona UNIQUE (plan_venta_id, zona_id) -- Una zona no puede estar duplicada en el mismo plan
);

-- Índices para plan_zona
CREATE INDEX IF NOT EXISTS idx_plan_zona_plan_venta_id ON plan_zona(plan_venta_id);
CREATE INDEX IF NOT EXISTS idx_plan_zona_zona_id ON plan_zona(zona_id);

-- Asegurar que los DEFAULTs estén configurados
ALTER TABLE plan_zona ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE plan_zona ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;

COMMENT ON TABLE plan_zona IS 'Zonas especiales asignadas a un plan de venta';

-- ----------------------------------------------------------------------------
-- DATOS DE EJEMPLO (Opcional - Para Testing)
-- ----------------------------------------------------------------------------
-- Insertar un plan de venta de ejemplo para el primer vendedor

DO $$
DECLARE
    v_vendedor_id UUID;
    v_tipo_plan_id UUID;
    v_plan_id UUID;
    v_region_id UUID;
    v_zona_id UUID;
    plan_count INTEGER;
BEGIN
    -- Obtener ID del primer vendedor (si existe)
    SELECT id INTO v_vendedor_id FROM vendedor WHERE activo = true LIMIT 1;
    
    IF v_vendedor_id IS NULL THEN
        RAISE NOTICE 'ℹ️  No hay vendedores activos. Saltando creación de plan de ejemplo.';
        RETURN;
    END IF;
    
    -- Verificar si el vendedor ya tiene un plan
    SELECT COUNT(*) INTO plan_count FROM plan_venta WHERE vendedor_id = v_vendedor_id;
    
    IF plan_count > 0 THEN
        RAISE NOTICE 'ℹ️  El vendedor ya tiene un plan. Saltando creación de plan de ejemplo.';
        RETURN;
    END IF;
    
    -- Obtener IDs de catálogos
    SELECT id INTO v_tipo_plan_id FROM tipo_plan WHERE codigo = 'PLAN_PREMIUM' LIMIT 1;
    SELECT id INTO v_region_id FROM region WHERE activo = true LIMIT 1;
    SELECT id INTO v_zona_id FROM zona WHERE activo = true LIMIT 1;
    
    -- Crear plan de venta de ejemplo
    INSERT INTO plan_venta (
        vendedor_id, 
        tipo_plan_id, 
        nombre_plan, 
        fecha_inicio, 
        fecha_fin, 
        meta_ventas, 
        comision_base, 
        estructura_bonificaciones,
        observaciones,
        activo
    ) VALUES (
        v_vendedor_id,
        v_tipo_plan_id,
        'Plan Premium Q1 2024',
        '2024-01-01',
        '2024-03-31',
        150000.00,
        8.0,
        '{"70": 2, "90": 5, "100": 10}'::jsonb,
        'Plan de ejemplo con metas agresivas y bonificaciones escalonadas',
        true
    ) RETURNING id INTO v_plan_id;
    
    -- Insertar productos de ejemplo (solo IDs, frontend consulta catalogo-service para detalles)
    INSERT INTO plan_producto (plan_venta_id, producto_id, meta_cantidad, precio_unitario) VALUES
    (v_plan_id, 'PROD001', 100, 1500.00),
    (v_plan_id, 'PROD002', 80, 2000.00),
    (v_plan_id, 'PROD003', 60, 3500.00);
    
    -- Insertar regiones asignadas (si existen)
    IF v_region_id IS NOT NULL THEN
        INSERT INTO plan_region (plan_venta_id, region_id) VALUES (v_plan_id, v_region_id);
    END IF;
    
    -- Insertar zonas asignadas (si existen)
    IF v_zona_id IS NOT NULL THEN
        INSERT INTO plan_zona (plan_venta_id, zona_id) VALUES (v_plan_id, v_zona_id);
    END IF;
    
    RAISE NOTICE '✅ Plan de venta de ejemplo creado para vendedor %', v_vendedor_id;
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE '⚠️  No se pudo crear plan de ejemplo: %', SQLERRM;
END $$;

-- ----------------------------------------------------------------------------
-- Resumen de migración
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    plan_venta_count INTEGER;
    plan_producto_count INTEGER;
    plan_region_count INTEGER;
    plan_zona_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO plan_venta_count FROM plan_venta;
    SELECT COUNT(*) INTO plan_producto_count FROM plan_producto;
    SELECT COUNT(*) INTO plan_region_count FROM plan_region;
    SELECT COUNT(*) INTO plan_zona_count FROM plan_zona;

    RAISE NOTICE '✅ Migración 006: Tablas de Plan de Venta creadas exitosamente.';
    RAISE NOTICE '   • Planes de Venta  : % registros', plan_venta_count;
    RAISE NOTICE '   • Productos Asign. : % registros', plan_producto_count;
    RAISE NOTICE '   • Regiones Asign.  : % registros', plan_region_count;
    RAISE NOTICE '   • Zonas Asignadas  : % registros', plan_zona_count;
END $$;

