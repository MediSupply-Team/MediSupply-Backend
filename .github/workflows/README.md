# 🚀 MediSupply CI/CD Workflows

Este directorio contiene los workflows de GitHub Actions para CI/CD automatizado de todos los servicios de MediSupply.

## 📋 Workflows Disponibles

### Servicios Backend

#### 1. `deploy-orders.yml` - Orders Service
Despliega el servicio de órdenes (servicio principal de pedidos).

**Trigger**: 
- Push a `main` o `develop` con cambios en `orders-service/**`
- Dispatch manual

**Endpoints**:
- ECS Service: `orders-svc`
- ECR: `orders-service`

---

#### 2. `deploy-catalogo-service.yml` - Catalogo Service ⭐ **NUEVO**
Despliega el servicio de catálogo de productos.

**Trigger**: 
- Push a `main` o `develop` con cambios en `catalogo-service/**`
- Dispatch manual

**Endpoints**:
- ECS Service: `medisupply-dev-catalogo-service-svc`
- ECR: `medisupply-dev-catalogo-service`
- ALB: `medisupply-dev-catalogo-service-alb`

**Datos Reales**: ✅ 25 productos, inventario multi-país (CO, MX, PE, CL)

---

#### 3. `deploy-cliente-service.yml` - Cliente Service ⭐ **NUEVO**
Despliega el servicio de gestión de clientes.

**Trigger**: 
- Push a `main` o `develop` con cambios en `cliente-service/**`
- Dispatch manual

**Endpoints**:
- ECS Service: `medisupply-dev-cliente-service-svc`
- ECR: `medisupply-dev-cliente-service`
- ALB: `medisupply-dev-cliente-service-alb`

**Datos Reales**: ✅ 5 clientes, historial de compras, productos preferidos

---

### Backend for Frontend (BFF)

#### 4. `deploy-bff-cliente.yml` - BFF Cliente ⭐ **ACTUALIZADO**
Despliega el BFF para clientes (proxy a cliente-service).

**Trigger**: 
- Push a `main` o `develop` con cambios en `bff-cliente/**`
- Dispatch manual

**Endpoints**:
- ECS Service: `medisupply-dev-bff-cliente-svc`
- ECR: `medisupply-dev-bff-cliente`
- ALB: `http://medisupply-dev-bff-cliente-alb-1673122993.us-east-1.elb.amazonaws.com`

**Funcionalidad**:
- ✅ Listar clientes
- ✅ Buscar clientes (nombre, email, NIT)
- ✅ Histórico completo del cliente
- ✅ Crear órdenes (vía SQS)

---

#### 5. `deploy-bff-venta.yml` - BFF Venta ⭐ **ACTUALIZADO**
Despliega el BFF para vendedores (proxy a catalogo-service).

**Trigger**: 
- Push a `main` o `develop` con cambios en `bff-venta/**`
- Dispatch manual

**Endpoints**:
- ECS Service: `medisupply-dev-bff-venta-svc`
- ECR: `medisupply-dev-bff-venta`
- ALB: `http://medisupply-dev-bff-venta-alb-607524362.us-east-1.elb.amazonaws.com`

**Funcionalidad**:
- ✅ Listar productos del catálogo
- ✅ Filtrar por categoría
- ✅ Buscar productos
- ✅ Consultar inventario por país/bodega
- ✅ Crear órdenes (vía SQS)

---

### Otros Servicios

#### 6. `deploy-consumer.yml` - Consumer Service
Despliega el consumer para procesar mensajes de SQS.

#### 7. `deploy-rutas.yml` - Rutas Service
Despliega el servicio de rutas de entrega.

---

## 🔑 Características Comunes de los Workflows

### ✅ Estándares Implementados

1. **OIDC Authentication** 
   - Autenticación segura con AWS sin credenciales estáticas
   - Role ARN: `arn:aws:iam::217466752988:role/github-actions-deploy`

