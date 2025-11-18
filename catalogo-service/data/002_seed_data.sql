-- ===================================================================
-- DATOS DE PRUEBA PARA DEMOSTRACIÓN - PRODUCTOS E INVENTARIO
-- ===================================================================

-- Insertar productos de muestra (25 productos para probar paginación)
-- Los IDs ahora son UUID para mayor escalabilidad
INSERT INTO producto (id, codigo, nombre, categoria_id, presentacion, precio_unitario, requisitos_almacenamiento, activo, stock_minimo, stock_critico, requiere_lote, requiere_vencimiento) VALUES
-- Antibióticos
('11111111-1111-1111-1111-000000000001', 'AMX500', 'Amoxicilina 500mg', 'ANTIBIOTICS', 'Cápsula', 1250.00, 'Temperatura ambiente, lugar seco', TRUE, 100, 50, TRUE, TRUE),
('11111111-1111-1111-1111-000000000002', 'CIP250', 'Ciprofloxacina 250mg', 'ANTIBIOTICS', 'Tableta', 850.00, 'Proteger de la luz', TRUE, 100, 50, TRUE, TRUE),
('11111111-1111-1111-1111-000000000003', 'AZI500', 'Azitromicina 500mg', 'ANTIBIOTICS', 'Tableta recubierta', 2100.00, 'Temperatura ambiente', TRUE, 100, 50, TRUE, TRUE),
('11111111-1111-1111-1111-000000000004', 'CLX500', 'Cloxacilina 500mg', 'ANTIBIOTICS', 'Cápsula', 980.00, 'Lugar seco, temperatura ambiente', TRUE, 100, 50, TRUE, TRUE),
('11111111-1111-1111-1111-000000000005', 'CFX100', 'Cefalexina 100mg', 'ANTIBIOTICS', 'Suspensión', 1450.00, 'Refrigerar después de reconstituir', TRUE, 100, 50, TRUE, TRUE),

-- Analgésicos
('22222222-2222-2222-2222-000000000006', 'IBU400', 'Ibuprofeno 400mg', 'ANALGESICS', 'Tableta', 320.00, 'Temperatura ambiente', TRUE, 100, 50, TRUE, TRUE),
('22222222-2222-2222-2222-000000000007', 'ACE500', 'Acetaminofén 500mg', 'ANALGESICS', 'Tableta', 180.00, 'Lugar seco', TRUE, 100, 50, TRUE, TRUE),
('22222222-2222-2222-2222-000000000008', 'ASP100', 'Aspirina 100mg', 'ANALGESICS', 'Tableta', 290.00, 'Proteger de la humedad', TRUE, 100, 50, TRUE, TRUE),
('22222222-2222-2222-2222-000000000009', 'DIC50', 'Diclofenaco 50mg', 'ANALGESICS', 'Tableta recubierta', 450.00, 'Temperatura ambiente', TRUE, 100, 50, TRUE, TRUE),
('22222222-2222-2222-2222-000000000010', 'NAP250', 'Naproxeno 250mg', 'ANALGESICS', 'Tableta', 380.00, 'Lugar seco', TRUE, 100, 50, TRUE, TRUE),

-- Cardiovasculares
('33333333-3333-3333-3333-000000000011', 'ENL10', 'Enalapril 10mg', 'CARDIOVASCULAR', 'Tableta', 520.00, 'Temperatura ambiente', TRUE, 100, 50, TRUE, TRUE),
('33333333-3333-3333-3333-000000000012', 'AML5', 'Amlodipino 5mg', 'CARDIOVASCULAR', 'Tableta', 420.00, 'Proteger de la luz', TRUE, 100, 50, TRUE, TRUE),
('33333333-3333-3333-3333-000000000013', 'ATE50', 'Atenolol 50mg', 'CARDIOVASCULAR', 'Tableta', 350.00, 'Temperatura ambiente', TRUE, 100, 50, TRUE, TRUE),
('33333333-3333-3333-3333-000000000014', 'LSN10', 'Losartán 10mg', 'CARDIOVASCULAR', 'Tableta recubierta', 680.00, 'Lugar seco', TRUE, 100, 50, TRUE, TRUE),
('33333333-3333-3333-3333-000000000015', 'MET500', 'Metformina 500mg', 'CARDIOVASCULAR', 'Tableta', 280.00, 'Temperatura ambiente', TRUE, 100, 50, TRUE, TRUE),

