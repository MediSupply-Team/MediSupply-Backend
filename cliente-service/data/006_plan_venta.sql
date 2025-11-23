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
    region_id UUID NOT NULL,  -- Cambiado a UUID
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
    zona_id UUID NOT NULL,  -- Cambiado a UUID
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

-- ============================================================================
-- DATOS REALISTAS DE PLANES DE VENTA PARA LOS 6 VENDEDORES
-- ============================================================================
-- Cada vendedor tiene un plan activo con productos, regiones y zonas asignadas
-- Los UUIDs de productos corresponden a los del catálogo-service

-- Plan 1: Carlos Mendoza (Vendedor Senior - Colombia - Bogotá Norte)
INSERT INTO plan_venta (
    id, vendedor_id, tipo_plan_id, nombre_plan, fecha_inicio, fecha_fin,
    meta_ventas, comision_base, estructura_bonificaciones, observaciones, activo
) VALUES (
    'plan0001-0001-0001-0001-000000000001',
    '11111111-1111-1111-1111-111111111111',  -- Carlos Mendoza
    'p0000001-0001-0001-0001-000000000001',  -- PREMIUM
    'Plan Q4 2025 - Carlos Mendoza',
    '2025-10-01',
    '2025-12-31',
    250000000.00,  -- $250M COP
    10.0,
    '{"70": 2, "90": 5, "100": 12}'::jsonb,
    'Plan premium con foco en hospitales de Bogotá Norte',
    true
) ON CONFLICT (vendedor_id) DO NOTHING;

-- Productos para Carlos Mendoza (UUIDs reales del catálogo)
INSERT INTO plan_producto (plan_venta_id, producto_id, meta_cantidad, precio_unitario) VALUES
('plan0001-0001-0001-0001-000000000001', '11111111-1111-1111-1111-000000000001', 200, 1500.00),  -- Amoxicilina
('plan0001-0001-0001-0001-000000000001', '22222222-2222-2222-2222-000000000007', 150, 1800.00),  -- Acetaminofén
('plan0001-0001-0001-0001-000000000001', '11111111-1111-1111-1111-000000000002', 100, 2200.00)   -- Ibuprofeno
ON CONFLICT (plan_venta_id, producto_id) DO NOTHING;

-- Regiones y Zonas para Carlos Mendoza
INSERT INTO plan_region (plan_venta_id, region_id) VALUES
('plan0001-0001-0001-0001-000000000001', 'g0000001-0001-0001-0001-000000000005')  -- REG-CENTRO
ON CONFLICT (plan_venta_id, region_id) DO NOTHING;

INSERT INTO plan_zona (plan_venta_id, zona_id) VALUES
('plan0001-0001-0001-0001-000000000001', 'z0000001-0001-0001-0001-000000000002')  -- ZONA-HOSP
ON CONFLICT (plan_venta_id, zona_id) DO NOTHING;


-- Plan 2: María López (Vendedora Junior - Colombia - Medellín)
INSERT INTO plan_venta (
    id, vendedor_id, tipo_plan_id, nombre_plan, fecha_inicio, fecha_fin,
    meta_ventas, comision_base, estructura_bonificaciones, observaciones, activo
) VALUES (
    'plan0002-0002-0002-0002-000000000002',
    '22222222-2222-2222-2222-222222222222',  -- María López
    'p0000001-0001-0001-0001-000000000002',  -- ESTANDAR
    'Plan Q4 2025 - María López',
    '2025-10-01',
    '2025-12-31',
    180000000.00,  -- $180M COP
    5.0,
    '{"70": 1, "90": 3, "100": 8}'::jsonb,
    'Plan estándar enfocado en farmacias independientes',
    true
) ON CONFLICT (vendedor_id) DO NOTHING;

-- Productos para María López
INSERT INTO plan_producto (plan_venta_id, producto_id, meta_cantidad, precio_unitario) VALUES
('plan0002-0002-0002-0002-000000000002', '11111111-1111-1111-1111-000000000003', 120, 3500.00),  -- Omeprazol
('plan0002-0002-0002-0002-000000000002', '11111111-1111-1111-1111-000000000004', 80, 800.00),   -- Loratadina
('plan0002-0002-0002-0002-000000000002', '22222222-2222-2222-2222-000000000007', 100, 1800.00)   -- Acetaminofén
ON CONFLICT (plan_venta_id, producto_id) DO NOTHING;

-- Regiones y Zonas para María López
INSERT INTO plan_region (plan_venta_id, region_id) VALUES
('plan0002-0002-0002-0002-000000000002', 'g0000001-0001-0001-0001-000000000004')  -- REG-OESTE
ON CONFLICT (plan_venta_id, region_id) DO NOTHING;

