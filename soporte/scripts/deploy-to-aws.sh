#!/bin/bash

# Script para desplegar catalogo-service y bff-venta a AWS
# Genera imágenes con tags basados en fecha/hora

set -e

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuración AWS
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Generar timestamp
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Despliegue a AWS - MediSupply Backend${NC}"
echo -e "${BLUE}  Timestamp: ${TIMESTAMP}${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Verificar AWS CLI
echo -e "${YELLOW}🔐 Paso 1: Verificando credenciales AWS...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ Error: No se pudo autenticar con AWS${NC}"
    echo -e "${YELLOW}   Ejecuta: aws configure${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Credenciales AWS válidas${NC}"
echo ""

# Login a ECR
echo -e "${YELLOW}🔐 Paso 2: Login a ECR...${NC}"
ECR_PASSWORD=$(aws ecr get-login-password --region $AWS_REGION)
echo $ECR_PASSWORD | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com || {
    echo -e "${RED}❌ Error en login a ECR${NC}"
    echo -e "${YELLOW}   Intenta manualmente:${NC}"
    echo -e "${YELLOW}   aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com${NC}"
    exit 1
}
echo -e "${GREEN}✅ Login a ECR exitoso${NC}"
echo ""

# ==================================================
# CATALOGO-SERVICE
# ==================================================
echo -e "${YELLOW}📦 Paso 3: Construyendo catalogo-service...${NC}"
CATALOGO_IMAGE_NAME="catalogo-service-${TIMESTAMP}"
CATALOGO_ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/medisupply-dev-catalogo-service"

docker build --platform linux/amd64 -t ${CATALOGO_IMAGE_NAME} ./catalogo-service
echo -e "${GREEN}✅ Imagen construida: ${CATALOGO_IMAGE_NAME}${NC}"
echo ""

echo -e "${YELLOW}🏷️  Paso 4: Taggeando catalogo-service...${NC}"
docker tag ${CATALOGO_IMAGE_NAME} ${CATALOGO_ECR_REPO}:${TIMESTAMP}
docker tag ${CATALOGO_IMAGE_NAME} ${CATALOGO_ECR_REPO}:latest
echo -e "${GREEN}✅ Tags aplicados${NC}"
echo ""

echo -e "${YELLOW}☁️  Paso 5: Subiendo catalogo-service a ECR...${NC}"
docker push ${CATALOGO_ECR_REPO}:${TIMESTAMP}
docker push ${CATALOGO_ECR_REPO}:latest
echo -e "${GREEN}✅ Imagen subida: ${CATALOGO_ECR_REPO}:${TIMESTAMP}${NC}"
echo ""

# ==================================================
# BFF-VENTA
# ==================================================
echo -e "${YELLOW}📦 Paso 6: Construyendo bff-venta...${NC}"
BFF_VENTA_IMAGE_NAME="bff-venta-${TIMESTAMP}"
BFF_VENTA_ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/medisupply-dev-bff-venta"

docker build --platform linux/amd64 -t ${BFF_VENTA_IMAGE_NAME} ./bff-venta
echo -e "${GREEN}✅ Imagen construida: ${BFF_VENTA_IMAGE_NAME}${NC}"
echo ""

echo -e "${YELLOW}🏷️  Paso 7: Taggeando bff-venta...${NC}"
docker tag ${BFF_VENTA_IMAGE_NAME} ${BFF_VENTA_ECR_REPO}:${TIMESTAMP}
docker tag ${BFF_VENTA_IMAGE_NAME} ${BFF_VENTA_ECR_REPO}:latest
echo -e "${GREEN}✅ Tags aplicados${NC}"
echo ""

echo -e "${YELLOW}☁️  Paso 8: Subiendo bff-venta a ECR...${NC}"
docker push ${BFF_VENTA_ECR_REPO}:${TIMESTAMP}
docker push ${BFF_VENTA_ECR_REPO}:latest
echo -e "${GREEN}✅ Imagen subida: ${BFF_VENTA_ECR_REPO}:${TIMESTAMP}${NC}"
echo ""

# ==================================================
# DESPLIEGUE EN ECS
# ==================================================
echo -e "${YELLOW}🚀 Paso 9: Forzando redespliegue en ECS...${NC}"

# Catalogo-service
echo -e "${BLUE}   Actualizando catalogo-service...${NC}"
aws ecs update-service \
    --cluster medisupply-dev-cluster \
    --service medisupply-dev-catalogo-service \
    --force-new-deployment \
    --region $AWS_REGION > /dev/null 2>&1

echo -e "${GREEN}   ✅ Catalogo-service actualizado${NC}"

# BFF-Venta
echo -e "${BLUE}   Actualizando bff-venta...${NC}"
aws ecs update-service \
    --cluster medisupply-dev-cluster \
    --service medisupply-dev-bff-venta \
    --force-new-deployment \
    --region $AWS_REGION > /dev/null 2>&1

echo -e "${GREEN}   ✅ BFF-Venta actualizado${NC}"
echo ""

# ==================================================
# RESUMEN
# ==================================================
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}✨ Despliegue completado exitosamente!${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "${YELLOW}📝 Imágenes desplegadas:${NC}"
echo -e "   • catalogo-service: ${CATALOGO_ECR_REPO}:${TIMESTAMP}"
echo -e "   • bff-venta:        ${BFF_VENTA_ECR_REPO}:${TIMESTAMP}"
echo ""
echo -e "${YELLOW}🔍 Verificar despliegue:${NC}"
echo -e "   aws ecs describe-services --cluster medisupply-dev-cluster --services medisupply-dev-catalogo-service --region $AWS_REGION --query 'services[0].deployments' --output table"
echo ""
echo -e "   aws ecs describe-services --cluster medisupply-dev-cluster --services medisupply-dev-bff-venta --region $AWS_REGION --query 'services[0].deployments' --output table"
echo ""
echo -e "${BLUE}================================================${NC}"

