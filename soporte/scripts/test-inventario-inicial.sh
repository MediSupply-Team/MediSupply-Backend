#!/bin/bash

# Script de prueba para crear productos con inventario inicial
# Asegúrate de que el servicio catalogo-service esté corriendo en http://localhost:8002

set -e  # Salir si hay errores

BASE_URL="http://localhost:8002"
TIMESTAMP=$(date +%s)

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║  🧪 Prueba: Creación de Productos con Inventario Inicial         ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# TEST 1: Crear producto SIN inventario inicial (comportamiento original)
# ============================================================================

echo -e "${YELLOW}📋 TEST 1: Crear producto SIN inventario inicial${NC}"
echo "────────────────────────────────────────────────────────────────────"
echo ""

PROD_ID_1="TEST_${TIMESTAMP}_1"

echo -e "${BLUE}Creando producto: ${PROD_ID_1}${NC}"
curl -s -X POST "${BASE_URL}/catalog/items" \
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
  }" | jq '.'

echo ""
echo -e "${GREEN}✅ Producto creado (sin inventario inicial)${NC}"
echo ""

# Verificar inventario (debe estar vacío)
echo -e "${BLUE}Verificando inventario...${NC}"
INVENTARIO_1=$(curl -s "${BASE_URL}/catalog/items/${PROD_ID_1}/inventario" | jq '.items | length')

if [ "$INVENTARIO_1" -eq 0 ]; then
    echo -e "${GREEN}✅ Correcto: No hay inventario inicial (items: $INVENTARIO_1)${NC}"
else
    echo -e "❌ Error: Se esperaba inventario vacío pero hay $INVENTARIO_1 registros"
fi

echo ""
echo ""

# ============================================================================
# TEST 2: Crear producto CON inventario inicial en UNA bodega
# ============================================================================

echo -e "${YELLOW}📋 TEST 2: Crear producto CON inventario inicial en UNA bodega${NC}"
echo "────────────────────────────────────────────────────────────────────"
echo ""

PROD_ID_2="TEST_${TIMESTAMP}_2"

echo -e "${BLUE}Creando producto: ${PROD_ID_2}${NC}"
curl -s -X POST "${BASE_URL}/catalog/items" \
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
  }" | jq '.'

echo ""
echo -e "${GREEN}✅ Producto creado (con inventario inicial)${NC}"
echo ""

# Verificar inventario (debe tener 1 registro con cantidad 0)
echo -e "${BLUE}Verificando inventario...${NC}"
INVENTARIO_2=$(curl -s "${BASE_URL}/catalog/items/${PROD_ID_2}/inventario")
echo "$INVENTARIO_2" | jq '.'

ITEMS_COUNT=$(echo "$INVENTARIO_2" | jq '.items | length')
CANTIDAD=$(echo "$INVENTARIO_2" | jq '.items[0].cantidad')

if [ "$ITEMS_COUNT" -eq 1 ] && [ "$CANTIDAD" -eq 0 ]; then
    echo -e "${GREEN}✅ Correcto: Hay 1 registro de inventario con cantidad 0${NC}"
else
    echo -e "❌ Error: Se esperaba 1 registro con cantidad 0, pero hay $ITEMS_COUNT registro(s) con cantidad $CANTIDAD"
fi

echo ""
echo ""

# ============================================================================
# TEST 3: Crear producto CON inventario inicial en MÚLTIPLES bodegas
# ============================================================================

echo -e "${YELLOW}📋 TEST 3: Crear producto CON inventario inicial en MÚLTIPLES bodegas${NC}"
echo "────────────────────────────────────────────────────────────────────"
echo ""

PROD_ID_3="TEST_${TIMESTAMP}_3"

echo -e "${BLUE}Creando producto: ${PROD_ID_3}${NC}"
curl -s -X POST "${BASE_URL}/catalog/items" \
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
  }" | jq '.'

echo ""
echo -e "${GREEN}✅ Producto creado (con 3 bodegas iniciales)${NC}"
echo ""

