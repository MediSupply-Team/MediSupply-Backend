# 🎯 FASES PENDIENTES - DESPLIEGUE AWS

**Estado Actual:** Fases 1A, 1B, 2A y 2B completadas ✅  
**Próximas Fases:** 3, 4 y 5

---

## ✅ COMPLETADO (Fases 1 y 2)

- [x] **FASE 1A:** catalogo-service funcionando localmente
- [x] **FASE 1B:** cliente-service funcionando localmente
- [x] **FASE 2A:** bff-venta revisado (código correcto)
- [x] **FASE 2B:** bff-cliente funcionando como proxy

**Documentación Generada:**
1. `PLAN-VALIDACION-COMPLETO.md`
2. `ENDPOINTS-CATALOGO-SERVICE.md`
3. `ENDPOINTS-CLIENTE-SERVICE.md`
4. `MAPEO-ENDPOINTS-BFFS.md`
5. `RESUMEN-VALIDACION-LOCAL.md`
6. `test-bffs.sh`

---

## 📋 FASE 3: GENERAR IMÁGENES DOCKER PARA AWS

**Objetivo:** Construir imágenes Docker optimizadas para AWS ECS Fargate

### ¿Qué haremos?

#### 3.1 Verificar y corregir Dockerfiles
- ✅ Verificar arquitectura correcta (`linux/amd64`)
- ✅ Verificar puertos expuestos (8000, no 8080)
- ✅ Verificar healthchecks configurados
- ✅ Verificar entrypoints para inicialización de datos
- ⚠️ Optimizar tamaño de imágenes (multi-stage builds si es necesario)

#### 3.2 Construir imágenes localmente
```bash
# catalogo-service
docker buildx build --platform linux/amd64 \
  -t catalogo-service:latest \
  ./catalogo-service

# cliente-service
docker buildx build --platform linux/amd64 \
  -t cliente-service:latest \
  ./cliente-service

# bff-cliente
docker buildx build --platform linux/amd64 \
  -t bff-cliente:latest \
  ./bff-cliente

# bff-venta
docker buildx build --platform linux/amd64 \
  -t bff-venta:latest \
  ./bff-venta
```

#### 3.3 Probar imágenes localmente
```bash
# Probar cada imagen con docker run
docker run -p 8000:8000 catalogo-service:latest
```

#### 3.4 Verificar tamaños de imágenes
```bash
docker images | grep -E "(catalogo|cliente|bff)"
```

### Checklist FASE 3:
- [ ] Dockerfiles verificados y optimizados
- [ ] Imágenes construidas con arquitectura correcta
- [ ] Imágenes probadas localmente
- [ ] Tamaños de imagen aceptables
- [ ] Healthchecks funcionan correctamente
- [ ] Entrypoints ejecutan populate_db correctamente

### Tiempo Estimado: 1-2 horas

---

## 📋 FASE 4: TERRAFORM - INFRAESTRUCTURA AWS

**Objetivo:** Desplegar infraestructura correcta en AWS con todas las correcciones

### ¿Qué haremos?

#### 4.1 Revisar y corregir módulos de Terraform

##### catalogo-service (`infra/terraform/modules/catalogo-service/main.tf`)
**Correcciones necesarias:**
```hcl
# ✅ 1. IAM Policy para Secrets Manager (CORREGIDO)
resource "aws_iam_policy" "catalogo_ecs_execution_secrets_policy" {
  policy = jsonencode({
    Statement = [{
      Action = ["secretsmanager:GetSecretValue"]
      Effect = "Allow"
      Resource = aws_secretsmanager_secret.catalogo_db_credentials.arn  # ✅ Correcto
    }]
  })
}

# ✅ 2. DATABASE_URL sin duplicación de puerto (CORREGIDO)
resource "aws_secretsmanager_secret_version" "catalogo_db_credentials" {
  secret_string = jsonencode({
    database_url = "postgresql+asyncpg://${var.db_username}:${random_password.catalogo_db_password.result}@${aws_db_instance.catalogo_postgres.address}:5432/${var.db_name}"
    # ✅ Usa .address en lugar de .endpoint
  })
}

# ✅ 3. Puerto correcto en ECS Task Definition
resource "aws_ecs_task_definition" "catalogo_service" {
  container_definitions = jsonencode([{
    portMappings = [{
      containerPort = 8000  # ✅ Puerto correcto (no 8080)
      hostPort      = 8000
      protocol      = "tcp"
    }]
  }])
}

# ✅ 4. Health Check correcto
healthCheck = {
  command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
  interval    = 30
  timeout     = 5
  retries     = 3
  startPeriod = 60  # ✅ Dar tiempo para populate_db
}

# ✅ 5. Target Group con puerto correcto
resource "aws_lb_target_group" "catalogo_service" {
  port     = 8000  # ✅ Puerto correcto
  protocol = "HTTP"
  
  health_check {
    path                = "/health"
    port                = 8000  # ✅ Puerto correcto
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }
}
```

