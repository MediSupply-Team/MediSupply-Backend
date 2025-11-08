# 📮 Cómo probar la Carga Masiva en Postman

## 📄 Archivo de ejemplo

**Ubicación**: `catalogo-service/data/ejemplo_carga_masiva_postman.xlsx`

**Contiene**: 3 productos de ejemplo listos para cargar

---

## 🚀 Paso a paso en Postman

### 1️⃣ **Crear nueva petición POST**

```
POST http://medisupply-dev-bff-venta-alb-114282636.us-east-1.elb.amazonaws.com/api/v1/catalog/items/bulk-upload
```

### 2️⃣ **Configurar Query Parameters (Params tab)**

| Key | Value | Descripción |
|-----|-------|-------------|
| `proveedor_id` | `PROV001` | ID del proveedor (usa el que quieras) |
| `reemplazar_duplicados` | `false` | `true` para actualizar, `false` para rechazar duplicados |

### 3️⃣ **Configurar Body (Body tab)**

1. Selecciona: **form-data**
2. Agrega una nueva fila:
   - **Key**: `file`
   - **Tipo**: Cambia de `Text` a `File` (click en el dropdown)
   - **Value**: Click en "Select Files" y selecciona `ejemplo_carga_masiva_postman.xlsx`

### 4️⃣ **Configurar Headers (opcional)**

```
Accept: application/json
```

### 5️⃣ **Enviar la petición**

Click en **Send**

---

## ✅ Respuesta esperada

```json
{
  "task_id": "88ae822d-d1be-4db5-8c81-9b331e85f0e0",
  "status": "pending",
  "message": "Archivo recibido y encolado para procesamiento",
  "filename": "ejemplo_carga_masiva_postman.xlsx",
  "proveedor_id": "PROV001",
  "status_url": "/api/catalog/bulk-upload/status/88ae822d-d1be-4db5-8c81-9b331e85f0e0"
}
```

---

## 📊 Consultar el estado de la carga

### **Petición GET**

```
GET http://medisupply-dev-bff-venta-alb-114282636.us-east-1.elb.amazonaws.com/api/v1/catalog/bulk-upload/status/{task_id}
```

Reemplaza `{task_id}` con el ID que recibiste en la respuesta anterior.

### **Respuesta cuando está procesando:**

```json
{
  "task_id": "88ae822d-d1be-4db5-8c81-9b331e85f0e0",
  "status": "processing",
  "progress": {
    "total": 3,
    "processed": 1,
    "successful": 1,
    "failed": 0
  },
  "filename": "ejemplo_carga_masiva_postman.xlsx",
  "proveedor_id": "PROV001"
}
```

### **Respuesta cuando completó:**

```json
{
  "task_id": "88ae822d-d1be-4db5-8c81-9b331e85f0e0",
  "status": "completed",
  "progress": {
    "total": 3,
    "processed": 3,
    "successful": 3,
    "failed": 0
  },
  "result": {
    "exitosos": 3,
    "rechazados": 0,
    "duplicados": 0,
    "productos_creados": [
      "PROD_POSTMAN_001",
      "PROD_POSTMAN_002",
      "PROD_POSTMAN_003"
    ],
    "productos_actualizados": [],
    "errores": []
  },
  "filename": "ejemplo_carga_masiva_postman.xlsx",
  "proveedor_id": "PROV001"
}
```

---

## 🔍 Verificar los productos creados

### **Listar todos los productos**

```
GET http://medisupply-dev-bff-venta-alb-114282636.us-east-1.elb.amazonaws.com/catalog/api/catalog/items
```

### **Buscar productos específicos**

```
GET http://medisupply-dev-bff-venta-alb-114282636.us-east-1.elb.amazonaws.com/catalog/api/catalog/items?codigo_contains=POSTMAN
```

### **Ver un producto específico**

```
GET http://medisupply-dev-bff-venta-alb-114282636.us-east-1.elb.amazonaws.com/catalog/api/catalog/items/PROD_POSTMAN_001
```

---

## 📝 Estructura del archivo Excel

El archivo debe tener estas columnas (en este orden):

| Columna | Tipo | Requerido | Ejemplo |
|---------|------|-----------|---------|
| `id` | String | ✅ | PROD_POSTMAN_001 |
| `nombre` | String | ✅ | Amoxicilina 500mg |
| `codigo` | String | ✅ | AMX500-POSTMAN |
| `categoria` | String | ✅ | ANTIBIOTICS |
| `presentacion` | String | ❌ | Cápsula |
| `precio_unitario` | Decimal | ✅ | 1250.00 |
| `certificado_sanitario` | String | ✅ | CERT-INVIMA-2024-001 |
| `condiciones_almacenamiento` | String | ✅ | Temperatura ambiente |
| `tiempo_entrega_dias` | Integer | ✅ | 5 |
| `stock_minimo` | Integer | ❌ | 100 |
| `stock_critico` | Integer | ❌ | 30 |
| `requiere_lote` | String | ❌ | true |
| `requiere_vencimiento` | String | ❌ | true |

---

## ⚠️ Categorías válidas

- `ANTIBIOTICS`
- `ANALGESICS`
- `ANTIINFLAMATORIOS`
- `CARDIOVASCULARES`
- `DIABETES`
- `GASTROINTESTINAL`
- `ANTIHISTAMINICOS`
- `VITAMINAS`

---

## 🎯 Consejos

1. **IDs únicos**: Cada producto debe tener un `id` único
2. **Códigos únicos**: El `codigo` también debe ser único
3. **Duplicados**: Si `reemplazar_duplicados=false`, los productos con ID o código duplicado serán rechazados
4. **Formato CSV**: También puedes usar archivos `.csv` con la misma estructura
5. **Tiempo de procesamiento**: Generalmente <5 segundos para archivos pequeños

---

## ❓ Troubleshooting

### Error: "Formato de archivo no soportado"
- ✅ Usa archivos `.xlsx` o `.csv`
- ❌ No uses `.xls` (Excel antiguo)

### Error: "Producto duplicado"
- El `id` o `codigo` ya existe
- Usa `reemplazar_duplicados=true` para actualizar

### Status: "failed"
- Consulta el `task_id` para ver los errores
- Verifica que todas las columnas requeridas estén presentes
- Revisa que los tipos de datos sean correctos

---

## 📞 Endpoints relacionados

### BFF-Venta (público)
- **Carga masiva**: `POST /api/v1/catalog/items/bulk-upload`
- **Estado**: `GET /api/v1/catalog/bulk-upload/status/{task_id}`

### Catalogo API (interno - via ALB)
- **Listar productos**: `GET /catalog/api/catalog/items`
- **Producto específico**: `GET /catalog/api/catalog/items/{id}`
- **Inventarios**: `GET /catalog/api/inventory`

---

**🎉 ¡Listo para probar!**

