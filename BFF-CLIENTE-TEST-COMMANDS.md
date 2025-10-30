# 🧪 BFF-Cliente - Comandos de Prueba

**URL Base:** `http://medisupply-dev-bff-cliente-alb-1673122993.us-east-1.elb.amazonaws.com`

---

## ✅ Endpoints Operativos

### 1. Health Check
```bash
curl -X GET http://medisupply-dev-bff-cliente-alb-1673122993.us-east-1.elb.amazonaws.com/health
```

**Respuesta esperada:** `200 OK`
```json
{"status":"ok"}
```

---

### 2. Backend Health (Cliente Service)
```bash
curl -X GET http://medisupply-dev-bff-cliente-alb-1673122993.us-east-1.elb.amazonaws.com/api/v1/client/health
```

**Respuesta esperada:** `200 OK`
```json
{
  "database": "connected",
  "service": "cliente-service",
  "sla_max_response_ms": 2000,
  "status": "healthy",
  "timestamp": "2025-10-22T04:04:50Z",
  "version": "1.0.0"
}
```

---

### 3. Listar Clientes
```bash
# Listar todos los clientes
curl -X GET "http://medisupply-dev-bff-cliente-alb-1673122993.us-east-1.elb.amazonaws.com/api/v1/client/"

# Con parámetros opcionales
curl -X GET "http://medisupply-dev-bff-cliente-alb-1673122993.us-east-1.elb.amazonaws.com/api/v1/client/?limite=10&offset=0&activos_solo=true"
```

**Respuesta esperada:** `200 OK`
```json
[]
```
*(Actualmente sin datos - base de datos vacía)*

---

### 4. Buscar Cliente
```bash
# Búsqueda requiere vendedor_id
curl -X GET "http://medisupply-dev-bff-cliente-alb-1673122993.us-east-1.elb.amazonaws.com/api/v1/client/search?q=empresa&vendedor_id=V001"
```

**Parámetros:**
- `q` (requerido): Término de búsqueda (NIT, nombre, código)
- `vendedor_id` (requerido): ID del vendedor

**Respuesta esperada:** `200 OK`

---

### 5. Histórico de Cliente
```bash
# Obtener histórico de un cliente específico
curl -X GET "http://medisupply-dev-bff-cliente-alb-1673122993.us-east-1.elb.amazonaws.com/api/v1/client/CLI001/historico"

# Con parámetros opcionales
curl -X GET "http://medisupply-dev-bff-cliente-alb-1673122993.us-east-1.elb.amazonaws.com/api/v1/client/CLI001/historico?dias=30&limite=50"
```

**Parámetros opcionales:**
- `dias`: Número de días hacia atrás (default: 90)
- `limite`: Máximo de registros (default: 100)

---

### 6. Métricas del Servicio
```bash
curl -X GET http://medisupply-dev-bff-cliente-alb-1673122993.us-east-1.elb.amazonaws.com/api/v1/client/metrics
```

**Respuesta esperada:** `200 OK`
```json
{
  "service": "cliente-service",
  "sla": {
    "description": "Todas las consultas deben responder en ≤ 2 segundos",
    "max_response_time_ms": 2000
  },
  "stats": {
    "clientes_activos": 0,
    "clientes_inactivos": 0,
    "consultas_realizadas_hoy": 0,
    "total_clientes": 0
  },
  "timestamp": "2025-10-22T04:05:04.623344",
  "version": "1.0.0"
}
```

---

### 7. Crear Orden (Envío a SQS) ⭐
```bash
curl -X POST http://medisupply-dev-bff-cliente-alb-1673122993.us-east-1.elb.amazonaws.com/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "body": {
      "customer_id": "CLI001",
      "items": [
        {
          "product_id": "PROD-ABC-123",
          "quantity": 5,
          "price": 150.00
        },
        {
          "product_id": "PROD-XYZ-456",
          "quantity": 2,
          "price": 89.99
        }
      ],
      "total": 929.98,
      "notes": "Entrega urgente"
    },
    "group_id": "customer-CLI001"
  }'
```

