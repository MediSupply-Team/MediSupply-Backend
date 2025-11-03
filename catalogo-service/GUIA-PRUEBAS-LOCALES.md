# 🧪 Guía de Pruebas Locales - Gestión de Inventario

## 📋 Requisitos Previos

- Docker y Docker Compose instalados
- Puerto 8000 disponible
- PostgreSQL corriendo en Docker

---

## 🚀 Paso 1: Iniciar el Servicio

### Opción A: Con Docker Compose (Recomendado)

```bash
# Desde la raíz del proyecto MediSupply-Backend
cd /Users/nicolasibarra/uniandes/miso-uniandes/semestre4/ciclo\ 2/proyecto\ final\ 2/MediSupply-Backend

# Iniciar todos los servicios
docker-compose up -d

# O solo el servicio de catálogo
docker-compose up -d catalogo-service
```

### Opción B: Desarrollo Local

```bash
# Navegar al directorio del servicio
cd catalogo-service

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/catalogo_db"

# Ejecutar migraciones (automático en entrypoint)
python3 -m app.populate_db

# Iniciar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## ✅ Paso 2: Verificar que el Servicio Está Corriendo

### 2.1 Health Check

```bash
curl http://localhost:8000/health
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "service": "catalogo-service",
  "version": "2.0.0",
  "features": ["catalog", "inventory-movements", "alerts"]
}
```

### 2.2 Documentación Interactiva

Abrir en el navegador:
```
http://localhost:8000/docs
```

Deberías ver la documentación Swagger con todos los endpoints, incluyendo los nuevos de `/api/inventory`.

---

## 🧪 Paso 3: Pruebas de Endpoints

### 3.1 Verificar Datos Iniciales

```bash
# Listar productos
curl http://localhost:8000/api/catalog/items

# Ver inventario de un producto específico
curl http://localhost:8000/api/catalog/items/PROD001/inventario
```

### 3.2 Probar Movimiento de Ingreso (COMPRA)

```bash
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
    "fecha_vencimiento": "2025-12-31",
    "usuario_id": "TEST_USER",
    "referencia_documento": "PO-TEST-001",
    "observaciones": "Prueba de ingreso desde curl"
  }'
```

**Respuesta esperada (201):**
```json
{
  "id": 5,
  "producto_id": "PROD001",
  "bodega_id": "BOG_CENTRAL",
  "pais": "CO",
  "lote": "AMX001_2024",
  "tipo_movimiento": "INGRESO",
  "motivo": "COMPRA",
  "cantidad": 100,
  "fecha_vencimiento": "2025-12-31",
  "saldo_anterior": 500,
  "saldo_nuevo": 600,
  "usuario_id": "TEST_USER",
  "referencia_documento": "PO-TEST-001",
  "observaciones": "Prueba de ingreso desde curl",
  "created_at": "2024-10-28T...",
  "estado": "ACTIVO"
}
```

**✅ ¡Éxito!** El saldo se actualizó de 500 a 600.

### 3.3 Probar Movimiento de Salida (VENTA)

```bash
curl -X POST http://localhost:8000/api/inventory/movements \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD001",
    "bodega_id": "BOG_CENTRAL",
    "pais": "CO",
    "lote": "AMX001_2024",
    "tipo_movimiento": "SALIDA",
    "motivo": "VENTA",
    "cantidad": 50,
    "usuario_id": "TEST_USER",
    "referencia_documento": "ORD-TEST-001",
    "observaciones": "Prueba de venta"
  }'
```

**Respuesta esperada (201):**
```json
{
  "id": 6,
  "saldo_anterior": 600,
  "saldo_nuevo": 550,
  ...
}
```

### 3.4 Probar Error de Stock Insuficiente

```bash
curl -X POST http://localhost:8000/api/inventory/movements \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD001",
    "bodega_id": "BOG_CENTRAL",
    "pais": "CO",
    "tipo_movimiento": "SALIDA",
    "motivo": "VENTA",
    "cantidad": 10000,
    "usuario_id": "TEST_USER"
  }'
