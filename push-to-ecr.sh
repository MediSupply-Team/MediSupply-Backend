#!/bin/bash
set -e

echo "🚀 Pushing Docker images to AWS ECR..."
echo "========================================"
echo ""

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
AWS_ACCOUNT_ID="838693051133"
AWS_REGION="us-east-1"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# Función para tag y push
tag_and_push() {
    local LOCAL_IMAGE=$1
    local ECR_REPO=$2
    
    echo -e "${BLUE}📦 Processing $LOCAL_IMAGE...${NC}"
    
    # Tag latest
    echo "  → Tagging as latest..."
    docker tag ${LOCAL_IMAGE}:latest ${ECR_REGISTRY}/${ECR_REPO}:latest
    
    # Tag v1.0.0
    echo "  → Tagging as v1.0.0..."
    docker tag ${LOCAL_IMAGE}:latest ${ECR_REGISTRY}/${ECR_REPO}:v1.0.0
    
    # Push latest
    echo "  → Pushing latest..."
    docker push ${ECR_REGISTRY}/${ECR_REPO}:latest
    
    # Push v1.0.0
    echo "  → Pushing v1.0.0..."
    docker push ${ECR_REGISTRY}/${ECR_REPO}:v1.0.0
    
    echo -e "${GREEN}✅ $LOCAL_IMAGE pushed successfully${NC}"
    echo ""
}

# Procesar cada servicio
tag_and_push "catalogo-service" "medisupply-dev-catalogo-service"
tag_and_push "cliente-service" "medisupply-dev-cliente-service"
tag_and_push "bff-cliente" "medisupply-dev-bff-cliente"
tag_and_push "bff-venta" "medisupply-dev-bff-venta"

echo "========================================"
echo -e "${GREEN}✅ ALL IMAGES PUSHED TO ECR!${NC}"
echo "========================================"
echo ""
echo "Verify images in ECR:"
echo "  aws ecr describe-images --repository-name medisupply-dev-catalogo-service --region $AWS_REGION"
echo "  aws ecr describe-images --repository-name medisupply-dev-cliente-service --region $AWS_REGION"
echo "  aws ecr describe-images --repository-name medisupply-dev-bff-cliente --region $AWS_REGION"
echo "  aws ecr describe-images --repository-name medisupply-dev-bff-venta --region $AWS_REGION"
echo ""

