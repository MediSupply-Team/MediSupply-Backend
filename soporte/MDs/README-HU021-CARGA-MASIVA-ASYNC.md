# 📤 HU021 - Carga Masiva de Productos (ASÍNCRONO con SQS)

## 🎯 Arquitectura de Alta Disponibilidad

```
┌─────────────┐
│   Usuario   │
│  sube .xlsx │
└──────┬──────┘
       │
       ▼
┌───────────────────────────────────────────┐
│  FastAPI Endpoint (catalog-service)       │
│  1. Valida archivo (.xlsx/.csv)           │
│  2. Sube archivo a S3 (LocalStack)        │
│  3. Crea tarea en Redis (task_id)         │
│  4. Envía mensaje a SQS                   │
│  5. ✅ Retorna INMEDIATO (< 1 segundo)    │
│     { task_id, status_url }               │
└───────────────┬───────────────────────────┘
                │
                ▼
         ┌──────────────┐
         │   AWS SQS    │  ← ✅ Si cae el servicio,
         │   (Cola)     │     mensajes persisten aquí
         └──────┬───────┘
                │ (Long polling 20s)
                ▼
         ┌──────────────┐
         │   Worker     │  ← Procesador asíncrono
         │ (Consumer)   │    - Descarga de S3
         │              │    - Procesa Excel
         │              │    - Guarda en PostgreSQL
         └──────┬───────┘    - Actualiza progreso
                │
                ├──────────────┐
                ▼              ▼
         ┌──────────┐   ┌──────────┐
         │   Redis  │   │PostgreSQL│
         │ (Estado) │   │(Productos)│
         └──────────┘   └──────────┘
                │
                ▼
         ┌──────────────┐
         │   Cliente    │  ← Poll: GET /status/{task_id}
         │ consulta     │     { status, progress, result }
         │   estado     │
         └──────────────┘
```

---

## ✅ Ventajas de esta Arquitectura

| Característica | Beneficio |
|----------------|-----------|
| **Alta Disponibilidad** | Si cae el servicio, los mensajes permanecen en SQS ✅ |
| **No Timeout** | Retorno inmediato al cliente (< 1s) ✅ |
| **Escalabilidad** | Múltiples workers procesando en paralelo ✅ |
| **Reintentos Automáticos** | Si falla, SQS reintenta automáticamente ✅ |
| **Tracking en Tiempo Real** | Cliente consulta progreso en Redis ✅ |
| **Desacoplamiento** | API y Worker son independientes ✅ |

---

## 🚀 Flujo Completo

### 1. Usuario Sube Archivo

```bash
curl -X POST "http://localhost:8001/api/v1/catalog/items/bulk-upload?proveedor_id=PROV001" \
  -F "file=@productos.xlsx"
```

**Respuesta INMEDIATA (< 1 segundo):**
```json
{
  "message": "Archivo recibido y encolado para procesamiento",
  "task_id": "abc123-def456-ghi789",
  "status": "pending",
  "status_url": "/api/catalog/bulk-upload/status/abc123-def456-ghi789",
  "filename": "productos.xlsx",
  "proveedor_id": "PROV001"
}
```

### 2. Cliente Consulta Estado (Polling)

```bash
curl "http://localhost:8001/api/v1/catalog/bulk-upload/status/abc123-def456-ghi789"
```

**Respuesta mientras procesa:**
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "processing",
  "filename": "productos.xlsx",
  "proveedor_id": "PROV001",
  "created_at": "2024-01-20T10:00:00",
  "updated_at": "2024-01-20T10:00:30",
  "progress": {
    "total": 300,
    "processed": 150,
    "successful": 145,
    "failed": 5
  },
  "result": null,
  "error": null
}
```

**Respuesta cuando termina:**
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "completed",
  "filename": "productos.xlsx",
  "completed_at": "2024-01-20T10:02:00",
  "progress": {
    "total": 300,
    "processed": 300,
    "successful": 290,
    "failed": 10
  },
  "result": {
    "mensaje": "Carga masiva completada",
    "resumen": {
      "total": 300,
      "exitosos": 290,
      "rechazados": 10,
      "duplicados": 5,
      "productos_creados": 285,
      "productos_actualizados": 5
    },
    "productos_creados": ["PROD001", "PROD002", ...],
    "errores": [
      {"fila": 25, "error": "Campos obligatorios vacíos: certificado_sanitario"}
    ]
  }
}
```

