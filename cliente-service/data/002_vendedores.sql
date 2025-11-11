-- ============================================================================
-- 002_vendedores.sql
-- HU: Registrar Vendedor - Tabla de vendedores y relación con clientes
-- ============================================================================

-- Crear tabla de vendedores con UUID
CREATE TABLE IF NOT EXISTS vendedor (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identificacion VARCHAR(32) UNIQUE NOT NULL,
    nombre_completo VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    telefono VARCHAR(32) NOT NULL,
    pais CHAR(2) NOT NULL,
    plan_de_ventas DECIMAL(12,2),
    rol VARCHAR(32) DEFAULT 'seller' NOT NULL,
    activo BOOLEAN DEFAULT TRUE NOT NULL,
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by_user_id VARCHAR(64)
);

-- Índices para búsquedas eficientes
CREATE INDEX IF NOT EXISTS idx_vendedor_identificacion ON vendedor(identificacion);
CREATE INDEX IF NOT EXISTS idx_vendedor_nombre ON vendedor(nombre_completo);
CREATE INDEX IF NOT EXISTS idx_vendedor_email ON vendedor(email);
CREATE INDEX IF NOT EXISTS idx_vendedor_pais ON vendedor(pais);
CREATE INDEX IF NOT EXISTS idx_vendedor_activo ON vendedor(activo);
CREATE INDEX IF NOT EXISTS idx_vendedor_created_at ON vendedor(created_at);

-- Agregar/actualizar columna vendedor_id a UUID en tabla cliente
DO $$ 
BEGIN
    -- Si la columna no existe, crearla como UUID
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'cliente' AND column_name = 'vendedor_id'
    ) THEN
        ALTER TABLE cliente ADD COLUMN vendedor_id UUID;
    -- Si existe pero es VARCHAR, convertir a UUID
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'cliente' 
        AND column_name = 'vendedor_id'
        AND data_type = 'character varying'
    ) THEN
        -- Eliminar FK si existe
        IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_cliente_vendedor') THEN
            ALTER TABLE cliente DROP CONSTRAINT fk_cliente_vendedor;
        END IF;
        -- Cambiar tipo a UUID
        ALTER TABLE cliente ALTER COLUMN vendedor_id TYPE UUID USING vendedor_id::uuid;
    END IF;
END $$;

-- Agregar FK en cliente
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_cliente_vendedor'
    ) THEN
        ALTER TABLE cliente 
        ADD CONSTRAINT fk_cliente_vendedor 
        FOREIGN KEY (vendedor_id) 
        REFERENCES vendedor(id)
        ON DELETE SET NULL;
    END IF;
END $$;

-- Índice en la FK
CREATE INDEX IF NOT EXISTS idx_cliente_vendedor_id ON cliente(vendedor_id);

-- Comentarios para documentación
COMMENT ON TABLE vendedor IS 'Tabla de vendedores del sistema MediSupply';
COMMENT ON COLUMN vendedor.id IS 'ID único del vendedor';
COMMENT ON COLUMN vendedor.identificacion IS 'Cédula, pasaporte o identificación del vendedor (único)';
COMMENT ON COLUMN vendedor.nombre_completo IS 'Nombre completo del vendedor';
COMMENT ON COLUMN vendedor.email IS 'Email del vendedor (único)';
COMMENT ON COLUMN vendedor.telefono IS 'Teléfono del vendedor';
COMMENT ON COLUMN vendedor.pais IS 'Código ISO del país (ej: CO, MX, PE)';
COMMENT ON COLUMN vendedor.plan_de_ventas IS 'Meta de ventas asignada al vendedor';
COMMENT ON COLUMN vendedor.rol IS 'Rol del vendedor (vendedor, supervisor, gerente)';
COMMENT ON COLUMN vendedor.activo IS 'Indica si el vendedor está activo en el sistema';
COMMENT ON COLUMN vendedor.password_hash IS 'Hash de la contraseña para autenticación (opcional)';
COMMENT ON COLUMN vendedor.created_at IS 'Fecha de creación del registro';
COMMENT ON COLUMN vendedor.updated_at IS 'Fecha de última actualización';
COMMENT ON COLUMN vendedor.created_by_user_id IS 'ID del usuario que creó el registro (trazabilidad)';

-- Datos de ejemplo para pruebas (id se genera automáticamente)
INSERT INTO vendedor (identificacion, nombre_completo, email, telefono, pais, plan_de_ventas, rol, activo) VALUES
('1234567890', 'Juan Pérez Gómez', 'juan.perez@medisupply.com', '+57-300-1234567', 'CO', 50000000.00, 'seller', true),
('0987654321', 'María Rodríguez López', 'maria.rodriguez@medisupply.com', '+57-311-7654321', 'CO', 75000000.00, 'seller', true),
('1122334455', 'Carlos Martínez Silva', 'carlos.martinez@medisupply.com', '+52-55-1122334', 'MX', 100000000.00, 'seller', true),
('5544332211', 'Ana García Torres', 'ana.garcia@medisupply.com', '+51-1-9988776', 'PE', 60000000.00, 'seller', true),
('6677889900', 'Luis Fernández Castro', 'luis.fernandez@medisupply.com', '+56-2-6677889', 'CL', 80000000.00, 'seller', true)
ON CONFLICT (identificacion) DO NOTHING;

-- Log de la migración
DO $$
BEGIN
    RAISE NOTICE '✅ Migración 002: Tabla vendedor creada exitosamente';
    RAISE NOTICE '✅ Se agregaron 5 vendedores de ejemplo';
    RAISE NOTICE '✅ FK vendedor_id agregada a tabla cliente';
END $$;