INSERT INTO plan_zona (plan_venta_id, zona_id) VALUES
('plan0002-0002-0002-0002-000000000002', 'z0000001-0001-0001-0001-000000000004')  -- ZONA-COMERCIAL
ON CONFLICT (plan_venta_id, zona_id) DO NOTHING;


-- Plan 3: José Hernández (Vendedor Senior - México - CDMX)
INSERT INTO plan_venta (
    id, vendedor_id, tipo_plan_id, nombre_plan, fecha_inicio, fecha_fin,
    meta_ventas, comision_base, estructura_bonificaciones, observaciones, activo
) VALUES (
    'plan0003-0003-0003-0003-000000000003',
    '33333333-3333-3333-3333-333333333333',  -- José Hernández
    'p0000001-0001-0001-0001-000000000001',  -- PREMIUM
    'Plan Q4 2025 - José Hernández',
    '2025-10-01',
    '2025-12-31',
    800000.00,  -- $800K MXN
    10.0,
    '{"70": 2, "90": 5, "100": 12}'::jsonb,
    'Plan premium para cadenas de farmacias en CDMX',
    true
) ON CONFLICT (vendedor_id) DO NOTHING;

-- Productos para José Hernández
INSERT INTO plan_producto (plan_venta_id, producto_id, meta_cantidad, precio_unitario) VALUES
('plan0003-0003-0003-0003-000000000003', '22222222-2222-2222-2222-000000000008', 180, 4200.00),  -- Losartán
('plan0003-0003-0003-0003-000000000003', '22222222-2222-2222-2222-000000000009', 150, 8500.00),  -- Atorvastatina
('plan0003-0003-0003-0003-000000000003', '22222222-2222-2222-2222-000000000010', 120, 5200.00)   -- Metformina
ON CONFLICT (plan_venta_id, producto_id) DO NOTHING;

-- Regiones y Zonas para José Hernández
INSERT INTO plan_region (plan_venta_id, region_id) VALUES
('plan0003-0003-0003-0003-000000000003', 'g0000002-0002-0002-0002-000000000001')  -- REG-CENTRO-MX
ON CONFLICT (plan_venta_id, region_id) DO NOTHING;

INSERT INTO plan_zona (plan_venta_id, zona_id) VALUES
('plan0003-0003-0003-0003-000000000003', 'z0000001-0001-0001-0001-000000000004')  -- ZONA-COMERCIAL
ON CONFLICT (plan_venta_id, zona_id) DO NOTHING;


-- Plan 4: Ana González (Vendedora Junior - México - Guadalajara)
INSERT INTO plan_venta (
    id, vendedor_id, tipo_plan_id, nombre_plan, fecha_inicio, fecha_fin,
    meta_ventas, comision_base, estructura_bonificaciones, observaciones, activo
) VALUES (
    'plan0004-0004-0004-0004-000000000004',
    '44444444-4444-4444-4444-444444444444',  -- Ana González
    'p0000001-0001-0001-0001-000000000002',  -- ESTANDAR
    'Plan Q4 2025 - Ana González',
    '2025-10-01',
    '2025-12-31',
    600000.00,  -- $600K MXN
    5.0,
    '{"70": 1, "90": 3, "100": 8}'::jsonb,
    'Plan estándar para distribución regional en Jalisco',
    true
) ON CONFLICT (vendedor_id) DO NOTHING;

-- Productos para Ana González
INSERT INTO plan_producto (plan_venta_id, producto_id, meta_cantidad, precio_unitario) VALUES
('plan0004-0004-0004-0004-000000000004', '33333333-3333-3333-3333-000000000011', 90, 6800.00),   -- Levotiroxina
('plan0004-0004-0004-0004-000000000004', '33333333-3333-3333-3333-000000000012', 70, 12500.00),  -- Insulina
('plan0004-0004-0004-0004-000000000004', '22222222-2222-2222-2222-000000000007', 100, 1800.00)   -- Acetaminofén
ON CONFLICT (plan_venta_id, producto_id) DO NOTHING;

-- Regiones y Zonas para Ana González
INSERT INTO plan_region (plan_venta_id, region_id) VALUES
('plan0004-0004-0004-0004-000000000004', 'g0000002-0002-0002-0002-000000000002')  -- REG-OCCIDENTE
ON CONFLICT (plan_venta_id, region_id) DO NOTHING;

INSERT INTO plan_zona (plan_venta_id, zona_id) VALUES
('plan0004-0004-0004-0004-000000000004', 'z0000001-0001-0001-0001-000000000001')  -- ZONA-IND
ON CONFLICT (plan_venta_id, zona_id) DO NOTHING;


