#!/bin/bash

# ============================================================
# SCRIPT DE LIMPIEZA DE RECURSOS PROBLEMÁTICOS
# ============================================================
# Este script limpia recursos que pueden causar conflictos

set -e

PROJECT="${PROJECT:-medisupply}"
ENV="${ENV:-dev}"
REGION="${AWS_REGION:-us-east-1}"

echo "🧹 Limpiando recursos problemáticos para ${PROJECT}-${ENV}..."
echo "=================================================="

# Función para confirmar acción
confirm() {
    read -p "¿Continuar? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Operación cancelada"
        exit 1
    fi
}

# ============================================================
# LIMPIEZA DE SECRETS MANAGER
# ============================================================

echo "🗑️  Limpiando secretos scheduled for deletion..."
echo "------------------------------------------------"

# Listar secretos que están programados para eliminación
SCHEDULED_SECRETS=$(aws secretsmanager list-secrets --region ${REGION} \
    --query "SecretList[?DeletedDate && contains(Name, '${PROJECT}-${ENV}-catalogo')].Name" \
    --output text)

if [ -n "$SCHEDULED_SECRETS" ]; then
    echo "Secretos encontrados programados para eliminación:"
    echo "$SCHEDULED_SECRETS"
    echo
    echo "⚠️  Estos secretos serán eliminados permanentemente"
    confirm
    
    for secret in $SCHEDULED_SECRETS; do
        echo "Eliminando permanentemente: $secret"
        aws secretsmanager delete-secret \
            --region ${REGION} \
            --secret-id "$secret" \
            --force-delete-without-recovery || true
    done
else
    echo "✅ No hay secretos programados para eliminación"
fi

echo

# ============================================================
# LIMPIEZA DE RECURSOS TERRAFORM HUÉRFANOS
# ============================================================

echo "🔄 Verificando state de Terraform..."
echo "------------------------------------"

if [ -f "terraform.tfstate" ]; then
    # Verificar recursos que están en el state pero no en AWS
    echo "Recursos en Terraform state:"
    terraform state list | grep -E "(secret|db_instance|ecr_repository)" || echo "No hay recursos relevantes"
    
    echo
    echo "⚠️  ¿Quieres limpiar el state de Terraform de recursos inexistentes?"
    confirm
    
    # Esto requiere verificación manual
    echo "💡 Para limpiar el state manualmente:"
    echo "   terraform state rm [resource_address]"
    echo "   Ejemplo: terraform state rm module.catalogo_service.aws_secretsmanager_secret.catalogo_db_credentials"
else
    echo "✅ No hay terraform.tfstate file"
fi

echo

# ============================================================
# VERIFICACIÓN FINAL
# ============================================================

echo "✅ Limpieza completada"
echo "====================="
echo
echo "🎯 Próximos pasos recomendados:"
echo "1. Ejecutar script de verificación: ./check-existing-resources.sh"
echo "2. Usar variables apropiadas en terraform plan:"
echo "   - create_new_resources=true para evitar conflictos"
echo "   - check_existing_resources=false para deployment rápido"
echo "3. Proceder con terraform apply"