#!/bin/bash

set -e

echo "=================================================="
echo "    DEPLOYING CLIENTE-SERVICE TO AWS ECS"
echo "=================================================="

# Variables de configuración
AWS_REGION="us-east-1"
ECR_REPO_NAME="medisupply-dev-cliente-service"
ECS_CLUSTER="orders-cluster"
ECS_SERVICE="medisupply-dev-cliente-service-svc"
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

# Función para obtener la cuenta AWS
get_aws_account() {
    aws sts get-caller-identity --query Account --output text
}

# Función para construir la imagen Docker
build_image() {
    echo_info "Construyendo imagen Docker para Cliente-Service..."
    
    cd cliente-service
    
    # Construir la imagen para arquitectura AMD64 (compatible con AWS ECS)
    docker build --platform linux/amd64 -t $ECR_REPO_NAME:$IMAGE_TAG .
    
    if [ $? -eq 0 ]; then
        echo_success "Imagen construida exitosamente"
    else
        echo_error "Error construyendo la imagen"
        exit 1
    fi
    
    cd ..
}

# Función para hacer login en ECR
ecr_login() {
    echo_info "Haciendo login en ECR..."
    
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $(get_aws_account).dkr.ecr.$AWS_REGION.amazonaws.com
    
    if [ $? -eq 0 ]; then
        echo_success "Login en ECR exitoso"
    else
        echo_error "Error en login ECR"
        exit 1
    fi
}

# Función para pushear la imagen
push_image() {
    echo_info "Pusheando imagen a ECR..."
    
    AWS_ACCOUNT=$(get_aws_account)
    ECR_URI="$AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME"
    
    # Taggear la imagen
    docker tag $ECR_REPO_NAME:$IMAGE_TAG $ECR_URI:$IMAGE_TAG
    
    # Push
    docker push $ECR_URI:$IMAGE_TAG
    
    if [ $? -eq 0 ]; then
        echo_success "Imagen pusheada exitosamente a $ECR_URI:$IMAGE_TAG"
    else
        echo_error "Error pusheando la imagen"
        exit 1
    fi
}

# Función para actualizar el servicio ECS
update_ecs_service() {
    echo_info "Actualizando servicio ECS..."
    
    # Verificar que el cluster existe
    if ! aws ecs describe-clusters --clusters $ECS_CLUSTER --region $AWS_REGION &> /dev/null; then
        echo_error "Cluster $ECS_CLUSTER no existe"
        exit 1
    fi
    
    # Verificar que el servicio existe
    if ! aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --region $AWS_REGION &> /dev/null; then
        echo_error "Servicio $ECS_SERVICE no existe en el cluster $ECS_CLUSTER"
        echo_info "Los servicios disponibles son:"
        aws ecs list-services --cluster $ECS_CLUSTER --region $AWS_REGION --query 'serviceArns' --output table
        exit 1
    fi
    
    # Forzar nuevo despliegue
    aws ecs update-service \
        --cluster $ECS_CLUSTER \
        --service $ECS_SERVICE \
        --force-new-deployment \
        --region $AWS_REGION \
        > /dev/null
    
    if [ $? -eq 0 ]; then
        echo_success "Servicio ECS actualizado, iniciando nuevo despliegue"
    else
        echo_error "Error actualizando servicio ECS"
        exit 1
    fi
}

# Función para monitorear el despliegue
monitor_deployment() {
    echo_info "Monitoreando despliegue..."
    
    echo "Esperando que el despliegue se complete..."
    
    # Esperar hasta que el despliegue esté estable
    aws ecs wait services-stable \
        --cluster $ECS_CLUSTER \
        --services $ECS_SERVICE \
        --region $AWS_REGION
    
    if [ $? -eq 0 ]; then
        echo_success "Despliegue completado exitosamente"
    else
        echo_error "El despliegue falló o tomó demasiado tiempo"
        exit 1
    fi
}

# Función para verificar el estado final
check_deployment_status() {
    echo_info "Verificando estado final del despliegue..."
    
    # Obtener información del servicio
    aws ecs describe-services \
        --cluster $ECS_CLUSTER \
        --services $ECS_SERVICE \
        --region $AWS_REGION \
        --query 'services[0].[serviceName,status,runningCount,desiredCount]' \
        --output table
    
    # Mostrar logs recientes
    echo_info "Logs recientes del servicio:"
    aws logs tail /ecs/medisupply-dev-cliente-service --since 2m --region $AWS_REGION --limit 10
}

# Función principal
main() {
    echo_info "Iniciando despliegue de Cliente-Service..."
    
    check_prerequisites
    build_image
    ecr_login
    push_image
    update_ecs_service
    monitor_deployment
    check_deployment_status
    
    echo ""
    echo_success "=================================================="
    echo_success "   CLIENTE-SERVICE DESPLEGADO EXITOSAMENTE!"
    echo_success "=================================================="
    echo ""
    echo_info "Endpoints disponibles:"
    echo "  Health Check: http://internal-medisupply-dev-cliente-alb-2066104303.us-east-1.elb.amazonaws.com/api/health"
    echo "  API Clients:  http://medisupply-dev-bff-cliente-alb-1141787956.us-east-1.elb.amazonaws.com/api/v1/client/"
}

# Ejecutar función principal
main "$@"