---

## 📂 Estructura de Archivos

```
/MediSupply-Backend/
├── catalogo-service/
│   ├── app/
│   │   ├── routes/
│   │   │   └── catalog.py          ← Endpoints async (upload + status)
│   │   ├── services/
│   │   │   ├── aws_service.py      ← Cliente S3/SQS
│   │   │   └── task_service.py     ← Gestión de tareas en Redis
│   │   ├── worker/
│   │   │   ├── __init__.py
│   │   │   └── sqs_consumer.py     ← Worker que procesa mensajes
│   │   └── models/
│   │       └── catalogo_model.py   ← Modelo con nuevos campos
│   ├── requirements.txt            ← aioboto3, celery, pandas, openpyxl
│   └── data/
│       ├── plantilla_productos_ejemplo.xlsx
│       └── plantilla_productos_vacia.xlsx
├── bff-venta/
│   └── app/routes/
│       └── catalog.py              ← Proxy endpoints
├── docker-compose.yml              ← LocalStack + Worker
├── init-localstack.sh              ← Script inicialización
└── README-HU021-CARGA-MASIVA-ASYNC.md  ← Este archivo
```

---

## 🛠️ Componentes Implementados

### 1. Servicios

#### `aws_service.py` - Cliente AWS/LocalStack
- ✅ Upload de archivos a S3
- ✅ Envío de mensajes a SQS
- ✅ Recepción de mensajes (worker)
- ✅ Descarga de archivos de S3
- ✅ Eliminación de mensajes procesados
- ✅ Creación automática de recursos (bucket/queue)

#### `task_service.py` - Tracking en Redis
- ✅ Crear tarea con estado `pending`
- ✅ Actualizar estado (`processing`, `completed`, `failed`)
- ✅ Actualizar progreso en tiempo real
- ✅ Consultar estado de tarea
- ✅ TTL de 24 horas

### 2. Endpoints

#### `POST /api/catalog/items/bulk-upload` (Asíncrono)
```
Status Code: 202 ACCEPTED
Response Time: < 1 segundo

Proceso:
1. Validar formato de archivo
2. Subir a S3
3. Crear tarea en Redis
4. Enviar mensaje a SQS
5. Retornar task_id

NO espera a procesar el archivo
```

#### `GET /api/catalog/bulk-upload/status/{task_id}`
```
Status Code: 200 OK
Response Time: < 100ms

Retorna:
- Estado actual (pending/processing/completed/failed)
- Progreso (total/processed/successful/failed)
- Resultado final (si completed)
- Error (si failed)
```

### 3. Worker

#### `sqs_consumer.py` - Procesador Asíncrono
```python
# Ejecuta en loop infinito:
1. Long polling de SQS (20s)
2. Recibe mensaje
3. Descarga archivo de S3
4. Procesa Excel fila por fila
5. Actualiza progreso cada 10 filas
6. Guarda en PostgreSQL
7. Marca tarea como completada
8. Elimina mensaje de SQS
```

**Características:**
- ✅ Procesamiento asíncrono
- ✅ Actualización de progreso en tiempo real
- ✅ Manejo de errores por fila
- ✅ Reintentos automáticos (SQS)
- ✅ Logs detallados

---

## 🐳 Docker Compose

### Servicios Configurados

