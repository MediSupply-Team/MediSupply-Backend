-- =====================================================
-- Script de creación de tabla BODEGA y precarga
-- Bodegas (warehouses) para gestión de inventario
-- =====================================================

-- Crear tabla bodega
CREATE TABLE IF NOT EXISTS bodega (
    codigo VARCHAR(64) PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    pais VARCHAR(2) NOT NULL,
    direccion VARCHAR(512),
    ciudad VARCHAR(128),
    responsable VARCHAR(255),
    telefono VARCHAR(32),
    email VARCHAR(255),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    capacidad_m3 DECIMAL(10,2),
    tipo VARCHAR(64),
    notas TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id VARCHAR(64)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_bodega_pais ON bodega(pais);
CREATE INDEX IF NOT EXISTS idx_bodega_activo ON bodega(activo);
CREATE INDEX IF NOT EXISTS idx_bodega_created_at ON bodega(created_at);

-- =====================================================
-- PRECARGA DE BODEGAS
-- =====================================================

-- Colombia
INSERT INTO bodega (codigo, nombre, pais, direccion, ciudad, responsable, telefono, tipo, activo, created_by_user_id) VALUES
('BOG_CENTRAL', 'Bodega Central Bogotá', 'CO', 'Calle 100 #15-25, Zona Industrial', 'Bogotá', 'Carlos Rodríguez', '+57 301 555 0101', 'PRINCIPAL', TRUE, 'SYSTEM'),
('BOG_NORTE', 'Bodega Norte Bogotá', 'CO', 'Autopista Norte Km 18', 'Bogotá', 'María López', '+57 301 555 0102', 'SECUNDARIA', TRUE, 'SYSTEM'),
('MED_CENTRO', 'Bodega Centro Medellín', 'CO', 'Carrera 65 #45-80', 'Medellín', 'Juan Pérez', '+57 304 555 0201', 'PRINCIPAL', TRUE, 'SYSTEM'),
('MED_NORTE', 'Bodega Norte Medellín', 'CO', 'Autopista Norte #120-50', 'Medellín', 'Ana García', '+57 304 555 0202', 'SECUNDARIA', TRUE, 'SYSTEM'),
('MED_SUR', 'Bodega Sur Medellín', 'CO', 'Carrera 43A #34-95', 'Medellín', 'Roberto Silva', '+57 304 555 0203', 'SECUNDARIA', TRUE, 'SYSTEM'),
('CALI_SUR', 'Bodega Sur Cali', 'CO', 'Calle 5 #70-15', 'Cali', 'Pedro Martínez', '+57 302 555 0301', 'PRINCIPAL', TRUE, 'SYSTEM'),
('BARR_CENTRAL', 'Bodega Central Barranquilla', 'CO', 'Calle 72 #43-94', 'Barranquilla', 'Laura Ramírez', '+57 305 555 0401', 'PRINCIPAL', TRUE, 'SYSTEM')
ON CONFLICT (codigo) DO NOTHING;

-- México
INSERT INTO bodega (codigo, nombre, pais, direccion, ciudad, responsable, telefono, tipo, activo, created_by_user_id) VALUES
('CDMX_CENTRAL', 'Bodega Central Ciudad de México', 'MX', 'Av. Insurgentes Sur 1234', 'Ciudad de México', 'José Hernández', '+52 55 5555 1001', 'PRINCIPAL', TRUE, 'SYSTEM'),
('CDMX_NORTE', 'Bodega Norte CDMX', 'MX', 'Av. Politécnico Nacional 890', 'Ciudad de México', 'Patricia González', '+52 55 5555 1002', 'SECUNDARIA', TRUE, 'SYSTEM'),
('GDL_CENTRO', 'Bodega Centro Guadalajara', 'MX', 'Av. López Mateos Sur 2000', 'Guadalajara', 'Ricardo Sánchez', '+52 33 3333 2001', 'PRINCIPAL', TRUE, 'SYSTEM'),
('GDL_OESTE', 'Bodega Oeste Guadalajara', 'MX', 'Av. Vallarta 3500', 'Guadalajara', 'Carmen Ortiz', '+52 33 3333 2002', 'SECUNDARIA', TRUE, 'SYSTEM'),
('MTY_INDUSTRIAL', 'Bodega Industrial Monterrey', 'MX', 'Av. Constitución 500', 'Monterrey', 'Sofía Morales', '+52 81 8181 3001', 'PRINCIPAL', TRUE, 'SYSTEM')
ON CONFLICT (codigo) DO NOTHING;

-- Perú
INSERT INTO bodega (codigo, nombre, pais, direccion, ciudad, responsable, telefono, tipo, activo, created_by_user_id) VALUES
('LIMA_CALLAO', 'Bodega Callao Lima', 'PE', 'Av. Colonial 1500', 'Lima', 'Miguel Torres', '+51 1 555 4001', 'PRINCIPAL', TRUE, 'SYSTEM'),
('LIMA_CENTRO', 'Bodega Centro Lima', 'PE', 'Jirón de la Unión 800', 'Lima', 'Carmen Flores', '+51 1 555 4002', 'SECUNDARIA', TRUE, 'SYSTEM'),
('AREQUIPA_CENTRAL', 'Bodega Central Arequipa', 'PE', 'Av. Ejército 700', 'Arequipa', 'Roberto Chávez', '+51 54 555 5001', 'PRINCIPAL', TRUE, 'SYSTEM')
ON CONFLICT (codigo) DO NOTHING;

-- Chile
INSERT INTO bodega (codigo, nombre, pais, direccion, ciudad, responsable, telefono, tipo, activo, created_by_user_id) VALUES
('SCL_CENTRO', 'Bodega Centro Santiago', 'CL', 'Av. Libertador Bernardo O Higgins 1234', 'Santiago', 'Felipe Silva', '+56 2 2555 6001', 'PRINCIPAL', TRUE, 'SYSTEM'),
('STGO_MAIPU', 'Bodega Maipú Santiago', 'CL', 'Av. Pajaritos 3000', 'Santiago', 'Carlos Ramírez', '+56 2 2555 6003', 'SECUNDARIA', TRUE, 'SYSTEM'),
('STGO_PUDAHUEL', 'Bodega Pudahuel Santiago', 'CL', 'Av. San Pablo 5000', 'Santiago', 'Valentina Rojas', '+56 2 2555 6002', 'SECUNDARIA', TRUE, 'SYSTEM'),
('VALP_PUERTO', 'Bodega Puerto Valparaíso', 'CL', 'Av. Brasil 2500', 'Valparaíso', 'Diego Muñoz', '+56 32 255 7001', 'PRINCIPAL', TRUE, 'SYSTEM')
ON CONFLICT (codigo) DO NOTHING;

-- Bodega para tránsito/temporal
INSERT INTO bodega (codigo, nombre, pais, direccion, ciudad, responsable, tipo, activo, notas, created_by_user_id) VALUES
('TRANSITO_TEMP', 'Bodega de Tránsito Temporal', 'CO', 'Múltiples ubicaciones', 'N/A', 'Sistema', 'TRANSITO', TRUE, 'Bodega virtual para transferencias en tránsito', 'SYSTEM')
ON CONFLICT (codigo) DO NOTHING;

COMMIT;

