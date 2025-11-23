-- ============================================================================
-- 002_vendedores.sql
-- HU: Registrar Vendedor - Tabla de vendedores y relación con clientes
-- DATOS REALISTAS POR PAÍS: Colombia, México, Perú, Chile
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
    created_by_user_id VARCHAR(64),
    username VARCHAR(64)
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
COMMENT ON COLUMN vendedor.id IS 'ID único del vendedor (UUID)';
COMMENT ON COLUMN vendedor.identificacion IS 'Cédula, RFC, RUT o identificación del vendedor según país (único)';
COMMENT ON COLUMN vendedor.nombre_completo IS 'Nombre completo del vendedor';
COMMENT ON COLUMN vendedor.email IS 'Email corporativo del vendedor (único)';
COMMENT ON COLUMN vendedor.telefono IS 'Teléfono del vendedor con formato internacional';
COMMENT ON COLUMN vendedor.pais IS 'Código ISO del país (CO, MX, PE, CL)';
COMMENT ON COLUMN vendedor.plan_de_ventas IS 'Meta de ventas mensual asignada al vendedor (en moneda local)';
COMMENT ON COLUMN vendedor.rol IS 'Rol del vendedor (seller, senior_seller, supervisor)';
COMMENT ON COLUMN vendedor.activo IS 'Indica si el vendedor está activo en el sistema';
COMMENT ON COLUMN vendedor.password_hash IS 'Hash de la contraseña para autenticación (opcional)';
COMMENT ON COLUMN vendedor.created_at IS 'Fecha de creación del registro';
COMMENT ON COLUMN vendedor.updated_at IS 'Fecha de última actualización';
COMMENT ON COLUMN vendedor.created_by_user_id IS 'ID del usuario que creó el registro (trazabilidad)';

-- ============================================================================
-- DATOS REALISTAS DE VENDEDORES POR PAÍS
-- ============================================================================
-- 6 vendedores distribuidos en 4 países (Colombia, México, Perú, Chile)
-- Cada vendedor tendrá 2 clientes asignados (total: 12 clientes)
-- ============================================================================

INSERT INTO vendedor (
    id, identificacion, nombre_completo, email, telefono, pais, rol, activo, username,
    rol_vendedor_id, territorio_id, fecha_ingreso, observaciones,
    created_at, updated_at
) VALUES

-- ========== COLOMBIA (2 vendedores) ==========
-- Vendedor 1: Carlos Andrés Mendoza Pérez (Senior Seller - Bogotá Norte)
('11111111-1111-1111-1111-111111111111', 
 '1012456789',  -- Cédula colombiana
 'Carlos Andrés Mendoza Pérez', 
 'carlos.mendoza@medisupply.com.co', 
 '+57-310-245-6789', 
 'CO', 
 'senior_seller', 
 true,
 'cmendoza',
 'r0000001-0001-0001-0001-000000000003',  -- VENDEDOR_SR
 't0000001-0001-0001-0001-000000000001',  -- BOG-NORTE
 '2023-01-15',
 'Vendedor senior con 5 años de experiencia en sector hospitalario',
 CURRENT_TIMESTAMP,
 CURRENT_TIMESTAMP),

-- Vendedor 2: María Fernanda López Torres (Junior Seller - Medellín)
('22222222-2222-2222-2222-222222222222', 
 '1098765432',  -- Cédula colombiana
 'María Fernanda López Torres', 
 'maria.lopez@medisupply.com.co', 
 '+57-320-987-6543', 
 'CO', 
 'seller', 
 true,
 'mlopez',
 'r0000001-0001-0001-0001-000000000004',  -- VENDEDOR_JR
 't0000001-0001-0001-0001-000000000003',  -- MED-CENTRO
 '2024-03-20',
 'Vendedora junior enfocada en farmacias independientes',
 CURRENT_TIMESTAMP,
 CURRENT_TIMESTAMP),

