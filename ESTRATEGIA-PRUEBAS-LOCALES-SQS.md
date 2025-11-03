# 🧪 ESTRATEGIA DE PRUEBAS LOCALES - Inventario + SQS

## 🎯 ENFOQUE ESTRATÉGICO

Tenemos **3 opciones** para probar localmente, de más simple a más completa:

| Opción | Complejidad | Tiempo Setup | ¿Prueba SQS? | Recomendado para |
|--------|-------------|--------------|--------------|------------------|
| **1. Sin SQS** | ⭐ Baja | 0 min | ❌ No | Desarrollo rápido |
| **2. LocalStack** | ⭐⭐ Media | 5 min | ✅ Sí | Testing completo |
| **3. AWS Real** | ⭐⭐⭐ Alta | 10 min | ✅ Sí | Pre-producción |

---

## ✅ OPCIÓN 1: PROBAR SIN SQS (RECOMENDADO PARA EMPEZAR)

### 🎯 Objetivo
Validar que **toda la lógica de negocio funciona** correctamente:
- Endpoints responden ✅
- Base de datos se actualiza ✅
- Movimientos se registran ✅
- Alertas se generan ✅
- **SQS está deshabilitado** (no bloquea nada)

### 📋 Ventajas
✅ **Cero configuración** - funciona out of the box
✅ **Más rápido** para desarrollo
✅ **No requiere** AWS credentials
✅ **No requiere** LocalStack
✅ **Valida** toda la lógica crítica

### 🚀 Cómo Hacerlo

#### 1. NO configurar SQS_QUEUE_URL

```bash
# .env o variables de entorno
# NO agregar estas líneas:
# SQS_QUEUE_URL=...
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...
```

#### 2. Iniciar servicios

```bash
# Iniciar base de datos
cd /path/to/MediSupply-Backend
docker-compose up -d catalog-db

# Esperar 5 segundos
sleep 5

# Iniciar catalogo-service
cd catalogo-service
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5433/catalogo"
export API_PREFIX="/api"
# SQS_QUEUE_URL NO DEFINIDO → SQS se deshabilita automáticamente

source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. Verificar logs de inicio

```
INFO:     Application startup complete.
INFO:     🔕 SQS Publisher deshabilitado (SQS_QUEUE_URL no configurado)
                        ↑
                  ESTO ES NORMAL Y ESPERADO
```

**✅ Si ves esto, TODO ESTÁ BIEN.** Los endpoints funcionan normalmente.

#### 4. Probar endpoints

```bash
# Crear movimiento
curl -X POST http://localhost:8000/api/inventory/movements \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD001",
    "bodega_id": "BOG_CENTRAL",
    "pais": "CO",
    "lote": "AMX001_2024",
    "tipo_movimiento": "INGRESO",
    "motivo": "COMPRA",
    "cantidad": 100,
    "usuario_id": "TEST_USER"
  }'

# ✅ Debería responder con 201 Created
# ✅ Stock se actualiza en BD
# 🔕 NO se publica a SQS (y está bien)
```

#### 5. Verificar en logs

```
INFO: 📦 Registrando movimiento: INGRESO - PROD001 - 100 unidades
INFO: ✅ Movimiento registrado: ID=1, Saldo: 0 → 100
INFO: 🔕 SQS deshabilitado, evento no publicado: InventoryMovementCreated
                        ↑
                  ESTO ES ESPERADO
```

### ⚠️ Limitaciones de esta opción

❌ No se envían emails
❌ No se envían SMS
❌ No se actualizan analytics
❌ No se prueba integración con SQS

✅ PERO... **toda la lógica de negocio funciona perfectamente**

---

## 🐳 OPCIÓN 2: PROBAR CON LOCALSTACK (TESTING COMPLETO)

### 🎯 Objetivo
Emular **AWS SQS localmente** para probar el flujo completo sin costos de AWS.

### 📋 Ventajas
✅ Prueba **flujo completo** con SQS
✅ **Sin costos** de AWS
✅ **Sin credenciales** reales
✅ Prueba publicación de eventos
✅ Prueba workers (opcional)

### 🚀 Cómo Hacerlo

#### 1. Instalar LocalStack

```bash
# Opción A: Docker (recomendado)
docker run -d \
  --name localstack \
  -p 4566:4566 \
  -e SERVICES=sqs \
  -e DEBUG=1 \
  localstack/localstack

# Opción B: pip
pip install localstack
localstack start -d
```

#### 2. Crear cola SQS en LocalStack

```bash
# Crear cola FIFO
aws --endpoint-url=http://localhost:4566 sqs create-queue \
  --queue-name catalogo-events.fifo \
  --attributes FifoQueue=true,ContentBasedDeduplication=false

# Obtener URL de la cola
aws --endpoint-url=http://localhost:4566 sqs get-queue-url \
  --queue-name catalogo-events.fifo