-- Respiratorios
('44444444-4444-4444-4444-000000000016', 'SAL100', 'Salbutamol 100mcg', 'RESPIRATORY', 'Inhalador', 1850.00, 'No exceder 30°C', TRUE, 100, 50, TRUE, TRUE),
('44444444-4444-4444-4444-000000000017', 'LOR10', 'Loratadina 10mg', 'RESPIRATORY', 'Tableta', 320.00, 'Lugar seco', TRUE, 100, 50, TRUE, TRUE),
('44444444-4444-4444-4444-000000000018', 'CET10', 'Cetirizina 10mg', 'RESPIRATORY', 'Tableta', 380.00, 'Temperatura ambiente', TRUE, 100, 50, TRUE, TRUE),
('44444444-4444-4444-4444-000000000019', 'FEX120', 'Fexofenadina 120mg', 'RESPIRATORY', 'Tableta', 450.00, 'Proteger de la humedad', TRUE, 100, 50, TRUE, TRUE),
('44444444-4444-4444-4444-000000000020', 'BUD200', 'Budesonida 200mcg', 'RESPIRATORY', 'Inhalador', 2100.00, 'Refrigerar', TRUE, 100, 50, TRUE, TRUE),

-- Gastrointestinales
('55555555-5555-5555-5555-000000000021', 'OME20', 'Omeprazol 20mg', 'GASTROINTESTINAL', 'Cápsula', 480.00, 'Proteger de la humedad', TRUE, 100, 50, TRUE, TRUE),
('55555555-5555-5555-5555-000000000022', 'RAN150', 'Ranitidina 150mg', 'GASTROINTESTINAL', 'Tableta', 320.00, 'Temperatura ambiente', TRUE, 100, 50, TRUE, TRUE),
('55555555-5555-5555-5555-000000000023', 'DOM10', 'Domperidona 10mg', 'GASTROINTESTINAL', 'Tableta', 290.00, 'Lugar seco', TRUE, 100, 50, TRUE, TRUE),
('55555555-5555-5555-5555-000000000024', 'LOP2', 'Loperamida 2mg', 'GASTROINTESTINAL', 'Cápsula', 380.00, 'Temperatura ambiente', TRUE, 100, 50, TRUE, TRUE),
('55555555-5555-5555-5555-000000000025', 'SMT40', 'Simeticona 40mg', 'GASTROINTESTINAL', 'Tableta masticable', 250.00, 'Lugar seco', TRUE, 100, 50, TRUE, TRUE)
ON CONFLICT (id) DO NOTHING;

-- Insertar inventario para los productos (múltiples países y bodegas para probar filtros)
INSERT INTO inventario (producto_id, pais, bodega_id, lote, cantidad, vence, condiciones) VALUES
-- Amoxicilina en varias ubicaciones
('11111111-1111-1111-1111-000000000001', 'CO', 'BOG_CENTRAL', 'AMX001_2024', 500, '2025-12-31', 'Almacén principal'),
('11111111-1111-1111-1111-000000000001', 'CO', 'MED_SUR', 'AMX002_2024', 300, '2025-11-30', 'Bodega refrigerada'),
('11111111-1111-1111-1111-000000000001', 'MX', 'CDMX_NORTE', 'AMX003_2024', 750, '2026-01-15', 'Centro de distribución'),
('11111111-1111-1111-1111-000000000001', 'PE', 'LIM_CALLAO', 'AMX004_2024', 200, '2025-10-31', 'Almacén secundario'),

