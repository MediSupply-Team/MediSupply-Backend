# 📋 BFF-Venta API Endpoints

**Base URL:** `http://medisupply-dev-bff-venta-alb-1773752444.us-east-1.elb.amazonaws.com`

---

## 🏥 Health Check

### ✅ Get Health Status
**Endpoint:** `GET /health`

**Full URL:**
```
GET http://medisupply-dev-bff-venta-alb-1773752444.us-east-1.elb.amazonaws.com/health
```

**Response:**
```json
{
  "status": "ok"
}
```

**curl Example:**
```bash
curl -s http://medisupply-dev-bff-venta-alb-1773752444.us-east-1.elb.amazonaws.com/health
```

---

## 📦 Catalog Management

### 📋 List All Items
**Endpoint:** `GET /api/v1/catalog/items`

**Full URL:**
```
GET http://medisupply-dev-bff-venta-alb-1773752444.us-east-1.elb.amazonaws.com/api/v1/catalog/items
```

**Query Parameters:**
- `q` (string, optional) - Search text
- `categoria_id` (string, optional) - Filter by category ID  
- `codigo` (string, optional) - Filter by product code
- `pais` (string, optional) - Filter by country
- `bodega_id` (string, optional) - Filter by warehouse ID
- `page` (int, optional) - Page number (default: 1)
- `size` (int, optional) - Page size (default: 20, max: 50)
- `sort` (string, optional) - Sort criteria

**Response:**
```json
{
  "items": [
    {
      "id": "PROD001",
      "nombre": "Amoxicilina 500mg",
      "codigo": "AMX500",
      "categoria": "ANTIBIOTICS",
      "presentacion": "Cápsula",
      "precioUnitario": 1250.0,
      "requisitosAlmacenamiento": "Temperatura ambiente, lugar seco",
      "inventarioResumen": {
        "cantidadTotal": 1000,
        "paises": ["CO", "MX", "PE"]
      }
    }
  ],
  "meta": {
    "page": 1,
    "size": 20,
    "total": 25,
    "tookMs": 45
  }
}
```

**curl Examples:**
```bash
# Get all items
curl -s http://medisupply-dev-bff-venta-alb-1773752444.us-east-1.elb.amazonaws.com/api/v1/catalog/items | jq '.'

# Search with filters
curl -s "http://medisupply-dev-bff-venta-alb-1773752444.us-east-1.elb.amazonaws.com/api/v1/catalog/items?q=Ibuprofeno&page=1&size=10" | jq '.'
```

---

### 🔍 Get Specific Item
**Endpoint:** `GET /api/v1/catalog/items/{item_id}`

**Full URL:**
```
GET http://medisupply-dev-bff-venta-alb-1773752444.us-east-1.elb.amazonaws.com/api/v1/catalog/items/{item_id}
```

**Path Parameters:**
- `item_id` (string, required) - Product ID

**Response:**
```json
{
  "id": "PROD001",
  "nombre": "Producto PROD001",
  "codigo": "CODPROD001",
  "categoria": "MOCK_CATEGORY",
  "presentacion": "Tableta",
  "precioUnitario": 999.99,
  "requisitosAlmacenamiento": "Mock storage requirements"
}
```

**curl Example:**
```bash
curl -s http://medisupply-dev-bff-venta-alb-1773752444.us-east-1.elb.amazonaws.com/api/v1/catalog/items/PROD001 | jq '.'
```

---

### 📦 Get Item Inventory
**Endpoint:** `GET /api/v1/catalog/items/{item_id}/inventario`

**Full URL:**
```
GET http://medisupply-dev-bff-venta-alb-1773752444.us-east-1.elb.amazonaws.com/api/v1/catalog/items/{item_id}/inventario
```

**Path Parameters:**
- `item_id` (string, required) - Product ID

**Query Parameters:**
- `page` (int, optional) - Page number (default: 1)
- `size` (int, optional) - Page size (default: 50)

**Response:**
```json
{
  "items": [
    {
      "pais": "CO",
      "bodegaId": "BOG_CENTRAL",
      "lote": "PROD001_001_2024",
      "cantidad": 500,
      "vence": "2025-12-31",
      "condiciones": "Almacén principal"
    }
  ],
  "meta": {
    "page": 1,
    "size": 50,
    "total": 2,
    "tookMs": 23
  }
}
```

**curl Example:**
```bash
curl -s http://medisupply-dev-bff-venta-alb-1773752444.us-east-1.elb.amazonaws.com/api/v1/catalog/items/PROD001/inventario | jq '.'
```

---

### ➕ Create New Item
**Endpoint:** `POST /api/v1/catalog/items`

**Full URL:**
```
POST http://medisupply-dev-bff-venta-alb-1773752444.us-east-1.elb.amazonaws.com/api/v1/catalog/items
```

**Headers:**
- `Content-Type: application/json`

**Request Body:**
```json
{
  "nombre": "Aspirina 500mg",
  "codigo": "ASP500",
  "categoria": "ANALGESICS",
  "presentacion": "Tableta",
  "precioUnitario": 150.0,
  "requisitosAlmacenamiento": "Lugar seco y fresco"
}
```

**Response:**
```json
{
  "id": "PROD_NEW",
  "message": "Item created successfully (MOCK)",
  "data": {
    "nombre": "Aspirina 500mg",
    "codigo": "ASP500",
    "categoria": "ANALGESICS",
    "presentacion": "Tableta",
    "precioUnitario": 150.0
  }
}
```

