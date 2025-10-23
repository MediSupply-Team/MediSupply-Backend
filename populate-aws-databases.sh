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
    
    # Ejecutar el script SQL de inicialización
    echo -e "${YELLOW}🔄 Cargando datos iniciales desde 001_init.sql...${NC}"
    
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        -f cliente-service/data/001_init.sql > /dev/null 2>&1
    
    # Verificar resultado
    NEW_COUNT=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM cliente;" | tr -d ' ')
    COMPRAS_COUNT=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM compra_historico;" | tr -d ' ')
    
    echo -e "${GREEN}✅ CLIENTE-SERVICE POBLADO EXITOSAMENTE${NC}"
    echo "   📊 Clientes: $NEW_COUNT"
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
    
    # Ejecutar el script SQL de inicialización
    echo -e "${YELLOW}🔄 Cargando datos iniciales desde 001_init.sql...${NC}"
    
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        -f catalogo-service/data/001_init.sql > /dev/null 2>&1
    
    # Verificar resultado
    NEW_PROD_COUNT=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM producto;" | tr -d ' ')
    INV_COUNT=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM inventario;" | tr -d ' ')
    
    echo -e "${GREEN}✅ CATALOGO-SERVICE POBLADO EXITOSAMENTE${NC}"
    echo "   📦 Productos: $NEW_PROD_COUNT"
    echo "   🏭 Inventarios: $INV_COUNT"
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


