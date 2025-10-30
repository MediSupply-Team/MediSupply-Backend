# 🔍 Aclaración: Diferencia entre Endpoints de Catálogo e Inventario

## ❓ Tu Confusión (¡Es Válida!)

Tienes razón en estar confundido. Hay **DOS formas diferentes** de consultar inventario que parecen hacer lo mismo pero tienen propósitos distintos:

### 1️⃣ **Endpoint ANTIGUO** (en `routes/catalog.py`)
```
GET /api/catalog/items/{producto_id}/inventario
```

### 2️⃣ **Endpoint NUEVO** (en `routes/inventario.py`)
```
GET /api/inventory/bodega/{bodega_id}/productos
```

---

## 📊 **¿Cuál es la Diferencia?**

### Endpoint 1: `/catalog/items/{id}/inventario`

**Pregunta que responde:** _"¿Dónde está este producto específico?"_

**Vista:** **Centrada en el PRODUCTO**

```bash
GET /api/catalog/items/PROD007/inventario
```

**Respuesta:**
```json
{
  "items": [
    {"pais": "CO", "bodegaId": "BOG_CENTRAL", "cantidad": 1500},
    {"pais": "CO", "bodegaId": "MED_SUR", "cantidad": 800},
    {"pais": "MX", "bodegaId": "CDMX_NORTE", "cantidad": 2000}
  ]
}
```

**Usa cuando:**
- ✅ Tienes un producto y quieres saber dónde está
- ✅ Necesitas ver TODO el inventario de UN producto
- ✅ Quieres saber en cuántas bodegas hay stock
- ✅ Planear transferencias de un producto específico

---

### Endpoint 2: `/inventory/bodega/{bodega_id}/productos`

**Pregunta que responde:** _"¿Qué productos hay en esta bodega?"_

**Vista:** **Centrada en la BODEGA**

```bash
GET /api/inventory/bodega/BOG_CENTRAL/productos
```

**Respuesta:**
```json
{
  "items": [
    {
      "producto_id": "PROD001",
      "producto_nombre": "Amoxicilina 500mg",
      "cantidad": 500,
      "estado_stock": "NORMAL"
    },
    {
      "producto_id": "PROD006",
      "producto_nombre": "Ibuprofeno 400mg",
      "cantidad": 1000,
      "estado_stock": "NORMAL"
    },
    {
      "producto_id": "PROD007",
      "producto_nombre": "Acetaminofén 500mg",
      "cantidad": 1500,
      "estado_stock": "NORMAL"
    }
  ]
}
```

**Usa cuando:**
- ✅ Estás en una bodega y quieres ver QUÉ hay disponible
- ✅ Antes de registrar una venta en una ubicación específica
- ✅ Hacer inventario físico de una bodega
- ✅ Ver productos con stock bajo en una ubicación

---

## 🎯 **Caso de Uso Real: Vender un Producto**

### ❌ **Flujo INCORRECTO** (Confuso)

```
1. Buscar producto por ID
2. Ver su inventario general (todas las bodegas)
3. ¿En cuál bodega vender? (no sabemos dónde está el usuario)
4. Registrar salida
```

### ✅ **Flujo CORRECTO** (Con el nuevo endpoint)

```
1. Usuario está en bodega "BOG_CENTRAL"
2. Consultar productos disponibles en BOG_CENTRAL
   → GET /api/inventory/bodega/BOG_CENTRAL/productos
3. Usuario ve lista de productos CON STOCK en esa bodega
4. Selecciona producto
5. Registrar salida en BOG_CENTRAL
   → POST /api/inventory/movements (tipo: SALIDA)
```

---

## 🔄 **¿Cómo se Actualiza el Stock al Vender?**

### La Tabla `inventario` es la ÚNICA FUENTE DE VERDAD

```sql
-- Tabla inventario (ÚNICA fuente de stock)
CREATE TABLE inventario (
  producto_id VARCHAR(64),
  bodega_id VARCHAR(64),
  pais CHAR(2),
  lote VARCHAR(64),
  cantidad INT,  -- ← ESTE ES EL STOCK REAL
  vence DATE
);
```

### Cuando registras una SALIDA:

```bash
POST /api/inventory/movements
{
  "producto_id": "PROD007",
  "bodega_id": "BOG_CENTRAL",
  "tipo_movimiento": "SALIDA",
  "motivo": "VENTA",
  "cantidad": 50
}
```

**Lo que pasa internamente:**

