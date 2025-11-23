#!/bin/bash
set -e

# Script para poblar las bases de datos en AWS con datos iniciales

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   🗄️  POBLACIÓN DE BASES DE DATOS AWS - MEDISUPPLY          ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

PROJECT="medisupply"
ENV="dev"
REGION="us-east-1"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================
# FUNCIÓN: Poblar Cliente Service
# ============================================================
populate_cliente_service() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  1. CLIENTE-SERVICE${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    
    # Obtener credenciales de la base de datos
    echo -e "${YELLOW}📥 Obteniendo credenciales de base de datos...${NC}"
    SECRET_ARN="${PROJECT}-${ENV}-cliente-service-db-credentials"
    
    DB_CREDS=$(aws secretsmanager get-secret-value \
        --secret-id "$SECRET_ARN" \
        --region "$REGION" \
        --query SecretString --output text)
    
    DB_URL=$(echo "$DB_CREDS" | jq -r '.database_url')
    DB_HOST=$(echo "$DB_CREDS" | jq -r '.endpoint' | cut -d':' -f1)
    DB_USER=$(echo "$DB_CREDS" | jq -r '.username')
    DB_PASS=$(echo "$DB_CREDS" | jq -r '.password')
    DB_NAME=$(echo "$DB_CREDS" | jq -r '.dbname')
    
    echo -e "${GREEN}✅ Credenciales obtenidas${NC}"
    echo "   Host: $DB_HOST"
    echo "   Database: $DB_NAME"
    echo ""
    
    # Verificar si ya hay datos
    echo -e "${YELLOW}🔍 Verificando datos existentes...${NC}"
    CLIENT_COUNT=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM cliente;" 2>/dev/null || echo "0")
    CLIENT_COUNT=$(echo "$CLIENT_COUNT" | tr -d ' ')
    
    if [ "$CLIENT_COUNT" != "0" ] && [ -n "$CLIENT_COUNT" ]; then
        echo -e "${YELLOW}⚠️  La base de datos ya tiene $CLIENT_COUNT clientes${NC}"
        echo -e "${YELLOW}   ¿Deseas recargar los datos? (s/N)${NC}"
        read -r response
        if [[ ! "$response" =~ ^[Ss]$ ]]; then
            echo -e "${BLUE}⏭️  Saltando cliente-service${NC}"
            echo ""
            return
        fi
    fi
    
    # Ejecutar los scripts SQL en orden
    echo -e "${YELLOW}🔄 Cargando datos iniciales (6 archivos SQL)...${NC}"
    
    # 1. Estructura base y clientes
    echo "   📄 [1/6] 001_init.sql - Estructura base y clientes..."
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        -f cliente-service/data/001_init.sql > /dev/null 2>&1
    
    # 2. Catálogos de soporte (roles, territorios, planes, regiones, zonas)
    echo "   📄 [2/6] 004_catalogos_vendedor.sql - Catálogos de soporte..."
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        -f cliente-service/data/004_catalogos_vendedor.sql > /dev/null 2>&1
    
    # 3. Vendedores con datos reales
    echo "   📄 [3/6] 002_vendedores.sql - Vendedores dummy reales..."
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        -f cliente-service/data/002_vendedores.sql > /dev/null 2>&1
    
    # 4. Extensión de vendedores (FK a catálogos)
    echo "   📄 [4/6] 005_vendedor_extended.sql - Extensión de vendedores..."
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        -f cliente-service/data/005_vendedor_extended.sql > /dev/null 2>&1
    
    # 5. Planes de venta
    echo "   📄 [5/6] 006_plan_venta.sql - Planes de venta..."
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        -f cliente-service/data/006_plan_venta.sql > /dev/null 2>&1
    
    # 6. Asignar vendedores a clientes
    echo "   📄 [6/6] 003_asignar_vendedores_clientes.sql - Asignación vendedores..."
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        -f cliente-service/data/003_asignar_vendedores_clientes.sql > /dev/null 2>&1
    
    # Verificar resultados
    NEW_COUNT=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM cliente;" | tr -d ' ')
    VENDEDORES_COUNT=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM vendedor;" | tr -d ' ')
    PLANES_COUNT=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM plan_venta;" | tr -d ' ')
    COMPRAS_COUNT=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM compra_historico;" | tr -d ' ')
    
    echo -e "${GREEN}✅ CLIENTE-SERVICE POBLADO EXITOSAMENTE${NC}"
    echo "   👥 Vendedores: $VENDEDORES_COUNT"
    echo "   📊 Clientes: $NEW_COUNT"
    echo "   🎯 Planes de Venta: $PLANES_COUNT"
    echo "   📦 Compras: $COMPRAS_COUNT"
    echo ""
}

