#!/bin/bash
set -e

echo "🏗️  Building Docker images for AWS ECS Fargate..."
echo "=================================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Servicios a construir
SERVICES=("catalogo-service" "cliente-service" "bff-cliente" "bff-venta")

# Verificar que buildx esté disponible
if ! docker buildx version > /dev/null 2>&1; then
    echo "❌ Docker buildx no está disponible. Instalando..."
    docker buildx create --use --name multiarch
else
    echo "✅ Docker buildx disponible"
fi

echo ""

# Construir cada servicio
for SERVICE in "${SERVICES[@]}"; do
    echo -e "${BLUE}📦 Building $SERVICE...${NC}"
    
    docker buildx build \
        --platform linux/amd64 \
        --load \
        -t $SERVICE:latest \
        -t $SERVICE:v1.0.0 \
        ./$SERVICE
    
    echo -e "${GREEN}✅ $SERVICE built successfully${NC}"
    echo ""
done

echo ""
echo "=================================================="
echo -e "${YELLOW}📊 IMAGE SIZES:${NC}"
echo "=================================================="
docker images | grep -E "(catalogo|cliente|bff)" | awk '{printf "%-35s %10s\n", $1":"$2, $7$8}'

echo ""
echo "=================================================="
echo -e "${YELLOW}🔍 ARCHITECTURES:${NC}"
echo "=================================================="
for SERVICE in "${SERVICES[@]}"; do
    ARCH=$(docker inspect $SERVICE:latest 2>/dev/null | jq -r '.[0].Architecture' || echo "ERROR")
    if [ "$ARCH" == "amd64" ]; then
        echo -e "${GREEN}✅ $SERVICE: $ARCH${NC}"
    else
        echo -e "${YELLOW}⚠️  $SERVICE: $ARCH${NC}"
    fi
done

echo ""
echo "=================================================="
echo -e "${YELLOW}🏥 HEALTHCHECKS:${NC}"
echo "=================================================="
for SERVICE in "${SERVICES[@]}"; do
    HC=$(docker inspect $SERVICE:latest 2>/dev/null | jq -r '.[0].Config.Healthcheck.Test[1]' || echo "none")
    if [ "$HC" != "none" ] && [ "$HC" != "null" ]; then
        echo -e "${GREEN}✅ $SERVICE: configured${NC}"
    else
        echo -e "${YELLOW}⚠️  $SERVICE: not configured${NC}"
    fi
done

echo ""
echo "=================================================="
echo -e "${GREEN}✅ ALL IMAGES BUILT SUCCESSFULLY!${NC}"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Test images locally (see FASE-3-BUILD-IMAGES.md)"
echo "2. Push to AWS ECR"
echo "3. Deploy with Terraform (FASE 4)"