```yaml
services:
  localstack:
    image: localstack/localstack:latest
    ports:
      - "4566:4566"
    environment:
      - SERVICES=s3,sqs
  
  catalog-service:
    environment:
      AWS_ENDPOINT_URL: http://localstack:4566
      AWS_ACCESS_KEY_ID: test
      AWS_SECRET_ACCESS_KEY: test
      S3_BUCKET_NAME: medisupply-bulk-uploads
      SQS_QUEUE_NAME: medisupply-bulk-upload-queue
  
  catalog-worker:
    command: python -m app.worker.sqs_consumer
    environment:
      # Mismas variables que catalog-service
    depends_on:
      - localstack
      - catalog-db
      - redis
```

---

## 🚀 Despliegue y Pruebas

### 1. Iniciar Servicios

```bash
cd MediSupply-Backend

# Levantar todo (incluyendo LocalStack y Worker)
docker-compose up -d localstack catalog-service catalog-worker bff-venta

# Esperar a que Local Stack esté listo
sleep 10

# Inicializar recursos de LocalStack
chmod +x init-localstack.sh
./init-localstack.sh
```

### 2. Verificar Servicios

```bash
# Verificar LocalStack
docker logs localstack --tail 50

# Verificar Worker
docker logs catalog-worker --tail 50
# Debe decir: "🚀 Worker iniciado - Escuchando mensajes de SQS..."

# Verificar API
curl http://localhost:3001/health
curl http://localhost:8001/api/v1/inventory/health
```

### 3. Probar Carga Masiva

```bash
# Cargar 10 productos de ejemplo
curl -X POST "http://localhost:8001/api/v1/catalog/items/bulk-upload?proveedor_id=PROV001" \
  -F "file=@catalogo-service/data/plantilla_productos_ejemplo.xlsx" \
  | jq '.'

# Guardar task_id de la respuesta
TASK_ID="<task_id de la respuesta>"

# Consultar estado (hacer varias veces)
curl "http://localhost:8001/api/v1/catalog/bulk-upload/status/$TASK_ID" | jq '.'

# Ver logs del worker en tiempo real
docker logs -f catalog-worker
```

### 4. Ejemplo Completo con Script

```bash
#!/bin/bash

# Cargar archivo
echo "📤 Subiendo archivo..."
RESPONSE=$(curl -s -X POST "http://localhost:8001/api/v1/catalog/items/bulk-upload?proveedor_id=PROV001" \
  -F "file=@catalogo-service/data/plantilla_productos_ejemplo.xlsx")

echo "$RESPONSE" | jq '.'

# Extraer task_id
TASK_ID=$(echo "$RESPONSE" | jq -r '.task_id')
echo "Task ID: $TASK_ID"

# Polling cada 2 segundos
echo ""
echo "📊 Consultando estado..."
while true; do
  STATUS=$(curl -s "http://localhost:8001/api/v1/catalog/bulk-upload/status/$TASK_ID")
  CURRENT_STATUS=$(echo "$STATUS" | jq -r '.status')
  
  echo "$STATUS" | jq '{status, progress}'
  
  if [[ "$CURRENT_STATUS" == "completed" ]] || [[ "$CURRENT_STATUS" == "failed" ]]; then
    echo ""
    echo "✅ Procesamiento finalizado"
    echo "$STATUS" | jq '.'
    break
  fi
  
  sleep 2
done
```

---

## 📊 Comparación: Antes vs Ahora

| Aspecto | Antes (Sincrónico) | Ahora (Asíncrono con SQS) |
|---------|-------------------|---------------------------|
| **Tiempo de respuesta** | 30s - 5 min | < 1 segundo ✅ |
| **Timeout** | Sí (después de 60s) | No ✅ |
| **Si cae el servicio** | Se pierde el proceso ❌ | Mensaje persiste en SQS ✅ |
| **Tracking** | No | Sí (Redis) ✅ |
| **Escalabilidad** | 1 request = 1 proceso | N workers paralelos ✅ |
| **Reintentos** | No | Automático (SQS) ✅ |
| **Progreso en tiempo real** | No | Sí ✅ |

---

## 🔧 Configuración AWS Real (Producción)

Para usar AWS real en lugar de LocalStack:

