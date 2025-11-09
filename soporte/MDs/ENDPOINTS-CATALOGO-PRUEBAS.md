# 🧪 Endpoints de Catálogo e Inventario para Pruebas

**ALB URL Base**: `http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com`

---

## ❤️ HEALTH CHECKS

### 1. **Health Check del BFF (General)**
```bash
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/health
```

**Respuesta esperada**:
```json
{
  "status": "ok"
}
```

**cURL**:
```bash
curl http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/health
```

---

### 2. **Health Check de Catálogo e Inventario**

**Catálogo e Inventario están en el mismo servicio** (catalogo-service), por lo que ambos se verifican con endpoints funcionales:

#### **Verificar Catálogo** (Listar productos):
```bash
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items?size=1
```

**Respuesta esperada**: 200 OK con lista de productos

```bash
curl -s "http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items?size=1" | jq '.meta.total'
# Debería mostrar: 26 (total de productos)
```

#### **Verificar Inventario** (Consultar alertas):
```bash
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/inventory/alerts?size=1
```

**Respuesta esperada**: 200 OK con lista de alertas

```bash
curl -s "http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/inventory/alerts?size=1" | jq '.meta'
# Debería mostrar metadata de paginación
```

**Nota**: El health check interno del servicio (`/health`) no es accesible públicamente a través del ALB por diseño de seguridad. El ALB solo rutea `/catalog/*` al servicio.

---

## 📦 CATÁLOGO (Productos)

### 1. **Listar todos los productos** (Paginado)
```bash
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items

# Con paginación
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items?page=1&size=10
```

**Resultado esperado**: 25 productos cargados en la BD

---

### 2. **Buscar productos por texto**
```bash
# Buscar "amoxicilina"
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items?q=amoxicilina

# Buscar "ibuprofeno"
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items?q=ibuprofeno
```

---

### 3. **Filtrar por categoría**
```bash
# Antibióticos
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items?categoriaId=ANTIBIOTICS

# Analgésicos
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items?categoriaId=ANALGESICS

# Cardiovasculares
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items?categoriaId=CARDIOVASCULAR

# Respiratorios
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items?categoriaId=RESPIRATORY

# Gastrointestinales
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items?categoriaId=GASTROINTESTINAL
```

---

### 4. **Filtrar por país y bodega**
```bash
# Productos en Colombia
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items?pais=CO

# Productos en bodega específica de Bogotá
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items?pais=CO&bodegaId=BOG_CENTRAL

# Productos en México
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items?pais=MX&bodegaId=CDMX_NORTE
```

---

### 5. **Buscar por código de producto**
```bash
# Amoxicilina por código
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items?codigo=AMX500

# Ibuprofeno por código
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items?codigo=IBU400
```

---

### 6. **Detalle de un producto específico**
```bash
# Producto PROD001 (Amoxicilina)
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items/PROD001

# Producto PROD006 (Ibuprofeno)
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items/PROD006
```

---

### 7. **Inventario de un producto**
```bash
# Ver inventario de Amoxicilina en todas las bodegas
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items/PROD001/inventario

# Con filtros de país
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items/PROD001/inventario?pais=CO

# Con filtros de país y bodega
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items/PROD001/inventario?pais=CO&bodegaId=BOG_CENTRAL
```

---

## 📊 INVENTARIO (Movimientos y Reportes)

### 1. **Registrar Ingreso (Entrada)**
```bash
POST http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/inventory/movements
Content-Type: application/json

{
  "producto_id": "PROD001",
  "bodega_id": "BOG_CENTRAL",
  "pais": "CO",
  "lote": "TEST001_2024",
  "tipo_movimiento": "ENTRADA",
  "motivo": "COMPRA",
  "cantidad": 100,
  "fecha_vencimiento": "2025-12-31",
  "usuario_id": "USR_TEST_001",
  "referencia_documento": "PO-2024-001",
  "observaciones": "Ingreso de prueba"
}
```

---

### 2. **Registrar Salida**
```bash
POST http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/inventory/movements
Content-Type: application/json

{
  "producto_id": "PROD001",
  "bodega_id": "BOG_CENTRAL",
  "pais": "CO",
  "lote": "AMX001_2024",
  "tipo_movimiento": "SALIDA",
  "motivo": "VENTA",
  "cantidad": 50,
  "fecha_vencimiento": "2025-12-31",
  "usuario_id": "USR_TEST_001",
  "referencia_documento": "SO-2024-001",
  "observaciones": "Salida por venta"
}
```

---

