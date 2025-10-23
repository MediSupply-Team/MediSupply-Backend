#!/bin/bash

# Script de prueba completo para BFF-Cliente y BFF-Venta
# Verifica que los BFFs están haciendo proxy correctamente a los microservicios

set -e

echo "========================================="
echo "   TEST COMPLETO BFF-CLIENTE Y BFF-VENTA"
echo "========================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para verificar respuesta
check_response() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ OK${NC}"
    else
        echo -e "${RED}❌ FAILED${NC}"
    fi
}

# ==========================================
# BFF-CLIENTE TESTS
# ==========================================

echo "========================================="
echo "   BFF-CLIENTE (Puerto 8002)"
echo "========================================="
echo ""

echo "1️⃣  Health Check BFF-Cliente..."
curl -sf "http://localhost:8002/health" > /dev/null
check_response

echo "2️⃣  Listar clientes a través de BFF..."
curl -sf "http://localhost:8002/api/v1/client/?limite=3" | jq -e 'length > 0' > /dev/null
check_response

echo "3️⃣  Buscar cliente por NIT a través de BFF..."
curl -sf "http://localhost:8002/api/v1/client/search?q=900123456-7&vendedor_id=VEND001" | jq -e '.nombre' > /dev/null
check_response

echo "4️⃣  Obtener histórico de cliente a través de BFF..."
curl -sf "http://localhost:8002/api/v1/client/CLI001/historico?vendedor_id=VEND001" | jq -e '.cliente.nombre' > /dev/null
check_response

echo ""
echo -e "${GREEN}✅ BFF-CLIENTE: Todos los tests pasaron${NC}"
echo ""

# ==========================================
# BFF-VENTA TESTS (Si está disponible)
# ==========================================

echo "========================================="
echo "   BFF-VENTA (Puerto 8001)"
echo "========================================="
echo ""

# Verificar si BFF-Venta está corriendo
if ! curl -sf "http://localhost:8001/health" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  BFF-Venta no está corriendo en puerto 8001${NC}"
    echo -e "${YELLOW}   Saltando tests de BFF-Venta...${NC}"
else
    echo "1️⃣  Health Check BFF-Venta..."
    curl -sf "http://localhost:8001/health" > /dev/null
    check_response

    echo "2️⃣  Listar productos a través de BFF-Venta..."
    curl -sf "http://localhost:8001/api/v1/catalog/items?size=3" | jq -e '.items | length > 0' > /dev/null
    check_response

    echo "3️⃣  Buscar producto específico a través de BFF-Venta..."
    curl -sf "http://localhost:8001/api/v1/catalog/items/PROD006" | jq -e '.nombre' > /dev/null
    check_response

    echo "4️⃣  Obtener inventario a través de BFF-Venta..."
    curl -sf "http://localhost:8001/api/v1/catalog/items/PROD006/inventario?size=3" | jq -e '.items | length > 0' > /dev/null
    check_response

    echo ""
    echo -e "${GREEN}✅ BFF-VENTA: Todos los tests pasaron${NC}"
fi

echo ""
echo "========================================="
echo "   COMPARACIÓN DIRECTA"
echo "   (BFF vs Microservicio Directo)"
echo "========================================="
echo ""

echo "Comparando respuestas BFF-Cliente vs Cliente-Service..."
BFF_RESPONSE=$(curl -s "http://localhost:8002/api/v1/client/?limite=1" | jq -c '.[0].id')
DIRECT_RESPONSE=$(curl -s "http://localhost:3003/api/cliente/?limite=1" | jq -c '.[0].id')

if [ "$BFF_RESPONSE" == "$DIRECT_RESPONSE" ]; then
    echo -e "${GREEN}✅ Respuestas coinciden: BFF-Cliente proxy funciona correctamente${NC}"
else
    echo -e "${RED}❌ Respuestas NO coinciden${NC}"
    echo "BFF: $BFF_RESPONSE"
    echo "Direct: $DIRECT_RESPONSE"
fi

echo ""

if curl -sf "http://localhost:8001/health" > /dev/null 2>&1; then
    echo "Comparando respuestas BFF-Venta vs Catalogo-Service..."
    BFF_CAT_RESPONSE=$(curl -s "http://localhost:8001/api/v1/catalog/items?size=1" | jq -c '.items[0].id')
    DIRECT_CAT_RESPONSE=$(curl -s "http://localhost:3001/api/catalog/items?size=1" | jq -c '.items[0].id')

    if [ "$BFF_CAT_RESPONSE" == "$DIRECT_CAT_RESPONSE" ]; then
        echo -e "${GREEN}✅ Respuestas coinciden: BFF-Venta proxy funciona correctamente${NC}"
    else
        echo -e "${RED}❌ Respuestas NO coinciden${NC}"
        echo "BFF: $BFF_CAT_RESPONSE"
        echo "Direct: $DIRECT_CAT_RESPONSE"
    fi
fi

echo ""
echo "========================================="
echo "   RESUMEN DE SERVICIOS"
echo "========================================="
echo ""

echo "Microservicios:"
echo "  - Cliente-Service (3003): $(curl -sf "http://localhost:3003/api/cliente/health" > /dev/null && echo -e "${GREEN}✅ UP${NC}" || echo -e "${RED}❌ DOWN${NC}")"
echo "  - Catalogo-Service (3001): $(curl -sf "http://localhost:3001/health" > /dev/null && echo -e "${GREEN}✅ UP${NC}" || echo -e "${RED}❌ DOWN${NC}")"
echo ""
echo "BFFs:"
echo "  - BFF-Cliente (8002): $(curl -sf "http://localhost:8002/health" > /dev/null && echo -e "${GREEN}✅ UP${NC}" || echo -e "${RED}❌ DOWN${NC}")"
echo "  - BFF-Venta (8001): $(curl -sf "http://localhost:8001/health" > /dev/null 2>&1 && echo -e "${GREEN}✅ UP${NC}" || echo -e "${YELLOW}⚠️  NOT RUNNING${NC}")"

echo ""
echo "========================================="
echo "   ✅ TESTS COMPLETADOS"
echo "========================================="