```

**Respuesta esperada (400):**
```json
{
  "detail": {
    "error": "STOCK_INSUFICIENTE",
    "message": "Stock insuficiente en BOG_CENTRAL",
    "saldo_actual": 550,
    "cantidad_requerida": 10000,
    "faltante": 9450,
    ...
  }
}
```

**✅ ¡Correcto!** El sistema validó correctamente el stock.

### 3.5 Probar Transferencia entre Bodegas

```bash
curl -X POST http://localhost:8000/api/inventory/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD001",
    "lote": "AMX001_2024",
    "cantidad": 100,
    "bodega_origen_id": "BOG_CENTRAL",
    "pais_origen": "CO",
    "bodega_destino_id": "MED_SUR",
    "pais_destino": "CO",
    "usuario_id": "TEST_USER",
    "referencia_documento": "TRANS-TEST-001"
  }'
```

**Respuesta esperada (201):**
```json
{
  "message": "Transferencia registrada exitosamente",
  "movimiento_salida_id": 7,
  "movimiento_ingreso_id": 8,
  "saldo_origen": 450,
  "saldo_destino": 100
}
```

### 3.6 Consultar Kardex

```bash
# Kardex completo de un producto
curl "http://localhost:8000/api/inventory/movements/kardex?producto_id=PROD001&page=1&size=10"

# Kardex de una bodega específica
curl "http://localhost:8000/api/inventory/movements/kardex?bodega_id=BOG_CENTRAL&page=1&size=10"

# Kardex filtrado por tipo
curl "http://localhost:8000/api/inventory/movements/kardex?tipo_movimiento=INGRESO&page=1"

# Kardex por rango de fechas
curl "http://localhost:8000/api/inventory/movements/kardex?fecha_desde=2024-10-01T00:00:00Z&fecha_hasta=2024-10-31T23:59:59Z"
```

### 3.7 Consultar Alertas

```bash
# Todas las alertas
curl "http://localhost:8000/api/inventory/alerts"

# Solo alertas no leídas
curl "http://localhost:8000/api/inventory/alerts?leida=false"

# Solo alertas críticas
curl "http://localhost:8000/api/inventory/alerts?nivel=CRITICAL"
```

### 3.8 Anular un Movimiento

```bash
# Primero obtener el ID del último movimiento
MOVIMIENTO_ID=6  # Reemplazar con un ID real

curl -X PUT "http://localhost:8000/api/inventory/movements/${MOVIMIENTO_ID}/anular" \
  -H "Content-Type: application/json" \
  -d '{
    "motivo_anulacion": "Prueba de anulación: movimiento registrado incorrectamente",
    "usuario_id": "ADMIN_USER"
  }'
```

### 3.9 Reporte de Saldos

```bash
# Reporte completo
curl "http://localhost:8000/api/inventory/reports/saldos?page=1&size=50"

# Solo productos con stock bajo
curl "http://localhost:8000/api/inventory/reports/saldos?estado_stock=BAJO"

# Saldos de una bodega específica
curl "http://localhost:8000/api/inventory/reports/saldos?bodega_id=BOG_CENTRAL"
```

---

## 📊 Paso 4: Verificar en Base de Datos

### 4.1 Conectarse a PostgreSQL

```bash
# Si usas Docker Compose
docker exec -it medisupply-backend-postgres-1 psql -U postgres -d catalogo_db

# O desde tu máquina
psql -h localhost -U your_user -d catalogo_db
```

### 4.2 Consultas SQL Útiles

```sql
-- Ver todos los movimientos
SELECT * FROM movimiento_inventario ORDER BY created_at DESC LIMIT 10;

-- Ver saldo actual de un producto en una bodega
SELECT 
    producto_id, 
    bodega_id, 
    pais, 
    SUM(cantidad) as saldo_total
FROM inventario
WHERE producto_id = 'PROD001' AND bodega_id = 'BOG_CENTRAL'
GROUP BY producto_id, bodega_id, pais;

-- Ver alertas activas
SELECT * FROM alerta_inventario WHERE leida = FALSE ORDER BY created_at DESC;

