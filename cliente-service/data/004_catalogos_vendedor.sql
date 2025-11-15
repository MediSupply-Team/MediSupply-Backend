-- ============================================================================
-- 004_catalogos_vendedor.sql
-- Catálogos de soporte para gestión de vendedores y planes de venta
-- HU: Registrar Vendedor - Fase 1 Extensión
-- ============================================================================

-- ============================================================================
-- CREACIÓN DE TABLAS DE CATÁLOGOS
-- ============================================================================

-- Tabla: tipo_rol_vendedor
-- Define roles jerárquicos para vendedores con sus permisos
CREATE TABLE IF NOT EXISTS tipo_rol_vendedor (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo VARCHAR(64) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    nivel_jerarquia INTEGER NOT NULL DEFAULT 5 CHECK (nivel_jerarquia BETWEEN 1 AND 10),
    permisos JSONB,
    activo BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tipo_rol_vendedor_codigo ON tipo_rol_vendedor(codigo);
CREATE INDEX IF NOT EXISTS idx_tipo_rol_vendedor_activo ON tipo_rol_vendedor(activo);
CREATE INDEX IF NOT EXISTS idx_tipo_rol_vendedor_nivel ON tipo_rol_vendedor(nivel_jerarquia);

-- Asegurar que los DEFAULTs estén configurados (por si la tabla fue creada por SQLAlchemy)
ALTER TABLE tipo_rol_vendedor ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE tipo_rol_vendedor ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE tipo_rol_vendedor ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;

COMMENT ON TABLE tipo_rol_vendedor IS 'Catálogo de tipos de rol para vendedores con jerarquía';
COMMENT ON COLUMN tipo_rol_vendedor.codigo IS 'Código único del rol (ej: GERENTE_REG, VENDEDOR_SR)';
COMMENT ON COLUMN tipo_rol_vendedor.nivel_jerarquia IS 'Nivel jerárquico: 1=más alto, 10=más bajo';
COMMENT ON COLUMN tipo_rol_vendedor.permisos IS 'Permisos del rol en formato JSON';


-- Tabla: territorio
-- Define territorios geográficos asignables a vendedores
CREATE TABLE IF NOT EXISTS territorio (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo VARCHAR(64) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    pais CHAR(2) NOT NULL,
    descripcion TEXT,
    activo BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_territorio_codigo ON territorio(codigo);
CREATE INDEX IF NOT EXISTS idx_territorio_pais ON territorio(pais);
CREATE INDEX IF NOT EXISTS idx_territorio_activo ON territorio(activo);
CREATE INDEX IF NOT EXISTS idx_territorio_nombre ON territorio(nombre);

-- Asegurar que los DEFAULTs estén configurados
ALTER TABLE territorio ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE territorio ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE territorio ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;

COMMENT ON TABLE territorio IS 'Catálogo de territorios geográficos para asignación de vendedores';
COMMENT ON COLUMN territorio.codigo IS 'Código único del territorio (ej: BOG-NORTE, MED-CENTRO)';
COMMENT ON COLUMN territorio.pais IS 'Código ISO 3166-1 alpha-2 del país';


-- Tabla: tipo_plan
-- Define tipos de plan de venta con comisiones base
CREATE TABLE IF NOT EXISTS tipo_plan (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo VARCHAR(64) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    comision_base_defecto DECIMAL(5,2) NOT NULL DEFAULT 5.0 CHECK (comision_base_defecto BETWEEN 0 AND 100),
    activo BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tipo_plan_codigo ON tipo_plan(codigo);
CREATE INDEX IF NOT EXISTS idx_tipo_plan_activo ON tipo_plan(activo);

-- Asegurar que los DEFAULTs estén configurados
ALTER TABLE tipo_plan ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE tipo_plan ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE tipo_plan ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;

COMMENT ON TABLE tipo_plan IS 'Catálogo de tipos de plan de venta';
COMMENT ON COLUMN tipo_plan.codigo IS 'Código único del tipo de plan (ej: PREMIUM, ESTANDAR, BASICO)';
COMMENT ON COLUMN tipo_plan.comision_base_defecto IS 'Comisión base por defecto en porcentaje (0-100)';


-- Tabla: region
-- Define regiones principales para planes de venta
CREATE TABLE IF NOT EXISTS region (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo VARCHAR(64) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    pais CHAR(2) NOT NULL,
    descripcion TEXT,
    activo BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_region_codigo ON region(codigo);
CREATE INDEX IF NOT EXISTS idx_region_pais ON region(pais);
CREATE INDEX IF NOT EXISTS idx_region_activo ON region(activo);
CREATE INDEX IF NOT EXISTS idx_region_nombre ON region(nombre);

-- Asegurar que los DEFAULTs estén configurados
ALTER TABLE region ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE region ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE region ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;

COMMENT ON TABLE region IS 'Catálogo de regiones geográficas principales para planes de venta';
COMMENT ON COLUMN region.codigo IS 'Código único de la región (ej: REG-NORTE, REG-SUR)';
COMMENT ON COLUMN region.pais IS 'Código ISO 3166-1 alpha-2 del país';


-- Tabla: zona
-- Define zonas especiales por tipo de mercado
CREATE TABLE IF NOT EXISTS zona (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo VARCHAR(64) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    tipo VARCHAR(64) NOT NULL,
    descripcion TEXT,
    activo BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_zona_codigo ON zona(codigo);
CREATE INDEX IF NOT EXISTS idx_zona_tipo ON zona(tipo);
CREATE INDEX IF NOT EXISTS idx_zona_activo ON zona(activo);
CREATE INDEX IF NOT EXISTS idx_zona_nombre ON zona(nombre);

-- Asegurar que los DEFAULTs estén configurados
ALTER TABLE zona ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE zona ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE zona ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;

COMMENT ON TABLE zona IS 'Catálogo de zonas especiales por tipo de mercado';
COMMENT ON COLUMN zona.codigo IS 'Código único de la zona (ej: ZONA-IND, ZONA-HOSP, ZONA-RURAL)';
COMMENT ON COLUMN zona.tipo IS 'Tipo de zona (industrial, hospitalaria, rural, etc.)';


-- ============================================================================
-- DATA PRECARGADA: TIPO ROL VENDEDOR
-- ============================================================================

INSERT INTO tipo_rol_vendedor (codigo, nombre, descripcion, nivel_jerarquia, permisos, activo) VALUES
('GERENTE_REG', 'Gerente Regional', 'Gerente responsable de una región completa con autoridad sobre múltiples vendedores', 1, 
 '{"ver_reportes": true, "aprobar_descuentos": true, "gestionar_vendedores": true, "modificar_planes": true, "ver_comisiones": true}'::jsonb, true),

('GERENTE_ZONA', 'Gerente de Zona', 'Gerente responsable de una zona específica con supervisión de vendedores', 2, 
 '{"ver_reportes": true, "aprobar_descuentos": true, "gestionar_vendedores": true, "ver_comisiones": true}'::jsonb, true),

('VENDEDOR_SR', 'Vendedor Senior', 'Vendedor con experiencia y autonomía para gestionar clientes clave', 3, 
 '{"ver_reportes": true, "crear_pedidos": true, "aplicar_descuentos_basicos": true, "ver_comision_propia": true}'::jsonb, true),

('VENDEDOR_JR', 'Vendedor Junior', 'Vendedor con experiencia limitada bajo supervisión', 4, 
 '{"crear_pedidos": true, "ver_productos": true, "ver_comision_propia": true}'::jsonb, true),

('VENDEDOR_TRAINEE', 'Vendedor en Entrenamiento', 'Vendedor nuevo en período de capacitación', 5, 
 '{"crear_pedidos": false, "ver_productos": true, "ver_comision_propia": false}'::jsonb, true)

ON CONFLICT (codigo) DO NOTHING;


-- ============================================================================
-- DATA PRECARGADA: TERRITORIO
-- ============================================================================

INSERT INTO territorio (codigo, nombre, pais, descripcion, activo) VALUES
('BOG-NORTE', 'Bogotá Norte', 'CO', 'Territorio norte de Bogotá incluyendo Usaquén, Chapinero y Suba', true),
('BOG-SUR', 'Bogotá Sur', 'CO', 'Territorio sur de Bogotá incluyendo Bosa, Kennedy y Tunjuelito', true),
('MED-CENTRO', 'Medellín Centro', 'CO', 'Territorio centro de Medellín incluyendo El Poblado y Laureles', true),
('CALI-OESTE', 'Cali Oeste', 'CO', 'Territorio oeste de Cali incluyendo Normandía y Pance', true),
('BARR-NORTE', 'Barranquilla Norte', 'CO', 'Territorio norte de Barranquilla incluyendo Riomar y El Prado', true)

ON CONFLICT (codigo) DO NOTHING;


-- ============================================================================
-- DATA PRECARGADA: TIPO PLAN
-- ============================================================================

INSERT INTO tipo_plan (codigo, nombre, descripcion, comision_base_defecto, activo) VALUES
('PREMIUM', 'Plan Premium', 'Plan para vendedores de alto rendimiento con comisión elevada y beneficios adicionales', 10.0, true),
('ESTANDAR', 'Plan Estándar', 'Plan estándar para vendedores regulares con comisión balanceada', 5.0, true),
('BASICO', 'Plan Básico', 'Plan básico para vendedores nuevos o en entrenamiento con comisión reducida', 3.0, true)

ON CONFLICT (codigo) DO NOTHING;


-- ============================================================================
-- DATA PRECARGADA: REGION
-- ============================================================================

INSERT INTO region (codigo, nombre, pais, descripcion, activo) VALUES
('REG-NORTE', 'Región Norte', 'CO', 'Región norte del país incluyendo Costa Atlántica', true),
('REG-SUR', 'Región Sur', 'CO', 'Región sur del país incluyendo Cali y Valle del Cauca', true),
('REG-ESTE', 'Región Este', 'CO', 'Región este del país incluyendo Llanos Orientales', true),
('REG-OESTE', 'Región Oeste', 'CO', 'Región oeste del país incluyendo Chocó y Antioquia', true),
('REG-CENTRO', 'Región Centro', 'CO', 'Región centro del país incluyendo Bogotá y Cundinamarca', true)

ON CONFLICT (codigo) DO NOTHING;


-- ============================================================================
-- DATA PRECARGADA: ZONA
-- ============================================================================

INSERT INTO zona (codigo, nombre, tipo, descripcion, activo) VALUES
('ZONA-IND', 'Zona Industrial', 'industrial', 'Zona con alta concentración de empresas manufactureras y bodegas', true),
('ZONA-HOSP', 'Zona Hospitalaria', 'hospitalaria', 'Zona con hospitales, clínicas y centros de salud', true),
('ZONA-RURAL', 'Zona Rural', 'rural', 'Zona rural con farmacias y centros de salud de baja densidad', true)

ON CONFLICT (codigo) DO NOTHING;


-- ============================================================================
-- TRIGGERS PARA UPDATED_AT
-- ============================================================================

-- Función genérica para actualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para cada tabla
DO $$
BEGIN
    -- tipo_rol_vendedor
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_tipo_rol_vendedor_updated_at') THEN
        CREATE TRIGGER update_tipo_rol_vendedor_updated_at
            BEFORE UPDATE ON tipo_rol_vendedor
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;

    -- territorio
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_territorio_updated_at') THEN
        CREATE TRIGGER update_territorio_updated_at
            BEFORE UPDATE ON territorio
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;

    -- tipo_plan
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_tipo_plan_updated_at') THEN
        CREATE TRIGGER update_tipo_plan_updated_at
            BEFORE UPDATE ON tipo_plan
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;

    -- region
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_region_updated_at') THEN
        CREATE TRIGGER update_region_updated_at
            BEFORE UPDATE ON region
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;

    -- zona
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_zona_updated_at') THEN
        CREATE TRIGGER update_zona_updated_at
            BEFORE UPDATE ON zona
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;


-- ============================================================================
-- VERIFICACIÓN Y RESUMEN
-- ============================================================================

DO $$
DECLARE
    tipo_rol_count INTEGER;
    territorio_count INTEGER;
    tipo_plan_count INTEGER;
    region_count INTEGER;
    zona_count INTEGER;
BEGIN
    -- Contar registros
    SELECT COUNT(*) INTO tipo_rol_count FROM tipo_rol_vendedor;
    SELECT COUNT(*) INTO territorio_count FROM territorio;
    SELECT COUNT(*) INTO tipo_plan_count FROM tipo_plan;
    SELECT COUNT(*) INTO region_count FROM region;
    SELECT COUNT(*) INTO zona_count FROM zona;
    
    -- Mostrar resumen
    RAISE NOTICE '======================================';
    RAISE NOTICE '✅ Migración 004: Catálogos Vendedor';
    RAISE NOTICE '======================================';
    RAISE NOTICE 'Tipos de Rol: % registros', tipo_rol_count;
    RAISE NOTICE 'Territorios: % registros', territorio_count;
    RAISE NOTICE 'Tipos de Plan: % registros', tipo_plan_count;
    RAISE NOTICE 'Regiones: % registros', region_count;
    RAISE NOTICE 'Zonas: % registros', zona_count;
    RAISE NOTICE '======================================';
END $$;

