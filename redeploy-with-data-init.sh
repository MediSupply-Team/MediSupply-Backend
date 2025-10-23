#!/bin/bash
set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   🚀 REDESPLIEGUE CON INICIALIZACIÓN AUTOMÁTICA DE DATOS    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

PROJECT="medisupply"
ENV="dev"
REGION="us-east-1"
AWS_ACCOUNT_ID="838693051133"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================
# FUNCIÓN: Build y Push de imagen
# ============================================================
build_and_push() {
    local service_name=$1
    local service_dir=$2
    
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  📦 ${service_name}${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    
    ECR_REPO="${PROJECT}-${ENV}-${service_name}"
    ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPO}"
    
    echo -e "${YELLOW}🔨 Construyendo imagen Docker...${NC}"
    docker build --platform linux/amd64 -t "${ECR_REPO}:latest" "$service_dir"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Error al construir imagen de $service_name${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ Imagen construida${NC}"
    
    echo -e "${YELLOW}🏷️  Etiquetando imagen...${NC}"
    docker tag "${ECR_REPO}:latest" "${ECR_URI}:latest"
    
    echo -e "${YELLOW}📤 Subiendo a ECR...${NC}"
    docker push "${ECR_URI}:latest"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Error al subir imagen de $service_name${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ Imagen subida a ECR${NC}"
    echo ""
}

# ============================================================
# FUNCIÓN: Forzar redespliegue del servicio ECS
# ============================================================
force_redeploy() {
    local service_name=$1
    
    echo -e "${YELLOW}🔄 Forzando redespliegue de $service_name...${NC}"
    
    aws ecs update-service \
        --cluster "${PROJECT}-${ENV}-cluster" \
        --service "${PROJECT}-${ENV}-${service_name}-svc" \
        --force-new-deployment \
        --region "$REGION" \
        > /dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Redespliegue iniciado${NC}"
    else
        echo -e "${RED}❌ Error al redesplegar $service_name${NC}"
    fi
    echo ""
}

# ============================================================
# MAIN
# ============================================================

echo -e "${YELLOW}🔐 Autenticando con ECR...${NC}"
aws ecr get-login-password --region "$REGION" | \
    docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error al autenticar con ECR${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Autenticado con ECR${NC}"
echo ""

# Desplegar cliente-service
build_and_push "cliente-service" "cliente-service"
force_redeploy "cliente-service"

# Desplegar catalogo-service
build_and_push "catalogo-service" "catalogo-service"
force_redeploy "catalogo-service"

# Resumen
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║              🎉 REDESPLIEGUE COMPLETADO                       ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${YELLOW}⏳ Esperando a que los servicios estén listos...${NC}"
echo ""
echo -e "${BLUE}Puedes monitorear el progreso con:${NC}"
echo ""
echo "  Cliente Service:"
echo "  aws ecs describe-services --cluster ${PROJECT}-${ENV}-cluster --services ${PROJECT}-${ENV}-cliente-service-svc --region $REGION"
echo ""
echo "  Catalogo Service:"
echo "  aws ecs describe-services --cluster ${PROJECT}-${ENV}-cluster --services ${PROJECT}-${ENV}-catalogo-service-svc --region $REGION"
echo ""
echo "  CloudWatch Logs (Cliente):"
echo "  aws logs tail /ecs/${PROJECT}-${ENV}-cliente-service --follow --region $REGION"
echo ""
echo "  CloudWatch Logs (Catalogo):"
echo "  aws logs tail /ecs/${PROJECT}-${ENV}-catalogo-service --follow --region $REGION"
echo ""
echo -e "${GREEN}✅ Los contenedores ahora ejecutarán automáticamente la inicialización de datos al arrancar${NC}"
echo ""


