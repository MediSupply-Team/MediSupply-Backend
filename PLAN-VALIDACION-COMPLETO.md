# 📋 PLAN DE VALIDACIÓN Y DESPLIEGUE MEDISUPPLY

## 🎯 OBJETIVO GENERAL
Validar end-to-end todos los servicios localmente antes de desplegar a AWS, asegurando que BFFs funcionan correctamente como proxies.

---

## 📐 FASE 1A: CATALOGO-SERVICE (En Progreso)

### Endpoints a Validar:
```bash
# Health check
GET http://localhost:3001/health

# Listar productos (con api_prefix)
GET http://localhost:3001/api/catalog/items
GET http://localhost:3001/api/catalog/items?q=ibuprofeno&page=1&size=10

# Detalle de producto
GET http://localhost:3001/api/catalog/items/{id}

# Inventario de producto
GET http://localhost:3001/api/catalog/items/{id}/inventario
```

### Configuración Docker-Compose:
- Puerto externo: `3001`
- Puerto interno: `8080`
- API Prefix: `/api`
- Router Prefix: `/catalog`
- Base de datos: `catalog-db` (puerto 5433:5432)
- Archivo init: `catalogo-service/data/001_init.sql`

### ✅ Checklist:
- [ ] Health check responde
- [ ] Base de datos tiene datos (verificar con SQL)
- [ ] Endpoint `/api/catalog/items` lista productos
- [ ] Endpoint devuelve estructura correcta (items, meta, paginación)
- [ ] Cache Redis funciona
- [ ] Logs no muestran errores

---

## 📐 FASE 1B: CLIENTE-SERVICE

### Endpoints a Validar:
```bash
# Health check (si existe)
GET http://localhost:3003/health

# Listar clientes
GET http://localhost:3003/api/cliente/
GET http://localhost:3003/api/cliente/?limite=10&activos_solo=true

# Detalle de cliente
GET http://localhost:3003/api/cliente/{cliente_id}/detalle
GET http://localhost:3003/api/cliente/{cliente_id}/historico-compras
```

### Configuración Docker-Compose:
- Puerto externo: `3003`
- Puerto interno: `8000`
- API Prefix: `/api`
- Router Prefix: `/cliente`
- Base de datos: `cliente-db` (puerto 5435:5432)
- Archivo init: `cliente-service/data/001_init.sql`

### ✅ Checklist:
- [ ] Health check responde (o crear uno)
- [ ] Base de datos tiene datos
- [ ] Endpoint `/api/cliente/` lista clientes
- [ ] Estructura de respuesta correcta
- [ ] Redis funciona
- [ ] Logs sin errores

---

## 📐 FASE 2A: BFF-VENTA → CATALOGO-SERVICE

### Endpoints del BFF-Venta a Validar:
```bash
# Revisar archivo: bff-venta/app/routes/catalog.py
# Verificar que apunta a: CATALOGO_SERVICE_URL
```

### Configuración Docker-Compose:
- Puerto externo: `8001` (por confirmar)
- Variable: `CATALOGO_SERVICE_URL: http://catalog-service:8080`

### ✅ Checklist:
- [ ] BFF-Venta levanta correctamente
- [ ] Endpoints de catálogo responden a través del BFF
- [ ] Proxy funciona (BFF → catalogo-service)
- [ ] Headers y CORS configurados
- [ ] Logs muestran llamadas correctas

---

## 📐 FASE 2B: BFF-CLIENTE → CLIENTE-SERVICE

### Endpoints del BFF-Cliente a Validar:
```bash
# Revisar archivo: bff-cliente/app/routes/client.py
# Verificar que apunta a: CLIENTE_SERVICE_URL
```

### Configuración Docker-Compose:
- Puerto externo: `8002`
- Variable: `CLIENTE_SERVICE_URL: http://cliente-service:8000`

### ✅ Checklist:
- [ ] BFF-Cliente levanta correctamente
- [ ] Endpoints de cliente responden a través del BFF
- [ ] Proxy funciona (BFF → cliente-service)
- [ ] SQS client configurado
- [ ] Logs muestran llamadas correctas

---

## 📐 FASE 3: GENERACIÓN DE IMÁGENES PARA AWS

