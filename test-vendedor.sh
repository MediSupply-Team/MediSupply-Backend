#!/bin/bash

###############################################################################
# Script de pruebas automatizado para Vendedor y Plan de Venta
# Uso: ./test-vendedor.sh
###############################################################################

set -e  # Salir si hay error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base URL (cambiar si usas BFF en puerto 8002)
BASE_URL="http://localhost:3003"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   TEST AUTOMATIZADO - VENDEDOR Y PLAN DE VENTA           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verificar que el servicio esté disponible
echo -e "${YELLOW}🔍 Verificando que cliente-service esté disponible...${NC}"
if ! curl -s -f "$BASE_URL/health" > /dev/null; then
    echo -e "${RED}❌ ERROR: cliente-service no está disponible en $BASE_URL${NC}"
    echo -e "${YELLOW}   Ejecuta: docker-compose up -d cliente-service${NC}"
    exit 1
fi
echo -e "${GREEN}✅ cliente-service está disponible${NC}"
echo ""

###############################################################################
# PASO 1: OBTENER IDS DE CATÁLOGOS
###############################################################################

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}PASO 1: Obteniendo IDs de catálogos pre-cargados${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Tipos de Rol
echo -e "${YELLOW}📋 Listando Tipos de Rol...${NC}"
TIPOS_ROL=$(curl -s "$BASE_URL/api/v1/catalogos/tipos-rol?activo=true")
TIPO_ROL_ID=$(echo $TIPOS_ROL | jq -r '.tipos_rol[0].id // empty')

if [ -z "$TIPO_ROL_ID" ]; then
    echo -e "${RED}❌ No se encontraron tipos de rol. Ejecuta populate_db.py${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Tipo de Rol ID: $TIPO_ROL_ID${NC}"

# Territorios
echo -e "${YELLOW}📋 Listando Territorios...${NC}"
TERRITORIOS=$(curl -s "$BASE_URL/api/v1/catalogos/territorios?activo=true")
TERRITORIO_ID=$(echo $TERRITORIOS | jq -r '.territorios[0].id // empty')

if [ -z "$TERRITORIO_ID" ]; then
    echo -e "${RED}❌ No se encontraron territorios${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Territorio ID: $TERRITORIO_ID${NC}"

# Tipos de Plan
echo -e "${YELLOW}📋 Listando Tipos de Plan...${NC}"
TIPOS_PLAN=$(curl -s "$BASE_URL/api/v1/catalogos/tipos-plan?activo=true")
TIPO_PLAN_ID=$(echo $TIPOS_PLAN | jq -r '.tipos_plan[0].id // empty')

if [ -z "$TIPO_PLAN_ID" ]; then
    echo -e "${RED}❌ No se encontraron tipos de plan${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Tipo de Plan ID: $TIPO_PLAN_ID${NC}"

# Regiones
echo -e "${YELLOW}📋 Listando Regiones...${NC}"
REGIONES=$(curl -s "$BASE_URL/api/v1/catalogos/regiones?activo=true")
REGION_ID=$(echo $REGIONES | jq -r '.regiones[0].id // empty')

if [ -z "$REGION_ID" ]; then
    echo -e "${RED}❌ No se encontraron regiones${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Región ID: $REGION_ID${NC}"

# Zonas
echo -e "${YELLOW}📋 Listando Zonas...${NC}"
ZONAS=$(curl -s "$BASE_URL/api/v1/catalogos/zonas?activo=true")
ZONA_ID=$(echo $ZONAS | jq -r '.zonas[0].id // empty')

if [ -z "$ZONA_ID" ]; then
    echo -e "${RED}❌ No se encontraron zonas${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Zona ID: $ZONA_ID${NC}"
echo ""

###############################################################################
# PASO 2: CREAR VENDEDOR CON PLAN COMPLETO
###############################################################################

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}PASO 2: Creando vendedor con plan de venta completo${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

VENDEDOR_JSON=$(cat <<EOF
{
  "identificacion": "TEST$(date +%s)",
  "nombre_completo": "Test Vendedor $(date +%H:%M:%S)",
  "email": "test.vendedor.$(date +%s)@medisupply.com",
  "telefono": "+57-311-$(date +%s | tail -c 8)",
  "pais": "CO",
  "username": "testuser$(date +%s)",
  "rol": "seller",
  "rol_vendedor_id": "$TIPO_ROL_ID",
  "territorio_id": "$TERRITORIO_ID",
  "fecha_ingreso": "2024-11-12",
  "observaciones": "Vendedor de prueba automatizada",
  "activo": true,
  "plan_venta": {
    "tipo_plan_id": "$TIPO_PLAN_ID",
    "nombre_plan": "Plan Test $(date +%Y%m%d%H%M%S)",
    "fecha_inicio": "2024-11-01",
    "fecha_fin": "2024-12-31",
    "meta_ventas": 100000.00,
    "comision_base": 7.5,
    "estructura_bonificaciones": {
      "70": 2,
      "90": 5,
      "100": 10
    },
    "observaciones": "Plan de prueba automatizada",
    "productos": [
      {
        "producto_id": "PROD001",
        "meta_cantidad": 50,
        "precio_unitario": 2000.00
      },
      {
        "producto_id": "PROD002",
        "meta_cantidad": 30,
        "precio_unitario": 1500.00
      }
    ],
    "region_ids": ["$REGION_ID"],
    "zona_ids": ["$ZONA_ID"]
  }
}
EOF
)

echo -e "${YELLOW}📤 Enviando request...${NC}"
CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/vendedores" \
    -H "Content-Type: application/json" \
    -d "$VENDEDOR_JSON")

VENDEDOR_ID=$(echo $CREATE_RESPONSE | jq -r '.id // empty')
PLAN_VENTA_ID=$(echo $CREATE_RESPONSE | jq -r '.plan_venta_id // empty')

if [ -z "$VENDEDOR_ID" ]; then
    echo -e "${RED}❌ ERROR al crear vendedor:${NC}"
    echo $CREATE_RESPONSE | jq '.'
    exit 1
fi

echo -e "${GREEN}✅ Vendedor creado exitosamente${NC}"
echo -e "${GREEN}   Vendedor ID: $VENDEDOR_ID${NC}"
echo -e "${GREEN}   Plan Venta ID: $PLAN_VENTA_ID${NC}"
echo ""

###############################################################################
# PASO 3: OBTENER VENDEDOR BÁSICO
###############################################################################

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}PASO 3: Obteniendo vendedor básico (con plan_venta_id)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

