#!/bin/bash
set -e

# Script para poblar las bases de datos ejecutando comandos dentro de los contenedores ECS

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   🗄️  POBLACIÓN DE BASES DE DATOS VIA ECS - MEDISUPPLY     ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

PROJECT="medisupply"
ENV="dev"
REGION="us-east-1"
CLUSTER="${PROJECT}-${ENV}-cluster"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================
# FUNCIÓN: Obtener Task ARN de un servicio
# ============================================================
get_task_arn() {
    local service_name=$1
    echo -e "${YELLOW}🔍 Buscando task activo para $service_name...${NC}"
    
    TASK_ARN=$(aws ecs list-tasks \
        --cluster "$CLUSTER" \
        --service-name "$service_name" \
        --desired-status RUNNING \
        --region "$REGION" \
        --query 'taskArns[0]' \
        --output text)
    
    if [ "$TASK_ARN" == "None" ] || [ -z "$TASK_ARN" ]; then
        echo -e "${RED}❌ No se encontró task activo para $service_name${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ Task encontrado: ${TASK_ARN##*/}${NC}"
    echo "$TASK_ARN"
}

# ============================================================
# FUNCIÓN: Poblar Cliente Service usando Python script
# ============================================================
populate_cliente_service() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  1. CLIENTE-SERVICE${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    
    SERVICE_NAME="${PROJECT}-${ENV}-cliente-service-svc"
    TASK_ARN=$(get_task_arn "$SERVICE_NAME")
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}⏭️  Saltando cliente-service (no hay task activo)${NC}"
        echo ""
        return
    fi
    
    echo -e "${YELLOW}🔄 Ejecutando script de población de datos...${NC}"
    
    # Ejecutar el script populate_db.py dentro del contenedor
    aws ecs execute-command \
        --cluster "$CLUSTER" \
        --task "$TASK_ARN" \
        --container "cliente-service" \
        --interactive \
        --region "$REGION" \
        --command "python3 /app/app/populate_db.py"
    
    echo -e "${GREEN}✅ CLIENTE-SERVICE - Comando ejecutado${NC}"
    echo ""
}

# ============================================================
# FUNCIÓN: Poblar Catalogo Service usando SQL
# ============================================================
populate_catalogo_service() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  2. CATALOGO-SERVICE${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    
    SERVICE_NAME="${PROJECT}-${ENV}-catalogo-service-svc"
    TASK_ARN=$(get_task_arn "$SERVICE_NAME")
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}⏭️  Saltando catalogo-service (no hay task activo)${NC}"
        echo ""
        return
    fi
    
    echo -e "${YELLOW}🔄 Creando script temporal de población...${NC}"
    
    # Crear un script Python que ejecute el SQL
    cat > /tmp/populate_catalogo.py << 'PYTHON_SCRIPT'
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def populate():
    database_url = os.getenv("DATABASE_URL")
    print(f"📡 Conectando a base de datos...")
    engine = create_async_engine(database_url, echo=False)
    
    async with engine.begin() as conn:
        # Verificar si ya hay datos
        result = await conn.execute(text("SELECT COUNT(*) FROM producto"))
        count = result.scalar()
        
        if count > 0:
            print(f"ℹ️  Base de datos ya tiene {count} productos")
            return
        
        print("🔄 Poblando catálogo con datos iniciales...")
        
        # Leer el archivo SQL
        with open('/app/data/001_init.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Ejecutar cada statement
        for statement in sql_content.split(';'):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    await conn.execute(text(statement))
                except Exception as e:
                    if 'already exists' not in str(e):
                        print(f"⚠️  Error en statement: {e}")
        
        # Verificar resultado
        result = await conn.execute(text("SELECT COUNT(*) FROM producto"))
        prod_count = result.scalar()
        result = await conn.execute(text("SELECT COUNT(*) FROM inventario"))
        inv_count = result.scalar()
        
        print(f"✅ Catálogo poblado exitosamente")
        print(f"   📦 Productos: {prod_count}")
        print(f"   🏭 Inventarios: {inv_count}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(populate())
PYTHON_SCRIPT
    
    echo -e "${YELLOW}📤 Copiando script al contenedor...${NC}"
    
    # Nota: ECS Execute Command no soporta copia de archivos directamente
    # Vamos a crear el script inline
    
    echo -e "${YELLOW}🔄 Ejecutando población de catálogo...${NC}"
    
    PYTHON_SCRIPT=$(cat /tmp/populate_catalogo.py)
    
    aws ecs execute-command \
        --cluster "$CLUSTER" \
        --task "$TASK_ARN" \
        --container "catalogo-service" \
        --interactive \
        --region "$REGION" \
        --command "python3 -c '$PYTHON_SCRIPT'"
    
    echo -e "${GREEN}✅ CATALOGO-SERVICE - Comando ejecutado${NC}"
    echo ""
}

# ============================================================
# MAIN
# ============================================================

# Verificar dependencias
echo -e "${YELLOW}🔍 Verificando dependencias...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI no está instalado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ AWS CLI disponible${NC}"
echo ""

# Verificar que ECS Execute Command esté habilitado
echo -e "${YELLOW}ℹ️  NOTA: Este script requiere que ECS Execute Command esté habilitado${NC}"
echo -e "${YELLOW}   Si falla, necesitarás modificar el task definition para habilitar execute command${NC}"
echo ""

# Ejecutar población
populate_cliente_service
populate_catalogo_service

# Resumen final
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║             🎉 COMANDOS ENVIADOS                              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${YELLOW}⚠️  Nota: Los comandos se enviaron a los contenedores${NC}"
echo -e "${YELLOW}   Verifica los logs en CloudWatch para confirmar ejecución${NC}"
echo ""