-- Plan 5: Miguel Torres (Gerente de Zona - Perú - Lima)
INSERT INTO plan_venta (
    id, vendedor_id, tipo_plan_id, nombre_plan, fecha_inicio, fecha_fin,
    meta_ventas, comision_base, estructura_bonificaciones, observaciones, activo
) VALUES (
    'plan0005-0005-0005-0005-000000000005',
    '55555555-5555-5555-5555-555555555555',  -- Miguel Torres
    'p0000001-0001-0001-0001-000000000001',  -- PREMIUM
    'Plan Q4 2025 - Miguel Torres',
    '2025-10-01',
    '2025-12-31',
    50000.00,  -- S/50K PEN
    10.0,
    '{"70": 2, "90": 5, "100": 12}'::jsonb,
    'Plan premium de gerencia con supervisión de 8 vendedores',
    true
) ON CONFLICT (vendedor_id) DO NOTHING;

-- Productos para Miguel Torres
INSERT INTO plan_producto (plan_venta_id, producto_id, meta_cantidad, precio_unitario) VALUES
('plan0005-0005-0005-0005-000000000005', '33333333-3333-3333-3333-000000000013', 120, 1200.00),  -- Salbutamol
('plan0005-0005-0005-0005-000000000005', '33333333-3333-3333-3333-000000000014', 100, 3800.00),  -- Montelukast
('plan0005-0005-0005-0005-000000000005', '33333333-3333-3333-3333-000000000015', 80, 4500.00)    -- Enalapril
ON CONFLICT (plan_venta_id, producto_id) DO NOTHING;

-- Regiones y Zonas para Miguel Torres
INSERT INTO plan_region (plan_venta_id, region_id) VALUES
('plan0005-0005-0005-0005-000000000005', 'g0000003-0003-0003-0003-000000000001')  -- REG-COSTA-PE
ON CONFLICT (plan_venta_id, region_id) DO NOTHING;

INSERT INTO plan_zona (plan_venta_id, zona_id) VALUES
('plan0005-0005-0005-0005-000000000005', 'z0000001-0001-0001-0001-000000000002')  -- ZONA-HOSP
ON CONFLICT (plan_venta_id, zona_id) DO NOTHING;


-- Plan 6: Carolina Silva (Vendedora Senior - Chile - Santiago)
INSERT INTO plan_venta (
    id, vendedor_id, tipo_plan_id, nombre_plan, fecha_inicio, fecha_fin,
    meta_ventas, comision_base, estructura_bonificaciones, observaciones, activo
) VALUES (
    'plan0006-0006-0006-0006-000000000006',
    '66666666-6666-6666-6666-666666666666',  -- Carolina Silva
    'p0000001-0001-0001-0001-000000000001',  -- PREMIUM
    'Plan Q4 2025 - Carolina Silva',
    '2025-10-01',
    '2025-12-31',
    15000000.00,  -- $15M CLP
    10.0,
    '{"70": 2, "90": 5, "100": 12}'::jsonb,
    'Plan premium especializado en clínicas privadas de Santiago',
    true
) ON CONFLICT (vendedor_id) DO NOTHING;

-- Productos para Carolina Silva
INSERT INTO plan_producto (plan_venta_id, producto_id, meta_cantidad, precio_unitario) VALUES
('plan0006-0006-0006-0006-000000000006', '44444444-4444-4444-4444-000000000016', 100, 9500.00),  -- Prednisona
('plan0006-0006-0006-0006-000000000006', '44444444-4444-4444-4444-000000000017', 80, 6200.00),   -- Diclofenaco
('plan0006-0006-0006-0006-000000000006', '44444444-4444-4444-4444-000000000018', 90, 7800.00)    -- Captopril
ON CONFLICT (plan_venta_id, producto_id) DO NOTHING;

-- Regiones y Zonas para Carolina Silva
INSERT INTO plan_region (plan_venta_id, region_id) VALUES
('plan0006-0006-0006-0006-000000000006', 'g0000004-0004-0004-0004-000000000001')  -- REG-METRO
ON CONFLICT (plan_venta_id, region_id) DO NOTHING;

INSERT INTO plan_zona (plan_venta_id, zona_id) VALUES
('plan0006-0006-0006-0006-000000000006', 'z0000001-0001-0001-0001-000000000002')  -- ZONA-HOSP
ON CONFLICT (plan_venta_id, zona_id) DO NOTHING;


-- Log de planes creados
DO $$
DECLARE
    plan_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO plan_count FROM plan_venta;
    RAISE NOTICE '✅ Planes de venta creados: % registros (6 vendedores con planes completos)', plan_count;
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

