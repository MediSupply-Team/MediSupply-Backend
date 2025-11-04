# 📦 Guía: Creación de Productos con Inventario Inicial

## 🎯 Objetivo

Esta guía explica cómo crear productos en el catálogo con registros de inventario inicial en 0, facilitando la consistencia entre catálogo e inventario.

## 🔄 Flujo Anterior vs. Nuevo

### ❌ Flujo Anterior (Sin inventario inicial)

```
1. POST /catalog/items
   → Crea producto en tabla `producto`
   → NO crea nada en tabla `inventario`
   
2. GET /catalog/items/{id}/inventario
   → Respuesta: [] (vacío)
   
3. POST /inventory/movements (INGRESO)
   → Valida producto existe
   → Crea registro en `inventario` con cantidad > 0
   → Stock disponible ✅
```

### ✅ Flujo Nuevo (Con inventario inicial)

```
1. POST /catalog/items (con bodegasIniciales)
   → Crea producto en tabla `producto`
   → Crea registros en `inventario` con cantidad = 0
   
2. GET /catalog/items/{id}/inventario
   → Respuesta: [{"bodega": "BOG_CENTRAL", "cantidad": 0}, ...]
   
3. POST /inventory/movements (INGRESO)
   → Valida producto existe
   → Actualiza registro existente: 0 → cantidad
   → Stock disponible ✅
```

## 📝 Ejemplos de Uso

### Ejemplo 1: Crear Producto SIN Inventario Inicial (Comportamiento Original)

```bash
curl -X POST "http://localhost:8002/catalog/items" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "PROD027",
    "nombre": "Losartán 50mg",
    "codigo": "LST50",
    "categoria": "CARDIOVASCULAR",
    "presentacion": "Tableta",
    "precioUnitario": 680.00,
    "requisitosAlmacenamiento": "Lugar seco",
    "stockMinimo": 30,
    "stockCritico": 10
  }'
```

**Resultado:**
- ✅ Se crea el producto
- ❌ NO se crea inventario
- El inventario se creará en el primer INGRESO

---

### Ejemplo 2: Crear Producto CON Inventario Inicial en UNA Bodega

```bash
curl -X POST "http://localhost:8002/catalog/items" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "PROD028",
    "nombre": "Metformina 850mg",
    "codigo": "MET850",
    "categoria": "CARDIOVASCULAR",
    "presentacion": "Tableta",
    "precioUnitario": 320.00,
    "requisitosAlmacenamiento": "Temperatura ambiente",
    "stockMinimo": 100,
    "stockCritico": 30,
    "requiereLote": true,
    "requiereVencimiento": true,
    "bodegasIniciales": [
      {
        "bodega_id": "BOG_CENTRAL",
        "pais": "CO",
        "lote": "MET-INICIAL-001",
        "fecha_vencimiento": "2099-12-31"
      }
    ]
  }'
```

**Resultado:**
- ✅ Se crea el producto
- ✅ Se crea inventario en BOG_CENTRAL (CO) con cantidad = 0
- Respuesta incluye: `"bodegasIniciales": ["BOG_CENTRAL (CO)"]`

---

### Ejemplo 3: Crear Producto CON Inventario Inicial en MÚLTIPLES Bodegas

```bash
curl -X POST "http://localhost:8002/catalog/items" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "PROD029",
    "nombre": "Insulina Glargina 100UI/ml",
    "codigo": "INS100",
    "categoria": "ENDOCRINOLOGY",
    "presentacion": "Cartucho 3ml",
    "precioUnitario": 45000.00,
    "requisitosAlmacenamiento": "Refrigerar entre 2-8°C",
    "stockMinimo": 20,
    "stockCritico": 5,
    "requiereLote": true,
    "requiereVencimiento": true,
    "bodegasIniciales": [
      {
        "bodega_id": "BOG_CENTRAL",
        "pais": "CO"
      },
      {
        "bodega_id": "MED_SUR",
        "pais": "CO"
      },
      {
        "bodega_id": "CDMX_NORTE",
        "pais": "MX"
      }
    ]
  }'
```

**Resultado:**
- ✅ Se crea el producto
- ✅ Se crean 3 registros de inventario con cantidad = 0:
  - BOG_CENTRAL (CO)
  - MED_SUR (CO)
  - CDMX_NORTE (MX)
