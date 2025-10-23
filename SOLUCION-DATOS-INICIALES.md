# 🗄️ Solución: Población de Datos Iniciales en AWS

## Problema Identificado

Las bases de datos RDS en AWS se crean **vacías** (solo estructura, sin datos), mientras que en Docker Compose se poblan automáticamente con los scripts SQL en `/docker-entrypoint-initdb.d/`.

---

## 🎯 Solución Recomendada: Inicialización Automática al Arrancar

### Opción 1: Script de Inicio en el Contenedor (RECOMENDADO)

Modificar el contenedor para que ejecute scripts de inicialización al arrancar, pero solo una vez.

#### Para cliente-service

**1. Crear script de inicialización**

```bash
# cliente-service/init-db.sh
#!/bin/bash
set -e

echo "🔍 Verificando inicialización de base de datos..."

# Esperar a que la base de datos esté lista
until pg_isready -h "$(echo $DATABASE_URL | sed 's/.*@\(.*\):.*/\1/')" -p 5432 -U cliente_user; do
  echo "⏳ Esperando a que PostgreSQL esté listo..."
  sleep 2
done

echo "✅ PostgreSQL está listo"

# Ejecutar el script SQL de inicialización si las tablas no existen
python3 << 'PYTHON_SCRIPT'
import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def init_db():
    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    
    async with engine.begin() as conn:
        # Verificar si ya hay datos
        result = await conn.execute(text("SELECT COUNT(*) FROM cliente"))
        count = result.scalar()
        
        if count == 0:
            print("🔄 Poblando base de datos con datos iniciales...")
            # Leer y ejecutar el archivo SQL
            with open('/app/data/001_init.sql', 'r') as f:
                sql_script = f.read()
            
            # Ejecutar el script (dividido por statements)
            for statement in sql_script.split(';'):
                if statement.strip():
                    await conn.execute(text(statement))
            
            print("✅ Datos iniciales cargados exitosamente")
        else:
            print(f"ℹ️  Base de datos ya tiene {count} clientes. Saltando inicialización.")
    
    await engine.dispose()

asyncio.run(init_db())
PYTHON_SCRIPT

echo "🎉 Inicialización completada. Iniciando aplicación..."
```

**2. Modificar Dockerfile**

```dockerfile
# Agregar al Dockerfile de cliente-service
COPY data/001_init.sql /app/data/001_init.sql
COPY init-db.sh /app/init-db.sh
RUN chmod +x /app/init-db.sh

# Modificar CMD para ejecutar init primero
CMD ["/bin/bash", "-c", "/app/init-db.sh && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

#### Para catalogo-service

Similar al cliente-service, pero con el script SQL del catálogo.

---

## Opción 2: ECS Run Task de Inicialización (Una Sola Vez)

Ejecutar un task de ECS que solo inicialice los datos y termine.

### Comando desde tu máquina local:

```bash
# Para cliente-service
aws ecs run-task \
  --cluster medisupply-dev-cluster \
  --task-definition medisupply-dev-cliente-service \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx]}" \
  --overrides '{
    "containerOverrides": [{
      "name": "cliente-service",
      "command": ["python3", "/app/app/populate_db.py"]
    }]
  }'
```

```bash
# Para catalogo-service - ejecutar SQL directamente con psql
# Necesitas conectarte a RDS y ejecutar el script 001_init.sql
```

---

## Opción 3: Conexión Manual a RDS + Ejecución de Scripts

### 1. Obtener credenciales de RDS

```bash
# Cliente Service DB
aws secretsmanager get-secret-value \
  --secret-id medisupply-dev-cliente-service-db-credentials \
  --query SecretString --output text | jq .

# Catalogo Service DB
aws secretsmanager get-secret-value \
  --secret-id medisupply-dev-catalogo-db-credentials-v2 \
  --query SecretString --output text | jq .
```

### 2. Conectarse a RDS desde tu máquina

```bash
# Necesitas estar en la VPC (o usar un bastion/tunneling)
# O modificar temporalmente el security group para permitir tu IP

psql "postgresql://cliente_user:PASSWORD@ENDPOINT:5432/cliente_db" \
  -f cliente-service/data/001_init.sql
```

---

## Opción 4: Lambda Function de Inicialización

Crear una Lambda que se ejecute una vez después del despliegue de Terraform.

```hcl
# En Terraform - agregar al módulo
resource "aws_lambda_function" "init_db" {
  filename      = "init_db_lambda.zip"
  function_name = "${local.service_id}-init-db"
  role          = aws_iam_role.lambda_init_role.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  
  environment {
    variables = {
      SECRET_ARN = aws_secretsmanager_secret.cliente_db_credentials.arn
      SQL_SCRIPT = file("${path.module}/../../cliente-service/data/001_init.sql")
    }
  }
}
```

---

## ✅ Recomendación Final

**Para ambiente de desarrollo**: Usar **Opción 1** (script de inicio automático)
- Más fácil de mantener
- Se ejecuta automáticamente en cada deploy
- Idempotente (verifica si ya hay datos)

**Para ambiente de producción**: Usar **Opción 3** (conexión manual) o **Opción 2** (ECS task)
- Control total sobre cuándo se ejecuta
- No ralentiza el inicio de la aplicación
- Más seguro para datos reales

---

## 🚀 Implementación Inmediata

Puedo implementar la **Opción 1** modificando los Dockerfiles y agregando scripts de inicio, o
Puedo ayudarte a ejecutar la **Opción 2** (ECS Run Task) para poblar las bases de datos **ahora mismo**.

¿Cuál prefieres?