2. **Multi-Architecture Build**
   - Platform: `linux/amd64` (compatible con AWS Fargate)
   - Optimizado para ECS

3. **Doble Tagging**
   ```bash
   - {git-sha}    # Tag específico del commit
   - latest       # Tag para último deployment
   ```

4. **ECS Integration**
   - Descarga automática de task definition existente
   - Update de imagen sin cambiar configuración
   - Espera hasta estabilización del servicio
   - Post-deploy diagnostics

5. **Manual Dispatch**
   - Permite deployments manuales
   - Selección de branch/tag/commit
   - Útil para hotfixes y rollbacks

---

## 🚀 Cómo Usar los Workflows

### Deployment Automático (Push)

1. **Hacer cambios en el servicio:**
   ```bash
   cd catalogo-service/
   # Hacer cambios en el código
   git add .
   git commit -m "feat: agregar nuevo endpoint"
   ```

2. **Push a develop o main:**
   ```bash
   git push origin develop
   ```

3. **El workflow se ejecuta automáticamente** ✅
   - Build de la imagen Docker
   - Push a ECR
   - Update de task definition
   - Deploy a ECS
   - Verificación de estabilidad

---

### Deployment Manual (Workflow Dispatch)

1. **Ir a GitHub Actions:**
   - https://github.com/YOUR_ORG/MediSupply-Backend/actions

2. **Seleccionar el workflow** (ej: "Deploy Catalogo Service")

3. **Click en "Run workflow"**

4. **Seleccionar parámetros:**
   - Branch/Tag/Commit: `develop`, `main`, `feature/xyz`, o SHA específico
   - Click "Run workflow"

5. **Monitorear ejecución en tiempo real**

---

## 📊 Logs y Monitoreo

### Ver Logs de Deployment

```bash
# Ver logs del workflow en GitHub
https://github.com/YOUR_ORG/MediSupply-Backend/actions

# Ver logs del servicio en AWS CloudWatch
aws logs tail /ecs/medisupply-dev-catalogo-service --follow
aws logs tail /ecs/medisupply-dev-cliente-service --follow
aws logs tail /ecs/medisupply-dev-bff-cliente --follow
aws logs tail /ecs/medisupply-dev-bff-venta --follow
```

### Verificar Estado del Servicio

```bash
# Ver estado del servicio ECS
aws ecs describe-services \
  --cluster orders-cluster \
  --services medisupply-dev-catalogo-service-svc \
  --query 'services[0].{status:status,desired:desiredCount,running:runningCount}'

# Ver últimos eventos
aws ecs describe-services \
  --cluster orders-cluster \
  --services medisupply-dev-catalogo-service-svc \
  --query 'services[0].events[0:10].[createdAt,message]' \
  --output table
```

---

## 🔧 Troubleshooting

### Problema: Workflow falla en "Build and push image"

**Causa**: Dockerfile inválido o falta de dependencias

**Solución**:
```bash
# Probar build local
cd catalogo-service/
docker build --platform linux/amd64 -t test:local .
```

---

### Problema: "Task failed health checks"

**Causa**: El contenedor no pasa el health check del ALB

**Solución**:
1. Verificar que el endpoint `/health` existe y responde 200 OK
2. Verificar que el puerto expuesto coincide con el configurado en Terraform
3. Revisar logs de CloudWatch

```bash
aws logs tail /ecs/medisupply-dev-catalogo-service --since 5m
```

---

### Problema: "Service failed to reach steady state"

**Causa**: El deployment no se estabiliza en 15 minutos

**Solución**:
1. Verificar eventos del servicio ECS
2. Revisar si hay errores en los logs del contenedor
3. Verificar límites de CPU/memoria

```bash
# Ver por qué falló
aws ecs describe-services \
  --cluster orders-cluster \
  --services medisupply-dev-catalogo-service-svc \
  --query 'services[0].events[0:20]'
```

---