- Lote generado automáticamente: `INICIAL-20250129`
- Fecha de vencimiento por defecto: `2099-12-31`

---

## 🔍 Verificación del Inventario

### Ver Inventario de un Producto

```bash
curl "http://localhost:8002/catalog/items/PROD029/inventario"
```

**Respuesta Esperada:**

```json
{
  "items": [
    {
      "pais": "CO",
      "bodegaId": "BOG_CENTRAL",
      "lote": "INICIAL-20250129",
      "cantidad": 0,
      "vence": "2099-12-31",
      "condiciones": "Producto habilitado - stock inicial en 0"
    },
    {
      "pais": "CO",
      "bodegaId": "MED_SUR",
      "lote": "INICIAL-20250129",
      "cantidad": 0,
      "vence": "2099-12-31",
      "condiciones": "Producto habilitado - stock inicial en 0"
    },
    {
      "pais": "MX",
      "bodegaId": "CDMX_NORTE",
      "lote": "INICIAL-20250129",
      "cantidad": 0,
      "vence": "2099-12-31",
      "condiciones": "Producto habilitado - stock inicial en 0"
    }
  ],
  "meta": {
    "page": 1,
    "size": 50,
    "total": 3,
    "tookMs": 0
  }
}
```

---

## 📥 Registrar Primer Ingreso

Una vez creado el producto con inventario inicial, puedes registrar el primer ingreso:

```bash
curl -X POST "http://localhost:8002/inventory/movements" \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD029",
    "bodega_id": "BOG_CENTRAL",
    "pais": "CO",
    "lote": "INS-LOTE-001",
    "tipo_movimiento": "INGRESO",
    "motivo": "COMPRA",
    "cantidad": 50,
    "fecha_vencimiento": "2026-06-30",
    "usuario_id": "ADMIN001",
    "referencia_documento": "PO-2025-100",
    "observaciones": "Compra inicial de insulina"
  }'
```

**Resultado:**
- ✅ Se actualiza el inventario existente o se crea uno nuevo con el lote especificado
- ✅ Stock pasa de 0 → 50
- ✅ Se registra el movimiento en el kardex
- ✅ Se pueden generar alertas si aplica

---

## 🎛️ Campos Opcionales de Inventario

Al crear un producto, puedes configurar estos campos:

| Campo | Tipo | Default | Descripción |
|-------|------|---------|-------------|
| `stockMinimo` | int | 10 | Stock mínimo antes de generar alerta WARNING |
| `stockCritico` | int | 5 | Stock crítico para alertas CRITICAL |
| `requiereLote` | bool | false | Si el producto requiere número de lote |
| `requiereVencimiento` | bool | true | Si el producto requiere fecha de vencimiento |

### Ejemplo de Configuración Personalizada

```json
{
  "id": "PROD030",
  "nombre": "Vacuna COVID-19",
  "codigo": "VAC-COVID",
  "categoria": "VACCINES",
  "presentacion": "Vial 5 dosis",
  "precioUnitario": 25000.00,
  "requisitosAlmacenamiento": "Ultra congelado -70°C",
  "stockMinimo": 100,
  "stockCritico": 20,
  "requiereLote": true,
  "requiereVencimiento": true,
  "bodegasIniciales": [
    {
      "bodega_id": "CADENA_FRIO_BOG",
      "pais": "CO",
      "lote": "VAC-INICIAL",
      "fecha_vencimiento": "2025-12-31"
    }
  ]
}
```

---

## ⚙️ Comportamiento del Sistema

### 1. **Si NO especificas `bodegasIniciales`:**
- ✅ Se crea solo el producto
- ❌ NO se crea inventario
- El inventario se creará automáticamente en el primer INGRESO

### 2. **Si especificas `bodegasIniciales`:**
- ✅ Se crea el producto
- ✅ Se crean registros de inventario con cantidad = 0
- ✅ Los movimientos de INGRESO actualizan el inventario existente
- ✅ Mayor consistencia en reportes (siempre habrá registros)

