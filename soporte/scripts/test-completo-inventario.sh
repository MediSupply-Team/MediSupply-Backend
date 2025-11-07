#!/bin/bash

# Script completo para probar las nuevas funcionalidades de inventario
# Levanta servicios, ejecuta pruebas y limpia

set -e  # Salir si hay errores

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║       🧪 Pruebas Completas: Inventario y Productos en Bodega     ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# PASO 1: Levantar servicios necesarios
# ============================================================================

echo -e "${YELLOW}📦 PASO 1: Levantando servicios con Docker Compose${NC}"
echo "────────────────────────────────────────────────────────────────────"
echo ""

# Exportar perfil para levantar los servicios
export APP_PROFILE=dev

echo "Levantando servicios: catalog-service, bff-venta y sus dependencias..."
docker-compose up -d redis catalog-db catalog-service bff-venta

echo ""
echo -e "${GREEN}✅ Servicios levantados${NC}"
echo ""

# ============================================================================
# PASO 2: Esperar a que los servicios estén listos
# ============================================================================

echo -e "${YELLOW}⏳ PASO 2: Esperando a que los servicios estén listos${NC}"
echo "────────────────────────────────────────────────────────────────────"
echo ""

# Función para verificar si un servicio está listo
check_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    
    echo -n "Esperando $name..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e " ${RED}✗ (timeout)${NC}"
    return 1
}

# Esperar a que catalog-service esté listo
check_service "http://localhost:3001/health" "catalog-service (puerto 3001)"

# Esperar a que bff-venta esté listo
check_service "http://localhost:8001/api/v1/inventory/health" "bff-venta (puerto 8001)"

echo ""
echo -e "${GREEN}✅ Todos los servicios están listos${NC}"
echo ""

# ============================================================================
# PASO 3: Ejecutar migraciones si es necesario
# ============================================================================

echo -e "${YELLOW}📊 PASO 3: Verificando esquema de base de datos${NC}"
echo "────────────────────────────────────────────────────────────────────"
echo ""

# Ejecutar el script de migración 002 si no se ha ejecutado
docker exec catalog-db psql -U catalog_user -d catalogo -c "SELECT COUNT(*) FROM movimiento_inventario LIMIT 1;" > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "Ejecutando migración 002_movimientos.sql..."
    docker exec -i catalog-db psql -U catalog_user -d catalogo < catalogo-service/data/002_movimientos.sql
    echo -e "${GREEN}✅ Migración ejecutada${NC}"
else
    echo -e "${GREEN}✅ Esquema ya está actualizado${NC}"
fi

echo ""

# ============================================================================
# PASO 4: URLs de los servicios
# ============================================================================

echo -e "${BLUE}🔗 URLs de los servicios:${NC}"
echo "────────────────────────────────────────────────────────────────────"
echo "• Catalog Service (directo): http://localhost:3001"
echo "• BFF-Venta:                 http://localhost:8001"
echo "• Swagger Catalog:           http://localhost:3001/docs"
echo ""

# ============================================================================
# PASO 5: Ejecutar pruebas
# ============================================================================

echo -e "${YELLOW}🧪 PASO 4: Ejecutando pruebas de funcionalidades${NC}"
echo "────────────────────────────────────────────────────────────────────"
echo ""

TIMESTAMP=$(date +%s)
CATALOG_URL="http://localhost:3001/api"
BFF_URL="http://localhost:8001/api/v1"

# Variables para tracking de tests
TESTS_PASSED=0
TESTS_FAILED=0

# ============================================================================
# TEST 1: Crear producto SIN inventario inicial (comportamiento original)
# ============================================================================

echo -e "${BLUE}Test 1: Crear producto SIN inventario inicial (retrocompatibilidad)${NC}"