VENDEDOR_BASICO=$(curl -s "$BASE_URL/api/v1/vendedores/$VENDEDOR_ID")
echo $VENDEDOR_BASICO | jq '{
    id,
    nombre_completo,
    email,
    plan_venta_id,
    activo
}'
echo ""

###############################################################################
# PASO 4: OBTENER DETALLE COMPLETO DEL VENDEDOR
###############################################################################

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}PASO 4: Obteniendo DETALLE COMPLETO (con plan completo)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

VENDEDOR_DETALLE=$(curl -s "$BASE_URL/api/v1/vendedores/$VENDEDOR_ID/detalle")

echo -e "${YELLOW}📊 Plan de Venta:${NC}"
echo $VENDEDOR_DETALLE | jq '.plan_venta | {
    id,
    nombre_plan,
    meta_ventas,
    comision_base,
    tipo_plan: .tipo_plan.nombre,
    productos_count: (.productos_asignados | length),
    regiones_count: (.regiones_asignadas | length),
    zonas_count: (.zonas_asignadas | length)
}'

echo -e "${YELLOW}📦 Productos Asignados:${NC}"
echo $VENDEDOR_DETALLE | jq '.plan_venta.productos_asignados[] | {
    producto_id,
    meta_cantidad,
    precio_unitario
}'

echo ""

###############################################################################
# PASO 5: LISTAR VENDEDORES
###############################################################################

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}PASO 5: Listando todos los vendedores${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

VENDEDORES=$(curl -s "$BASE_URL/api/v1/vendedores?activo=true&size=10")
TOTAL=$(echo $VENDEDORES | jq -r '.total')

echo -e "${GREEN}✅ Total de vendedores activos: $TOTAL${NC}"
echo $VENDEDORES | jq '.items[] | {
    id,
    nombre_completo,
    email,
    tiene_plan: (.plan_venta_id != null)
}'
echo ""

###############################################################################
# PASO 6: ACTUALIZAR VENDEDOR
###############################################################################

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}PASO 6: Actualizando vendedor${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

UPDATE_JSON=$(cat <<EOF
{
  "telefono": "+57-311-9999999",
  "observaciones": "Vendedor actualizado por test automatizado",
  "activo": true
}
EOF
)

UPDATE_RESPONSE=$(curl -s -X PUT "$BASE_URL/api/v1/vendedores/$VENDEDOR_ID" \
    -H "Content-Type: application/json" \
    -d "$UPDATE_JSON")

echo -e "${GREEN}✅ Vendedor actualizado${NC}"
echo $UPDATE_RESPONSE | jq '{
    id,
    telefono,
    observaciones,
    updated_at
}'
echo ""

###############################################################################
# PASO 7: DESACTIVAR VENDEDOR
###############################################################################

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}PASO 7: Desactivando vendedor (soft delete)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

DELETE_RESPONSE=$(curl -s -X DELETE "$BASE_URL/api/v1/vendedores/$VENDEDOR_ID")

echo -e "${GREEN}✅ Vendedor desactivado${NC}"
echo $DELETE_RESPONSE | jq '.'
echo ""

###############################################################################
# RESUMEN FINAL
###############################################################################

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              ✅ PRUEBAS COMPLETADAS EXITOSAMENTE          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}📝 IDs generados en esta ejecución:${NC}"
echo -e "   Vendedor ID    : ${GREEN}$VENDEDOR_ID${NC}"
echo -e "   Plan Venta ID  : ${GREEN}$PLAN_VENTA_ID${NC}"
echo -e "   Tipo Rol ID    : ${GREEN}$TIPO_ROL_ID${NC}"
echo -e "   Territorio ID  : ${GREEN}$TERRITORIO_ID${NC}"
echo -e "   Tipo Plan ID   : ${GREEN}$TIPO_PLAN_ID${NC}"
echo -e "   Región ID      : ${GREEN}$REGION_ID${NC}"
echo -e "   Zona ID        : ${GREEN}$ZONA_ID${NC}"
echo ""
echo -e "${BLUE}🔍 Para ver detalles completos:${NC}"
echo -e "   curl $BASE_URL/api/v1/vendedores/$VENDEDOR_ID/detalle | jq '.'"
echo ""

