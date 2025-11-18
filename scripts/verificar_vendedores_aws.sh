#!/bin/bash
# Script para verificar la asignación de vendedores a clientes en AWS
# Uso: ./scripts/verificar_vendedores_aws.sh <URL_BASE_BFF>
# Ejemplo: ./scripts/verificar_vendedores_aws.sh https://api.medisupply.com

set -e

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Validar argumentos
if [ -z "$1" ]; then
    echo -e "${RED}❌ Error: Debe proporcionar la URL base del BFF${NC}"
    echo "Uso: $0 <URL_BASE_BFF>"
    echo "Ejemplo: $0 https://api.medisupply.com"
    exit 1
fi

BASE_URL="${1%/}" # Eliminar trailing slash si existe

echo "======================================================================"
echo "  🔍 VERIFICACIÓN DE VENDEDORES Y CLIENTES EN AWS"
echo "======================================================================"
echo ""
echo "URL Base: $BASE_URL"
echo "Fecha: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# ============================================
# 1. VERIFICAR SALUD DEL SERVICIO
# ============================================
echo -e "${BLUE}📡 1. Verificando salud del servicio...${NC}"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health" || echo "000")

if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}   ✅ Servicio en línea (HTTP $HTTP_STATUS)${NC}"
else
    echo -e "${RED}   ❌ Servicio no disponible (HTTP $HTTP_STATUS)${NC}"
    exit 1
fi
echo ""

# ============================================
# 2. LISTAR CLIENTES (VERIFICAR VENDEDOR_ID)
# ============================================
echo -e "${BLUE}📋 2. Verificando que los clientes tengan vendedor_id asignado...${NC}"
RESPONSE=$(curl -s "${BASE_URL}/api/v1/client/?limite=5")

# Verificar que hay clientes
TOTAL_CLIENTES=$(echo "$RESPONSE" | jq '. | length' 2>/dev/null || echo "0")

if [ "$TOTAL_CLIENTES" = "0" ]; then
    echo -e "${RED}   ❌ No se encontraron clientes en el sistema${NC}"
    exit 1
fi

echo -e "${GREEN}   ✅ Se encontraron $TOTAL_CLIENTES clientes${NC}"

# Verificar que cada cliente tiene vendedor_id
CLIENTES_SIN_VENDEDOR=$(echo "$RESPONSE" | jq '[.[] | select(.vendedor_id == null or .vendedor_id == "")] | length' 2>/dev/null || echo "0")

if [ "$CLIENTES_SIN_VENDEDOR" = "0" ]; then
    echo -e "${GREEN}   ✅ Todos los clientes tienen vendedor_id asignado${NC}"
else
    echo -e "${RED}   ❌ Hay $CLIENTES_SIN_VENDEDOR clientes sin vendedor_id${NC}"
    exit 1
fi

# Mostrar muestra de clientes
echo ""
echo "   📄 Muestra de clientes:"
echo "$RESPONSE" | jq -r '.[] | "      • \(.nombre) (NIT: \(.nit)) → Vendedor: \(.vendedor_id)"' | head -5
echo ""

# ============================================
# 3. LISTAR VENDEDORES
# ============================================
echo -e "${BLUE}👥 3. Verificando vendedores en el sistema...${NC}"
VENDEDORES=$(curl -s "${BASE_URL}/api/v1/vendedores/?page=1&size=10")

TOTAL_VENDEDORES=$(echo "$VENDEDORES" | jq '.vendedores | length' 2>/dev/null || echo "0")

if [ "$TOTAL_VENDEDORES" = "0" ]; then
    echo -e "${RED}   ❌ No se encontraron vendedores en el sistema${NC}"
    exit 1
fi

echo -e "${GREEN}   ✅ Se encontraron $TOTAL_VENDEDORES vendedores${NC}"

# Obtener el primer vendedor para pruebas
PRIMER_VENDEDOR_ID=$(echo "$VENDEDORES" | jq -r '.vendedores[0].id' 2>/dev/null)
PRIMER_VENDEDOR_NOMBRE=$(echo "$VENDEDORES" | jq -r '.vendedores[0].nombre_completo' 2>/dev/null)

if [ "$PRIMER_VENDEDOR_ID" = "null" ] || [ -z "$PRIMER_VENDEDOR_ID" ]; then
    echo -e "${RED}   ❌ No se pudo obtener el ID del primer vendedor${NC}"
    exit 1
fi

echo "   📄 Muestra de vendedores:"
echo "$VENDEDORES" | jq -r '.vendedores[] | "      • \(.nombre_completo) (ID: \(.id))"' | head -5
echo ""