```python
# 1. Obtener stock actual
saldo_anterior = SELECT SUM(cantidad) FROM inventario 
                 WHERE producto_id='PROD007' AND bodega_id='BOG_CENTRAL'
# Resultado: 1500

# 2. Calcular nuevo saldo
saldo_nuevo = saldo_anterior - cantidad  # 1500 - 50 = 1450

# 3. Validar stock suficiente
if saldo_nuevo < 0:
    raise "STOCK_INSUFICIENTE"

# 4. Registrar movimiento (kardex)
INSERT INTO movimiento_inventario (
  producto_id, tipo_movimiento, cantidad,
  saldo_anterior, saldo_nuevo
) VALUES ('PROD007', 'SALIDA', 50, 1500, 1450)

# 5. ACTUALIZAR inventario (ESTO ES CLAVE)
UPDATE inventario 
SET cantidad = 1450  # ← AQUÍ SE ACTUALIZA EL STOCK
WHERE producto_id='PROD007' AND bodega_id='BOG_CENTRAL'
```

---

## 📋 **Resumen de Todos los Endpoints**

### **Endpoints de CATÁLOGO** (Vista de Producto)

| Endpoint | Propósito | Cuándo Usar |
|----------|-----------|-------------|
| `GET /catalog/items` | Listar productos del catálogo | Buscar productos por nombre/código |
| `GET /catalog/items/{id}` | Ver detalles de un producto | Ver info básica (nombre, precio, etc) |
| `GET /catalog/items/{id}/inventario` | Ver dónde está un producto | Saber en qué bodegas hay stock |
| `POST /catalog/items` | Crear producto | Agregar nuevo producto al catálogo |

### **Endpoints de INVENTARIO** (Vista de Bodega/Movimientos)

| Endpoint | Propósito | Cuándo Usar |
|----------|-----------|-------------|
| `GET /inventory/bodega/{id}/productos` | Ver productos en una bodega | **ANTES DE VENDER** - ver qué hay |
| `POST /inventory/movements` | Registrar ingreso/salida | **AL VENDER** - reduce stock |
| `POST /inventory/transfers` | Transferir entre bodegas | Mover stock de bodega A → B |
| `GET /inventory/movements/kardex` | Ver historial de movimientos | Auditoría, trazabilidad |
| `GET /inventory/alerts` | Ver alertas de stock bajo | Notificaciones de reabastecimiento |

---

## 🎬 **Flujo Completo: De Crear Producto a Venderlo**

### Paso 1: **Crear Producto con Inventario Inicial**

```bash
POST /api/catalog/items
{
  "id": "PROD_NEW",
  "nombre": "Nuevo Medicamento",
  "codigo": "NEW001",
  "precioUnitario": 5000,
  "bodegasIniciales": [
    {"bodega_id": "BOG_CENTRAL", "pais": "CO"},
    {"bodega_id": "MED_SUR", "pais": "CO"}
  ]
}
```

**Resultado:**
- ✅ Producto creado en tabla `producto`
- ✅ 2 registros en tabla `inventario` con cantidad = 0

---

### Paso 2: **Registrar Ingreso (Compra al Proveedor)**

```bash
POST /api/inventory/movements
{
  "producto_id": "PROD_NEW",
  "bodega_id": "BOG_CENTRAL",
  "tipo_movimiento": "INGRESO",
  "motivo": "COMPRA",
  "cantidad": 500
}
```

**Resultado:**
- ✅ Stock en `inventario`: 0 → 500
- ✅ Movimiento registrado en `movimiento_inventario` (kardex)

---

### Paso 3: **Consultar Productos Disponibles en Bodega** (NUEVO)

```bash
GET /api/inventory/bodega/BOG_CENTRAL/productos
```

**Respuesta:**
```json
{
  "items": [
    {
      "producto_id": "PROD_NEW",
      "producto_nombre": "Nuevo Medicamento",
      "cantidad": 500,
      "estado_stock": "NORMAL"
    },
    // ... otros productos
  ]
}
```

---

### Paso 4: **Registrar Venta (Salida)**

```bash
POST /api/inventory/movements
{
  "producto_id": "PROD_NEW",
  "bodega_id": "BOG_CENTRAL",
  "tipo_movimiento": "SALIDA",
  "motivo": "VENTA",
  "cantidad": 50
}
```

**Resultado:**
- ✅ Stock en `inventario`: 500 → 450
- ✅ Movimiento registrado en `movimiento_inventario`

---

### Paso 5: **Verificar Stock Actualizado**