# Output:
# {
#   "QueueUrl": "http://localhost:4566/000000000000/catalogo-events.fifo"
# }
```

#### 3. Configurar catalogo-service para LocalStack

```bash
# .env o variables de entorno
export SQS_QUEUE_URL="http://localhost:4566/000000000000/catalogo-events.fifo"
export SQS_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
export AWS_ENDPOINT_URL="http://localhost:4566"  # Importante para LocalStack
```

#### 4. Modificar sqs_publisher.py temporalmente

```python
# En catalogo-service/app/services/sqs_publisher.py
# Línea 54-57, cambiar:

self.client = boto3.client(
    'sqs',
    region_name=self.region_name,
    endpoint_url=os.getenv("AWS_ENDPOINT_URL")  # ← Agregar esta línea
)
```

#### 5. Iniciar catalogo-service

```bash
cd catalogo-service
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5433/catalogo"
export SQS_QUEUE_URL="http://localhost:4566/000000000000/catalogo-events.fifo"
export AWS_ENDPOINT_URL="http://localhost:4566"
export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"

source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 6. Verificar logs de inicio

```
INFO: ✅ SQS Publisher inicializado: http://localhost:4566/000000000000/catalogo-events.fifo
                        ↑
                  AHORA SÍ ESTÁ HABILITADO
```

#### 7. Probar endpoint

```bash
curl -X POST http://localhost:8000/api/inventory/movements \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD001",
    "bodega_id": "BOG_CENTRAL",
    "pais": "CO",
    "tipo_movimiento": "INGRESO",
    "motivo": "COMPRA",
    "cantidad": 100,
    "usuario_id": "TEST_USER"
  }'
```

#### 8. Verificar mensaje en LocalStack

```bash
# Ver mensajes en la cola
aws --endpoint-url=http://localhost:4566 sqs receive-message \
  --queue-url http://localhost:4566/000000000000/catalogo-events.fifo

# Output:
# {
#   "Messages": [
#     {
#       "MessageId": "...",
#       "Body": "{\"event_type\":\"InventoryMovementCreated\", ...}",
#       ...
#     }
#   ]
# }
```

✅ **Si ves el mensaje, ¡SQS funciona correctamente!**

#### 9. (Opcional) Probar worker simple

```python
# test_worker.py

import boto3
import json

sqs = boto3.client(
    'sqs',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

queue_url = 'http://localhost:4566/000000000000/catalogo-events.fifo'

while True:
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=5
    )
    
    messages = response.get('Messages', [])
    
    for message in messages:
        body = json.loads(message['Body'])
        print(f"📨 Evento recibido: {body['event_type']}")
        print(f"   Datos: {json.dumps(body['data'], indent=2)}")
        
        # Eliminar mensaje
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=message['ReceiptHandle']
        )
        print("✅ Mensaje procesado")
```

```bash
# Ejecutar worker
python test_worker.py

# Output:
# 📨 Evento recibido: InventoryMovementCreated
#    Datos: {
#      "movimiento_id": 1,
#      "producto_id": "PROD001",
#      ...
#    }
# ✅ Mensaje procesado
```

---

## 🌐 OPCIÓN 3: PROBAR CON AWS SQS REAL (PRE-PRODUCCIÓN)

### 🎯 Objetivo
Probar con **AWS real** antes de desplegar a producción.

### 📋 Ventajas
✅ **100% real** - igual que producción
✅ Prueba con **infraestructura real**
✅ Valida **permisos IAM**
✅ Prueba **latencia real**

### ⚠️ Consideraciones
⚠️ Requiere credenciales de AWS
⚠️ Puede generar costos mínimos (~$0.01)
⚠️ Requiere cola SQS creada en AWS

### 🚀 Cómo Hacerlo

#### 1. Crear cola en AWS (si no existe)

```bash
# Crear cola FIFO en AWS
aws sqs create-queue \
  --queue-name catalogo-events-dev.fifo \
  --region us-east-1 \
  --attributes FifoQueue=true

# Obtener URL
aws sqs get-queue-url \
  --queue-name catalogo-events-dev.fifo \
  --region us-east-1
```

#### 2. Configurar credenciales

```bash
# Opción A: AWS CLI configurado
aws configure
# Ingresa: Access Key ID, Secret Access Key, Region

# Opción B: Variables de entorno
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-1"
```

#### 3. Configurar catalogo-service

```bash
export SQS_QUEUE_URL="https://sqs.us-east-1.amazonaws.com/123456789012/catalogo-events-dev.fifo"
export SQS_REGION="us-east-1"
# AWS credentials desde ~/.aws/credentials o env vars
```

#### 4. Iniciar y probar

```bash
cd catalogo-service
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Probar endpoint
curl -X POST http://localhost:8000/api/inventory/movements \
  -H "Content-Type: application/json" \
  -d '{...}'
```

#### 5. Verificar en AWS Console

