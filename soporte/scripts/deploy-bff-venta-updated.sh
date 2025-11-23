#!/bin/bash

set -e

echo "=================================================="
echo "  DEPLOYING BFF-VENTA WITH CATALOG INTEGRATION"
echo "=================================================="

# Variables de configuración
AWS_REGION="us-east-1"
ECR_REPO_NAME="medisupply-dev-bff-venta"
ECS_CLUSTER="orders-cluster"
ECS_SERVICE="medisupply-dev-bff-venta-svc"
IMAGE_TAG="latest"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() { echo -e "${YELLOW}[INFO]${NC} $1"; }
echo_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Función para verificar prerrequisitos
check_prerequisites() {
    echo_info "Verificando prerrequisitos..."
    
    # Verificar AWS CLI
    if ! command -v aws &> /dev/null; then
        echo_error "AWS CLI no está instalado"
        exit 1
    fi
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        echo_error "Docker no está instalado"
        exit 1
    fi
    
    # Verificar autenticación AWS
    if ! aws sts get-caller-identity &> /dev/null; then
        echo_error "No hay credenciales AWS configuradas"
        exit 1
    fi
    
    echo_success "Prerrequisitos OK"
}

# Función para construir imagen Docker
build_docker_image() {
    echo_info "Construyendo imagen Docker para bff-venta..."
    
    cd bff-venta
    
    # Construir imagen con plataforma específica para AWS Fargate
    docker build --platform linux/amd64 -t $ECR_REPO_NAME:$IMAGE_TAG .
    
    if [ $? -eq 0 ]; then
        echo_success "Imagen Docker construida exitosamente"
    else
        echo_error "Error construyendo imagen Docker"
        exit 1
    fi
    
    cd ..
}

# Función para obtener URI de ECR
get_ecr_uri() {
    echo_info "Obteniendo URI de ECR..."
    
    # Obtener account ID
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    ECR_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME"
    
    echo_success "ECR URI: $ECR_URI"
}

# Función para verificar repositorio ECR
ensure_ecr_repo() {
    echo_info "Verificando repositorio ECR..."
    
    # Verificar si el repositorio existe
    if aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $AWS_REGION &> /dev/null; then
        echo_success "Repositorio ECR existe"
    else
        echo_error "Repositorio ECR no existe"
        exit 1
    fi
}

# Función para hacer push a ECR
push_to_ecr() {
    echo_info "Subiendo imagen a ECR..."
    
    # Login a ECR
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI
    
    # Tag y push
    docker tag $ECR_REPO_NAME:$IMAGE_TAG $ECR_URI:$IMAGE_TAG
    docker push $ECR_URI:$IMAGE_TAG
    
    echo_success "Imagen subida a ECR: $ECR_URI:$IMAGE_TAG"
}

# Función para actualizar servicio ECS
update_ecs_service() {
    echo_info "Actualizando servicio ECS con nueva imagen..."
    
    # Forzar nuevo deployment del servicio
    aws ecs update-service \
        --cluster $ECS_CLUSTER \
        --service $ECS_SERVICE \
        --force-new-deployment \
        --region $AWS_REGION > /dev/null
    
    echo_success "Deployment iniciado"
    
    # Esperar que el servicio se estabilice
    echo_info "Esperando que el servicio se estabilice..."
    aws ecs wait services-stable --cluster $ECS_CLUSTER --services $ECS_SERVICE --region $AWS_REGION
    
    echo_success "Servicio estabilizado"
}

# Función para verificar health del servicio
verify_deployment() {
    echo_info "Verificando deployment..."
    
    # Obtener información del servicio
    SERVICE_INFO=$(aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --region $AWS_REGION --query 'services[0].[serviceName,status,runningCount,desiredCount]' --output text)
    
    echo "Estado del servicio: $SERVICE_INFO"
    
    # Verificar si hay tareas ejecutándose
    RUNNING_COUNT=$(echo $SERVICE_INFO | awk '{print $3}')
    DESIRED_COUNT=$(echo $SERVICE_INFO | awk '{print $4}')
    
    if [ "$RUNNING_COUNT" = "$DESIRED_COUNT" ] && [ "$RUNNING_COUNT" != "0" ]; then
        echo_success "Deployment exitoso: $RUNNING_COUNT/$DESIRED_COUNT tareas ejecutándose"
        return 0
    else
        echo_error "Deployment falló: $RUNNING_COUNT/$DESIRED_COUNT tareas ejecutándose"
        return 1
    fi
}

# Función para probar endpoints
test_endpoints() {
    echo_info "Probando endpoints de catalog..."
    
    # Obtener URL del ALB
    ALB_DNS=$(aws elbv2 describe-load-balancers --names medisupply-dev-bff-venta-alb --region $AWS_REGION --query 'LoadBalancers[0].DNSName' --output text)
    BFF_URL="http://$ALB_DNS"
    
    echo_info "URL Base: $BFF_URL"
    
    # Probar health endpoint
    echo_info "Probando /health..."
    if curl -f -s "$BFF_URL/health" > /dev/null; then
        echo_success "Health endpoint OK"
    else
        echo_error "Health endpoint falló"
    fi
    
    # Probar catalog endpoint
    echo_info "Probando /api/v1/catalog/items..."
    CATALOG_RESPONSE=$(curl -s "$BFF_URL/api/v1/catalog/items")
    
    if echo "$CATALOG_RESPONSE" | grep -q "items"; then
        echo_success "Catalog endpoint OK - Respuesta con datos"
        echo "$CATALOG_RESPONSE" | head -n 10
    else
        echo_error "Catalog endpoint falló"
        echo "Respuesta: $CATALOG_RESPONSE"
    fi
}

# Función principal
main() {
    echo_info "Iniciando deployment de bff-venta con integración de catálogo..."
    
    check_prerequisites
    get_ecr_uri
    ensure_ecr_repo
    build_docker_image
    push_to_ecr
    update_ecs_service
    
    if verify_deployment; then
        echo_success "BFF-Venta desplegado exitosamente!"
        test_endpoints
        
        echo ""
        echo "=================================================="
        echo "  DEPLOYMENT COMPLETO"
        echo "=================================================="
        echo "ECR Image: $ECR_URI:$IMAGE_TAG"
        echo "ECS Service: $ECS_SERVICE"
        echo "Cluster: $ECS_CLUSTER"
        echo ""
        echo "Endpoints de Catálogo disponibles:"
        echo "- GET /api/v1/catalog/items"
        echo "- GET /api/v1/catalog/items/{id}"
        echo "- GET /api/v1/catalog/items/{id}/inventario"
        echo "- POST /api/v1/catalog/items"
        echo "- PUT /api/v1/catalog/items/{id}"
        echo "- DELETE /api/v1/catalog/items/{id}"
        echo ""
        echo "Para verificar logs:"
        echo "aws logs tail /ecs/$ECS_SERVICE --follow --region $AWS_REGION"
        echo ""
    else
        echo_error "Deployment falló"
        exit 1
    fi
}

# Ejecutar función principal
main "$@"