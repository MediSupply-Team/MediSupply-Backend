-- ============================================================================
-- 004_proveedores.sql
-- HU: Registrar Proveedor - Tabla de proveedores y relación con productos
-- ============================================================================

-- Crear tabla de proveedores con UUID
CREATE TABLE IF NOT EXISTS proveedor (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nit VARCHAR(32) UNIQUE NOT NULL,
    empresa VARCHAR(255) NOT NULL,
    contacto_nombre VARCHAR(255) NOT NULL,
    contacto_email VARCHAR(255) UNIQUE NOT NULL,
    contacto_telefono VARCHAR(32),
    contacto_cargo VARCHAR(128),
    direccion VARCHAR(512),
    pais CHAR(2) NOT NULL,
    activo BOOLEAN DEFAULT TRUE NOT NULL,
    notas TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by_user_id VARCHAR(64)
);

-- Índices para búsquedas eficientes
CREATE INDEX IF NOT EXISTS idx_proveedor_nit ON proveedor(nit);
CREATE INDEX IF NOT EXISTS idx_proveedor_empresa ON proveedor(empresa);
CREATE INDEX IF NOT EXISTS idx_proveedor_email ON proveedor(contacto_email);
CREATE INDEX IF NOT EXISTS idx_proveedor_pais ON proveedor(pais);
CREATE INDEX IF NOT EXISTS idx_proveedor_activo ON proveedor(activo);
CREATE INDEX IF NOT EXISTS idx_proveedor_created_at ON proveedor(created_at);

-- Cambiar proveedor_id a UUID en tabla producto (si existe como VARCHAR)
DO $$ 
BEGIN
    -- Primero verificar si la columna existe y es VARCHAR
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'producto' 
        AND column_name = 'proveedor_id'
        AND data_type = 'character varying'
    ) THEN
        -- Eliminar FK si existe
        IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_producto_proveedor') THEN
            ALTER TABLE producto DROP CONSTRAINT fk_producto_proveedor;
        END IF;
        
        -- Cambiar tipo a UUID
        ALTER TABLE producto ALTER COLUMN proveedor_id TYPE UUID USING proveedor_id::uuid;
    END IF;
    
    -- Agregar FK
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_producto_proveedor'
    ) THEN
        ALTER TABLE producto 
        ADD CONSTRAINT fk_producto_proveedor 
        FOREIGN KEY (proveedor_id) 
        REFERENCES proveedor(id)
        ON DELETE SET NULL;
    END IF;
END $$;

-- Comentarios para documentación
COMMENT ON TABLE proveedor IS 'Tabla de proveedores de productos médicos';
COMMENT ON COLUMN proveedor.id IS 'ID único del proveedor';
COMMENT ON COLUMN proveedor.nit IS 'NIT o identificación fiscal del proveedor (único)';
COMMENT ON COLUMN proveedor.empresa IS 'Nombre de la empresa proveedora';
COMMENT ON COLUMN proveedor.contacto_nombre IS 'Nombre de la persona de contacto';
COMMENT ON COLUMN proveedor.contacto_email IS 'Email de contacto (único)';
COMMENT ON COLUMN proveedor.contacto_telefono IS 'Teléfono de contacto';
COMMENT ON COLUMN proveedor.contacto_cargo IS 'Cargo de la persona de contacto (ej: Gerente de Ventas)';
COMMENT ON COLUMN proveedor.direccion IS 'Dirección física del proveedor';
COMMENT ON COLUMN proveedor.pais IS 'Código ISO del país (ej: CO, MX, PE)';
COMMENT ON COLUMN proveedor.activo IS 'Indica si el proveedor está activo en el sistema';
COMMENT ON COLUMN proveedor.notas IS 'Notas adicionales sobre el proveedor';
COMMENT ON COLUMN proveedor.created_at IS 'Fecha de creación del registro';
COMMENT ON COLUMN proveedor.updated_at IS 'Fecha de última actualización';
COMMENT ON COLUMN proveedor.created_by_user_id IS 'ID del usuario que creó el registro (trazabilidad)';

-- Datos de ejemplo para pruebas (id se genera automáticamente)
INSERT INTO proveedor (nit, empresa, contacto_nombre, contacto_email, contacto_telefono, contacto_cargo, direccion, pais, activo) VALUES
('900111222-3', 'Suministros Médicos Global', 'Ana López', 'ana.lopez@suministrosmedicos.com', '+57-1-3456789', 'Gerente de Ventas', 'Calle 45 #12-34, Bogotá', 'CO', true),
('900222333-4', 'Farmacéutica del Sur', 'Carlos Martínez', 'carlos.martinez@farmaciasur.com', '+57-2-7654321', 'Director Comercial', 'Carrera 10 #20-30, Cali', 'CO', true),
('900333444-5', 'MediSupply Internacional', 'Laura Gómez', 'laura.gomez@medisupply-int.com', '+52-55-1234567', 'Coordinadora de Exportaciones', 'Av. Reforma 123, Ciudad de México', 'MX', true),
('900444555-6', 'Productos Hospitalarios Andinos', 'Jorge Ramírez', 'jorge.ramirez@hospitalarios.com', '+51-1-9876543', 'Gerente Regional', 'Jr. Lima 456, Lima', 'PE', true),
('900555666-7', 'Equipamiento Médico Chile', 'María Fernández', 'maria.fernandez@equipmed.cl', '+56-2-8765432', 'Jefa de Ventas', 'Av. Libertador 789, Santiago', 'CL', true)
ON CONFLICT (nit) DO NOTHING;

-- Log de la migración
DO $$
BEGIN
    RAISE NOTICE '✅ Migración 004: Tabla proveedor creada exitosamente';
    RAISE NOTICE '✅ Se agregaron 5 proveedores de ejemplo';
END $$;

