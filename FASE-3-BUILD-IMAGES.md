# 🐳 FASE 3: BUILD DE IMÁGENES DOCKER PARA AWS

**Objetivo:** Construir imágenes optimizadas con arquitectura correcta para AWS ECS Fargate

---

## 📋 CHECKLIST DE VERIFICACIÓN

### Requisitos de las imágenes:
- [x] Arquitectura: `linux/amd64` (Fargate no soporta ARM)
- [x] Puerto correcto: `8000` (no 8080)
- [x] Healthcheck configurado
- [x] Entrypoint para inicialización de datos
- [ ] Imágenes construidas localmente
- [ ] Imágenes probadas
- [ ] Tamaños optimizados

---

## 🏗️ CONSTRUCCIÓN DE IMÁGENES

### 1. catalogo-service

```bash
docker buildx build \
  --platform linux/amd64 \
  -t catalogo-service:latest \
  -t catalogo-service:v1.0.0 \
  ./catalogo-service
```

**Dockerfile verificado:**
- ✅ Puerto 8000 expuesto
- ✅ Healthcheck configurado con `/health`
- ✅ Entrypoint ejecuta populate_db.py
- ✅ Base: python:3.12-slim

---

### 2. cliente-service

```bash
docker buildx build \
  --platform linux/amd64 \
  -t cliente-service:latest \
  -t cliente-service:v1.0.0 \
  ./cliente-service
```

**Dockerfile verificado:**
- ✅ Puerto 8000 expuesto
- ✅ Healthcheck configurado con `/api/health`
- ✅ Entrypoint ejecuta populate_db.py
- ✅ Base: python:3.11-slim

---

### 3. bff-cliente

```bash
docker buildx build \
  --platform linux/amd64 \
  -t bff-cliente:latest \
  -t bff-cliente:v1.0.0 \
  ./bff-cliente
```

**Dockerfile verificado:**
- ✅ Puerto 8001 interno (mapeo flexible)
- ✅ Base: python:3.11-slim
- ✅ Gunicorn como servidor

---

### 4. bff-venta

```bash
docker buildx build \
  --platform linux/amd64 \
  -t bff-venta:latest \
  -t bff-venta:v1.0.0 \
  ./bff-venta
```

**Dockerfile verificado:**
- ✅ Puerto 8000 interno
- ✅ Base: python:3.11-slim
- ✅ Gunicorn como servidor
- ✅ Dependencias: requests, aiohttp, boto3

---

## 🧪 PRUEBAS LOCALES

### Probar catalogo-service:
```bash
docker run -d --name test-catalogo \
  -p 3001:8000 \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db" \
  catalogo-service:latest

# Verificar
curl http://localhost:3001/health
docker logs test-catalogo

# Limpiar
docker rm -f test-catalogo
```

### Probar cliente-service:
```bash
docker run -d --name test-cliente \
  -p 3003:8000 \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db" \
  cliente-service:latest

# Verificar
curl http://localhost:3003/api/cliente/health
docker logs test-cliente

# Limpiar
docker rm -f test-cliente
```

### Probar bff-cliente:
```bash
docker run -d --name test-bff-cliente \
  -p 8002:8001 \
  -e CLIENTE_SERVICE_URL="http://host:8000" \
  bff-cliente:latest

# Verificar
curl http://localhost:8002/health
docker logs test-bff-cliente

# Limpiar
docker rm -f test-bff-cliente
```

### Probar bff-venta:
```bash
docker run -d --name test-bff-venta \
  -p 8001:8000 \
  -e CATALOGO_SERVICE_URL="http://host:8000" \
  bff-venta:latest

# Verificar
curl http://localhost:8001/health
docker logs test-bff-venta

# Limpiar
docker rm -f test-bff-venta
```

---

## 📊 VERIFICACIÓN DE TAMAÑOS

```bash
docker images | grep -E "(catalogo|cliente|bff)" | awk '{print $1":"$2, $7$8}'
```

**Tamaños esperados:**
- catalogo-service: ~200-300 MB
- cliente-service: ~200-300 MB
- bff-cliente: ~150-250 MB
- bff-venta: ~150-250 MB

---

## 🔍 INSPECCIÓN DE IMÁGENES

```bash
# Ver arquitectura
docker inspect catalogo-service:latest | jq '.[0].Architecture'

# Ver configuración
docker inspect catalogo-service:latest | jq '.[0].Config'

# Ver healthcheck
docker inspect catalogo-service:latest | jq '.[0].Config.Healthcheck'

# Ver CMD/ENTRYPOINT
docker inspect catalogo-service:latest | jq '.[0].Config.Cmd, .[0].Config.Entrypoint'
```

---

## ⚠️ PROBLEMAS COMUNES Y SOLUCIONES

### 1. Arquitectura incorrecta (ARM en lugar de AMD64)
**Síntoma:** `exec format error` en AWS
**Solución:** 
```bash
# Asegurar que buildx esté configurado
docker buildx create --use --name multiarch

# Construir con platform específico
docker buildx build --platform linux/amd64 ...
```

### 2. Entrypoint sin permisos
**Síntoma:** `permission denied` al iniciar
**Solución:**
```dockerfile
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
```

### 3. Puerto incorrecto
**Síntoma:** Health checks fallan en ECS
**Solución:** Verificar que EXPOSE y CMD usen el mismo puerto (8000)

---

## 🚀 SCRIPT DE BUILD AUTOMATIZADO

```bash
#!/bin/bash
set -e

echo "🏗️  Building Docker images for AWS ECS..."

# Servicios a construir
SERVICES=("catalogo-service" "cliente-service" "bff-cliente" "bff-venta")

for SERVICE in "${SERVICES[@]}"; do
    echo ""
    echo "📦 Building $SERVICE..."
    docker buildx build \
        --platform linux/amd64 \
        --load \
        -t $SERVICE:latest \
        -t $SERVICE:v1.0.0 \
        ./$SERVICE
    
    echo "✅ $SERVICE built successfully"
done

echo ""
echo "📊 Image sizes:"
docker images | grep -E "(catalogo|cliente|bff)" | awk '{printf "%-30s %10s\n", $1":"$2, $7$8}'

echo ""
echo "🔍 Verifying architectures:"
for SERVICE in "${SERVICES[@]}"; do
    ARCH=$(docker inspect $SERVICE:latest | jq -r '.[0].Architecture')
    echo "$SERVICE: $ARCH"
done

echo ""
echo "✅ All images built successfully!"
```

---

## 📝 PRÓXIMOS PASOS (FASE 4)

Una vez construidas las imágenes:
1. Pushear a AWS ECR
2. Actualizar task definitions en Terraform
3. Desplegar en ECS

Comando para tag y push:
```bash
# Login a ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Tag
docker tag catalogo-service:latest ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/catalogo-service:latest

# Push
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/catalogo-service:latest
```

---

## ✅ CRITERIOS DE ACEPTACIÓN

- [ ] 4 imágenes construidas exitosamente
- [ ] Todas con arquitectura linux/amd64
- [ ] Healthchecks funcionando
- [ ] Tamaños razonables (< 500MB cada una)
- [ ] Probadas localmente
- [ ] Listas para push a ECR