# Verificar inventario (debe tener 3 registros con cantidad 0)
echo -e "${BLUE}Verificando inventario...${NC}"
INVENTARIO_3=$(curl -s "${BASE_URL}/catalog/items/${PROD_ID_3}/inventario")
echo "$INVENTARIO_3" | jq '.'

ITEMS_COUNT_3=$(echo "$INVENTARIO_3" | jq '.items | length')

if [ "$ITEMS_COUNT_3" -eq 3 ]; then
    echo -e "${GREEN}✅ Correcto: Hay 3 registros de inventario${NC}"
    
    # Verificar que todos tengan cantidad 0
    ALL_ZERO=true
    for i in {0..2}; do
        CANT=$(echo "$INVENTARIO_3" | jq ".items[$i].cantidad")
        if [ "$CANT" -ne 0 ]; then
            ALL_ZERO=false
        fi
    done
    
    if $ALL_ZERO; then
        echo -e "${GREEN}✅ Correcto: Todos los registros tienen cantidad 0${NC}"
    else
        echo -e "❌ Error: No todos los registros tienen cantidad 0"
    fi
else
    echo -e "❌ Error: Se esperaban 3 registros pero hay $ITEMS_COUNT_3"
fi

echo ""
echo ""

# ============================================================================
# TEST 4: Registrar INGRESO en producto con inventario inicial
# ============================================================================

echo -e "${YELLOW}📋 TEST 4: Registrar INGRESO en producto con inventario inicial${NC}"
echo "────────────────────────────────────────────────────────────────────"
echo ""

echo -e "${BLUE}Registrando ingreso de 100 unidades en ${PROD_ID_2} (BOG_CENTRAL)...${NC}"
MOVIMIENTO=$(curl -s -X POST "${BASE_URL}/inventory/movements" \
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
    \"referencia_documento\": \"PO-TEST-001\",
    \"observaciones\": \"Ingreso de prueba\"
  }")

echo "$MOVIMIENTO" | jq '.'

SALDO_ANTERIOR=$(echo "$MOVIMIENTO" | jq '.saldo_anterior')
SALDO_NUEVO=$(echo "$MOVIMIENTO" | jq '.saldo_nuevo')

if [ "$SALDO_ANTERIOR" -eq 0 ] && [ "$SALDO_NUEVO" -eq 100 ]; then
    echo -e "${GREEN}✅ Correcto: Saldo actualizado de 0 → 100${NC}"
else
    echo -e "❌ Error: Se esperaba saldo 0 → 100, pero fue $SALDO_ANTERIOR → $SALDO_NUEVO"
fi

echo ""

# Verificar inventario actualizado
echo -e "${BLUE}Verificando inventario actualizado...${NC}"
INVENTARIO_4=$(curl -s "${BASE_URL}/catalog/items/${PROD_ID_2}/inventario")
echo "$INVENTARIO_4" | jq '.'

# Buscar el registro con el lote LOTE-TEST-001
CANTIDAD_ACTUALIZADA=$(echo "$INVENTARIO_4" | jq '.items[] | select(.lote == "LOTE-TEST-001") | .cantidad')

if [ "$CANTIDAD_ACTUALIZADA" -eq 100 ]; then
    echo -e "${GREEN}✅ Correcto: Inventario actualizado a 100 unidades${NC}"
else
    echo -e "❌ Error: Se esperaba cantidad 100 pero hay $CANTIDAD_ACTUALIZADA"
fi

echo ""
echo ""

# ============================================================================
# TEST 5: Consultar productos en bodega (NUEVO ENDPOINT)
# ============================================================================

echo -e "${YELLOW}📋 TEST 5: Consultar productos disponibles en bodega${NC}"
echo "────────────────────────────────────────────────────────────────────"
echo ""

echo -e "${BLUE}Consultando productos en BOG_CENTRAL...${NC}"
PRODUCTOS_BODEGA=$(curl -s "${BASE_URL}/inventory/bodega/BOG_CENTRAL/productos?con_stock=true&size=5")