1. Ir a: https://console.aws.amazon.com/sqs/
2. Buscar cola: `catalogo-events-dev.fifo`
3. Ver métricas:
   - Messages Available
   - Messages In Flight
4. Click "Send and receive messages" → "Poll for messages"
5. Ver mensaje publicado ✅

---

## 🎯 COMPARACIÓN DE OPCIONES

### Flujo sin SQS (Opción 1)
```
Frontend → BFF → Catalogo → BD ✅ → Response
                                ↓
                          🔕 SQS OFF (OK)
```

**✅ Perfecto para desarrollo rápido**

### Flujo con LocalStack (Opción 2)
```
Frontend → BFF → Catalogo → BD ✅ → Response
                                ↓
                         LocalStack SQS ✅
                                ↓
                          Test Worker ✅
```

**✅ Perfecto para testing completo**

### Flujo con AWS Real (Opción 3)
```
Frontend → BFF → Catalogo → BD ✅ → Response
                                ↓
                           AWS SQS ✅
                                ↓
                       (Workers en ECS/EC2) ✅
```

**✅ Perfecto para validación final**

---

## 📊 RECOMENDACIÓN ESTRATÉGICA

### Para DESARROLLO DIARIO:
**→ Usa OPCIÓN 1** (Sin SQS)
- Más rápido
- Menos fricción
- Valida lógica de negocio

### Para TESTING DE INTEGRACIÓN:
**→ Usa OPCIÓN 2** (LocalStack)
- Prueba flujo completo
- Sin costos
- Más realista

### Para VALIDACIÓN PRE-DEPLOY:
**→ Usa OPCIÓN 3** (AWS Real)
- 100% real
- Valida todo
- Última verificación antes de producción

---

## 🧪 SCRIPT DE PRUEBAS RÁPIDAS (OPCIÓN 1)

```bash
#!/bin/bash
# test-inventory-local.sh

echo "🧪 PRUEBAS LOCALES DE INVENTARIO (SIN SQS)"
echo "=========================================="

BASE_URL="http://localhost:8000/api/inventory"

echo ""
echo "1️⃣  Crear INGRESO de 100 unidades..."
curl -s -X POST $BASE_URL/movements \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD001",
    "bodega_id": "BOG_CENTRAL",
    "pais": "CO",
    "tipo_movimiento": "INGRESO",
    "motivo": "COMPRA",
    "cantidad": 100,
    "usuario_id": "TEST_USER"
  }' | jq '.id, .saldo_nuevo'

echo ""
echo "2️⃣  Crear SALIDA de 30 unidades..."
curl -s -X POST $BASE_URL/movements \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD001",
    "bodega_id": "BOG_CENTRAL",
    "pais": "CO",
    "tipo_movimiento": "SALIDA",
    "motivo": "VENTA",
    "cantidad": 30,
    "usuario_id": "TEST_USER"
  }' | jq '.id, .saldo_anterior, .saldo_nuevo'

echo ""
echo "3️⃣  Consultar KARDEX..."
curl -s "$BASE_URL/movements/kardex?producto_id=PROD001&bodega_id=BOG_CENTRAL&pais=CO" \
  | jq '.meta.total, .items[0:2]'

echo ""
echo "4️⃣  Consultar ALERTAS..."
curl -s "$BASE_URL/alerts" | jq '.meta.total'

echo ""
echo "5️⃣  Reporte de SALDOS..."
curl -s "$BASE_URL/reports/saldos?pais=CO&size=5" \
  | jq '.items[0:3] | .[] | {producto: .producto_nombre, bodega: .bodega_id, cantidad: .cantidad_total}'

echo ""
echo "✅ PRUEBAS COMPLETADAS"
echo ""
echo "📝 NOTA: SQS está deshabilitado (normal para local)"
```

Hacer ejecutable:
```bash
chmod +x test-inventory-local.sh
./test-inventory-local.sh
```

---

## 🎯 RESUMEN EJECUTIVO

### ✅ Opción 1: Sin SQS
- **Usa para:** Desarrollo día a día
- **Setup:** 0 minutos
- **Comando:** Simplemente NO configurar `SQS_QUEUE_URL`

### ✅ Opción 2: LocalStack
- **Usa para:** Testing completo
- **Setup:** 5 minutos
- **Comando:** `docker run -p 4566:4566 localstack/localstack`

### ✅ Opción 3: AWS Real
- **Usa para:** Validación pre-deploy
- **Setup:** 10 minutos
- **Comando:** Configurar AWS credentials

---

## 🚀 SIGUIENTE PASO RECOMENDADO

**Para empezar AHORA:**
1. Usa **Opción 1** (Sin SQS)
2. Ejecuta el script de pruebas
3. Valida que todo funciona
4. Despliega a AWS (donde SQS sí estará activo)

**Para testing avanzado:**
1. Instala LocalStack
2. Prueba flujo completo
3. Valida workers

---

¿Quieres que prepare el script de pruebas listo para ejecutar? 🚀