# ============================================================
# FUNCIÓN: Poblar Catalogo Service
# ============================================================
populate_catalogo_service() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  2. CATALOGO-SERVICE${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    
    # Obtener credenciales de la base de datos
    echo -e "${YELLOW}📥 Obteniendo credenciales de base de datos...${NC}"
    SECRET_ARN="${PROJECT}-${ENV}-catalogo-db-credentials-v2"
    
    DB_CREDS=$(aws secretsmanager get-secret-value \
        --secret-id "$SECRET_ARN" \
        --region "$REGION" \
        --query SecretString --output text)
    
    DB_URL=$(echo "$DB_CREDS" | jq -r '.database_url')
    DB_HOST=$(echo "$DB_CREDS" | jq -r '.endpoint' | cut -d':' -f1)
    DB_USER=$(echo "$DB_CREDS" | jq -r '.username')
    DB_PASS=$(echo "$DB_CREDS" | jq -r '.password')
    DB_NAME=$(echo "$DB_CREDS" | jq -r '.dbname')
    
    echo -e "${GREEN}✅ Credenciales obtenidas${NC}"
    echo "   Host: $DB_HOST"
    echo "   Database: $DB_NAME"
    echo ""
    
    # Verificar si ya hay datos
    echo -e "${YELLOW}🔍 Verificando datos existentes...${NC}"
    PROD_COUNT=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM producto;" 2>/dev/null || echo "0")
    PROD_COUNT=$(echo "$PROD_COUNT" | tr -d ' ')
    
    if [ "$PROD_COUNT" != "0" ] && [ -n "$PROD_COUNT" ]; then
        echo -e "${YELLOW}⚠️  La base de datos ya tiene $PROD_COUNT productos${NC}"
        echo -e "${YELLOW}   ¿Deseas recargar los datos? (s/N)${NC}"
        read -r response
        if [[ ! "$response" =~ ^[Ss]$ ]]; then
            echo -e "${BLUE}⏭️  Saltando catalogo-service${NC}"
            echo ""
            return
        fi
    fi
    
    # Ejecutar los scripts SQL en orden
    echo -e "${YELLOW}🔄 Cargando datos iniciales (6 archivos SQL)...${NC}"
    
    # 1. Estructura base
    echo "   📄 [1/6] 001_init.sql - Estructura base..."
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        -f catalogo-service/data/001_init.sql > /dev/null 2>&1
    
    # 2. Productos con UUID
    echo "   📄 [2/6] 002_seed_data.sql - Productos con UUID..."
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        -f catalogo-service/data/002_seed_data.sql > /dev/null 2>&1
    
    # 3. Movimientos de inventario
    echo "   📄 [3/6] 002_movimientos.sql - Movimientos de inventario..."
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        -f catalogo-service/data/002_movimientos.sql > /dev/null 2>&1
    
    # 4. Campos adicionales de proveedor
    echo "   📄 [4/6] 003_campos_proveedor.sql - Campos adicionales de proveedor..."
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        -f catalogo-service/data/003_campos_proveedor.sql > /dev/null 2>&1
    
    # 5. Proveedores dummy
    echo "   📄 [5/6] 004_proveedores.sql - Proveedores dummy..."
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        -f catalogo-service/data/004_proveedores.sql > /dev/null 2>&1
    
    # 6. Bodegas (NUEVO)
    echo "   📄 [6/6] 005_bodegas.sql - Bodegas..."
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        -f catalogo-service/data/005_bodegas.sql > /dev/null 2>&1
    
    # Verificar resultados
    NEW_PROD_COUNT=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM producto;" | tr -d ' ')
    INV_COUNT=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM inventario;" | tr -d ' ')
    PROV_COUNT=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM proveedor;" | tr -d ' ')
    BODEGA_COUNT=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM bodega;" | tr -d ' ')
    
    echo -e "${GREEN}✅ CATALOGO-SERVICE POBLADO EXITOSAMENTE${NC}"
    echo "   📦 Productos: $NEW_PROD_COUNT"
    echo "   🏭 Inventarios: $INV_COUNT"
    echo "   🏢 Proveedores: $PROV_COUNT"
    echo "   📍 Bodegas: $BODEGA_COUNT"
    echo ""
}

# ============================================================
# MAIN
# ============================================================

# Verificar dependencias
echo -e "${YELLOW}🔍 Verificando dependencias...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI no está instalado${NC}"
    exit 1
fi

if ! command -v psql &> /dev/null; then
    echo -e "${RED}❌ PostgreSQL client (psql) no está instalado${NC}"
    echo "   Instalar en macOS: brew install postgresql"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo -e "${RED}❌ jq no está instalado${NC}"
    echo "   Instalar en macOS: brew install jq"
    exit 1
fi

echo -e "${GREEN}✅ Todas las dependencias están disponibles${NC}"
echo ""

# Ejecutar población
populate_cliente_service
populate_catalogo_service

# Resumen final
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║               🎉 POBLACIÓN COMPLETADA                         ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}✅ Ahora puedes probar los endpoints:${NC}"
echo ""
echo "   Cliente Service:"
echo "   curl http://medisupply-dev-bff-cliente-alb-1673122993.us-east-1.elb.amazonaws.com/api/v1/client/?limite=10"
echo ""
echo "   Catalogo Service:"
echo "   curl http://medisupply-dev-catalogo-alb-1899906226.us-east-1.elb.amazonaws.com/api/productos?limite=10"
echo ""