**curl Example:**
```bash
curl -X POST http://medisupply-dev-bff-venta-alb-1773752444.us-east-1.elb.amazonaws.com/api/v1/catalog/items \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Paracetamol 500mg",
    "codigo": "PAR500",
    "categoria": "ANALGESICS", 
    "presentacion": "Tableta",
    "precioUnitario": 120.0
  }' | jq '.'
```

---

### ✏️ Update Existing Item
**Endpoint:** `PUT /api/v1/catalog/items/{item_id}`

**Full URL:**
```
PUT http://medisupply-dev-bff-venta-alb-1773752444.us-east-1.elb.amazonaws.com/api/v1/catalog/items/{item_id}
```

**Path Parameters:**
- `item_id` (string, required) - Product ID

**Headers:**
- `Content-Type: application/json`

**Request Body:**
```json
{
  "nombre": "Aspirina 500mg Actualizada",
  "precioUnitario": 175.0
}
```

**curl Example:**
```bash
curl -X PUT http://medisupply-dev-bff-venta-alb-1773752444.us-east-1.elb.amazonaws.com/api/v1/catalog/items/PROD001 \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Producto Actualizado",
    "precioUnitario": 200.0
  }' | jq '.'
```

---

### 🗑️ Delete Item
**Endpoint:** `DELETE /api/v1/catalog/items/{item_id}`

**Full URL:**
```
DELETE http://medisupply-dev-bff-venta-alb-1773752444.us-east-1.elb.amazonaws.com/api/v1/catalog/items/{item_id}
```

**Path Parameters:**
- `item_id` (string, required) - Product ID

**curl Example:**
```bash
curl -X DELETE http://medisupply-dev-bff-venta-alb-1773752444.us-east-1.elb.amazonaws.com/api/v1/catalog/items/PROD001
```

---

## 📝 Orders Management

### 📝 Create New Order
**Endpoint:** `POST /api/v1/orders`

**Full URL:**
```
POST http://medisupply-dev-bff-venta-alb-1773752444.us-east-1.elb.amazonaws.com/api/v1/orders
```

**Headers:**
- `Content-Type: application/json`

**Request Body:**
```json
{
  "body": {
    "customer_id": "123",
    "items": [
      {
        "product_id": "PROD001",
        "quantity": 5
      },
      {
        "product_id": "PROD006", 
        "quantity": 2
      }
    ],
    "total": 6890.00
  },
  "group_id": "orders-group-1",
  "dedup_id": "order-unique-123"
}
```

**Request Body (Minimal):**
```json
{
  "body": {
    "customer_id": "123",
    "items": [
      {
        "product_id": "PROD001",
        "quantity": 5
      }
    ],
    "total": 6250.00
  }
}
```

**Response:**
```json
{
  "messageId": "async-908a8b9d-9763-44a5-9dc1-8983c6aef5dd",
  "event_id": "908a8b9d-9763-44a5-9dc1-8983c6aef5dd",
  "status": "accepted"
}
```

**curl Examples:**
```bash
# Simple order
curl -X POST http://medisupply-dev-bff-venta-alb-1773752444.us-east-1.elb.amazonaws.com/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "body": {
      "customer_id": "456",
      "items": [
        {
          "product_id": "PROD001",
          "quantity": 3
        }
      ],
      "total": 3750.00
    }
  }' | jq '.'

# Order with custom IDs
curl -X POST http://medisupply-dev-bff-venta-alb-1773752444.us-east-1.elb.amazonaws.com/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "body": {
      "customer_id": "789",
      "items": [
        {
          "product_id": "PROD001",
          "quantity": 2
        },
        {
          "product_id": "PROD006",
          "quantity": 1
        }
      ],
      "total": 2820.00
    },
    "group_id": "priority-orders",
    "dedup_id": "order-789-001"
  }' | jq '.'
```

---

## 📊 Response Codes

| Code | Status | Description |
|------|--------|-------------|
| `200` | OK | Successful operation |
| `201` | Created | Resource created successfully |
| `202` | Accepted | Order accepted for processing |
| `400` | Bad Request | Invalid parameters |
| `404` | Not Found | Resource not found |
| `500` | Internal Server Error | Server error |

---

## 📝 Notes

### 🎯 System Status
- ✅ **All endpoints are functional** and return valid responses
- 🔄 **Mock mode active** for catalog-service (simulated but consistent responses)
- ⚡ **Asynchronous processing** for orders (sent to SQS)
- 📋 **Full CRUD operations** available for catalog management
- 📄 **Pagination implemented** with `page` and `size` parameters

### 🔧 Configuration
- **Environment:** Development
- **Region:** us-east-1
- **Cluster:** medisupply-dev-cluster
- **Load Balancer:** medisupply-dev-bff-venta-alb-1773752444.us-east-1.elb.amazonaws.com

### 🚀 Quick Test Commands

```bash
# Health check
curl -s http://medisupply-dev-bff-venta-alb-1773752444.us-east-1.elb.amazonaws.com/health

# List products
curl -s http://medisupply-dev-bff-venta-alb-1773752444.us-east-1.elb.amazonaws.com/api/v1/catalog/items | jq '.items[0]'

# Create order
curl -X POST http://medisupply-dev-bff-venta-alb-1773752444.us-east-1.elb.amazonaws.com/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{"body":{"customer_id":"test","items":[{"product_id":"PROD001","quantity":1}],"total":1250.00}}' | jq '.'
```

---

**Last Updated:** October 19, 2025  
**Version:** 1.0  
**Environment:** Development