## 🆕 Agregar Nuevo Servicio

### Template para Nuevo Workflow

```yaml
name: Deploy Mi Nuevo Servicio

on:
  push:
    branches: ["main", "develop"]
    paths:
      - "mi-nuevo-servicio/**"
      - ".github/workflows/deploy-mi-nuevo-servicio.yml"
  workflow_dispatch:
    inputs:
      ref:
        description: "Branch/Tag/Commit a desplegar"
        required: true
        default: "develop"

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: medisupply-dev-mi-nuevo-servicio
  ECS_CLUSTER: orders-cluster
  ECS_SERVICE: medisupply-dev-mi-nuevo-servicio-svc
  CONTAINER_NAME: mi-nuevo-servicio
  IMAGE_TAG: ${{ github.sha }}

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          ref: ${{ github.event_name == 'workflow_dispatch' && inputs.ref || github.ref }}

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::217466752988:role/github-actions-deploy
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build, tag, and push image
        id: build-image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          TAG: ${{ github.event_name == 'workflow_dispatch' && inputs.ref || github.sha }}
        working-directory: ./mi-nuevo-servicio
        run: |
          IMAGE_URI=${ECR_REGISTRY}/${{ env.ECR_REPOSITORY }}:${TAG}
          docker build --platform linux/amd64 -t "${IMAGE_URI}" .
          docker push "${IMAGE_URI}"
          docker tag "${IMAGE_URI}" "${ECR_REGISTRY}/${{ env.ECR_REPOSITORY }}:latest"
          docker push "${ECR_REGISTRY}/${{ env.ECR_REPOSITORY }}:latest"
          echo "image=${IMAGE_URI}" >> $GITHUB_OUTPUT

      - name: Download current task definition
        run: |
          aws ecs describe-task-definition \
            --task-definition medisupply-dev-mi-nuevo-servicio \
            --query 'taskDefinition' > task-definition.json

      - name: Fill new image in task definition
        id: task-def
        uses: aws-actions/amazon-ecs-render-task-definition@v1
        with:
          task-definition: task-definition.json
          container-name: ${{ env.CONTAINER_NAME }}
          image: ${{ steps.build-image.outputs.image }}

      - name: Deploy task definition to ECS
        uses: aws-actions/amazon-ecs-deploy-task-definition@v1
        with:
          task-definition: ${{ steps.task-def.outputs.task-definition }}
          service: ${{ env.ECS_SERVICE }}
          cluster: ${{ env.ECS_CLUSTER }}
          wait-for-service-stability: true

      - name: Post-deploy status
        run: |
          echo "✅ Deployment successful!"
          echo "🔗 Service: ${{ env.ECS_SERVICE }}"
          echo "🖼️  Image: ${{ steps.build-image.outputs.image }}"
```

---

## 📚 Referencias

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS ECS Deploy Task Definition Action](https://github.com/aws-actions/amazon-ecs-deploy-task-definition)
- [AWS ECR Login Action](https://github.com/aws-actions/amazon-ecr-login)
- [Configure AWS Credentials Action](https://github.com/aws-actions/configure-aws-credentials)

---

## ✅ Estado Actual

| Servicio | Workflow | Estado | Última Actualización |
|----------|----------|--------|---------------------|
| orders-service | ✅ | Funcional | Oct 2025 |
| catalogo-service | ✅ | **NUEVO** | Oct 24, 2025 |
| cliente-service | ✅ | **NUEVO** | Oct 24, 2025 |
| bff-cliente | ✅ | **ACTUALIZADO** | Oct 24, 2025 |
| bff-venta | ✅ | **ACTUALIZADO** | Oct 24, 2025 |
| consumer-lb | ✅ | Funcional | Oct 2025 |
| rutas-service | ✅ | Funcional | Oct 2025 |

---

**Mantenido por**: Equipo de DevOps MediSupply  
**Última actualización**: 24 de Octubre, 2025


