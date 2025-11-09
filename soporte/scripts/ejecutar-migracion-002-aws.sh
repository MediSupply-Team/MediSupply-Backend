#!/bin/bash
set -e

# Script para ejecutar migraciones de inventario en la base de datos RDS de AWS

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Migración de Inventario - AWS RDS${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Configuración
AWS_REGION="us-east-1"
CLUSTER_NAME="orders-cluster"
SERVICE_NAME="medisupply-dev-catalogo-service"
SQL_FILE="./catalogo-service/data/002_movimientos.sql"

# Verificar que el archivo SQL existe
if [ ! -f "$SQL_FILE" ]; then
    echo -e "${RED}❌ Error: No se encontró el archivo $SQL_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Paso 1: Obteniendo información del servicio ECS...${NC}"

# Obtener el Task ARN del contenedor corriendo
TASK_ARN=$(aws ecs list-tasks \
    --cluster $CLUSTER_NAME \
    --service-name $SERVICE_NAME \
    --region $AWS_REGION \
    --query 'taskArns[0]' \
    --output text)

if [ -z "$TASK_ARN" ] || [ "$TASK_ARN" == "None" ]; then
    echo -e "${RED}❌ No se encontró ninguna tarea corriendo para $SERVICE_NAME${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Task ARN: $TASK_ARN${NC}"
echo ""

echo -e "${YELLOW}📋 Paso 2: Ejecutando migración en el contenedor...${NC}"
echo ""

# Copiar el archivo SQL al contenedor y ejecutarlo
echo -e "${BLUE}   Copiando archivo SQL al contenedor...${NC}"

# Crear un comando temporal para ejecutar la migración
cat > /tmp/run-migration.sh << 'EOF'
#!/bin/bash
set -e

echo "🔍 Conectando a la base de datos..."
echo ""

# Ejecutar el SQL usando psql con las variables de entorno del contenedor
psql "$DATABASE_URL" -f /tmp/002_movimientos.sql

echo ""
echo "✅ Migración completada exitosamente!"
EOF

chmod +x /tmp/run-migration.sh

echo -e "${BLUE}   Subiendo archivos al contenedor...${NC}"

# Ejecutar el comando en el contenedor ECS
aws ecs execute-command \
    --cluster $CLUSTER_NAME \
    --task ${TASK_ARN##*/} \
    --container catalogo-service \
    --interactive \
    --command "/bin/bash -c 'cat > /tmp/002_movimientos.sql && cat > /tmp/run-migration.sh && chmod +x /tmp/run-migration.sh && /tmp/run-migration.sh'" \
    --region $AWS_REGION < <(cat "$SQL_FILE" && echo "---EOF---" && cat /tmp/run-migration.sh)

echo ""
echo -e "${GREEN}✅ Migración aplicada exitosamente!${NC}"
echo ""

# Limpiar archivos temporales
rm -f /tmp/run-migration.sh

echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}✨ Proceso completado!${NC}"
echo -e "${BLUE}================================================${NC}"