-- Ciprofloxacina
('11111111-1111-1111-1111-000000000002', 'CO', 'BOG_CENTRAL', 'CIP001_2024', 400, '2025-09-30', 'Área protegida de luz'),
('11111111-1111-1111-1111-000000000002', 'MX', 'GDL_OESTE', 'CIP002_2024', 600, '2025-08-31', 'Bodega climatizada'),
('11111111-1111-1111-1111-000000000002', 'CL', 'SCL_CENTRO', 'CIP003_2024', 350, '2026-02-28', 'Almacén principal'),

-- Ibuprofeno (popular, muchas existencias)
('22222222-2222-2222-2222-000000000006', 'CO', 'BOG_CENTRAL', 'IBU001_2024', 1000, '2026-06-30', 'Almacén general'),
('22222222-2222-2222-2222-000000000006', 'CO', 'MED_SUR', 'IBU002_2024', 800, '2026-05-31', 'Bodega principal'),
('22222222-2222-2222-2222-000000000006', 'MX', 'CDMX_NORTE', 'IBU003_2024', 1200, '2026-07-31', 'Centro de distribución'),
('22222222-2222-2222-2222-000000000006', 'PE', 'LIM_CALLAO', 'IBU004_2024', 600, '2026-04-30', 'Almacén secundario'),
('22222222-2222-2222-2222-000000000006', 'CL', 'SCL_CENTRO', 'IBU005_2024', 900, '2026-08-31', 'Bodega central'),

-- Acetaminofén (muy popular)
('22222222-2222-2222-2222-000000000007', 'CO', 'BOG_CENTRAL', 'ACE001_2024', 1500, '2025-12-31', 'Almacén general'),
('22222222-2222-2222-2222-000000000007', 'MX', 'CDMX_NORTE', 'ACE002_2024', 2000, '2026-01-31', 'Centro principal'),
('22222222-2222-2222-2222-000000000007', 'PE', 'LIM_CALLAO', 'ACE003_2024', 800, '2025-11-30', 'Bodega local'),

-- Enalapril cardiovascular
('33333333-3333-3333-3333-000000000011', 'CO', 'BOG_CENTRAL', 'ENL001_2024', 300, '2025-10-31', 'Medicamentos especiales'),
('33333333-3333-3333-3333-000000000011', 'MX', 'GDL_OESTE', 'ENL002_2024', 250, '2025-09-30', 'Área cardiovascular'),
('33333333-3333-3333-3333-000000000011', 'CL', 'SCL_CENTRO', 'ENL003_2024', 400, '2026-03-31', 'Bodega especializada'),

-- Salbutamol respiratorio (requiere refrigeración)
('44444444-4444-4444-4444-000000000016', 'CO', 'BOG_CENTRAL', 'SAL001_2024', 150, '2025-08-31', 'Refrigeración controlada'),
('44444444-4444-4444-4444-000000000016', 'MX', 'CDMX_NORTE', 'SAL002_2024', 200, '2025-07-31', 'Cámara fría'),
('44444444-4444-4444-4444-000000000016', 'PE', 'LIM_CALLAO', 'SAL003_2024', 100, '2025-06-30', 'Almacén refrigerado'),

-- Omeprazol gastrointestinal
('55555555-5555-5555-5555-000000000021', 'CO', 'BOG_CENTRAL', 'OME001_2024', 600, '2025-12-31', 'Zona seca'),
('55555555-5555-5555-5555-000000000021', 'MX', 'GDL_OESTE', 'OME002_2024', 450, '2025-11-30', 'Almacén principal'),
('55555555-5555-5555-5555-000000000021', 'CL', 'SCL_CENTRO', 'OME003_2024', 500, '2026-01-31', 'Bodega climatizada'),