-- Ver la vista de saldos
SELECT * FROM v_saldos_bodega WHERE bodega_id = 'BOG_CENTRAL' LIMIT 10;

-- Kardex de un producto (últimos 10 movimientos)
SELECT 
    m.id,
    m.tipo_movimiento,
    m.motivo,
    m.cantidad,
    m.saldo_anterior,
    m.saldo_nuevo,
    m.created_at,
    p.nombre as producto_nombre
FROM movimiento_inventario m
JOIN producto p ON m.producto_id = p.id
WHERE m.producto_id = 'PROD001'
ORDER BY m.created_at DESC
LIMIT 10;
```

---

## 🔍 Paso 5: Revisar Logs

### 5.1 Logs del Contenedor Docker

```bash
# Ver logs en tiempo real
docker-compose logs -f catalogo-service

# Ver últimos 100 líneas
docker-compose logs --tail=100 catalogo-service

# Buscar errores
docker-compose logs catalogo-service | grep "ERROR"

# Buscar movimientos registrados
docker-compose logs catalogo-service | grep "Movimiento registrado"
```

### 5.2 Logs que Deberías Ver

```
📦 CATALOGO SERVICE - INICIALIZANDO
✅ DATABASE_URL configurado
🚀 Iniciando población de base de datos...
📄 Ejecutando 001_init.sql (estructura y datos)...
   ✅ 001_init.sql: 45 statements ejecutados, 12 omitidos
📊 Creando tablas de movimientos de inventario...
📄 Ejecutando 002_movimientos.sql (kardex y alertas)...
   ✅ 002_movimientos.sql: 38 statements ejecutados, 0 omitidos

✅ Población completada exitosamente
   📦 Productos: 25
   🏭 Inventario: 24 registros
   📋 Movimientos: 4
   🔔 Alertas: 2

🚀 Iniciando aplicación...
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 🧪 Paso 6: Script de Pruebas Automatizado

Crea un archivo `test_inventory_endpoints.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:8000/api/inventory"
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🧪 Iniciando pruebas de endpoints de inventario..."
echo ""

# Test 1: Registrar ingreso
echo "1️⃣ Test: Registrar ingreso (COMPRA)"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST ${BASE_URL}/movements \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD006",
    "bodega_id": "TEST_BODEGA",
    "pais": "CO",
    "tipo_movimiento": "INGRESO",
    "motivo": "COMPRA",
    "cantidad": 100,
    "usuario_id": "TEST_USER",
    "referencia_documento": "TEST-001"
  }')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 201 ]; then
    echo -e "${GREEN}✅ PASS${NC} - Ingreso registrado (HTTP $HTTP_CODE)"
    MOVIMIENTO_ID=$(echo $BODY | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
    echo "   Movimiento ID: $MOVIMIENTO_ID"
else
    echo -e "${RED}❌ FAIL${NC} - HTTP $HTTP_CODE"
    echo "$BODY"
fi
echo ""

# Test 2: Registrar salida
echo "2️⃣ Test: Registrar salida (VENTA)"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST ${BASE_URL}/movements \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD006",
    "bodega_id": "TEST_BODEGA",
    "pais": "CO",
    "tipo_movimiento": "SALIDA",
    "motivo": "VENTA",
    "cantidad": 20,
    "usuario_id": "TEST_USER"
  }')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" -eq 201 ]; then
    echo -e "${GREEN}✅ PASS${NC} - Salida registrada (HTTP $HTTP_CODE)"
else
    echo -e "${RED}❌ FAIL${NC} - HTTP $HTTP_CODE"
fi
echo ""

# Test 3: Validar stock insuficiente
echo "3️⃣ Test: Validar stock insuficiente"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST ${BASE_URL}/movements \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD006",
    "bodega_id": "TEST_BODEGA",
    "pais": "CO",
    "tipo_movimiento": "SALIDA",
    "motivo": "VENTA",
    "cantidad": 10000,
    "usuario_id": "TEST_USER"
  }')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" -eq 400 ]; then
    echo -e "${GREEN}✅ PASS${NC} - Validación correcta (HTTP $HTTP_CODE)"
else
    echo -e "${RED}❌ FAIL${NC} - HTTP $HTTP_CODE (esperaba 400)"
fi
echo ""

# Test 4: Consultar kardex
echo "4️⃣ Test: Consultar kardex"
RESPONSE=$(curl -s -w "\n%{http_code}" "${BASE_URL}/movements/kardex?producto_id=PROD006&page=1&size=10")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✅ PASS${NC} - Kardex consultado (HTTP $HTTP_CODE)"
else
    echo -e "${RED}❌ FAIL${NC} - HTTP $HTTP_CODE"
fi
echo ""

# Test 5: Consultar alertas
echo "5️⃣ Test: Consultar alertas"
RESPONSE=$(curl -s -w "\n%{http_code}" "${BASE_URL}/alerts?page=1&size=10")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✅ PASS${NC} - Alertas consultadas (HTTP $HTTP_CODE)"
else
    echo -e "${RED}❌ FAIL${NC} - HTTP $HTTP_CODE"
fi
echo ""

# Test 6: Reporte de saldos
echo "6️⃣ Test: Reporte de saldos"
RESPONSE=$(curl -s -w "\n%{http_code}" "${BASE_URL}/reports/saldos?page=1&size=10")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✅ PASS${NC} - Reporte generado (HTTP $HTTP_CODE)"
else
    echo -e "${RED}❌ FAIL${NC} - HTTP $HTTP_CODE"
fi
echo ""

echo "✅ Pruebas completadas"
```