##### cliente-service (`infra/terraform/modules/cliente-service/main.tf`)
**Correcciones similares:**
- ✅ DATABASE_URL con `postgresql+asyncpg://`
- ✅ Puerto 8000 en todas partes
- ✅ Health check apuntando a `/api/cliente/health`
- ✅ IAM policy correcta para Secrets Manager
- ✅ StartPeriod de 60s para healthcheck

##### bff-cliente y bff-venta
**Verificar:**
- ✅ Variables de entorno apuntan a servicios con puerto 8000
- ✅ CATALOGO_SERVICE_URL usa puerto 8000
- ✅ CLIENTE_SERVICE_URL usa puerto 8000

#### 4.2 Plan de ejecución
```bash
cd infra/terraform

# 1. Destruir infraestructura existente (CUIDADO)
terraform destroy -auto-approve

# 2. Limpiar estado si es necesario
# (Opcional, solo si hay problemas)

# 3. Verificar cambios con plan
terraform plan -out=tfplan

# 4. Revisar el plan manualmente
terraform show tfplan

# 5. Aplicar cambios
terraform apply tfplan

# 6. Obtener outputs (URLs de ALBs)
terraform output
```

#### 4.3 Verificaciones post-deploy

**A. Verificar ECR repositories:**
```bash
aws ecr describe-repositories \
  --region us-east-1 \
  --query 'repositories[*].repositoryName'
```

**B. Verificar RDS instances:**
```bash
aws rds describe-db-instances \
  --region us-east-1 \
  --query 'DBInstances[*].[DBInstanceIdentifier,Endpoint.Address,DBInstanceStatus]'
```

**C. Verificar ECS services:**
```bash
aws ecs list-services \
  --cluster medisupply-dev-cluster \
  --region us-east-1
```

**D. Verificar ALBs:**
```bash
aws elbv2 describe-load-balancers \
  --region us-east-1 \
  --query 'LoadBalancers[*].[LoadBalancerName,DNSName]'
```

**E. Verificar Secrets Manager:**
```bash
aws secretsmanager list-secrets \
  --region us-east-1 \
  --query 'SecretList[*].Name'
```

#### 4.4 Pruebas de endpoints en AWS

```bash
# Obtener URLs de ALBs desde terraform output
CATALOGO_ALB_URL=$(terraform output -raw catalogo_alb_dns_name)
CLIENTE_ALB_URL=$(terraform output -raw cliente_alb_dns_name)
BFF_CLIENTE_ALB_URL=$(terraform output -raw bff_cliente_alb_dns_name)

# Probar endpoints
curl "http://${CATALOGO_ALB_URL}/health"
curl "http://${CLIENTE_ALB_URL}/api/cliente/health"
curl "http://${BFF_CLIENTE_ALB_URL}/health"
curl "http://${BFF_CLIENTE_ALB_URL}/api/v1/client/?limite=5"
```

### Checklist FASE 4:
- [ ] Módulos de Terraform revisados y corregidos
- [ ] Variables de entorno correctas
- [ ] Puertos correctos (8000)
- [ ] DATABASE_URL con formato correcto
- [ ] IAM policies correctas
- [ ] Terraform plan revisado
- [ ] Infraestructura desplegada exitosamente
- [ ] Servicios ECS corriendo (healthy)
- [ ] Health checks pasando
- [ ] Endpoints respondiendo correctamente
- [ ] Datos precargados en bases de datos

