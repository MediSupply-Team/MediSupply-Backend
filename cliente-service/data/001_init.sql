-- Inicialización de base de datos para cliente-service
-- HU07: Consultar Cliente - Estructura y datos iniciales

-- ====================================================
-- CREACIÓN DE TABLAS
-- ====================================================

-- Tabla principal de clientes
CREATE TABLE IF NOT EXISTS cliente (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nit VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    codigo_unico VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(255),  -- Hash de contraseña para autenticación
    email VARCHAR(255),
    telefono VARCHAR(50),
    direccion TEXT,
    ciudad VARCHAR(100),
    pais CHAR(2) DEFAULT 'CO',
    vendedor_id UUID,  -- FK a vendedor (se agrega constraint después)
    rol VARCHAR(32) DEFAULT 'cliente' NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================
-- MIGRACIONES (Para tablas existentes)
-- ====================================================

-- Agregar columna password_hash si no existe (para bases de datos existentes)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'cliente' 
        AND column_name = 'password_hash'
    ) THEN
        ALTER TABLE cliente 
        ADD COLUMN password_hash VARCHAR(255) NULL;
        RAISE NOTICE '✅ Columna password_hash agregada a tabla cliente';
    END IF;
END $$;

-- Tabla de histórico de compras
CREATE TABLE IF NOT EXISTS compra_historico (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id UUID NOT NULL REFERENCES cliente(id),
    orden_id VARCHAR(64) NOT NULL,
    estado_orden VARCHAR(50) DEFAULT 'completada',
    producto_id VARCHAR(64) NOT NULL,
    producto_nombre VARCHAR(255) NOT NULL,
    categoria_producto VARCHAR(100),
    cantidad INTEGER NOT NULL,
    precio_unitario DECIMAL(12,2) NOT NULL,
    precio_total DECIMAL(12,2) NOT NULL,
    fecha_compra DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de devoluciones
CREATE TABLE IF NOT EXISTS devolucion_historico (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id UUID NOT NULL REFERENCES cliente(id),
    compra_id UUID,
    compra_orden_id VARCHAR(64),
    producto_id VARCHAR(64) NOT NULL,
    producto_nombre VARCHAR(255) NOT NULL,
    cantidad_devuelta INTEGER NOT NULL,
    motivo TEXT NOT NULL,
    categoria_motivo VARCHAR(100),
    estado VARCHAR(50) DEFAULT 'procesada',
    fecha_devolucion DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de log de consultas (trazabilidad)
CREATE TABLE IF NOT EXISTS consulta_cliente_log (
    id BIGSERIAL PRIMARY KEY,
    vendedor_id UUID,
    cliente_id UUID,
    tipo_consulta VARCHAR(100) NOT NULL,
    tipo_busqueda VARCHAR(50),
    termino_busqueda VARCHAR(255),
    took_ms INTEGER,
    metadatos JSONB,
    fecha_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de productos preferidos (calculada)
CREATE TABLE IF NOT EXISTS producto_preferido (
    id BIGSERIAL PRIMARY KEY,
    cliente_id UUID NOT NULL REFERENCES cliente(id),
    producto_id VARCHAR(64) NOT NULL,
    producto_nombre VARCHAR(255) NOT NULL,
    categoria_producto VARCHAR(100),
    frecuencia_compra INTEGER DEFAULT 1,
    cantidad_total INTEGER DEFAULT 0,
    cantidad_promedio DECIMAL(8,2) DEFAULT 0,
    ultima_compra DATE,
    meses_desde_ultima INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de estadísticas de cliente
CREATE TABLE IF NOT EXISTS estadistica_cliente (
    id BIGSERIAL PRIMARY KEY,
    cliente_id UUID NOT NULL REFERENCES cliente(id),
    total_compras INTEGER DEFAULT 0,
    total_productos_unicos INTEGER DEFAULT 0,
    total_devoluciones INTEGER DEFAULT 0,
    valor_total_compras DECIMAL(15,2) DEFAULT 0,
    promedio_orden DECIMAL(12,2) DEFAULT 0,
    frecuencia_compra_mensual DECIMAL(8,2) DEFAULT 0,
    tasa_devolucion DECIMAL(5,2) DEFAULT 0,
    cliente_desde DATE,
    ultima_compra DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_cliente_nit ON cliente(nit);
CREATE INDEX IF NOT EXISTS idx_cliente_codigo ON cliente(codigo_unico);
CREATE INDEX IF NOT EXISTS idx_cliente_nombre ON cliente(nombre);
CREATE INDEX IF NOT EXISTS idx_cliente_vendedor_id ON cliente(vendedor_id);
CREATE INDEX IF NOT EXISTS idx_compra_cliente ON compra_historico(cliente_id);
CREATE INDEX IF NOT EXISTS idx_compra_fecha ON compra_historico(fecha_compra);
CREATE INDEX IF NOT EXISTS idx_compra_producto ON compra_historico(producto_id);
CREATE INDEX IF NOT EXISTS idx_devolucion_cliente ON devolucion_historico(cliente_id);
CREATE INDEX IF NOT EXISTS idx_devolucion_fecha ON devolucion_historico(fecha_devolucion);
CREATE INDEX IF NOT EXISTS idx_consulta_vendedor ON consulta_cliente_log(vendedor_id);
CREATE INDEX IF NOT EXISTS idx_consulta_cliente ON consulta_cliente_log(cliente_id);
CREATE INDEX IF NOT EXISTS idx_consulta_fecha ON consulta_cliente_log(fecha_consulta);

-- ====================================================
-- DATOS REALISTAS DE CLIENTES POR PAÍS
-- ====================================================
-- 12 clientes distribuidos en 4 países (2 clientes por cada vendedor)
-- Los IDs y vendedor_id están HARDCODEADOS con UUID fijo
-- 
-- VENDEDORES Y SUS CLIENTES:
-- Vendedor 1 (Carlos Mendoza - CO): UUID = 11111111-1111-1111-1111-111111111111
-- Vendedor 2 (María López - CO): UUID = 22222222-2222-2222-2222-222222222222
-- Vendedor 3 (José Hernández - MX): UUID = 33333333-3333-3333-3333-333333333333
-- Vendedor 4 (Ana González - MX): UUID = 44444444-4444-4444-4444-444444444444
-- Vendedor 5 (Miguel Torres - PE): UUID = 55555555-5555-5555-5555-555555555555
-- Vendedor 6 (Carolina Silva - CL): UUID = 66666666-6666-6666-6666-666666666666

INSERT INTO cliente (id, nit, nombre, codigo_unico, email, telefono, direccion, ciudad, pais, vendedor_id, rol, activo, created_at) VALUES

-- ========== COLOMBIA - Vendedor 1: Carlos Mendoza ==========
('c1111111-1111-1111-1111-000000000001', 
 '900345678-9',  -- NIT empresa colombiana
 'Farmacias San Rafael Ltda', 
 'FSR001', 
 'compras@farmaciassanrafael.com.co', 
 '+57-1-745-2890', 
 'Calle 127 #15-45, Centro Empresarial', 
 'Bogotá', 
 'CO', 
 '11111111-1111-1111-1111-111111111111', 
 'cliente', 
 true, 
 NOW()),

('c1111111-1111-1111-1111-000000000002', 
 '860234567-1',  -- NIT empresa colombiana
 'Droguería y Perfumería La Rebaja SA', 
 'DLR002', 
 'pedidos@larebaja.com.co', 
 '+57-1-654-3210', 
 'Carrera 7 #32-16, Local 102', 
 'Bogotá', 
 'CO', 
 '11111111-1111-1111-1111-111111111111', 
 'cliente', 
 true, 
 NOW()),

-- ========== COLOMBIA - Vendedor 2: María López ==========
('c2222222-2222-2222-2222-000000000003', 
 '890567890-2',  -- NIT empresa colombiana
 'Centro Médico del Norte SAS', 
 'CMN003', 
 'suministros@centromediconorte.com', 
 '+57-5-362-8945', 
 'Avenida Circunvalar #98-45', 
 'Barranquilla', 
 'CO', 
 '22222222-2222-2222-2222-222222222222', 
 'cliente', 
 true, 
 NOW()),

('c2222222-2222-2222-2222-000000000004', 
 '805123456-7',  -- NIT empresa colombiana
 'Farmacias Audifarma Medellín', 
 'FAM004', 
 'gerencia@audifarma-med.com', 
 '+57-4-444-5566', 
 'Carrera 43A #34-95', 
 'Medellín', 
 'CO', 
 '22222222-2222-2222-2222-222222222222', 
 'cliente', 
 true, 
 NOW()),

-- ========== MÉXICO - Vendedor 3: José Hernández ==========
('c3333333-3333-3333-3333-000000000005', 
 'FSA850615GT8',  -- RFC empresa mexicana
 'Farmacias Similares del Ahorro SA de CV', 
 'FSA005', 
 'compras@farmaciasimilares.com.mx', 
 '+52-55-5678-9012', 
 'Av. Insurgentes Sur 1234, Col. Del Valle', 
 'Ciudad de México', 
 'MX', 
 '33333333-3333-3333-3333-333333333333', 
 'cliente', 
 true, 
 NOW()),

('c3333333-3333-3333-3333-000000000006', 
 'GME920310MX5',  -- RFC empresa mexicana
 'Grupo Médico Especializado SA de CV', 
 'GME006', 
 'proveeduria@grupomedico.mx', 
 '+52-55-8765-4321', 
 'Paseo de la Reforma 456, Polanco', 
 'Ciudad de México', 
 'MX', 
 '33333333-3333-3333-3333-333333333333', 
 'cliente', 
 true, 
 NOW()),

-- ========== MÉXICO - Vendedor 4: Ana González ==========
('c4444444-4444-4444-4444-000000000007', 
 'FGU780925JA3',  -- RFC empresa mexicana
 'Farmacias Guadalajara SA de CV', 
 'FGU007', 
 'adquisiciones@farmaciasguadalajara.com', 
 '+52-33-3145-6789', 
 'Av. López Mateos Sur 2345', 
 'Guadalajara', 
 'MX', 
 '44444444-4444-4444-4444-444444444444', 
 'cliente', 
 true, 
 NOW()),

('c4444444-4444-4444-4444-000000000008', 
 'DBI881215MX2',  -- RFC empresa mexicana
 'Distribuidora Bio-Médica SA de CV', 
 'DBM008', 
 'ventas@biomedicamx.com', 
 '+52-33-3987-6543', 
 'Av. Américas 1456, Piso 3', 
 'Guadalajara', 
 'MX', 
 '44444444-4444-4444-4444-444444444444', 
 'cliente', 
 true, 
 NOW()),

-- ========== PERÚ - Vendedor 5: Miguel Torres ==========
('c5555555-5555-5555-5555-000000000009', 
 '20456789012',  -- RUC empresa peruana (11 dígitos)
 'Boticas y Salud SAC', 
 'BYS009', 
 'logistica@boticasysalud.pe', 
 '+51-1-234-5678', 
 'Av. Javier Prado Este 4567', 
 'Lima', 
 'PE', 
 '55555555-5555-5555-5555-555555555555', 
 'cliente', 
 true, 
 NOW()),

('c5555555-5555-5555-5555-000000000010', 
 '20567890123',  -- RUC empresa peruana
 'Inkafarma SA', 
 'INK010', 
 'compras@inkafarma.pe', 
 '+51-1-987-6543', 
 'Av. Arequipa 2890, Lince', 
 'Lima', 
 'PE', 
 '55555555-5555-5555-5555-555555555555', 
 'cliente', 
 true, 
 NOW()),

-- ========== CHILE - Vendedor 6: Carolina Silva ==========
('c6666666-6666-6666-6666-000000000011', 
 '76234567-8',  -- RUT empresa chilena (8 dígitos + verificador)
 'Farmacias Cruz Verde SA', 
 'FCV011', 
 'abastecimiento@cruzverde.cl', 
 '+56-2-2890-4567', 
 'Av. Libertador Bernardo O Higgins 2345', 
 'Santiago', 
 'CL', 
 '66666666-6666-6666-6666-666666666666', 
 'cliente', 
 true, 
 NOW()),

('c6666666-6666-6666-6666-000000000012', 
 '78567890-2',  -- RUT empresa chilena
 'Salcobrand SA', 
 'SCB012', 
 'proveedores@salcobrand.cl', 
 '+56-2-2765-4321', 
 'Av. Apoquindo 3456, Las Condes', 
 'Santiago', 
 'CL', 
 '66666666-6666-6666-6666-666666666666', 
 'cliente', 
 true, 
 NOW())

ON CONFLICT (nit) DO NOTHING;

-- ====================================================
-- HISTÓRICO DE COMPRAS DE EJEMPLO
-- ====================================================
-- NOTA: Comentado porque los IDs ahora son UUID autogenerados
-- No se pueden usar IDs fijos tipo 'COMP001' o 'CLI001'
-- Los datos de ejemplo deberían insertarse dinámicamente con referencias a los UUIDs generados

/*
INSERT INTO compra_historico (id, cliente_id, orden_id, estado_orden, producto_id, producto_nombre, categoria_producto, cantidad, precio_unitario, precio_total, fecha_compra, created_at) VALUES
-- Cliente CLI001 - Farmacia San José (comprador frecuente)
('COMP001', 'CLI001', 'ORD2024001', 'completada', 'ACETA500', 'Acetaminofén 500mg x 20 tabletas', 'Analgésicos', 50, 1200.00, 60000.00, '2024-09-15', NOW()),
('COMP002', 'CLI001', 'ORD2024002', 'completada', 'IBUPRO400', 'Ibuprofeno 400mg x 20 cápsulas', 'Antiinflamatorios', 30, 1800.00, 54000.00, '2024-09-10', NOW()),
('COMP003', 'CLI001', 'ORD2024003', 'completada', 'ACETA500', 'Acetaminofén 500mg x 20 tabletas', 'Analgésicos', 75, 1200.00, 90000.00, '2024-08-20', NOW()),
('COMP004', 'CLI001', 'ORD2024004', 'completada', 'OMEPRA20', 'Omeprazol 20mg x 14 cápsulas', 'Gastroprotectores', 20, 3500.00, 70000.00, '2024-08-15', NOW()),
('COMP005', 'CLI001', 'ORD2024005', 'completada', 'ACETA500', 'Acetaminofén 500mg x 20 tabletas', 'Analgésicos', 100, 1200.00, 120000.00, '2024-07-30', NOW()),
('COMP006', 'CLI001', 'ORD2024006', 'completada', 'LORATA10', 'Loratadina 10mg x 10 tabletas', 'Antihistamínicos', 25, 800.00, 20000.00, '2024-07-15', NOW()),

-- Cliente CLI002 - Droguería El Buen Pastor
('COMP007', 'CLI002', 'ORD2024007', 'completada', 'IBUPRO400', 'Ibuprofeno 400mg x 20 cápsulas', 'Antiinflamatorios', 40, 1800.00, 72000.00, '2024-09-12', NOW()),
('COMP008', 'CLI002', 'ORD2024008', 'completada', 'DIPIRO500', 'Dipirona 500mg x 20 tabletas', 'Analgésicos', 60, 900.00, 54000.00, '2024-09-05', NOW()),
('COMP009', 'CLI002', 'ORD2024009', 'completada', 'AMOXIC500', 'Amoxicilina 500mg x 21 cápsulas', 'Antibióticos', 15, 4200.00, 63000.00, '2024-08-25', NOW()),

-- Cliente CLI003 - Farmatodo Zona Norte
('COMP010', 'CLI003', 'ORD2024010', 'completada', 'ACETA500', 'Acetaminofén 500mg x 20 tabletas', 'Analgésicos', 80, 1200.00, 96000.00, '2024-09-08', NOW()),
('COMP011', 'CLI003', 'ORD2024011', 'completada', 'VITAMI500', 'Complejo B x 30 tabletas', 'Vitaminas', 35, 2500.00, 87500.00, '2024-08-30', NOW()),

-- Cliente CLI004 - Centro Médico Salud Total
('COMP012', 'CLI004', 'ORD2024012', 'completada', 'OMEPRA20', 'Omeprazol 20mg x 14 cápsulas', 'Gastroprotectores', 50, 3500.00, 175000.00, '2024-09-01', NOW()),
('COMP013', 'CLI004', 'ORD2024013', 'completada', 'LOSART50', 'Losartán 50mg x 30 tabletas', 'Antihipertensivos', 25, 2800.00, 70000.00, '2024-08-18', NOW()),

-- Cliente CLI005 - Farmacia Popular
('COMP014', 'CLI005', 'ORD2024014', 'completada', 'ACETA500', 'Acetaminofén 500mg x 20 tabletas', 'Analgésicos', 40, 1200.00, 48000.00, '2024-08-10', NOW()),
('COMP015', 'CLI005', 'ORD2024015', 'completada', 'DIPIRO500', 'Dipirona 500mg x 20 tabletas', 'Analgésicos', 30, 900.00, 27000.00, '2024-07-25', NOW());
*/

-- ====================================================
-- DEVOLUCIONES DE EJEMPLO
-- ====================================================
-- NOTA: Comentado - usar UUIDs dinámicos

/*
INSERT INTO devolucion_historico (id, cliente_id, compra_id, compra_orden_id, producto_id, producto_nombre, cantidad_devuelta, motivo, categoria_motivo, estado, fecha_devolucion, created_at) VALUES
-- Devoluciones de CLI001
('DEV001', 'CLI001', 'COMP002', 'ORD2024002', 'IBUPRO400', 'Ibuprofeno 400mg x 20 cápsulas', 5, 'Producto próximo a vencer - fecha de vencimiento muy cercana', 'vencimiento', 'procesada', '2024-09-18', NOW()),
('DEV002', 'CLI001', 'COMP004', 'ORD2024004', 'OMEPRA20', 'Omeprazol 20mg x 14 cápsulas', 3, 'Cápsulas con defecto en el blister - empaque dañado', 'calidad', 'procesada', '2024-08-22', NOW()),

-- Devoluciones de CLI002
('DEV003', 'CLI002', 'COMP009', 'ORD2024009', 'AMOXIC500', 'Amoxicilina 500mg x 21 cápsulas', 2, 'Error en el pedido - cliente solicitó presentación de 250mg', 'error_pedido', 'procesada', '2024-08-28', NOW()),

-- Devoluciones de CLI003
('DEV004', 'CLI003', 'COMP010', 'ORD2024010', 'ACETA500', 'Acetaminofén 500mg x 20 tabletas', 8, 'Producto vencido al momento de la entrega', 'vencimiento', 'procesada', '2024-09-12', NOW());
*/

-- ====================================================
-- LOGS DE CONSULTA DE EJEMPLO (para trazabilidad)
-- ====================================================
-- NOTA: Comentado - usar UUIDs dinámicos

/*
INSERT INTO consulta_cliente_log (vendedor_id, cliente_id, tipo_consulta, tipo_busqueda, termino_busqueda, took_ms, metadatos, fecha_consulta) VALUES
-- Consultas del vendedor VEN001
('VEN001', 'CLI001', 'busqueda_cliente', 'nit', '900123456-7', 850, '{"resultado_encontrado": true, "cliente_nombre": "Farmacia San José"}', '2024-10-10 10:30:00'),
('VEN001', 'CLI001', 'historico_completo', null, null, 1200, '{"limite_meses": 12, "total_compras": 6, "total_devoluciones": 2}', '2024-10-10 10:31:00'),
('VEN001', 'CLI002', 'busqueda_cliente', 'nombre', 'Droguería El Buen Pastor', 650, '{"resultado_encontrado": true, "cliente_nit": "800987654-3"}', '2024-10-10 11:15:00'),

-- Consultas del vendedor VEN002
('VEN002', 'CLI003', 'busqueda_cliente', 'codigo', 'FZN003', 400, '{"resultado_encontrado": true, "cliente_nombre": "Farmatodo Zona Norte"}', '2024-10-10 14:20:00'),
('VEN002', 'CLI003', 'historico_completo', null, null, 980, '{"limite_meses": 6, "total_compras": 2, "total_devoluciones": 1}', '2024-10-10 14:21:00');
*/

-- ====================================================
-- COMENTARIOS EXPLICATIVOS
-- ====================================================

-- Este script de datos de ejemplo incluye:
--
-- 1. CLIENTES DIVERSOS:
--    - Farmacias independientes
--    - Cadenas de droguerías  
--    - Centros médicos
--    - Diferentes ciudades de Colombia
--
-- 2. HISTÓRICO DE COMPRAS REALISTA:
--    - Productos farmacéuticos comunes
--    - Diferentes categorías (analgésicos, antibióticos, etc.)
--    - Cantidades y precios realistas
--    - Fechas distribuidas en los últimos meses
--    - Productos preferidos (Acetaminofén aparece frecuentemente)
--
-- 3. DEVOLUCIONES CON MOTIVOS REALES:
--    - Productos vencidos
--    - Defectos de calidad
--    - Errores en pedidos
--    - Categorías de motivos para análisis
--
-- 4. TRAZABILIDAD DE CONSULTAS:
--    - Logs de diferentes vendedores
--    - Diferentes tipos de búsqueda (NIT, nombre, código)
--    - Métricas de performance (tiempo de respuesta)
--    - Cumplimiento de SLA
--
-- Estos datos permiten probar todos los criterios de aceptación:
-- ✅ Búsqueda por NIT, nombre o código único
-- ✅ Histórico de compras con productos, cantidades, fechas  
-- ✅ Productos preferidos y frecuencia de compra
-- ✅ Devoluciones con motivos
-- ✅ Performance ≤ 2 segundos (datos en logs)
-- ✅ Trazabilidad registrada