### Imágenes a Generar:
```bash
# Construir para arquitectura correcta (linux/amd64)
docker buildx build --platform linux/amd64 \
  -t catalogo-service:latest ./catalogo-service

docker buildx build --platform linux/amd64 \
  -t cliente-service:latest ./cliente-service

docker buildx build --platform linux/amd64 \
  -t bff-venta:latest ./bff-venta

docker buildx build --platform linux/amd64 \
  -t bff-cliente:latest ./bff-cliente
```

### ✅ Checklist:
- [ ] Imágenes con arquitectura correcta (amd64)
- [ ] Healthchecks configurados en Dockerfile
- [ ] Entrypoints funcionan (populate_db.py)
- [ ] Variables de entorno correctas
- [ ] Tamaño de imagen optimizado

---

## 📐 FASE 4: TERRAFORM - INFRAESTRUCTURA AWS

### Archivos a Revisar:
```
infra/terraform/modules/catalogo-service/main.tf
infra/terraform/modules/cliente-service/main.tf
infra/terraform/modules/bff-venta/main.tf
infra/terraform/modules/bff-cliente/main.tf
```

### Pasos:
1. **Destruir infraestructura existente:**
   ```bash
   cd infra/terraform
   terraform destroy -auto-approve
   ```

2. **Verificar limpieza:**
   - ECR repositories vaciados
   - RDS instances eliminados
   - ECS services detenidos
   - Load balancers eliminados

3. **Aplicar nueva infraestructura:**
   ```bash
   terraform init
   terraform plan -out=tfplan
   terraform apply tfplan
   ```

### ✅ Checklist:
- [ ] Secrets Manager con credenciales DB correctas
- [ ] DATABASE_URL con formato `postgresql+asyncpg://`
- [ ] IAM roles con permisos correctos (secrets, logs, ECR)
- [ ] Health checks configurados en ECS task definitions
- [ ] ALB target groups apuntando a puertos correctos
- [ ] Security groups permiten tráfico necesario
- [ ] Entrypoint ejecuta populate_db.py en inicio

---

## 📐 FASE 5: CI/CD - GITHUB WORKFLOWS

### Archivos a Revisar:
```
.github/workflows/deploy-catalogo-service.yml
.github/workflows/deploy-cliente-service.yml
.github/workflows/deploy-bff-venta.yml
.github/workflows/deploy-bff-cliente.yml
```

### Patrón Deseado:
1. **Trigger**: Push a `main` o `develop`
2. **Build**: Construir imagen Docker (linux/amd64)
3. **Push**: Subir a ECR
4. **Deploy**: Actualizar ECS service (force new deployment)

### ✅ Checklist:
- [ ] Workflows existen para cada servicio
- [ ] Autenticación con AWS via OIDC
- [ ] Build con arquitectura correcta
- [ ] Tags de imagen consistentes
- [ ] Rollback automático en caso de fallo
- [ ] Notificaciones de deploy

---

## 🔍 PROBLEMAS IDENTIFICADOS HASTA AHORA

### Catalogo-Service:
- ❌ Endpoint `/api/catalog/items` devuelve 404
- ❌ Puerto interno/externo confuso (8080 vs 3001)
- ⚠️ Necesita verificación de datos en BD

### Cliente-Service:
- ❌ No tiene endpoint `/health`
- ❌ Todos los endpoints devuelven 404
- ⚠️ Necesita verificación de datos en BD

---

## 📊 PROGRESO ACTUAL

```
[█████░░░░░░░░░░░░░░░] 25% - FASE 1A en progreso
```

**Siguiente Paso:** Diagnosticar por qué catalogo-service no responde en `/api/catalog/items`

---

## 🚀 COMANDO RÁPIDO DE REFERENCIA

```bash
# Ver logs de servicio específico
docker-compose logs -f catalog-service
docker-compose logs -f cliente-service

# Probar endpoints
curl http://localhost:3001/health
curl http://localhost:3001/api/catalog/items

# Verificar base de datos
docker-compose exec catalog-db psql -U catalog_user -d catalogo -c "SELECT * FROM producto LIMIT 5;"

# Reiniciar servicio específico
docker-compose restart catalog-service

# Ver estado de contenedores
docker-compose ps
```