### 3. **Transferencia entre bodegas**
```bash
POST http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/inventory/transfers
Content-Type: application/json

{
  "producto_id": "PROD006",
  "lote": "IBU001_2024",
  "bodega_origen_id": "BOG_CENTRAL",
  "bodega_destino_id": "MED_SUR",
  "pais": "CO",
  "cantidad": 100,
  "fecha_vencimiento": "2026-06-30",
  "usuario_id": "USR_TEST_001",
  "referencia_documento": "TRANS-2024-001",
  "observaciones": "Transferencia de prueba"
}
```

---

### 4. **Consultar Kardex (historial de movimientos)**
```bash
# Kardex de un producto
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/inventory/movements?producto_id=PROD001

# Kardex con filtros de bodega
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/inventory/movements?producto_id=PROD001&bodega_id=BOG_CENTRAL&pais=CO

# Con paginación
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/inventory/movements?producto_id=PROD001&page=1&size=10
```

---

### 5. **Anular un movimiento**
```bash
POST http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/inventory/movements/{movimiento_id}/anular
Content-Type: application/json

{
  "motivo_anulacion": "Error en el registro",
  "usuario_id": "USR_TEST_001"
}
```

---

### 6. **Consultar Alertas de inventario**
```bash
# Todas las alertas
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/inventory/alerts

# Alertas por tipo
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/inventory/alerts?tipo_alerta=STOCK_MINIMO

# Alertas por país
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/inventory/alerts?pais=CO

# Solo alertas no leídas
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/inventory/alerts?leida=false
```

---

### 7. **Reporte de Saldos por Bodega**
```bash
# Saldos de un producto en todas las bodegas
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/inventory/reports/saldos?producto_id=PROD001

# Saldos con filtros
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/inventory/reports/saldos?producto_id=PROD001&pais=CO

# Saldos de bodega específica
GET http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/inventory/reports/saldos?producto_id=PROD001&pais=CO&bodega_id=BOG_CENTRAL
```

---

## 🧪 Comandos cURL para Copiar y Pegar

### Listar productos
```bash
curl -X GET "http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items?page=1&size=10"
```

### Buscar antibióticos
```bash
curl -X GET "http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items?categoriaId=ANTIBIOTICS"
```

### Ver detalle de Amoxicilina
```bash
curl -X GET "http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items/PROD001"
```

### Registrar ingreso de inventario
```bash
curl -X POST "http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/inventory/movements" \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD001",
    "bodega_id": "BOG_CENTRAL",
    "pais": "CO",
    "lote": "TEST001_2024",
    "tipo_movimiento": "ENTRADA",
    "motivo": "COMPRA",
    "cantidad": 100,
    "fecha_vencimiento": "2025-12-31",
    "usuario_id": "USR_TEST_001",
    "referencia_documento": "PO-2024-001",
    "observaciones": "Ingreso de prueba"
  }'
```

### Ver kardex
```bash
curl -X GET "http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/inventory/movements?producto_id=PROD001&page=1&size=10"
```

### Ver alertas
```bash
curl -X GET "http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/inventory/alerts"
```

---

## 📋 Datos de Prueba Disponibles

### Productos (25 en total):
- **PROD001**: Amoxicilina 500mg (ANTIBIOTICS)
- **PROD006**: Ibuprofeno 400mg (ANALGESICS) - Muy popular
- **PROD007**: Acetaminofén 500mg (ANALGESICS) - Muy popular
- **PROD011**: Enalapril 10mg (CARDIOVASCULAR)
- **PROD016**: Salbutamol 100mcg (RESPIRATORY)
- **PROD021**: Omeprazol 20mg (GASTROINTESTINAL)

### Bodegas Disponibles:
- **Colombia**: BOG_CENTRAL, MED_SUR
- **México**: CDMX_NORTE, GDL_OESTE
- **Perú**: LIM_CALLAO
- **Chile**: SCL_CENTRO

### Total Inventario Inicial:
- **48 registros** de inventario distribuidos en diferentes países y bodegas

---

## ✅ Verificación Rápida

```bash
# 1. Verificar que el servicio responde
curl http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/health

# 2. Verificar carga de productos (debería retornar 25)
curl "http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items" | jq '.meta.total'

# 3. Verificar filtros por categoría
curl "http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items?categoriaId=ANTIBIOTICS" | jq '.meta.total'

# 4. Verificar detalle de producto con inventario
curl "http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com/catalog/api/catalog/items/PROD001" | jq '.'
```

---

**Nota**: Todos los endpoints están funcionando correctamente según los logs de AWS ECS. ✅