```yaml
# docker-compose.yml (producción)
catalog-service:
  environment:
    # ❌ Quitar AWS_ENDPOINT_URL (usa AWS real)
    # AWS_ENDPOINT_URL: http://localstack:4566
    
    AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
    AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
    AWS_DEFAULT_REGION: us-east-1
    S3_BUCKET_NAME: medisupply-bulk-uploads-prod
    SQS_QUEUE_NAME: medisupply-bulk-upload-queue-prod
```

**Crear recursos en AWS:**
```bash
# S3 Bucket
aws s3 mb s3://medisupply-bulk-uploads-prod

# SQS Queue
aws sqs create-queue \
  --queue-name medisupply-bulk-upload-queue-prod \
  --attributes VisibilityTimeout=300,MessageRetentionPeriod=86400
```

---

## 📚 Documentación Adicional

- `GUIA-CARGA-MASIVA-PRODUCTOS.md` - Guía de uso (actualizada para async)
- `GUIA-INTEGRACION-FRONTEND.md` - Ejemplos de código React/JS
- `ENDPOINT-PRODUCTOS-BODEGA.md` - Nuevo endpoint de productos en bodega
- `ACLARACION-ENDPOINTS-INVENTARIO.md` - Diferencia entre endpoints

---

## ✅ Checklist Final

### Backend
- [x] Modelo actualizado (certificado_sanitario, tiempo_entrega_dias, proveedor_id)
- [x] Servicio AWS (S3 + SQS)
- [x] Servicio de Tareas (Redis tracking)
- [x] Endpoint asíncrono (upload + status)
- [x] Worker SQS consumer
- [x] LocalStack configurado
- [x] Docker compose actualizado
- [x] Script de inicialización

### Testing
- [ ] Pruebas con LocalStack (siguiente paso)
- [ ] Pruebas de carga (300+ productos)
- [ ] Pruebas de resiliencia (reiniciar servicios)

### Frontend
- [ ] Componente de carga masiva
- [ ] Polling de estado
- [ ] Barra de progreso
- [ ] Descarga de plantillas

---

## 🎯 Próximos Pasos

1. ✅ **Levantar servicios** con LocalStack
2. ✅ **Inicializar recursos** (bucket y cola)
3. 🔄 **Probar carga masiva** con archivo de ejemplo
4. 📊 **Verificar progreso** en tiempo real
5. ✅ **Revisar logs** del worker
6. 🎨 **Integrar en frontend**

---

## 🐛 Troubleshooting

### Worker no procesa mensajes

```bash
# Ver logs del worker
docker logs catalog-worker

# Verificar que LocalStack esté corriendo
docker ps | grep localstack

# Verificar cola SQS
aws --endpoint-url=http://localhost:4566 sqs list-queues

# Ver mensajes en la cola
aws --endpoint-url=http://localhost:4566 sqs receive-message \
  --queue-url http://localhost:4566/000000000000/medisupply-bulk-upload-queue
```

### Tarea se queda en "pending"

- ✅ Verificar que el worker esté corriendo
- ✅ Verificar logs del worker
- ✅ Verificar que LocalStack esté accesible
- ✅ Verificar que el mensaje llegó a SQS

### Error de conexión a S3/SQS

- ✅ Verificar `AWS_ENDPOINT_URL=http://localstack:4566`
- ✅ Verificar que LocalStack esté en la misma red Docker
- ✅ Ejecutar `init-localstack.sh` para crear recursos

---

## 🎉 ¡Listo!

Ahora tienes un sistema de carga masiva:
- ✅ **Asíncrono** - No bloquea el cliente
- ✅ **Alta Disponibilidad** - Mensajes persisten en SQS
- ✅ **Escalable** - Múltiples workers
- ✅ **Observable** - Tracking en tiempo real
- ✅ **Resiliente** - Reintentos automáticos

**¿Listo para probar?** 🚀
```bash
docker-compose up -d
./init-localstack.sh
# ¡A cargar productos!
```