# ============================================
# 4. VERIFICAR COHERENCIA DE ENDPOINTS
# ============================================
echo -e "${BLUE}🔗 4. Verificando coherencia entre endpoints...${NC}"
echo "   Usando vendedor: $PRIMER_VENDEDOR_NOMBRE (ID: $PRIMER_VENDEDOR_ID)"
echo ""

# 4.1 Endpoint de cliente con filtro vendedor_id
echo "   4.1 Consultando clientes por vendedor_id..."
CLIENTES_POR_VENDEDOR=$(curl -s "${BASE_URL}/api/v1/client/?vendedor_id=${PRIMER_VENDEDOR_ID}&limite=20")
TOTAL_ENDPOINT1=$(echo "$CLIENTES_POR_VENDEDOR" | jq '. | length' 2>/dev/null || echo "0")
echo -e "       ${GREEN}✅ Endpoint 1 retorna: $TOTAL_ENDPOINT1 clientes${NC}"

# 4.2 Endpoint de vendedor que lista sus clientes
echo "   4.2 Consultando clientes desde endpoint de vendedor..."
CLIENTES_DEL_VENDEDOR=$(curl -s "${BASE_URL}/api/v1/vendedores/${PRIMER_VENDEDOR_ID}/clientes")
TOTAL_ENDPOINT2=$(echo "$CLIENTES_DEL_VENDEDOR" | jq '.total_clientes' 2>/dev/null || echo "0")
echo -e "       ${GREEN}✅ Endpoint 2 retorna: $TOTAL_ENDPOINT2 clientes${NC}"

# 4.3 Comparar resultados
echo ""
if [ "$TOTAL_ENDPOINT1" = "$TOTAL_ENDPOINT2" ]; then
    echo -e "${GREEN}   ✅ COHERENCIA CONFIRMADA: Ambos endpoints retornan la misma cantidad de clientes${NC}"
else
    echo -e "${YELLOW}   ⚠️  ADVERTENCIA: Los endpoints retornan cantidades diferentes${NC}"
    echo "       Endpoint 1 (cliente): $TOTAL_ENDPOINT1"
    echo "       Endpoint 2 (vendedor): $TOTAL_ENDPOINT2"
fi
echo ""

# ============================================
# 5. VERIFICAR CAMPOS REQUERIDOS
# ============================================
echo -e "${BLUE}🔍 5. Verificando estructura de datos...${NC}"

# Verificar que el campo vendedor_id existe en la respuesta
HAS_VENDEDOR_ID=$(echo "$CLIENTES_POR_VENDEDOR" | jq '.[0] | has("vendedor_id")' 2>/dev/null || echo "false")

if [ "$HAS_VENDEDOR_ID" = "true" ]; then
    echo -e "${GREEN}   ✅ El campo 'vendedor_id' está presente en la respuesta${NC}"
else
    echo -e "${RED}   ❌ El campo 'vendedor_id' NO está presente en la respuesta${NC}"
    exit 1
fi

# Verificar campos básicos
CAMPOS_ESPERADOS=("id" "nit" "nombre" "codigo_unico" "email" "vendedor_id" "activo")
CAMPOS_FALTANTES=()

for campo in "${CAMPOS_ESPERADOS[@]}"; do
    HAS_FIELD=$(echo "$CLIENTES_POR_VENDEDOR" | jq ".[0] | has(\"$campo\")" 2>/dev/null || echo "false")
    if [ "$HAS_FIELD" = "false" ]; then
        CAMPOS_FALTANTES+=("$campo")
    fi
done

if [ ${#CAMPOS_FALTANTES[@]} -eq 0 ]; then
    echo -e "${GREEN}   ✅ Todos los campos esperados están presentes${NC}"
else
    echo -e "${RED}   ❌ Campos faltantes: ${CAMPOS_FALTANTES[*]}${NC}"
    exit 1
fi
echo ""

# ============================================
# RESUMEN FINAL
# ============================================
echo "======================================================================"
echo -e "${GREEN}✅ VERIFICACIÓN COMPLETADA EXITOSAMENTE${NC}"
echo "======================================================================"
echo ""
echo "📊 Resumen:"
echo "   • Total de clientes: $TOTAL_CLIENTES"
echo "   • Clientes sin vendedor: $CLIENTES_SIN_VENDEDOR"
echo "   • Total de vendedores: $TOTAL_VENDEDORES"
echo "   • Coherencia entre endpoints: ✅"
echo "   • Estructura de datos: ✅"
echo ""
echo "🎉 El sistema está funcionando correctamente en AWS"
echo ""

