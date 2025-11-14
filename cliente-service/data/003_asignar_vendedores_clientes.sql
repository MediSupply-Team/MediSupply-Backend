-- ====================================================
-- 003_asignar_vendedores_clientes.sql
-- Asigna vendedores a los clientes existentes
-- ====================================================
-- Este archivo se ejecuta después de que clientes y vendedores han sido creados
-- Asigna vendedores a clientes que no tengan vendedor_id asignado

DO $$
DECLARE
    vendedor_juan_id UUID;
    vendedor_maria_id UUID;
    vendedor_carlos_id UUID;
BEGIN
    -- Obtener IDs de vendedores existentes
    SELECT id INTO vendedor_juan_id 
    FROM vendedor 
    WHERE identificacion = '1234567890' 
    LIMIT 1;
    
    SELECT id INTO vendedor_maria_id 
    FROM vendedor 
    WHERE identificacion = '0987654321' 
    LIMIT 1;
    
    SELECT id INTO vendedor_carlos_id 
    FROM vendedor 
    WHERE identificacion = '1122334455' 
    LIMIT 1;
    
    -- Si no existen vendedores, usar el primer vendedor disponible
    IF vendedor_juan_id IS NULL THEN
        SELECT id INTO vendedor_juan_id FROM vendedor WHERE activo = true LIMIT 1;
    END IF;
    
    IF vendedor_maria_id IS NULL THEN
        SELECT id INTO vendedor_maria_id FROM vendedor WHERE activo = true OFFSET 1 LIMIT 1;
    END IF;
    
    IF vendedor_carlos_id IS NULL THEN
        SELECT id INTO vendedor_carlos_id FROM vendedor WHERE activo = true OFFSET 2 LIMIT 1;
    END IF;
    
    -- Asignar vendedores a clientes si aún no tienen vendedor asignado
    -- Farmacia San José -> Juan Pérez
    UPDATE cliente 
    SET vendedor_id = vendedor_juan_id, updated_at = NOW()
    WHERE nit = '900123456-7' AND vendedor_id IS NULL;
    
    -- Droguería El Buen Pastor -> María Rodríguez
    UPDATE cliente 
    SET vendedor_id = vendedor_maria_id, updated_at = NOW()
    WHERE nit = '800987654-3' AND vendedor_id IS NULL;
    
    -- Farmatodo Zona Norte -> Carlos Martínez
    UPDATE cliente 
    SET vendedor_id = vendedor_carlos_id, updated_at = NOW()
    WHERE nit = '700456789-1' AND vendedor_id IS NULL;
    
    -- Centro Médico Salud Total -> Juan Pérez
    UPDATE cliente 
    SET vendedor_id = vendedor_juan_id, updated_at = NOW()
    WHERE nit = '600345678-9' AND vendedor_id IS NULL;
    
    -- Farmacia Popular -> María Rodríguez
    UPDATE cliente 
    SET vendedor_id = vendedor_maria_id, updated_at = NOW()
    WHERE nit = '500234567-5' AND vendedor_id IS NULL;
    
    -- Asignar vendedores a cualquier cliente sin vendedor_id
    -- Distribuir entre los vendedores disponibles
    UPDATE cliente c
    SET vendedor_id = (
        SELECT id FROM vendedor 
        WHERE activo = true 
        ORDER BY random() 
        LIMIT 1
    ),
    updated_at = NOW()
    WHERE vendedor_id IS NULL;
    
    RAISE NOTICE '✅ Vendedores asignados a clientes existentes';
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '⚠️  Error asignando vendedores: %', SQLERRM;
END $$;

-- Verificar resultado
DO $$
DECLARE
    total_clientes INTEGER;
    clientes_con_vendedor INTEGER;
    clientes_sin_vendedor INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_clientes FROM cliente;
    SELECT COUNT(*) INTO clientes_con_vendedor FROM cliente WHERE vendedor_id IS NOT NULL;
    SELECT COUNT(*) INTO clientes_sin_vendedor FROM cliente WHERE vendedor_id IS NULL;
    
    RAISE NOTICE '';
    RAISE NOTICE '📊 Resumen de asignación:';
    RAISE NOTICE '   Total clientes: %', total_clientes;
    RAISE NOTICE '   Con vendedor asignado: %', clientes_con_vendedor;
    RAISE NOTICE '   Sin vendedor asignado: %', clientes_sin_vendedor;
    RAISE NOTICE '';
END $$;

