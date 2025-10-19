#!/bin/bash

# ============================================================
# SCRIPT DE VERIFICACIÓN DE RECURSOS EXISTENTES EN AWS
# ============================================================
# Este script verifica qué recursos ya existen antes del deployment

set -e

PROJECT="${PROJECT:-medisupply}"
ENV="${ENV:-dev}"
REGION="${AWS_REGION:-us-east-1}"

echo "🔍 Verificando recursos existentes para ${PROJECT}-${ENV}..."
echo "=================================================="

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verificar dependencias
if ! command_exists aws; then
    echo "❌ AWS CLI no está instalado"
    exit 1
fi

if ! command_exists terraform; then
    echo "❌ Terraform no está instalado"
    exit 1
fi

echo "✅ Dependencias verificadas"
echo

# ============================================================
# VERIFICACIONES DE RECURSOS AWS
# ============================================================

echo "📊 SECRETS MANAGER"
echo "-------------------"
aws secretsmanager list-secrets --region ${REGION} --query "SecretList[?contains(Name, '${PROJECT}-${ENV}-catalogo')].{Name:Name,Status:DeletedDate}" --output table || echo "No hay secretos de catálogo"
echo

echo "🗄️  RDS INSTANCES"
echo "-------------------"
aws rds describe-db-instances --region ${REGION} --query "DBInstances[?contains(DBInstanceIdentifier, '${PROJECT}-${ENV}-catalogo')].{Instance:DBInstanceIdentifier,Status:DBInstanceStatus,Engine:Engine}" --output table || echo "No hay instancias RDS de catálogo"
echo

echo "🐳 ECR REPOSITORIES"
echo "-------------------"
aws ecr describe-repositories --region ${REGION} --query "repositories[?contains(repositoryName, '${PROJECT}-${ENV}-catalogo')].{Repository:repositoryName,CreatedAt:createdAt}" --output table || echo "No hay repositorios ECR de catálogo"
echo

echo "📨 SQS QUEUES"
echo "-------------------"
aws sqs list-queues --region ${REGION} --queue-name-prefix "${PROJECT}-${ENV}-catalogo" --query "QueueUrls" --output table || echo "No hay colas SQS de catálogo"
echo

echo "🎯 ECS SERVICES"
echo "-------------------"
aws ecs list-services --cluster "${PROJECT}-${ENV}-cluster" --region ${REGION} --query "serviceArns[?contains(@, 'catalogo')]" --output table || echo "No hay servicios ECS de catálogo"
echo

echo "🔐 IAM ROLES"
echo "-------------------"
aws iam list-roles --query "Roles[?contains(RoleName, '${PROJECT}-${ENV}-catalogo')].{Role:RoleName,Created:CreateDate}" --output table || echo "No hay roles IAM de catálogo"
echo

# ============================================================
# VERIFICACIÓN DEL STATE DE TERRAFORM
# ============================================================

echo "📋 TERRAFORM STATE"
echo "-------------------"
if [ -f "terraform.tfstate" ]; then
    echo "State file encontrado. Recursos relacionados con catálogo:"
    terraform state list | grep -i catalogo || echo "No hay recursos de catálogo en el state"
else
    echo "No hay terraform.tfstate file"
fi
echo

# ============================================================
# RECOMENDACIONES
# ============================================================

echo "💡 RECOMENDACIONES"
echo "==================="
echo "1. Si hay secretos 'scheduled for deletion', esperar o usar nombres diferentes"
echo "2. Si hay recursos existentes que quieres reutilizar, considera terraform import"
echo "3. Si hay conflictos, puedes usar sufijos de timestamp"
echo "4. Para cleanup completo, usa el script de limpieza"
echo

echo "🎯 Para proceder con el deployment:"
echo "   terraform plan -var='create_new_resources=true'  # Para recursos nuevos"
echo "   terraform plan -var='check_existing_resources=false'  # Para ignorar verificaciones"
echo "   terraform import [resource] [aws-id]  # Para importar recursos existentes"