**Ejecutar:**
```bash
chmod +x test_inventory_endpoints.sh
./test_inventory_endpoints.sh
```

---

## ✅ Checklist de Verificación

- [ ] Servicio inicia correctamente
- [ ] Health check responde OK
- [ ] Documentación Swagger visible en /docs
- [ ] Se ejecutan migraciones SQL automáticamente
- [ ] Se crean tablas: `movimiento_inventario`, `alerta_inventario`
- [ ] Se agregan campos a `producto`: `stock_minimo`, `stock_critico`, etc
- [ ] Endpoint POST /movements registra ingresos
- [ ] Endpoint POST /movements registra salidas
- [ ] Validación de stock insuficiente funciona
- [ ] Endpoint POST /transfers crea 2 movimientos vinculados
- [ ] Endpoint GET /kardex retorna historial
- [ ] Endpoint GET /alerts retorna alertas
- [ ] Endpoint PUT /anular marca movimiento como anulado
- [ ] Endpoint GET /reports/saldos genera reporte
- [ ] Alertas se generan automáticamente cuando stock < mínimo
- [ ] Logs muestran información de movimientos

---

## 🐛 Troubleshooting

### Error: "Cannot connect to database"
```bash
# Verificar que PostgreSQL está corriendo
docker ps | grep postgres

# Verificar la variable DATABASE_URL
echo $DATABASE_URL

# Reiniciar contenedor de base de datos
docker-compose restart postgres
```

### Error: "Table does not exist"
```bash
# Re-ejecutar población de datos
docker-compose exec catalogo-service python3 -m app.populate_db

# O recrear todo
docker-compose down -v
docker-compose up -d
```

### Error: "Port 8000 already in use"
```bash
# Ver qué está usando el puerto
lsof -i :8000

# Matar el proceso
kill -9 <PID>
```

### No se ven los nuevos endpoints en /docs
```bash
# Verificar que main.py tiene el router registrado
cat app/main.py | grep inventario

# Reiniciar el servicio
docker-compose restart catalogo-service
```

---

## 📝 Próximos Pasos

1. ✅ Verificar que todos los tests pasan
2. ✅ Revisar logs para detectar warnings
3. ✅ Probar desde Postman o Insomnia
4. ✅ Integrar con el frontend
5. ✅ Desplegar a AWS cuando esté listo

---

**¿Listo para probar?** Ejecuta los comandos y verifica que todo funcione correctamente. 🚀

