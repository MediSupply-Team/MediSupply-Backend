# 🚀 Cheat Sheet - Integración Frontend

## 🎯 ¿Qué Endpoint Usar?

### Vista: "Productos" (Catálogo)

```javascript
// Listar TODOS los productos del sistema
GET /api/v1/catalog/items?q={busqueda}&categoriaId={categoria}

// Ver DÓNDE está un producto (todas las bodegas)
GET /api/v1/catalog/items/{producto_id}/inventario
```

**Ejemplo de respuesta:**
```json
{
  "items": [
    {"bodegaId": "BOG_CENTRAL", "cantidad": 1500},
    {"bodegaId": "MED_SUR", "cantidad": 800}
  ]
}
```

---

### Vista: "Inventario" (Por Bodega) ⭐ NUEVO

```javascript
// Listar QUÉ productos hay en UNA bodega
GET /api/v1/inventory/bodega/{bodega_id}/productos?con_stock=true

// Ejemplo real:
GET /api/v1/inventory/bodega/BOG_CENTRAL/productos
```

**Ejemplo de respuesta:**
```json
{
  "items": [
    {
      "producto_id": "PROD007",
      "producto_nombre": "Amoxicilina 500mg",
      "producto_codigo": "AMX500",
      "cantidad": 1500,
      "precio_unitario": 1250.00,
      "estado_stock": "NORMAL",
      "lote": "LOTE-001",
      "fecha_vencimiento": "2025-12-31"
    }
  ],
  "meta": {
    "total": 45,
    "bodega_id": "BOG_CENTRAL"
  }
}
```

---

## 💰 Registrar VENTA (Salida)

```javascript
POST /api/v1/inventory/movements
Content-Type: application/json

{
  "producto_id": "PROD007",
  "bodega_id": "BOG_CENTRAL",
  "pais": "CO",
  "lote": "LOTE-001",
  "tipo_movimiento": "SALIDA",
  "motivo": "VENTA",
  "cantidad": 50,
  "usuario_id": "VENDEDOR_001",
  "referencia_documento": "VENTA-12345"
}
```

**Respuesta:**
```json
{
  "id": 123,
  "saldo_anterior": 1500,
  "saldo_nuevo": 1450,
  "estado": "ACTIVO"
}
```

**⚠️ El stock se actualiza AUTOMÁTICAMENTE** (no necesitas hacer UPDATE manual).

---

## 📥 Registrar INGRESO (Compra)

```javascript
POST /api/v1/inventory/movements
Content-Type: application/json

{
  "producto_id": "PROD007",
  "bodega_id": "BOG_CENTRAL",
  "pais": "CO",
  "lote": "LOTE-NEW-001",
  "tipo_movimiento": "INGRESO",
  "motivo": "COMPRA",
  "cantidad": 500,
  "fecha_vencimiento": "2026-12-31",
  "usuario_id": "COMPRADOR_001",
  "referencia_documento": "PO-2024-001"
}
```

---

## 📜 Ver Historial (Kardex)

```javascript
GET /api/v1/inventory/movements/kardex?producto_id={id}&size=50

// Con filtros:
GET /api/v1/inventory/movements/kardex?producto_id=PROD007&tipo_movimiento=SALIDA&fecha_desde=2024-01-01
```

---

## 🔧 Código React - Ejemplo Completo

### 1. Listar Productos en Bodega

```jsx
const [productos, setProductos] = useState([]);
const [bodegaId, setBodegaId] = useState('BOG_CENTRAL');

useEffect(() => {
  fetch(`/api/v1/inventory/bodega/${bodegaId}/productos?con_stock=true`)
    .then(res => res.json())
    .then(data => setProductos(data.items))
    .catch(err => console.error(err));
}, [bodegaId]);

return (
  <div>
    <select value={bodegaId} onChange={(e) => setBodegaId(e.target.value)}>
      <option value="BOG_CENTRAL">Bogotá Central</option>
      <option value="MED_SUR">Medellín Sur</option>
    </select>
    
    <table>
      {productos.map(p => (
        <tr key={p.producto_id}>
          <td>{p.producto_nombre}</td>
          <td>{p.cantidad}</td>
          <td>
            <button onClick={() => vender(p)}>Vender</button>
          </td>
        </tr>
      ))}
    </table>
  </div>
);
```

### 2. Registrar Venta

```jsx
const vender = async (producto) => {
  const cantidad = prompt('¿Cuántas unidades?', '1');
  
  if (!cantidad || cantidad <= 0) return;
  
  try {
    const response = await fetch('/api/v1/inventory/movements', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        producto_id: producto.producto_id,
        bodega_id: bodegaId,
        pais: producto.pais,
        lote: producto.lote,
        tipo_movimiento: 'SALIDA',
        motivo: 'VENTA',
        cantidad: parseInt(cantidad),
        usuario_id: 'VENDEDOR_001',
        referencia_documento: `VENTA-${Date.now()}`
      })
    });
    
    const resultado = await response.json();
    
    if (response.ok) {
      alert(`✅ Venta exitosa!\nStock: ${resultado.saldo_anterior} → ${resultado.saldo_nuevo}`);
      // Recargar productos
      cargarProductos();
    } else {
      alert(`❌ Error: ${resultado.message}`);
    }
  } catch (err) {
    alert(`❌ Error: ${err.message}`);
  }
};
```

---

## 📊 Tabla Comparativa

