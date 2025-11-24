-- ═══════════════════════════════════════════════════════════════════════════════
-- SCRIPT PARA VERIFICAR DATOS PRECARGADOS EN AWS
-- Ejecutar este script en cada base de datos (cliente_db y catalogo_db)
-- ═══════════════════════════════════════════════════════════════════════════════

-- ============================================================================
-- PARA CLIENTE_DB
-- ============================================================================

-- 1. Verificar vendedores hardcodeados
SELECT '═══ VENDEDORES HARDCODEADOS (3) ═══' AS seccion;
SELECT 
    id,
    nombre_completo,
    email,
    telefono,
    activo
FROM vendedor
WHERE id::text IN (
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222222',
    '33333333-3333-3333-3333-333333333333'
)
ORDER BY id;

-- 2. Contar todos los vendedores
SELECT '═══ TOTAL VENDEDORES ═══' AS seccion;
SELECT COUNT(*) as total_vendedores FROM vendedor;

-- 3. Verificar clientes hardcodeados
SELECT '═══ CLIENTES HARDCODEADOS (6) ═══' AS seccion;
SELECT 
    id,
    nombre,
    codigo_unico,
    nit,
    vendedor_id,
    activo
FROM cliente
WHERE id::text LIKE 'aaaaaaaa%' 
   OR id::text LIKE 'bbbbbbbb%' 
   OR id::text LIKE 'cccccccc%'
ORDER BY vendedor_id, id;

-- 4. Contar todos los clientes
SELECT '═══ TOTAL CLIENTES ═══' AS seccion;
SELECT COUNT(*) as total_clientes FROM cliente;

-- 5. Verificar distribución de clientes por vendedor
SELECT '═══ CLIENTES POR VENDEDOR ═══' AS seccion;
SELECT 
    v.nombre_completo as vendedor,
    COUNT(c.id) as num_clientes,
    ARRAY_AGG(c.nombre ORDER BY c.nombre) as clientes
FROM vendedor v
LEFT JOIN cliente c ON c.vendedor_id = v.id
WHERE v.id::text IN (
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222222',
    '33333333-3333-3333-3333-333333333333'
)
GROUP BY v.id, v.nombre_completo
ORDER BY v.nombre_completo;

-- 6. Verificar clientes sin vendedor
SELECT '═══ CLIENTES SIN VENDEDOR ═══' AS seccion;
SELECT COUNT(*) as clientes_sin_vendedor 
FROM cliente 
WHERE vendedor_id IS NULL;


-- ============================================================================
-- PARA CATALOGO_DB
-- ============================================================================

-- 7. Verificar productos hardcodeados
SELECT '═══ PRODUCTOS HARDCODEADOS (20) ═══' AS seccion;
SELECT 
    id,
    codigo,
    nombre,
    categoria_id,
    precio_unitario,
    activo
FROM producto
WHERE id::text LIKE '11111111-1111-1111-1111-%'
ORDER BY codigo
LIMIT 10;

-- 8. Contar todos los productos
SELECT '═══ TOTAL PRODUCTOS ═══' AS seccion;
SELECT COUNT(*) as total_productos FROM producto;

-- 9. Verificar inventarios
SELECT '═══ INVENTARIOS ═══' AS seccion;
SELECT 
    COUNT(*) as total_inventarios,
    SUM(cantidad_disponible) as cantidad_total,
    COUNT(DISTINCT producto_id) as productos_con_inventario
FROM inventario;

-- 10. Verificar movimientos de inventario
SELECT '═══ MOVIMIENTOS DE INVENTARIO ═══' AS seccion;
SELECT 
    COUNT(*) as total_movimientos,
    MIN(fecha_movimiento) as primer_movimiento,
    MAX(fecha_movimiento) as ultimo_movimiento
FROM movimiento_inventario;

-- 11. Verificar productos por categoría
SELECT '═══ PRODUCTOS POR CATEGORÍA ═══' AS seccion;
SELECT 
    categoria_id,
    COUNT(*) as num_productos,
    AVG(precio_unitario) as precio_promedio
FROM producto
WHERE activo = true
GROUP BY categoria_id
ORDER BY num_productos DESC;

-- 12. Verificar alertas de inventario
SELECT '═══ ALERTAS DE INVENTARIO ═══' AS seccion;
SELECT 
    COUNT(*) as total_alertas,
    COUNT(CASE WHEN activa = true THEN 1 END) as alertas_activas,
    COUNT(CASE WHEN tipo_alerta = 'STOCK_BAJO' THEN 1 END) as stock_bajo,
    COUNT(CASE WHEN tipo_alerta = 'STOCK_CRITICO' THEN 1 END) as stock_critico
FROM alerta_inventario;


-- ═══════════════════════════════════════════════════════════════════════════════
-- RESUMEN DE DATOS ESPERADOS
-- ═══════════════════════════════════════════════════════════════════════════════
/*
RESULTADOS ESPERADOS:

CLIENTE_DB:
✅ 3-5 vendedores (3 hardcoded + extras opcionales)
✅ 6+ clientes (6 hardcoded + los que se creen)
✅ Cada vendedor hardcodeado debe tener 2 clientes asignados
✅ Los IDs deben coincidir con los hardcodeados

CATALOGO_DB:
✅ 20+ productos (20 hardcoded + extras opcionales)
✅ Inventarios para todos los productos
✅ Movimientos de inventario registrados
✅ Alertas de inventario configuradas

Si alguno de estos no aparece:
1. Verifica los logs del contenedor en CloudWatch
2. Verifica que DATABASE_URL esté correctamente configurada
3. Ejecuta manualmente el script de población
4. Reinicia el servicio en ECS
*/

