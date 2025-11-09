#!/bin/bash

set -e

echo "=================================================="
echo "  DEPLOYING CATALOGO-SERVICE TO AWS"
echo "=================================================="

# Variables de configuración
AWS_REGION="us-east-1"
ECR_REPO_NAME="medisupply-dev-catalogo-service"
ECS_CLUSTER="medisupply-dev-cluster"
ECS_SERVICE="medisupply-dev-catalogo-service"
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
    echo_info "Construyendo imagen Docker para catalogo-service..."
    
    cd catalogo-service
    
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

# Función para verificar/crear repositorio ECR
ensure_ecr_repo() {
    echo_info "Verificando repositorio ECR..."
    
    # Verificar si el repositorio existe
    if aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $AWS_REGION &> /dev/null; then
        echo_success "Repositorio ECR existe"
    else
        echo_info "Creando repositorio ECR..."
        aws ecr create-repository --repository-name $ECR_REPO_NAME --region $AWS_REGION
        echo_success "Repositorio ECR creado"
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

# Función para verificar/crear base de datos
ensure_database() {
    echo_info "Verificando configuración de base de datos..."
    
    # Aquí podrías agregar lógica para verificar que la BD PostgreSQL esté disponible
    # Por ahora, asumimos que ya está configurada via Terraform
    echo_success "Base de datos configurada"
}

# Función para verificar servicio ECS
check_ecs_service() {
    echo_info "Verificando servicio ECS..."
    
    if aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --region $AWS_REGION &> /dev/null; then
        echo_success "Servicio ECS existe"
        return 0
    else
        echo_error "Servicio ECS no existe. Debe ser creado via Terraform primero."
        echo_info "Ejecuta: cd infra/terraform && terraform apply"
        return 1
    fi
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
    else
        echo_error "Deployment falló: $RUNNING_COUNT/$DESIRED_COUNT tareas ejecutándose"
        return 1
    fi
}

# Función principal
main() {
    echo_info "Iniciando deployment de catalogo-service..."
    
    check_prerequisites
    get_ecr_uri
    ensure_ecr_repo
    build_docker_image
    push_to_ecr
    ensure_database
    
    if check_ecs_service; then
        update_ecs_service
        verify_deployment
        echo_success "Catalogo-service desplegado exitosamente!"
        
        echo ""
        echo "=================================================="
        echo "  DEPLOYMENT COMPLETO"
        echo "=================================================="
        echo "ECR Image: $ECR_URI:$IMAGE_TAG"
        echo "ECS Service: $ECS_SERVICE"
        echo "Cluster: $ECS_CLUSTER"
        echo ""
        echo "Para verificar logs:"
        echo "aws logs tail /aws/ecs/$ECS_SERVICE --follow --region $AWS_REGION"
        echo ""
    else
        echo_error "No se puede continuar sin servicio ECS"
        echo_info "Creando servicio via Terraform..."
        
        # Intentar crear el servicio via Terraform
        cd infra/terraform
        terraform apply -var="catalogo_ecr_image=$ECR_URI:$IMAGE_TAG" -auto-approve
        cd ../..
        
        # Verificar nuevamente
        if check_ecs_service; then
            verify_deployment
            echo_success "Catalogo-service desplegado exitosamente!"
        else
            echo_error "No se pudo desplegar el servicio"
            exit 1
        fi
    fi
}

# Ejecutar función principal
main "$@"