| Vista | Endpoint | Agrupación | Cuándo Usar |
|-------|----------|------------|-------------|
| **Productos** | `/catalog/items/{id}/inventario` | Por PRODUCTO | Ver dónde está un producto |
| **Inventario** | `/inventory/bodega/{id}/productos` | Por BODEGA | Ver qué hay en una bodega |

**Ambos leen de la misma tabla `inventario`**, solo agrupan diferente.

---

## ⚡ Diferencia Clave

### ❌ ANTES (Sin nuevo endpoint)

```
Usuario quiere vender → ¿Qué productos hay aquí?
  → No hay endpoint directo
  → Tenía que:
    1. Listar TODOS los productos (/catalog/items)
    2. Por cada producto, consultar inventario
    3. Filtrar manualmente los que tengan stock en esta bodega
```

### ✅ AHORA (Con nuevo endpoint)

```
Usuario quiere vender → ¿Qué productos hay aquí?
  → GET /inventory/bodega/BOG_CENTRAL/productos ⭐
  → ¡Listo! Lista completa en 1 llamada
```

---

## 🎬 Flujo de Venta Recomendado

```
┌─────────────────────────────────────────────┐
│ 1. Usuario entra a "Inventario"            │
│    Selecciona: Bodega = "BOG_CENTRAL"      │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 2. Sistema carga productos en esa bodega    │
│    GET /inventory/bodega/BOG_CENTRAL/...    │
│    Muestra: 45 productos disponibles        │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 3. Usuario busca "Amoxicilina"             │
│    Encuentra: Stock = 1500 unidades         │
│    Click en "Vender"                        │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 4. Modal: ¿Cuántas unidades?               │
│    Usuario ingresa: 50                      │
│    Confirma venta                           │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 5. POST /inventory/movements                │
│    Backend actualiza: 1500 → 1450           │
│    Retorna: saldo_nuevo = 1450              │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 6. Sistema recarga lista                    │
│    Ahora muestra: Stock = 1450 ✅           │
└─────────────────────────────────────────────┘
```

---

## 🚨 Errores Comunes

### Error: "STOCK_INSUFICIENTE"

```javascript
// Validar ANTES de enviar:
if (cantidad > producto.cantidad) {
  alert('Stock insuficiente');
  return;
}
```

### Error: "Network Error"

```javascript
// Verificar que los servicios estén corriendo:
// 1. catalog-service en puerto 3001
// 2. bff-venta en puerto 8001

// Usar la URL correcta:
const API_URL = 'http://localhost:8001/api/v1';  // ✅ BFF
// NO: http://localhost:3000  ❌
```

### Error: "Producto no encontrado en bodega"

```javascript
// Asegúrate de que el producto tenga inventario en esa bodega
// Consultar primero:
GET /catalog/items/{id}/inventario
// Verificar que aparezca la bodega
```

---

## 📱 Mockup de UI Sugerido

```
┌──────────────────────────────────────────────────────────┐
│  Inventario                                   🔍 Buscar  │
├──────────────────────────────────────────────────────────┤
│  📍 Ubicación: [BOG_CENTRAL ▼]                           │
│                                                           │
│  [●] Con stock    [ ] Stock Bajo    [ ] Stock Crítico   │
├──────────────────────────────────────────────────────────┤
│  Producto            | Código  | Stock | Estado | Acción│
├──────────────────────────────────────────────────────────┤
│  Amoxicilina 500mg   | AMX500  | 1500  | 🟢 NORMAL       │
│  Lote: LOTE-001      |         |       | [Vender] [+]  │
├──────────────────────────────────────────────────────────┤
│  Ibuprofeno 400mg    | IBU400  | 45    | 🟡 BAJO         │
│  Lote: LOTE-002      |         |       | [Vender] [+]  │
├──────────────────────────────────────────────────────────┤
│  Acetaminofén 500mg  | ACE500  | 8     | 🔴 CRITICO      │
│  Lote: LOTE-003      |         |       | [Vender] [+]  │
└──────────────────────────────────────────────────────────┘
```

---

## ✅ Checklist de Implementación

- [ ] Configurar URL base del API
- [ ] Implementar Vista de Inventario (usar nuevo endpoint)
- [ ] Implementar Modal de Venta
- [ ] Implementar Modal de Ingreso
- [ ] Implementar Vista de Kardex
- [ ] Agregar manejo de errores
- [ ] Agregar validaciones (stock, cantidad > 0, etc)
- [ ] Agregar indicadores de estado (loading, success, error)
- [ ] Probar flujo completo de venta

---

## 📞 Endpoints Completos

```bash
# Base URL
BASE_URL = http://localhost:8001/api/v1

# Inventario por bodega (NUEVO)
GET  ${BASE_URL}/inventory/bodega/{bodega_id}/productos

# Movimientos
POST ${BASE_URL}/inventory/movements
GET  ${BASE_URL}/inventory/movements/kardex

# Catálogo
GET  ${BASE_URL}/catalog/items
GET  ${BASE_URL}/catalog/items/{id}
GET  ${BASE_URL}/catalog/items/{id}/inventario

# Alertas
GET  ${BASE_URL}/inventory/alerts
```

---

## 🎉 ¡Empieza Aquí!

1. **Lee:** `GUIA-INTEGRACION-FRONTEND.md` (código completo)
2. **Implementa:** Vista de Inventario con el NUEVO endpoint
3. **Prueba:** Registrar una venta desde tu UI
4. **Verifica:** Stock actualizado automáticamente

**¿Dudas? Revisa:** `ACLARACION-ENDPOINTS-INVENTARIO.md`

