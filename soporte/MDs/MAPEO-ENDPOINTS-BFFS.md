# 🔀 MAPEO DE ENDPOINTS - BFF a MICROSERVICIOS

**Documento:** Mapeo completo de cómo los BFFs hacen proxy a los microservicios  
**Fecha:** 23 de Octubre, 2025

---

## 📋 TABLA DE CONTENIDOS

1. [BFF-CLIENTE](#bff-cliente)
2. [BFF-VENTA](#bff-venta)
3. [Resumen de Servicios](#resumen-de-servicios)
4. [Configuración de Variables](#configuración-de-variables)
5. [Ejemplos de Uso](#ejemplos-de-uso)

---

## 🔵 BFF-CLIENTE

**Puerto Local:** `8002`  
**Puerto Interno:** `8001`  
**Microservicios que consume:**
- `cliente-service` (puerto 8000)
- `orders-service` (puerto 8000)
- `sqs` (AWS SQS)

### Arquitectura:
```
Cliente/App → BFF-Cliente (8002) → {
    cliente-service (3003)
    orders-service (8000)
    AWS SQS
}
```

---

### 📍 ENDPOINTS DE CLIENTES (Proxy a cliente-service)

#### 1. Listar Clientes
```yaml
BFF Endpoint:
  GET /api/v1/client/
  Puerto: 8002

Microservicio Destino:
  GET /api/cliente/
  Service: cliente-service:8000
  Puerto Local: 3003

Parámetros:
  - limite (int): Número máximo de clientes
  - offset (int): Paginación
  - activos_solo (bool): Filtrar solo activos
  - ordenar_por (string): nombre | nit | codigo_unico | created_at
  - vendedor_id (string): Para trazabilidad

Ejemplo:
  # A través del BFF
  curl "http://localhost:8002/api/v1/client/?limite=5"
  
  # Directo al microservicio (para comparación)
  curl "http://localhost:3003/api/cliente/?limite=5"
```

#### 2. Buscar Cliente
```yaml
BFF Endpoint:
  GET /api/v1/client/search
  Puerto: 8002

Microservicio Destino:
  GET /api/cliente/search
  Service: cliente-service:8000
  Puerto Local: 3003

Parámetros:
  - q (string, required): NIT, nombre o código único
  - vendedor_id (string, required): ID del vendedor

Ejemplo:
  # A través del BFF
  curl "http://localhost:8002/api/v1/client/search?q=900123456-7&vendedor_id=VEND001"
  
  # Directo al microservicio
  curl "http://localhost:3003/api/cliente/search?q=900123456-7&vendedor_id=VEND001"
```

#### 3. Histórico del Cliente
```yaml
BFF Endpoint:
  GET /api/v1/client/{cliente_id}/historico
  Puerto: 8002

Microservicio Destino:
  GET /api/cliente/{cliente_id}/historico
  Service: cliente-service:8000
  Puerto Local: 3003

Parámetros:
  - cliente_id (path, required): ID del cliente
  - vendedor_id (query, required): ID del vendedor
  - limite_meses (int): Meses hacia atrás (default: 12)
  - incluir_devoluciones (bool): Incluir devoluciones (default: true)

Ejemplo:
  # A través del BFF
  curl "http://localhost:8002/api/v1/client/CLI001/historico?vendedor_id=VEND001"
  
  # Directo al microservicio
  curl "http://localhost:3003/api/cliente/CLI001/historico?vendedor_id=VEND001"
```

---

### 📍 ENDPOINTS DE ÓRDENES (Envia a SQS)

#### 4. Crear Orden
```yaml
BFF Endpoint:
  POST /api/v1/orders
  Puerto: 8002

Microservicio Destino:
  AWS SQS Queue (asíncrono)
  No llama directamente a orders-service

Enriquecimiento:
  - created_by_role: "customer"
  - source: "bff-cliente"

Body:
  {
    "body": {
      "customer_id": "CLI001",
      "items": [
        {
          "product_id": "PROD006",
          "quantity": 100
        }
      ]
    },
    "group_id": "customer-123",  // Opcional
    "dedup_id": "order-456"      // Opcional
  }

Respuesta:
  HTTP 202 (Accepted)
  {
    "messageId": "async-uuid-here",
    "event_id": "uuid-here",
    "status": "accepted"
  }

Ejemplo:
  curl -X POST "http://localhost:8002/api/v1/orders" \
    -H "Content-Type: application/json" \
    -d '{
      "body": {
        "customer_id": "CLI001",
        "items": [{"product_id": "PROD006", "quantity": 100}]
      }
    }'
```

---

### 📍 HEALTH CHECK

```yaml
BFF Endpoint:
  GET /health
  Puerto: 8002

Response:
  {
    "status": "ok"
  }

Ejemplo:
  curl "http://localhost:8002/health"
```

---

## 🟢 BFF-VENTA

**Puerto Local:** `8001` (por configurar en docker-compose)  
**Puerto Interno:** `8000`  
**Microservicios que consume:**
- `catalogo-service` (puerto 8000)
- `orders-service` (puerto 8000)
- `rutas-service` (puerto 8000)
- `sqs` (AWS SQS)

### Arquitectura:
```
Vendedor/App → BFF-Venta (8001) → {
    catalogo-service (3001)
    orders-service (8000)
    rutas-service (8003)
    AWS SQS
}
```

---

### 📍 ENDPOINTS DE CATÁLOGO (Proxy a catalogo-service)

#### 1. Listar Productos del Catálogo
```yaml
BFF Endpoint:
  GET /api/v1/catalog/items
  Puerto: 8001

Microservicio Destino:
  GET /api/catalog/items
  Service: catalog-service:8000
  Puerto Local: 3001

Parámetros:
  - q (string): Búsqueda por nombre
  - categoria_id (string): Filtro por categoría
  - codigo (string): Filtro por código de producto
  - pais (string): Filtro por país
  - bodega_id (string): Filtro por bodega
  - page (int): Número de página
  - size (int): Tamaño de página
  - sort (string): relevancia | precio | cantidad | vencimiento

Ejemplo:
  # A través del BFF
  curl "http://localhost:8001/api/v1/catalog/items?q=ibuprofeno"
  
  # Directo al microservicio
  curl "http://localhost:3001/api/catalog/items?q=ibuprofeno"
```

#### 2. Detalle de Producto
```yaml
BFF Endpoint:
  GET /api/v1/catalog/items/{item_id}
  Puerto: 8001

Microservicio Destino:
  GET /api/catalog/items/{id}
  Service: catalog-service:8000
  Puerto Local: 3001

Parámetros:
  - item_id (path, required): ID del producto

Ejemplo:
  # A través del BFF
  curl "http://localhost:8001/api/v1/catalog/items/PROD006"
  
  # Directo al microservicio
  curl "http://localhost:3001/api/catalog/items/PROD006"
```

#### 3. Inventario de Producto
```yaml
BFF Endpoint:
  GET /api/v1/catalog/items/{item_id}/inventario
  Puerto: 8001

Microservicio Destino:
  GET /api/catalog/items/{id}/inventario
  Service: catalog-service:8000
  Puerto Local: 3001

Parámetros:
  - item_id (path, required): ID del producto
  - page (int): Número de página
  - size (int): Tamaño de página

Ejemplo:
  # A través del BFF
  curl "http://localhost:8001/api/v1/catalog/items/PROD006/inventario?size=3"
  
  # Directo al microservicio
  curl "http://localhost:3001/api/catalog/items/PROD006/inventario?size=3"
```

#### 4. Crear Producto (POST)
```yaml
BFF Endpoint:
  POST /api/v1/catalog/items
  Puerto: 8001

Microservicio Destino:
  POST /api/catalog/items
  Service: catalog-service:8000
  Puerto Local: 3001

Body:
  {
    "nombre": "Producto Nuevo",
    "codigo": "PN001",
    "categoria": "ANALGESICS",
    "presentacion": "Tableta",
    "precio_unitario": 250.0,
    "requisitos_almacenamiento": "Temperatura ambiente"
  }

Ejemplo:
  curl -X POST "http://localhost:8001/api/v1/catalog/items" \
    -H "Content-Type: application/json" \
    -d '{"nombre": "Producto Nuevo", "codigo": "PN001"}'
```

#### 5. Actualizar Producto (PUT)
```yaml
BFF Endpoint:
  PUT /api/v1/catalog/items/{item_id}
  Puerto: 8001

Microservicio Destino:
  PUT /api/catalog/items/{id}
  Service: catalog-service:8000
  Puerto Local: 3001
```

#### 6. Eliminar Producto (DELETE)
```yaml
BFF Endpoint:
  DELETE /api/v1/catalog/items/{item_id}
  Puerto: 8001

Microservicio Destino:
  DELETE /api/catalog/items/{id}
  Service: catalog-service:8000
  Puerto Local: 3001
```

---

### 📍 ENDPOINTS DE RUTAS (Proxy a rutas-service)

#### 7. Obtener Ruta por Fecha
```yaml
BFF Endpoint:
  GET /api/v1/rutas/visita/{fecha}
  Puerto: 8001

Microservicio Destino:
  GET /api/rutas/visita/{fecha}
  Service: rutas-service:8000
  Puerto Local: 8003

Parámetros:
  - fecha (path, required): Fecha en formato YYYY-MM-DD

Ejemplo:
  # A través del BFF
  curl "http://localhost:8001/api/v1/rutas/visita/2025-01-15"
  
  # Directo al microservicio
  curl "http://localhost:8003/api/rutas/visita/2025-01-15"
```

#### 8. Health Check de Rutas
```yaml
BFF Endpoint:
  GET /api/v1/rutas/health
  Puerto: 8001

Microservicio Destino:
  GET /health
  Service: rutas-service:8000
  Puerto Local: 8003

Ejemplo:
  curl "http://localhost:8001/api/v1/rutas/health"
```

---

### 📍 ENDPOINTS DE ÓRDENES (Envia a SQS)

#### 9. Crear Orden (Vendedor)
```yaml
BFF Endpoint:
  POST /api/v1/orders
  Puerto: 8001

Microservicio Destino:
  AWS SQS Queue (asíncrono)
  No llama directamente a orders-service

Enriquecimiento:
  - created_by_role: "vendor"
  - source: "bff-venta"

Body:
  {
    "body": {
      "customer_id": "CLI001",
      "items": [
        {
          "product_id": "PROD006",
          "quantity": 100
        }
      ]
    },
    "group_id": "vendor-456",  // Opcional
    "dedup_id": "order-789"    // Opcional
  }

Respuesta:
  HTTP 202 (Accepted)
  {
    "messageId": "async-uuid-here",
    "event_id": "uuid-here",
    "status": "accepted"
  }

Ejemplo:
  curl -X POST "http://localhost:8001/api/v1/orders" \
    -H "Content-Type: application/json" \
    -d '{
      "body": {
        "customer_id": "CLI001",
        "items": [{"product_id": "PROD006", "quantity": 100}]
      }
    }'
```

---

### 📍 HEALTH CHECK

```yaml
BFF Endpoint:
  GET /health
  Puerto: 8001

Response:
  {
    "status": "ok"
  }

Ejemplo:
  curl "http://localhost:8001/health"
```

---

## 📊 RESUMEN DE SERVICIOS

### Tabla de Mapeo Completa:

| BFF | Endpoint BFF | Microservicio Destino | Endpoint Microservicio | Método |
|-----|-------------|----------------------|----------------------|---------|
| **BFF-CLIENTE** | | | | |
| | `/api/v1/client/` | `cliente-service:8000` | `/api/cliente/` | GET |
| | `/api/v1/client/search` | `cliente-service:8000` | `/api/cliente/search` | GET |
| | `/api/v1/client/{id}/historico` | `cliente-service:8000` | `/api/cliente/{id}/historico` | GET |
| | `/api/v1/orders` | `AWS SQS` | `orders-events.fifo` | POST |
| | `/health` | `N/A (propio)` | `N/A` | GET |
| **BFF-VENTA** | | | | |
| | `/api/v1/catalog/items` | `catalog-service:8000` | `/api/catalog/items` | GET |
| | `/api/v1/catalog/items/{id}` | `catalog-service:8000` | `/api/catalog/items/{id}` | GET |
| | `/api/v1/catalog/items/{id}/inventario` | `catalog-service:8000` | `/api/catalog/items/{id}/inventario` | GET |
| | `/api/v1/catalog/items` | `catalog-service:8000` | `/api/catalog/items` | POST |
| | `/api/v1/catalog/items/{id}` | `catalog-service:8000` | `/api/catalog/items/{id}` | PUT |
| | `/api/v1/catalog/items/{id}` | `catalog-service:8000` | `/api/catalog/items/{id}` | DELETE |
| | `/api/v1/rutas/visita/{fecha}` | `rutas-service:8000` | `/api/rutas/visita/{fecha}` | GET |
| | `/api/v1/rutas/health` | `rutas-service:8000` | `/health` | GET |
| | `/api/v1/orders` | `AWS SQS` | `orders-events.fifo` | POST |
| | `/health` | `N/A (propio)` | `N/A` | GET |

---

## ⚙️ CONFIGURACIÓN DE VARIABLES

### BFF-CLIENTE (`docker-compose.yml`):
```yaml
environment:
  PORT: "8001"
  FLASK_ENV: development
  AWS_REGION: us-east-1
  SQS_QUEUE_URL: ${SQS_QUEUE_URL}
  CLIENTE_SERVICE_URL: http://cliente-service:8000  ✅
  CATALOGO_SERVICE_URL: http://catalog-service:8000
  ORDERS_SERVICE_URL: http://orders-service:8000

ports:
  - "8002:8001"  # Puerto externo 8002
```

### BFF-VENTA (necesita ser agregado a `docker-compose.yml`):
```yaml
bff-venta:
  build:
    context: ./bff-venta
    dockerfile: Dockerfile
  container_name: bff-venta
  ports:
    - "8001:8000"
  environment:
    PORT: "8000"
    FLASK_ENV: development
    AWS_REGION: us-east-1
    SQS_QUEUE_URL: ${SQS_QUEUE_URL}
    CATALOGO_SERVICE_URL: http://catalog-service:8000  ✅
    ORDERS_SERVICE_URL: http://orders-service:8000
    RUTAS_SERVICE_URL: http://backend:8000  ✅ (ruta-service)
  depends_on:
    catalog-service: { condition: service_started }
  command: gunicorn wsgi:app --bind 0.0.0.0:8000 --workers 2 --threads 4
```

---

## 🧪 EJEMPLOS DE USO

### Escenario 1: Cliente busca productos
```bash
# 1. Cliente consulta catálogo a través de BFF-Cliente
# (BFF-Cliente no tiene endpoints de catálogo directamente)
# El cliente debería usar BFF-Venta para catálogo

# 2. Cliente consulta su historial
curl "http://localhost:8002/api/v1/client/CLI001/historico?vendedor_id=VEND001"

# 3. Cliente crea una orden
curl -X POST "http://localhost:8002/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "body": {
      "customer_id": "CLI001",
      "items": [{"product_id": "PROD006", "quantity": 50}]
    }
  }'
```

### Escenario 2: Vendedor gestiona catálogo y rutas
```bash
# 1. Vendedor consulta productos disponibles
curl "http://localhost:8001/api/v1/catalog/items?pais=CO&size=10"

# 2. Vendedor verifica inventario
curl "http://localhost:8001/api/v1/catalog/items/PROD006/inventario"

# 3. Vendedor consulta su ruta del día
curl "http://localhost:8001/api/v1/rutas/visita/2025-10-24"

# 4. Vendedor busca cliente
# (Usar BFF-Cliente para esto, o agregar proxy en BFF-Venta)
curl "http://localhost:8002/api/v1/client/search?q=900123456-7&vendedor_id=VEND001"

# 5. Vendedor crea orden para cliente
curl -X POST "http://localhost:8001/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "body": {
      "customer_id": "CLI001",
      "vendor_id": "VEND001",
      "items": [{"product_id": "PROD006", "quantity": 100}]
    }
  }'
```

---

## 🔍 DIFERENCIAS CLAVE ENTRE BFFs

### BFF-Cliente:
- **Audiencia:** Clientes finales (farmacias, hospitales)
- **Enfoque:** Consultar historial, hacer pedidos
- **No tiene:** Endpoints de catálogo (debería usar BFF-Venta o tener proxy)
- **Enriquecimiento SQS:** `created_by_role: "customer"`, `source: "bff-cliente"`

### BFF-Venta:
- **Audiencia:** Vendedores/Representantes
- **Enfoque:** Gestionar catálogo, consultar rutas, tomar pedidos
- **Tiene:** Endpoints completos de catálogo, rutas
- **Enriquecimiento SQS:** `created_by_role: "vendor"`, `source: "bff-venta"`

---

## ⚠️ NOTAS IMPORTANTES

### 1. Puertos Correctos
- ✅ **catalogo-service** usa puerto `8000` (NO 8080)
- ✅ **cliente-service** usa puerto `8000`
- ✅ **rutas-service** (backend) usa puerto `8000` (local: 8003)
- ✅ **orders-service** usa puerto `8000`

### 2. Consistencia de Nombres
- En Docker Compose: usar nombres de servicio (`catalog-service`, `cliente-service`)
- En AWS ECS: usar ALB URLs o service discovery

### 3. Timeouts
- BFFs tienen timeout de `30s` por defecto en llamadas HTTP
- SQS envío es asíncrono (no bloqueante)

### 4. Swagger/Documentación
- BFF-Cliente: Swagger UI disponible en `/docs`
- BFF-Venta: Swagger UI disponible en `/docs`

---

## 📚 ARCHIVOS RELACIONADOS

1. **`bff-cliente/app/routes/client.py`** - Rutas de cliente
2. **`bff-cliente/app/routes/orders.py`** - Rutas de órdenes (cliente)
3. **`bff-venta/app/routes/catalog.py`** - Rutas de catálogo
4. **`bff-venta/app/routes/rutas.py`** - Rutas de visitas
5. **`bff-venta/app/routes/orders.py`** - Rutas de órdenes (vendedor)
6. **`bff-cliente/app/services/cliente_client.py`** - Cliente HTTP para cliente-service
7. **`bff-venta/app/services/catalogo_client.py`** - Cliente HTTP para catalogo-service
8. **`bff-*/app/services/sqs_client.py`** - Cliente SQS compartido

---

## ✅ VERIFICACIÓN DE CONECTIVIDAD

```bash
#!/bin/bash

echo "🔍 Verificando conectividad BFF → Microservicios..."

# BFF-Cliente → Cliente-Service
echo "1. BFF-Cliente → Cliente-Service:"
curl -s "http://localhost:8002/api/v1/client/?limite=1" | jq 'length'

# BFF-Venta → Catalogo-Service  
echo "2. BFF-Venta → Catalogo-Service:"
curl -s "http://localhost:8001/api/v1/catalog/items?size=1" | jq '.meta.total'

# BFF-Venta → Rutas-Service
echo "3. BFF-Venta → Rutas-Service:"
curl -s "http://localhost:8001/api/v1/rutas/health" | jq '.status'

echo "✅ Verificación completada"
```

---

## 🎯 RECOMENDACIONES

### Para Producción (AWS):
1. ⚠️ Usar ALB o Service Discovery en lugar de nombres de contenedor
2. ⚠️ Configurar Circuit Breakers en llamadas HTTP
3. ⚠️ Implementar retry logic con backoff exponencial
4. ⚠️ Agregar rate limiting en BFFs
5. ⚠️ Monitorear latencias end-to-end

### Para Desarrollo Local:
1. ✅ Asegurar que todos los servicios estén en la misma red Docker
2. ✅ Usar nombres de servicio de docker-compose
3. ✅ Verificar puertos correctos en variables de entorno
4. ✅ Probar endpoints directos antes de probar a través de BFF