PROD_ID_1="TEST_${TIMESTAMP}_1"

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${CATALOG_URL}/catalog/items" \
  -H "Content-Type: application/json" \
  -d "{
    \"id\": \"${PROD_ID_1}\",
    \"nombre\": \"Producto Test Sin Inventario\",
    \"codigo\": \"TST${TIMESTAMP}1\",
    \"categoria\": \"TEST\",
    \"presentacion\": \"Unidad\",
    \"precioUnitario\": 1000.00,
    \"stockMinimo\": 10,
    \"stockCritico\": 5
  }")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "201" ]; then
    echo -e "   ${GREEN}✓ Producto creado exitosamente${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "   ${RED}✗ Error al crear producto (HTTP $HTTP_CODE)${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Verificar que no hay inventario
INVENTARIO=$(curl -s "${CATALOG_URL}/catalog/items/${PROD_ID_1}/inventario" | jq '.items | length')
if [ "$INVENTARIO" -eq 0 ]; then
    echo -e "   ${GREEN}✓ Sin inventario inicial (esperado)${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "   ${RED}✗ Hay inventario cuando no debería (${INVENTARIO} items)${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""

# ============================================================================
# TEST 2: Crear producto CON inventario inicial en UNA bodega
# ============================================================================

echo -e "${BLUE}Test 2: Crear producto CON inventario inicial en UNA bodega${NC}"

PROD_ID_2="TEST_${TIMESTAMP}_2"

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${CATALOG_URL}/catalog/items" \
  -H "Content-Type: application/json" \
  -d "{
    \"id\": \"${PROD_ID_2}\",
    \"nombre\": \"Producto Test Con Inventario Inicial\",
    \"codigo\": \"TST${TIMESTAMP}2\",
    \"categoria\": \"TEST\",
    \"presentacion\": \"Caja\",
    \"precioUnitario\": 2500.00,
    \"stockMinimo\": 20,
    \"stockCritico\": 10,
    \"requiereLote\": true,
    \"requiereVencimiento\": true,
    \"bodegasIniciales\": [
      {
        \"bodega_id\": \"BOG_CENTRAL\",
        \"pais\": \"CO\",
        \"lote\": \"LOTE-TEST-001\",
        \"fecha_vencimiento\": \"2099-12-31\"
      }
    ]
  }")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" == "201" ]; then
    echo -e "   ${GREEN}✓ Producto con inventario inicial creado${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "   ${RED}✗ Error al crear producto (HTTP $HTTP_CODE)${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Verificar inventario inicial
INVENTARIO_DATA=$(curl -s "${CATALOG_URL}/catalog/items/${PROD_ID_2}/inventario")
ITEMS_COUNT=$(echo "$INVENTARIO_DATA" | jq '.items | length')
CANTIDAD=$(echo "$INVENTARIO_DATA" | jq '.items[0].cantidad // 0')

if [ "$ITEMS_COUNT" -eq 1 ] && [ "$CANTIDAD" -eq 0 ]; then
    echo -e "   ${GREEN}✓ Inventario inicial con cantidad 0 (esperado)${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "   ${RED}✗ Inventario incorrecto (items: $ITEMS_COUNT, cantidad: $CANTIDAD)${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""

# ============================================================================
# TEST 3: Crear producto CON inventario inicial en MÚLTIPLES bodegas
# ============================================================================

echo -e "${BLUE}Test 3: Crear producto CON inventario inicial en MÚLTIPLES bodegas${NC}"

PROD_ID_3="TEST_${TIMESTAMP}_3"

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${CATALOG_URL}/catalog/items" \
  -H "Content-Type: application/json" \
  -d "{
    \"id\": \"${PROD_ID_3}\",
    \"nombre\": \"Producto Test Multi-Bodega\",
    \"codigo\": \"TST${TIMESTAMP}3\",
    \"categoria\": \"TEST\",
    \"presentacion\": \"Frasco\",
    \"precioUnitario\": 3500.00,
    \"stockMinimo\": 30,
    \"stockCritico\": 15,
    \"bodegasIniciales\": [
      {\"bodega_id\": \"BOG_CENTRAL\", \"pais\": \"CO\"},
      {\"bodega_id\": \"MED_SUR\", \"pais\": \"CO\"},
      {\"bodega_id\": \"CDMX_NORTE\", \"pais\": \"MX\"}
    ]
  }")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" == "201" ]; then
    echo -e "   ${GREEN}✓ Producto multi-bodega creado${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "   ${RED}✗ Error al crear producto (HTTP $HTTP_CODE)${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Verificar 3 registros de inventario
ITEMS_COUNT=$(curl -s "${CATALOG_URL}/catalog/items/${PROD_ID_3}/inventario" | jq '.items | length')

if [ "$ITEMS_COUNT" -eq 3 ]; then
    echo -e "   ${GREEN}✓ 3 registros de inventario creados${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "   ${RED}✗ Se esperaban 3 registros pero hay $ITEMS_COUNT${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""

# ============================================================================
# TEST 4: Registrar INGRESO y verificar actualización
# ============================================================================

echo -e "${BLUE}Test 4: Registrar ingreso de producto${NC}"

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${CATALOG_URL}/inventory/movements" \
  -H "Content-Type: application/json" \
  -d "{
    \"producto_id\": \"${PROD_ID_2}\",
    \"bodega_id\": \"BOG_CENTRAL\",
    \"pais\": \"CO\",
    \"lote\": \"LOTE-TEST-001\",
    \"tipo_movimiento\": \"INGRESO\",
    \"motivo\": \"COMPRA\",
    \"cantidad\": 100,
    \"fecha_vencimiento\": \"2026-12-31\",
    \"usuario_id\": \"TEST_USER\",
    \"referencia_documento\": \"PO-TEST-001\"
  }")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "201" ]; then
    SALDO_ANTERIOR=$(echo "$BODY" | jq '.saldo_anterior')
    SALDO_NUEVO=$(echo "$BODY" | jq '.saldo_nuevo')
    
    if [ "$SALDO_ANTERIOR" -eq 0 ] && [ "$SALDO_NUEVO" -eq 100 ]; then
        echo -e "   ${GREEN}✓ Ingreso registrado (0 → 100)${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "   ${RED}✗ Saldos incorrectos ($SALDO_ANTERIOR → $SALDO_NUEVO)${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "   ${RED}✗ Error al registrar ingreso (HTTP $HTTP_CODE)${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""

# ============================================================================
# TEST 5: Consultar productos en bodega (NUEVO ENDPOINT - Directo)
# ============================================================================

echo -e "${BLUE}Test 5: Consultar productos en bodega (endpoint directo)${NC}"

RESPONSE=$(curl -s -w "\n%{http_code}" "${CATALOG_URL}/inventory/bodega/BOG_CENTRAL/productos?con_stock=true&size=10")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "200" ]; then
    PRODUCTOS_COUNT=$(echo "$BODY" | jq '.items | length')
    TOTAL=$(echo "$BODY" | jq '.meta.total')
    
    echo -e "   ${GREEN}✓ Endpoint funciona (${PRODUCTOS_COUNT} productos, ${TOTAL} total)${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    
    # Verificar que nuestro producto aparece
    PROD_ENCONTRADO=$(echo "$BODY" | jq ".items[] | select(.producto_id == \"${PROD_ID_2}\")")
    
    if [ -n "$PROD_ENCONTRADO" ]; then
        CANTIDAD=$(echo "$PROD_ENCONTRADO" | jq '.cantidad')
        echo -e "   ${GREEN}✓ Producto de prueba encontrado (cantidad: $CANTIDAD)${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "   ${YELLOW}⚠️ Producto de prueba no encontrado en la página${NC}"
    fi
else
    echo -e "   ${RED}✗ Error al consultar productos (HTTP $HTTP_CODE)${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""

# ============================================================================
# TEST 6: Consultar productos en bodega a través del BFF
# ============================================================================

echo -e "${BLUE}Test 6: Consultar productos en bodega (a través del BFF-Venta)${NC}"

RESPONSE=$(curl -s -w "\n%{http_code}" "${BFF_URL}/inventory/bodega/BOG_CENTRAL/productos?con_stock=true&size=5")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "200" ]; then
    PRODUCTOS_COUNT=$(echo "$BODY" | jq '.items | length')
    echo -e "   ${GREEN}✓ BFF-Venta funciona correctamente (${PRODUCTOS_COUNT} productos)${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "   ${RED}✗ Error en BFF-Venta (HTTP $HTTP_CODE)${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""

# ============================================================================
# TEST 7: Filtrar productos por país
# ============================================================================

echo -e "${BLUE}Test 7: Filtrar productos por país${NC}"

RESPONSE=$(curl -s -w "\n%{http_code}" "${CATALOG_URL}/inventory/bodega/BOG_CENTRAL/productos?pais=CO&size=10")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "200" ]; then
    PRODUCTOS_CO=$(echo "$BODY" | jq '.items | length')
    echo -e "   ${GREEN}✓ Filtro por país funciona (${PRODUCTOS_CO} productos de CO)${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    
    # Verificar que todos son de CO
    TODOS_CO=$(echo "$BODY" | jq '.items | all(.pais == "CO")')
    if [ "$TODOS_CO" == "true" ]; then
        echo -e "   ${GREEN}✓ Todos los productos son de Colombia${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "   ${RED}✗ Hay productos de otros países${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "   ${RED}✗ Error al filtrar (HTTP $HTTP_CODE)${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""

# ============================================================================
# TEST 8: Consultar productos sin stock (con_stock=false)
# ============================================================================

echo -e "${BLUE}Test 8: Consultar productos incluyendo sin stock${NC}"

# Primero con stock
CON_STOCK=$(curl -s "${CATALOG_URL}/inventory/bodega/BOG_CENTRAL/productos?con_stock=true" | jq '.meta.total')

# Luego incluyendo sin stock
TODOS=$(curl -s "${CATALOG_URL}/inventory/bodega/BOG_CENTRAL/productos?con_stock=false" | jq '.meta.total')

echo -e "   ${BLUE}Con stock: $CON_STOCK | Todos: $TODOS${NC}"

if [ "$TODOS" -ge "$CON_STOCK" ]; then
    echo -e "   ${GREEN}✓ Parámetro con_stock funciona correctamente${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "   ${RED}✗ Lógica incorrecta (todos < con stock)${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""

# ============================================================================
# RESUMEN DE PRUEBAS
# ============================================================================

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                        📊 RESUMEN DE PRUEBAS                       ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
echo -e "${BLUE}Total de pruebas:${NC}      $TOTAL_TESTS"
echo -e "${GREEN}Pruebas exitosas:${NC}    $TESTS_PASSED"
echo -e "${RED}Pruebas fallidas:${NC}     $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ¡Todas las pruebas pasaron exitosamente!${NC}"
    EXIT_CODE=0
else
    echo -e "${RED}⚠️  Algunas pruebas fallaron${NC}"
    EXIT_CODE=1
fi

echo ""

# ============================================================================
# CLEANUP (opcional)
# ============================================================================

echo "📝 Productos de prueba creados:"
echo "   - ${PROD_ID_1} (sin inventario inicial)"
echo "   - ${PROD_ID_2} (con 1 bodega inicial)"
echo "   - ${PROD_ID_3} (con 3 bodegas iniciales)"
echo ""

read -p "¿Deseas detener los servicios? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${YELLOW}Deteniendo servicios...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ Servicios detenidos${NC}"
fi

echo ""
echo "✅ Script completado"
exit $EXIT_CODE

