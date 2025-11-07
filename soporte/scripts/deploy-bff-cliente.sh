#!/bin/bash

set -e

echo "=================================================="
echo "  DEPLOYING BFF-CLIENTE WITH CLIENT INTEGRATION"
echo "=================================================="

# Variables de configuración
AWS_REGION="us-east-1"
ECR_REPO_NAME="medisupply-dev-bff-cliente"
ECS_CLUSTER="orders-cluster"
ECS_SERVICE="medisupply-dev-bff-cliente-svc"
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
    echo_info "Construyendo imagen Docker para BFF-Cliente..."
    
    cd bff-cliente
    
    # Construir la imagen
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
        
        # Mostrar estado del servicio
        echo_info "Estado final del servicio:"
        aws ecs describe-services \
            --cluster $ECS_CLUSTER \
            --services $ECS_SERVICE \
            --region $AWS_REGION \
            --query 'services[0].[serviceName,status,runningCount,desiredCount,deployments[0].status]' \
            --output table
    else
        echo_error "El despliegue falló o tardó demasiado tiempo"
        exit 1
    fi
}

# Función para verificar la salud del servicio
health_check() {
    echo_info "Verificando salud del servicio..."
    
    # Obtener la URL del ALB (esto requiere que esté en los outputs de Terraform)
    ALB_URL=$(aws elbv2 describe-load-balancers --region $AWS_REGION --query "LoadBalancers[?starts_with(LoadBalancerName, 'medisupply-dev-bff-cliente')].DNSName" --output text)
    
    if [ -n "$ALB_URL" ]; then
        echo_info "Probando endpoint de salud: http://$ALB_URL/health"
        
        # Esperar un poco para que el servicio esté listo
        sleep 30
        
        HEALTH_RESPONSE=$(curl -s -w "%{http_code}" http://$ALB_URL/health || echo "000")
        
        if [[ $HEALTH_RESPONSE == *"200"* ]]; then
            echo_success "Health check exitoso - Servicio está funcionando"
            echo_info "URL del BFF-Cliente: http://$ALB_URL"
            echo_info "Documentación API: http://$ALB_URL/docs"
        else
            echo_error "Health check falló - HTTP Status: $HEALTH_RESPONSE"
        fi
    else
        echo_info "No se pudo obtener la URL del ALB, pero el despliegue ECS fue exitoso"
    fi
}

# Función principal
main() {
    echo_info "Iniciando despliegue del BFF-Cliente..."
    echo_info "Región: $AWS_REGION"
    echo_info "ECR Repo: $ECR_REPO_NAME"
    echo_info "ECS Cluster: $ECS_CLUSTER"
    echo_info "ECS Service: $ECS_SERVICE"
    echo ""
    
    check_prerequisites
    build_image
    ecr_login
    push_image
    update_ecs_service
    monitor_deployment
    health_check
    
    echo ""
    echo_success "¡Despliegue del BFF-Cliente completado exitosamente!"
    echo_info "El servicio está listo para recibir peticiones"
}

# Ejecutar función principal
main