-- Agregar inventario para más productos para tener datos suficientes
('11111111-1111-1111-1111-000000000003', 'CO', 'BOG_CENTRAL', 'AZI001_2024', 200, '2025-09-30', 'Almacén antibióticos'),
('11111111-1111-1111-1111-000000000003', 'MX', 'GDL_OESTE', 'AZI002_2024', 150, '2025-08-31', 'Bodega secundaria'),
('11111111-1111-1111-1111-000000000004', 'CO', 'BOG_CENTRAL', 'CLX001_2024', 180, '2025-10-31', 'Almacén antibióticos'),
('11111111-1111-1111-1111-000000000005', 'CO', 'MED_SUR', 'CFX001_2024', 120, '2025-07-31', 'Refrigeración'),
('22222222-2222-2222-2222-000000000008', 'CO', 'MED_SUR', 'ASP001_2024', 800, '2026-03-31', 'Bodega general'),
('22222222-2222-2222-2222-000000000008', 'MX', 'CDMX_NORTE', 'ASP002_2024', 600, '2026-02-28', 'Centro principal'),
('22222222-2222-2222-2222-000000000009', 'CO', 'BOG_CENTRAL', 'DIC001_2024', 400, '2025-12-31', 'Almacén analgésicos'),
('22222222-2222-2222-2222-000000000010', 'MX', 'GDL_OESTE', 'NAP001_2024', 350, '2025-11-30', 'Bodega principal'),
('33333333-3333-3333-3333-000000000012', 'MX', 'CDMX_NORTE', 'AML001_2024', 350, '2025-10-31', 'Área cardiovascular'),
('33333333-3333-3333-3333-000000000012', 'CO', 'BOG_CENTRAL', 'AML002_2024', 280, '2025-09-30', 'Medicamentos cardiovasculares'),
('33333333-3333-3333-3333-000000000013', 'CO', 'BOG_CENTRAL', 'ATE001_2024', 300, '2025-11-30', 'Área cardiovascular'),
('33333333-3333-3333-3333-000000000014', 'MX', 'CDMX_NORTE', 'LSN001_2024', 400, '2026-01-31', 'Centro principal'),
('33333333-3333-3333-3333-000000000015', 'CO', 'MED_SUR', 'MET001_2024', 900, '2025-10-31', 'Bodega diabetes'),
('33333333-3333-3333-3333-000000000015', 'PE', 'LIM_CALLAO', 'MET002_2024', 700, '2025-09-30', 'Almacén medicamentos'),
('44444444-4444-4444-4444-000000000017', 'PE', 'LIM_CALLAO', 'LOR001_2024', 600, '2026-02-28', 'Medicamentos respiratorios'),
('44444444-4444-4444-4444-000000000017', 'CO', 'BOG_CENTRAL', 'LOR002_2024', 450, '2026-01-31', 'Área respiratoria'),
('44444444-4444-4444-4444-000000000018', 'MX', 'GDL_OESTE', 'CET001_2024', 500, '2025-12-31', 'Bodega principal'),
('44444444-4444-4444-4444-000000000019', 'CL', 'SCL_CENTRO', 'FEX001_2024', 350, '2026-03-31', 'Almacén respiratorios'),
('44444444-4444-4444-4444-000000000020', 'CO', 'BOG_CENTRAL', 'BUD001_2024', 100, '2025-06-30', 'Refrigeración controlada'),
('55555555-5555-5555-5555-000000000022', 'CL', 'SCL_CENTRO', 'RAN001_2024', 400, '2025-11-30', 'Zona gastrointestinal'),
('55555555-5555-5555-5555-000000000022', 'CO', 'BOG_CENTRAL', 'RAN002_2024', 350, '2025-10-31', 'Almacén digestivos'),
('55555555-5555-5555-5555-000000000023', 'MX', 'CDMX_NORTE', 'DOM001_2024', 300, '2025-12-31', 'Bodega medicamentos'),
('55555555-5555-5555-5555-000000000024', 'PE', 'LIM_CALLAO', 'LOP001_2024', 250, '2026-02-28', 'Área gastrointestinal'),
('55555555-5555-5555-5555-000000000025', 'CO', 'MED_SUR', 'SMT001_2024', 800, '2026-04-30', 'Almacén general')
ON CONFLICT (producto_id, pais, bodega_id, lote) DO NOTHING;