**Respuesta esperada:** `202 ACCEPTED`
```json
{
  "event_id": "b7ae1faa-a9af-4daf-9896-9319c3d7b652",
  "messageId": "async-b7ae1faa-a9af-4daf-9896-9319c3d7b652",
  "status": "accepted"
}
```

**Campos opcionales:**
- `group_id`: ID del grupo SQS para ordenamiento FIFO
- `dedup_id`: ID para deduplicación (si no se envía, usa `event_id`)

---

## 📚 Documentación Swagger

### Swagger UI
Abrir en navegador:
```
http://medisupply-dev-bff-cliente-alb-1673122993.us-east-1.elb.amazonaws.com/docs
```

### API Spec JSON
```bash
curl -X GET http://medisupply-dev-bff-cliente-alb-1673122993.us-east-1.elb.amazonaws.com/apispec.json
```

---

## 🔍 Testing Avanzado

### Script completo de pruebas
```bash
#!/bin/bash
BFF_URL="http://medisupply-dev-bff-cliente-alb-1673122993.us-east-1.elb.amazonaws.com"

echo "1. Health Check"
curl -s "$BFF_URL/health" | jq

echo -e "\n2. Backend Health"
curl -s "$BFF_URL/api/v1/client/health" | jq

echo -e "\n3. Metrics"
curl -s "$BFF_URL/api/v1/client/metrics" | jq

echo -e "\n4. List Clients"
curl -s "$BFF_URL/api/v1/client/?limite=5" | jq

echo -e "\n5. Create Order"
curl -s -X POST "$BFF_URL/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{"body":{"customer_id":"TEST-001","items":[{"product_id":"P1","quantity":1}]},"group_id":"test"}' | jq
```

---

## 🔧 Variables de Entorno del Servicio

El BFF-Cliente necesita estas variables configuradas:

- `CLIENTE_SERVICE_URL`: URL del microservicio cliente-service
- `SQS_QUEUE_URL`: URL de la cola SQS
- `AWS_REGION`: Región de AWS (us-east-1)
- `MESSAGE_GROUP_ID`: Grupo por defecto para SQS
- `HTTP_TIMEOUT`: Timeout para llamadas HTTP

---

## ✅ Estado Actual

| Componente | Estado | Notas |
|-----------|--------|-------|
| BFF-Cliente | ✅ Corriendo (2/2 tareas) | Desplegado correctamente |
| Cliente-Service Backend | ✅ Conectado | Database conectada |
| SQS Integration | ✅ Funcionando | Mensajes aceptados |
| Health Endpoints | ✅ OK | Todos responden 200 |
| Swagger UI | ✅ Disponible | `/docs` |

---

## 🚨 Notas Importantes

1. **Base de datos vacía**: Actualmente no hay clientes en la base de datos, por lo que las consultas devuelven arrays vacíos
2. **Búsqueda requiere vendedor_id**: El endpoint de búsqueda necesita el parámetro `vendedor_id` obligatorio
3. **Órdenes asíncronas**: Las órdenes se envían a SQS y son procesadas de forma asíncrona
4. **SLA de respuesta**: El servicio tiene un SLA de 2000ms (2 segundos) máximo

---

## 📊 Integración con Otros Servicios

### Cliente-Service (Backend)
- **Endpoint:** Configurado via variable `CLIENTE_SERVICE_URL`
- **Health:** ✅ Conectado y respondiendo
- **Database:** ✅ PostgreSQL conectada

### SQS (Órdenes)
- **Cola:** FIFO Queue configurada
- **Región:** us-east-1
- **Estado:** ✅ Aceptando mensajes

---

## 🎯 Próximos Pasos Sugeridos

1. **Poblar base de datos** con clientes de prueba
2. **Probar flujo completo** de creación de órdenes
3. **Monitorear CloudWatch Logs** para ver procesamiento de órdenes
4. **Configurar alertas** para health checks
5. **Pruebas de carga** con múltiples peticiones concurrentes