### Tiempo Estimado: 2-3 horas

### ⚠️ PRECAUCIONES:
1. **Backup de estado de Terraform** antes de destroy
2. **Revisar plan** cuidadosamente antes de aplicar
3. **Costos:** Destruir recursos no usados después de pruebas
4. **Logs:** Monitorear CloudWatch Logs durante despliegue
5. **Rollback:** Tener plan B si algo falla

---

## 📋 FASE 5: GITHUB WORKFLOWS - CI/CD

**Objetivo:** Automatizar despliegues futuros y facilitar desarrollo

### ¿Qué haremos?

#### 5.1 Revisar workflows existentes
```bash
ls -la .github/workflows/
```

#### 5.2 Crear/actualizar workflows para cada servicio

**Estructura recomendada:**
```
.github/workflows/
  ├── deploy-catalogo-service.yml
  ├── deploy-cliente-service.yml
  ├── deploy-bff-cliente.yml
  ├── deploy-bff-venta.yml
  ├── deploy-orders-service.yml
  └── deploy-infrastructure.yml  (Terraform)
```

#### 5.3 Template de workflow (ejemplo: catalogo-service)

```yaml
name: Deploy Catalogo Service

on:
  push:
    branches:
      - main
      - develop
    paths:
      - 'catalogo-service/**'
      - '.github/workflows/deploy-catalogo-service.yml'
  workflow_dispatch:  # Trigger manual

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: medisupply-dev-catalogo-service
  ECS_SERVICE: medisupply-dev-catalogo-service
  ECS_CLUSTER: medisupply-dev-cluster
  CONTAINER_NAME: catalogo-service

jobs:
  deploy:
    name: Deploy to AWS
    runs-on: ubuntu-latest
    
    permissions:
      id-token: write  # Para OIDC
      contents: read
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2
      
      - name: Build Docker image
        working-directory: ./catalogo-service
        run: |
          docker buildx build \
            --platform linux/amd64 \
            -t ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ github.sha }} \
            -t ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:latest \
            .
      
      - name: Push image to ECR
        run: |
          docker push ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ github.sha }}
          docker push ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:latest
      
      - name: Update ECS service
        run: |
          aws ecs update-service \
            --cluster ${{ env.ECS_CLUSTER }} \
            --service ${{ env.ECS_SERVICE }} \
            --force-new-deployment
      
      - name: Wait for deployment
        run: |
          aws ecs wait services-stable \
            --cluster ${{ env.ECS_CLUSTER }} \
            --services ${{ env.ECS_SERVICE }}
      
      - name: Verify deployment
        run: |
          TASK_ARN=$(aws ecs list-tasks \
            --cluster ${{ env.ECS_CLUSTER }} \
            --service-name ${{ env.ECS_SERVICE }} \
            --query 'taskArns[0]' \
            --output text)
          
          aws ecs describe-tasks \
            --cluster ${{ env.ECS_CLUSTER }} \
            --tasks $TASK_ARN \
            --query 'tasks[0].containers[0].healthStatus'
```

#### 5.4 Workflow para Terraform (Infraestructura)

```yaml
name: Deploy Infrastructure (Terraform)

on:
  push:
    branches:
      - main
    paths:
      - 'infra/terraform/**'
  workflow_dispatch:

jobs:
  terraform:
    name: Terraform Plan & Apply
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.5.0
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1
      
      - name: Terraform Init
        working-directory: ./infra/terraform
        run: terraform init
      
      - name: Terraform Plan
        working-directory: ./infra/terraform
        run: terraform plan -out=tfplan
      
      - name: Terraform Apply
        if: github.ref == 'refs/heads/main'
        working-directory: ./infra/terraform
        run: terraform apply -auto-approve tfplan
```

#### 5.5 Secrets de GitHub necesarios

**Configurar en GitHub → Settings → Secrets:**
```
AWS_ROLE_ARN=arn:aws:iam::ACCOUNT_ID:role/github-actions-role
AWS_REGION=us-east-1
```

