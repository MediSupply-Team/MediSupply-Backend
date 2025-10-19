# 🚀 Scripts de Deployment BFF-Catalogo

Esta carpeta contiene scripts automatizados para el deployment y gestión del BFF-Catalogo de MediSupply.

## 📋 Scripts Disponibles

### 1. `./deploy-bff-catalogo.sh` - Deployment Completo
**Descripción:** Script principal que ejecuta todo el proceso de deployment de forma automatizada.

**Funciones:**
- ✅ Verifica prerequisitos (Docker, AWS CLI, Terraform)
- 🔐 Login automático a ECR
- 🏗️ Build de imagen Docker con plataforma correcta
- ⬆️ Push a ECR con tags automáticos
- 🏛️ Deployment de infraestructura con Terraform  
- 🔄 Update del servicio ECS
- ⏳ Espera estabilización del servicio
- 🏥 Verificación de salud
- 📊 Reporte de estado final

**Uso:**
```bash
./deploy-bff-catalogo.sh
```

### 2. `./test-bff-catalogo.sh` - Testing de Endpoints
**Descripción:** Prueba todos los endpoints del BFF-Catalogo para verificar funcionamiento.

**Tests incluidos:**
- Health check (`/health`)
- Listar items (`GET /catalog/items`)
- Crear item (`POST /catalog/items`)
- Validación de respuestas HTTP

**Uso:**
```bash
./test-bff-catalogo.sh
```

### 3. `./monitor-bff-catalogo.sh` - Monitoreo
**Descripción:** Dashboard de monitoreo del estado del servicio.

**Información mostrada:**
- 📊 Estado del servicio ECS
- 🏥 Salud de tareas
- 🎯 Estado del Target Group
- 📝 Logs recientes
- 🔗 Test de endpoints

**Uso:**
```bash
# Monitoreo único
./monitor-bff-catalogo.sh

# Monitoreo continuo (actualiza cada 30s)
./monitor-bff-catalogo.sh --watch
```

## 🎯 Flujo Recomendado

### Deployment Inicial
```bash
# 1. Deployment completo
./deploy-bff-catalogo.sh

# 2. Verificar funcionamiento
./test-bff-catalogo.sh

# 3. Monitoreo (opcional)
./monitor-bff-catalogo.sh
```

### Redeploy por Cambios
```bash
# Solo rebuild y redeploy (más rápido)
./deploy-bff-catalogo.sh

# Verificar cambios
./test-bff-catalogo.sh
```

### Troubleshooting
```bash
# Monitoreo continuo para debug
./monitor-bff-catalogo.sh --watch
```

## 📍 URLs y Endpoints

Una vez desplegado, los endpoints estarán disponibles en:
- **Base URL:** `http://medisupply-dev-bff-catalogo-alb-{id}.us-east-1.elb.amazonaws.com`

### Endpoints Disponibles:
- `GET /health` - Health check
- `GET /catalog/items` - Listar todos los items
- `GET /catalog/items/{id}` - Obtener item específico
- `GET /catalog/items/{id}/inventario` - Inventario de item
- `POST /catalog/items` - Crear nuevo item
- `PUT /catalog/items/{id}` - Actualizar item
- `DELETE /catalog/items/{id}` - Eliminar item

## 🔧 Configuración

Los scripts están configurados para:
- **Región AWS:** us-east-1
- **Cluster ECS:** medisupply-dev-cluster
- **Repositorio ECR:** medisupply-dev-bff-catalogo
- **Puerto:** 3000 (interno del contenedor)

## 🚨 Troubleshooting

### Error: "Docker no encontrado"
```bash
# Instalar Docker Desktop para macOS
brew install --cask docker
```

### Error: "AWS CLI no configurado"
```bash
# Configurar credenciales AWS
aws configure
```

### Error: "Terraform no encontrado"
```bash
# Instalar Terraform
brew install terraform
```

### Error: "Servicio no responde"
```bash
# Verificar estado con monitoreo
./monitor-bff-catalogo.sh

# Ver logs detallados
aws logs tail /ecs/medisupply-dev-bff-catalogo --follow
```

## 🎨 Features de los Scripts

- 🎨 **Output colorizado** para fácil lectura
- ⚠️ **Manejo de errores** con mensajes claros
- ⏱️ **Timeouts inteligentes** para evitar esperas infinitas
- 🧹 **Limpieza automática** de imágenes Docker
- 📊 **Reportes detallados** de estado
- 🔄 **Versionado automático** de imágenes

## 📝 Logs

Los logs del servicio se pueden ver en CloudWatch:
- **Log Group:** `/ecs/medisupply-dev-bff-catalogo`
- **Región:** us-east-1

```bash
# Ver logs en tiempo real
aws logs tail /ecs/medisupply-dev-bff-catalogo --follow
```

---
*Scripts creados para MediSupply Backend - BFF Catalogo Module*