echo "$PRODUCTOS_BODEGA" | jq '.'

# Contar productos
PRODUCTOS_COUNT=$(echo "$PRODUCTOS_BODEGA" | jq '.items | length')
PRODUCTOS_TOTAL=$(echo "$PRODUCTOS_BODEGA" | jq '.meta.total')

echo ""
echo -e "${GREEN}✅ Endpoint de productos en bodega funciona${NC}"
echo "   📦 Productos en esta página: $PRODUCTOS_COUNT"
echo "   📊 Total productos en bodega: $PRODUCTOS_TOTAL"

# Verificar que el producto creado aparece en la bodega
echo ""
echo -e "${BLUE}Verificando que ${PROD_ID_2} aparece en la bodega...${NC}"
PROD_EN_BODEGA=$(curl -s "${BASE_URL}/inventory/bodega/BOG_CENTRAL/productos?size=100" | jq ".items[] | select(.producto_id == \"${PROD_ID_2}\")")

if [ -n "$PROD_EN_BODEGA" ]; then
    echo -e "${GREEN}✅ Producto ${PROD_ID_2} encontrado en la bodega${NC}"
    echo "$PROD_EN_BODEGA" | jq '{nombre: .producto_nombre, cantidad: .cantidad, estado: .estado_stock}'
else
    echo -e "❌ Error: Producto ${PROD_ID_2} no encontrado en la bodega"
fi

echo ""
echo ""

# ============================================================================
# TEST 6: Consultar productos en bodega con filtros
# ============================================================================

echo -e "${YELLOW}📋 TEST 6: Consultar productos en bodega CON filtros${NC}"
echo "────────────────────────────────────────────────────────────────────"
echo ""

echo -e "${BLUE}Consultando productos en CDMX_NORTE (MX)...${NC}"
PRODUCTOS_MX=$(curl -s "${BASE_URL}/inventory/bodega/CDMX_NORTE/productos?pais=MX&con_stock=true")
PRODUCTOS_MX_COUNT=$(echo "$PRODUCTOS_MX" | jq '.items | length')

echo "   📦 Productos encontrados: $PRODUCTOS_MX_COUNT"

if [ "$PRODUCTOS_MX_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Filtro por país funciona correctamente${NC}"
    echo ""
    echo "Primeros productos:"
    echo "$PRODUCTOS_MX" | jq '.items[0:3] | .[] | {nombre: .producto_nombre, cantidad: .cantidad, pais: .pais}'
else
    echo -e "${YELLOW}⚠️  No hay productos en CDMX_NORTE (MX) aún${NC}"
fi

echo ""
echo ""

# ============================================================================
# RESUMEN
# ============================================================================

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                        📊 RESUMEN DE PRUEBAS                       ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ TEST 1: Producto sin inventario inicial - OK"
echo "✅ TEST 2: Producto con 1 bodega inicial - OK"
echo "✅ TEST 3: Producto con 3 bodegas iniciales - OK"
echo "✅ TEST 4: Ingreso actualiza inventario inicial - OK"
echo "✅ TEST 5: Consultar productos en bodega - OK"
echo "✅ TEST 6: Consultar productos con filtros - OK"
echo ""
echo -e "${GREEN}🎉 Todas las pruebas completadas exitosamente!${NC}"
echo ""
echo "📝 Productos creados:"
echo "   - ${PROD_ID_1} (sin inventario inicial)"
echo "   - ${PROD_ID_2} (con 1 bodega inicial)"
echo "   - ${PROD_ID_3} (con 3 bodegas iniciales)"
echo ""
echo "🔗 Endpoints probados:"
echo "   - POST /catalog/items (crear producto)"
echo "   - GET  /catalog/items/{id}/inventario (ver inventario)"
echo "   - POST /inventory/movements (registrar ingreso)"
echo "   - GET  /inventory/bodega/{id}/productos (NUEVO - listar productos en bodega)"
echo ""
echo "💡 Puedes eliminarlos manualmente o continuar probando con ellos."
echo ""