### 3. **Ventajas del Inventario Inicial:**
- 📊 Reportes más completos (productos siempre visibles aunque tengan stock 0)
- 🔍 Facilita queries (no necesitas LEFT JOIN)
- ✅ Claridad: sabes explícitamente en qué bodegas está habilitado el producto
- 🎯 Consistencia: el producto existe tanto en catálogo como en inventario

---

## 🧪 Pruebas Locales

### Script de Prueba Completo

```bash
#!/bin/bash

echo "🧪 Prueba: Creación de producto con inventario inicial"
echo ""

# 1. Crear producto con inventario inicial en 2 bodegas
echo "📝 1. Creando producto con inventario inicial..."
curl -X POST "http://localhost:8002/catalog/items" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "TEST001",
    "nombre": "Producto de Prueba",
    "codigo": "TST001",
    "categoria": "TEST",
    "presentacion": "Unidad",
    "precioUnitario": 1000.00,
    "stockMinimo": 10,
    "stockCritico": 5,
    "bodegasIniciales": [
      {"bodega_id": "BOG_CENTRAL", "pais": "CO"},
      {"bodega_id": "MED_SUR", "pais": "CO"}
    ]
  }'

echo ""
echo ""

# 2. Verificar inventario (debe mostrar 2 registros con cantidad 0)
echo "🔍 2. Verificando inventario inicial..."
curl "http://localhost:8002/catalog/items/TEST001/inventario"

echo ""
echo ""

# 3. Registrar ingreso en BOG_CENTRAL
echo "📥 3. Registrando ingreso de 100 unidades en BOG_CENTRAL..."
curl -X POST "http://localhost:8002/inventory/movements" \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "TEST001",
    "bodega_id": "BOG_CENTRAL",
    "pais": "CO",
    "tipo_movimiento": "INGRESO",
    "motivo": "COMPRA",
    "cantidad": 100,
    "usuario_id": "TEST_USER",
    "referencia_documento": "TEST-001"
  }'

echo ""
echo ""

# 4. Verificar inventario actualizado
echo "🔍 4. Verificando inventario después del ingreso..."
curl "http://localhost:8002/catalog/items/TEST001/inventario"

echo ""
echo ""
echo "✅ Prueba completada"
```

Guarda esto como `test-inventario-inicial.sh` y ejecútalo:

```bash
chmod +x test-inventario-inicial.sh
./test-inventario-inicial.sh
```

---

## 📊 Consulta en Base de Datos

Para verificar directamente en la base de datos:

```sql
-- Ver producto creado
SELECT id, nombre, codigo, stock_minimo, stock_critico, 
       requiere_lote, requiere_vencimiento
FROM producto 
WHERE id = 'PROD029';

-- Ver inventario inicial
SELECT producto_id, bodega_id, pais, lote, cantidad, vence, condiciones
FROM inventario
WHERE producto_id = 'PROD029';

-- Ver kardex después del ingreso
SELECT id, producto_id, bodega_id, tipo_movimiento, cantidad, 
       saldo_anterior, saldo_nuevo, created_at
FROM movimiento_inventario
WHERE producto_id = 'PROD029'
ORDER BY created_at DESC;
```

---

## ✅ Ventajas de Esta Implementación

1. **Retrocompatible**: Si no especificas `bodegasIniciales`, funciona como antes
2. **Flexible**: Puedes especificar 1 o N bodegas iniciales
3. **Consistente**: Los productos siempre tienen representación en inventario
4. **Trazable**: El lote y fecha de vencimiento quedan registrados
5. **Automático**: Si no especificas lote/fecha, se generan automáticamente

---

## 🚨 Consideraciones

1. **No es obligatorio**: Puedes seguir creando productos sin inventario inicial
2. **Stock siempre en 0**: Los registros iniciales siempre tienen cantidad = 0
3. **Primer INGRESO**: Actualiza el registro existente o crea uno nuevo según el lote
4. **Bodegas múltiples**: Ideal para empresas con operación multi-país/multi-bodega

---

## 📞 Soporte

Para más información, consulta:
- `ENDPOINTS-INVENTARIO.md` - Documentación completa de endpoints
- `GUIA-PRUEBAS-LOCALES.md` - Guía de pruebas locales
- Código fuente: `app/routes/catalog.py` (líneas 109-217)