```bash
# Opción A: Ver inventario del producto (todas las bodegas)
GET /api/catalog/items/PROD_NEW/inventario

# Opción B: Ver productos en la bodega (todos los productos)
GET /api/inventory/bodega/BOG_CENTRAL/productos
```

Ambos mostrarán `cantidad: 450`

---

## ✅ **Respuestas a tus Preguntas Específicas**

### 1. ¿Es necesario tener inventario inicial?

**Respuesta:** NO es obligatorio, pero SÍ es recomendado.

- **Sin inventario inicial:** El primer INGRESO crea el registro automáticamente
- **Con inventario inicial:** Mayor consistencia, el producto aparece desde el inicio

### 2. ¿Los endpoints son redundantes?

**Respuesta:** NO, son complementarios.

- `/catalog/items/{id}/inventario` → Vista de PRODUCTO (dónde está)
- `/inventory/bodega/{id}/productos` → Vista de BODEGA (qué hay aquí)

### 3. ¿Cómo se actualiza el stock al vender?

**Respuesta:** Automáticamente con `POST /inventory/movements`

El servicio de inventario:
1. Valida stock disponible
2. Actualiza tabla `inventario` (resta cantidad)
3. Registra movimiento en `movimiento_inventario` (trazabilidad)

### 4. ¿Se elimina el producto al vender?

**Respuesta:** NO. Solo se reduce la `cantidad` en la tabla `inventario`.

```sql
-- Antes de vender
SELECT * FROM inventario WHERE producto_id='PROD007';
-- cantidad: 1500

-- Después de vender 50 unidades
SELECT * FROM inventario WHERE producto_id='PROD007';
-- cantidad: 1450  ← Solo se actualizó el número
```

---

## 🎯 **Recomendación Final: ¿Qué Usar en tu UI?**

### En tu Pantalla de "Inventario de Productos":

```javascript
// OPCIÓN 1: Vista por BODEGA (RECOMENDADO para ventas)
async function cargarProductosEnBodega(bodegaId) {
  const response = await fetch(
    `/api/v1/inventory/bodega/${bodegaId}/productos?con_stock=true`
  );
  const data = await response.json();
  
  // Mostrar lista de productos DISPONIBLES en esa bodega
  // Usuario puede vender directamente desde esta lista
}

// OPCIÓN 2: Vista por PRODUCTO (para consultas)
async function verInventarioDeProducto(productoId) {
  const response = await fetch(
    `/api/v1/catalog/items/${productoId}/inventario`
  );
  const data = await response.json();
  
  // Mostrar en qué bodegas está este producto
  // Útil para planear transferencias
}
```

### Para VENDER:

```javascript
async function venderProducto(productoId, bodegaId, cantidad) {
  // 1. Verificar stock (opcional, el backend valida)
  const stock = await fetch(
    `/api/v1/inventory/bodega/${bodegaId}/productos`
  );
  
  // 2. Registrar salida
  const response = await fetch('/api/v1/inventory/movements', {
    method: 'POST',
    body: JSON.stringify({
      producto_id: productoId,
      bodega_id: bodegaId,
      tipo_movimiento: 'SALIDA',
      motivo: 'VENTA',
      cantidad: cantidad,
      usuario_id: currentUser.id
    })
  });
  
  // 3. Stock se actualiza automáticamente
  if (response.ok) {
    alert('Venta registrada. Stock actualizado automáticamente');
  }
}
```

---

## 📞 **Conclusión**

### ✅ **SÍ necesitas los DOS tipos de endpoints:**

1. **`/catalog/items/{id}/inventario`** - Para saber DÓNDE está un producto
2. **`/inventory/bodega/{id}/productos`** - Para saber QUÉ hay en una bodega

### ✅ **El stock SE ACTUALIZA automáticamente:**

Cuando registras un movimiento (INGRESO/SALIDA), el servicio:
- Actualiza la tabla `inventario` (stock real)
- Registra el movimiento en `movimiento_inventario` (trazabilidad)
- Genera alertas si el stock queda bajo

### ✅ **El inventario inicial ES OPCIONAL:**

- Puedes crear producto SIN inventario inicial
- El primer INGRESO lo crea automáticamente
- PERO es mejor crear con inventario inicial para consistencia

---

**¿Te quedó más claro?** Los endpoints NO son redundantes, son **perspectivas diferentes** del mismo dato (inventario).

- **Perspectiva PRODUCTO:** "¿Dónde está mi producto?"
- **Perspectiva BODEGA:** "¿Qué tengo aquí?"

Ambos leen de la misma tabla `inventario`, solo agrupan diferente.