-- ========== MÉXICO (2 vendedores) ==========
-- Vendedor 3: José Luis Hernández García (Senior Seller - CDMX)
('33333333-3333-3333-3333-333333333333', 
 'HEGJ850615ABC',  -- RFC mexicano (persona física)
 'José Luis Hernández García', 
 'jose.hernandez@medisupply.com.mx', 
 '+52-55-1234-5678', 
 'MX', 
 'senior_seller', 
 true,
 'jhernandez',
 'r0000001-0001-0001-0001-000000000003',  -- VENDEDOR_SR
 't0000002-0002-0002-0002-000000000001',  -- CDMX-NORTE
 '2022-06-10',
 'Vendedor senior especializado en cadenas de farmacias',
 CURRENT_TIMESTAMP,
 CURRENT_TIMESTAMP),

-- Vendedor 4: Ana Patricia González Martínez (Junior Seller - Guadalajara)
('44444444-4444-4444-4444-444444444444', 
 'GOMA920310XYZ',  -- RFC mexicano (persona física)
 'Ana Patricia González Martínez', 
 'ana.gonzalez@medisupply.com.mx', 
 '+52-33-9876-5432', 
 'MX', 
 'seller', 
 true,
 'agonzalez',
 'r0000001-0001-0001-0001-000000000004',  -- VENDEDOR_JR
 't0000002-0002-0002-0002-000000000002',  -- GDL-CENTRO
 '2024-02-01',
 'Vendedora junior con experiencia en distribución regional',
 CURRENT_TIMESTAMP,
 CURRENT_TIMESTAMP),

-- ========== PERÚ (1 vendedor) ==========
-- Vendedor 5: Miguel Ángel Torres Valdez (Gerente de Zona - Lima)
('55555555-5555-5555-5555-555555555555', 
 '10234567891',  -- DNI peruano (8 dígitos + complemento)
 'Miguel Ángel Torres Valdez', 
 'miguel.torres@medisupply.com.pe', 
 '+51-1-9876-5432', 
 'PE', 
 'supervisor', 
 true,
 'mtorres',
 'r0000001-0001-0001-0001-000000000002',  -- GERENTE_ZONA
 't0000003-0003-0003-0003-000000000001',  -- LIMA-CENTRO
 '2021-09-01',
 'Gerente de zona con supervisión de 8 vendedores',
 CURRENT_TIMESTAMP,
 CURRENT_TIMESTAMP),

-- ========== CHILE (1 vendedor) ==========
-- Vendedor 6: Carolina Isabel Silva Rojas (Senior Seller - Santiago)
('66666666-6666-6666-6666-666666666666', 
 '18765432-5',  -- RUT chileno (8 dígitos + dígito verificador)
 'Carolina Isabel Silva Rojas', 
 'carolina.silva@medisupply.cl', 
 '+56-2-2345-6789', 
 'CL', 
 'senior_seller', 
 true,
 'csilva',
 'r0000001-0001-0001-0001-000000000003',  -- VENDEDOR_SR
 't0000004-0004-0004-0004-000000000001',  -- SCL-CENTRO
 '2023-04-15',
 'Vendedora senior con expertise en clínicas privadas',
 CURRENT_TIMESTAMP,
 CURRENT_TIMESTAMP)

ON CONFLICT (identificacion) DO NOTHING;

-- Log de la migración
DO $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count FROM vendedor;
    RAISE NOTICE '✅ Migración 002: Tabla vendedor creada exitosamente';
    RAISE NOTICE '✅ Vendedores cargados: % registros', v_count;
    RAISE NOTICE '   - Colombia: 2 vendedores (Carlos Mendoza, María López)';
    RAISE NOTICE '   - México: 2 vendedores (José Hernández, Ana González)';
    RAISE NOTICE '   - Perú: 1 vendedor (Miguel Torres)';
    RAISE NOTICE '   - Chile: 1 vendedor (Carolina Silva)';
    RAISE NOTICE '✅ FK vendedor_id agregada a tabla cliente';
END $$;