#### 5.6 Mejoras adicionales

**A. Tests antes de deploy:**
```yaml
- name: Run tests
  working-directory: ./catalogo-service
  run: |
    pip install -r test-requirements.txt
    pytest tests/ -v
```

**B. Notificaciones:**
```yaml
- name: Notify Slack on failure
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
```

**C. Rollback automático:**
```yaml
- name: Rollback on failure
  if: failure()
  run: |
    # Revertir a versión anterior
```

### Checklist FASE 5:
- [ ] Workflows creados para cada servicio
- [ ] OIDC configurado para GitHub Actions
- [ ] Secrets de GitHub configurados
- [ ] Tests integrados en workflows
- [ ] Build de imágenes con arquitectura correcta
- [ ] Push a ECR funcionando
- [ ] Update de ECS services funcionando
- [ ] Verificación post-deploy incluida
- [ ] Notificaciones configuradas (opcional)
- [ ] Rollback strategy definida
- [ ] Documentación de workflows

### Tiempo Estimado: 2-3 horas

---

## 📊 RESUMEN DE TODAS LAS FASES

| Fase | Nombre | Estado | Tiempo | Complejidad |
|------|--------|--------|--------|-------------|
| 1A | catalogo-service local | ✅ Completado | - | Baja |
| 1B | cliente-service local | ✅ Completado | - | Baja |
| 2A | bff-venta revisión | ✅ Completado | - | Baja |
| 2B | bff-cliente proxy | ✅ Completado | - | Baja |
| **3** | **Imágenes Docker AWS** | ⏳ **Pendiente** | 1-2h | Media |
| **4** | **Terraform AWS** | ⏳ **Pendiente** | 2-3h | **Alta** |
| **5** | **GitHub Workflows** | ⏳ **Pendiente** | 2-3h | Media |

**Total estimado fases pendientes:** 5-8 horas

---

## 🎯 ORDEN RECOMENDADO DE EJECUCIÓN

### Opción A: Secuencial (Recomendado)
1. **FASE 3** → Construir y probar imágenes localmente
2. **FASE 4** → Desplegar en AWS con Terraform
3. **FASE 5** → Configurar CI/CD para futuros deploys

**Ventaja:** Cada fase valida la anterior

### Opción B: Paralelo (Rápido pero arriesgado)
1. **FASE 3 + 5** → Construir imágenes y workflows simultáneamente
2. **FASE 4** → Desplegar todo junto

**Ventaja:** Más rápido  
**Desventaja:** Si algo falla en FASE 3, tendrás que revisar workflows

---

## 🚀 SIGUIENTES PASOS INMEDIATOS

### Para comenzar FASE 3:
```bash
# 1. Revisar Dockerfiles
cat catalogo-service/Dockerfile
cat cliente-service/Dockerfile
cat bff-cliente/Dockerfile
cat bff-venta/Dockerfile

# 2. Construir imágenes
docker buildx build --platform linux/amd64 -t catalogo-service:latest ./catalogo-service

# 3. Verificar imágenes
docker images | grep -E "(catalogo|cliente|bff)"
```

### Para comenzar FASE 4:
```bash
cd infra/terraform

# 1. Revisar módulos
ls -la modules/

# 2. Verificar configuración actual
terraform show

# 3. Planificar cambios
terraform plan
```

---

## ❓ PREGUNTAS PARA DECIDIR

1. **¿Quieres ir secuencial o intentar paralelizar?**
2. **¿Tienes acceso a AWS CLI configurado?**
3. **¿Quieres hacer backup del estado de Terraform antes de destroy?**
4. **¿Prefieres que te guíe paso a paso o quieres scripts automatizados?**

---

## 💡 RECOMENDACIÓN

**Comenzar con FASE 3** porque:
1. ✅ No requiere AWS (todo local)
2. ✅ Valida que las imágenes funcionan
3. ✅ Descubre problemas antes de AWS
4. ✅ Es rápido (1-2 horas)
5. ✅ Necesario para FASE 4 de todos modos

**¿Empezamos con FASE 3?** 🚀

