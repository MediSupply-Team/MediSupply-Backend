# 🧪 ENDPOINTS CATALOGO-SERVICE - Pruebas Manuales

**Base URL Local:** `http://localhost:3001`  
**API Prefix:** `/api`  
**Router Prefix:** `/catalog`

---

## ✅ 1. HEALTH CHECK

```bash
# Health check básico
curl http://localhost:3001/health

# Con formato JSON
curl -s http://localhost:3001/health | jq '.'
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "service": "catalogo-service"
}
```

---

## 📋 2. LISTAR PRODUCTOS (GET /api/catalog/items)

### 2.1 Sin filtros (todos los productos)
```bash
curl -s "http://localhost:3001/api/catalog/items" | jq '.'
```

### 2.2 Con paginación
```bash
# Primera página, 5 items
curl -s "http://localhost:3001/api/catalog/items?page=1&size=5" | jq '.meta'

# Segunda página, 10 items
curl -s "http://localhost:3001/api/catalog/items?page=2&size=10" | jq '.'

# Página 1, solo 3 items
curl -s "http://localhost:3001/api/catalog/items?size=3" | jq '.items'
```

### 2.3 Búsqueda por query (nombre del producto)
```bash
# Buscar "ibuprofeno"
curl -s "http://localhost:3001/api/catalog/items?q=ibuprofeno" | jq '.'

# Buscar "acetaminofen"
curl -s "http://localhost:3001/api/catalog/items?q=acetaminofen" | jq '.items'

# Buscar "amoxicilina"
curl -s "http://localhost:3001/api/catalog/items?q=amoxicilina" | jq '.'

# Buscar "insulina"
curl -s "http://localhost:3001/api/catalog/items?q=insulina" | jq '.items[0]'
```

### 2.4 Filtrar por categoría
```bash
# Analgésicos
curl -s "http://localhost:3001/api/catalog/items?categoriaId=ANALGESICS" | jq '.meta'

# Antibióticos
curl -s "http://localhost:3001/api/catalog/items?categoriaId=ANTIBIOTICS" | jq '.items[0:2]'

# Cardiovasculares
curl -s "http://localhost:3001/api/catalog/items?categoriaId=CARDIOVASCULAR" | jq '.'

# Diabetes
curl -s "http://localhost:3001/api/catalog/items?categoriaId=DIABETES" | jq '.items'

# Respiratorios
curl -s "http://localhost:3001/api/catalog/items?categoriaId=RESPIRATORY" | jq '.'
```

### 2.5 Filtrar por código de producto
```bash
# Código IBU400
curl -s "http://localhost:3001/api/catalog/items?codigo=IBU400" | jq '.'

# Código ACE500
curl -s "http://localhost:3001/api/catalog/items?codigo=ACE500" | jq '.items[0]'

# Código AMX500
curl -s "http://localhost:3001/api/catalog/items?codigo=AMX500" | jq '.'
```

### 2.6 Filtrar por país
```bash
# Productos en Colombia
curl -s "http://localhost:3001/api/catalog/items?pais=CO" | jq '.meta'

# Productos en México
curl -s "http://localhost:3001/api/catalog/items?pais=MX" | jq '.items[0:3]'

# Productos en Perú
curl -s "http://localhost:3001/api/catalog/items?pais=PE" | jq '.'

# Productos en Chile
curl -s "http://localhost:3001/api/catalog/items?pais=CL" | jq '.items'
```

### 2.7 Filtrar por bodega
```bash
# Bodega BOG_NORTE (Colombia)
curl -s "http://localhost:3001/api/catalog/items?bodegaId=BOG_NORTE" | jq '.'

# Bodega CDMX_CENTRO (México)
curl -s "http://localhost:3001/api/catalog/items?bodegaId=CDMX_CENTRO" | jq '.items'

# Bodega LIM_CALLAO (Perú)
curl -s "http://localhost:3001/api/catalog/items?bodegaId=LIM_CALLAO" | jq '.'

# Bodega SCL_OESTE (Chile)
curl -s "http://localhost:3001/api/catalog/items?bodegaId=SCL_OESTE" | jq '.meta'
```

### 2.8 Ordenamiento (sort)
```bash
# Ordenar por relevancia (default)
curl -s "http://localhost:3001/api/catalog/items?sort=relevancia&size=5" | jq '.items[].nombre'

# Ordenar por precio
curl -s "http://localhost:3001/api/catalog/items?sort=precio&size=5" | jq '.items[] | {nombre, precioUnitario}'

# Ordenar por cantidad
curl -s "http://localhost:3001/api/catalog/items?sort=cantidad&size=5" | jq '.items[] | {nombre, inventarioResumen}'

# Ordenar por vencimiento
curl -s "http://localhost:3001/api/catalog/items?sort=vencimiento&size=5" | jq '.items[].nombre'
```

### 2.9 Combinación de filtros
```bash
# Query + Categoría
curl -s "http://localhost:3001/api/catalog/items?q=ibu&categoriaId=ANALGESICS" | jq '.'

# Categoría + País + Paginación
curl -s "http://localhost:3001/api/catalog/items?categoriaId=ANTIBIOTICS&pais=CO&page=1&size=5" | jq '.'

# Query + País + Sort
curl -s "http://localhost:3001/api/catalog/items?q=a&pais=MX&sort=precio&size=10" | jq '.items[] | {nombre, precioUnitario}'

# Categoría + Bodega + Sort
curl -s "http://localhost:3001/api/catalog/items?categoriaId=CARDIOVASCULAR&bodegaId=BOG_NORTE&sort=cantidad" | jq '.'

# Todos los filtros combinados
curl -s "http://localhost:3001/api/catalog/items?q=a&categoriaId=ANALGESICS&pais=CO&bodegaId=BOG_NORTE&page=1&size=3&sort=precio" | jq '.'
```

### 2.10 Verificar caché (performance)
```bash
# Primera llamada (sin caché) - ver tookMs
curl -s "http://localhost:3001/api/catalog/items?q=ibuprofeno" | jq '.meta.tookMs'

# Segunda llamada inmediata (con caché) - debería ser más rápido
curl -s "http://localhost:3001/api/catalog/items?q=ibuprofeno" | jq '.meta.tookMs'
```

---

## 🔍 3. DETALLE DE PRODUCTO (GET /api/catalog/items/{id})

```bash
# Producto PROD006 (Ibuprofeno)
curl -s "http://localhost:3001/api/catalog/items/PROD006" | jq '.'

# Producto PROD007 (Acetaminofén)
curl -s "http://localhost:3001/api/catalog/items/PROD007" | jq '.'

# Producto PROD008 (Amoxicilina)
curl -s "http://localhost:3001/api/catalog/items/PROD008" | jq '.'

# Producto PROD009 (Loratadina)
curl -s "http://localhost:3001/api/catalog/items/PROD009" | jq '.'

# Producto PROD010 (Insulina)
curl -s "http://localhost:3001/api/catalog/items/PROD010" | jq '.'

# Producto PROD011 (Omeprazol)
curl -s "http://localhost:3001/api/catalog/items/PROD011" | jq '.'

# Producto PROD012 (Amlodipino)
curl -s "http://localhost:3001/api/catalog/items/PROD012" | jq '.'
```

**Respuesta esperada (ejemplo):**
```json
{
  "id": "PROD006",
  "nombre": "Ibuprofeno 400mg",
  "codigo": "IBU400",
  "categoria": "ANALGESICS",
  "presentacion": "Tableta",
  "precioUnitario": 320.0,
  "requisitosAlmacenamiento": "Temperatura ambiente"
}
```

### 3.1 Producto no existe (404)
```bash
# Producto que no existe
curl -s "http://localhost:3001/api/catalog/items/PROD999" | jq '.'
```

---

## 📦 4. INVENTARIO DE PRODUCTO (GET /api/catalog/items/{id}/inventario)

### 4.1 Sin paginación (default)
```bash
# Inventario de Ibuprofeno
curl -s "http://localhost:3001/api/catalog/items/PROD006/inventario" | jq '.'

# Inventario de Acetaminofén
curl -s "http://localhost:3001/api/catalog/items/PROD007/inventario" | jq '.items'

# Inventario de Amoxicilina
curl -s "http://localhost:3001/api/catalog/items/PROD008/inventario" | jq '.'
```

### 4.2 Con paginación
```bash
# Primera página, 3 items
curl -s "http://localhost:3001/api/catalog/items/PROD006/inventario?page=1&size=3" | jq '.'

# Segunda página, 2 items
curl -s "http://localhost:3001/api/catalog/items/PROD006/inventario?page=2&size=2" | jq '.items'

# Limitar a 5 registros
curl -s "http://localhost:3001/api/catalog/items/PROD007/inventario?size=5" | jq '.meta'
```

### 4.3 Ver detalles específicos del inventario
```bash
# Ver solo países y cantidades
curl -s "http://localhost:3001/api/catalog/items/PROD006/inventario" | jq '.items[] | {pais, cantidad, lote}'

# Ver fechas de vencimiento
curl -s "http://localhost:3001/api/catalog/items/PROD006/inventario" | jq '.items[] | {lote, vence, cantidad}'

# Ver bodegas disponibles
curl -s "http://localhost:3001/api/catalog/items/PROD006/inventario" | jq '.items[] | {bodegaId, pais, cantidad}'
```

**Respuesta esperada:**
```json
{
  "items": [
    {
      "pais": "PE",
      "bodegaId": "LIM_CALLAO",
      "lote": "IBU004_2024",
      "cantidad": 600,
      "vence": "2026-04-30",
      "condiciones": "Almacén secundario"
    },
    {
      "pais": "CO",
      "bodegaId": "MED_SUR",
      "lote": "IBU002_2024",
      "cantidad": 800,
      "vence": "2026-05-31",
      "condiciones": "Bodega principal"
    }
  ],
  "meta": {
    "page": 1,
    "size": 50,
    "total": 5,
    "tookMs": 0
  }
}
```

---

## 🧪 5. CASOS DE PRUEBA AVANZADOS

### 5.1 Verificar estructura de respuesta completa
```bash
# Listar productos - verificar estructura
curl -s "http://localhost:3001/api/catalog/items?size=1" | jq 'keys'
# Debe tener: ["items", "meta"]

curl -s "http://localhost:3001/api/catalog/items?size=1" | jq '.items[0] | keys'
# Debe tener: ["categoria", "codigo", "id", "inventarioResumen", "nombre", "precioUnitario", "presentacion", "requisitosAlmacenamiento"]

curl -s "http://localhost:3001/api/catalog/items?size=1" | jq '.meta | keys'
# Debe tener: ["page", "size", "tookMs", "total"]
```

### 5.2 Pruebas de límites
```bash
# Página muy alta (sin resultados)
curl -s "http://localhost:3001/api/catalog/items?page=999&size=10" | jq '.items | length'

# Size muy grande (limitado por backend)
curl -s "http://localhost:3001/api/catalog/items?size=1000" | jq '.meta.size'

# Page 0 (debería usar 1)
curl -s "http://localhost:3001/api/catalog/items?page=0&size=5" | jq '.meta.page'
```

### 5.3 Búsquedas sin resultados
```bash
# Query que no existe
curl -s "http://localhost:3001/api/catalog/items?q=NOEXISTE123" | jq '.'

# Categoría inválida
curl -s "http://localhost:3001/api/catalog/items?categoriaId=INVALID" | jq '.items | length'

# País sin inventario
curl -s "http://localhost:3001/api/catalog/items?pais=US" | jq '.'
```

### 5.4 Productos específicos por categoría
```bash
# Todos los ANALGESICS
curl -s "http://localhost:3001/api/catalog/items?categoriaId=ANALGESICS&size=50" | jq '.items[] | {id, nombre, codigo}'

# Todos los ANTIBIOTICS
curl -s "http://localhost:3001/api/catalog/items?categoriaId=ANTIBIOTICS&size=50" | jq '.items[] | {id, nombre, codigo}'

# Todos los CARDIOVASCULAR
curl -s "http://localhost:3001/api/catalog/items?categoriaId=CARDIOVASCULAR&size=50" | jq '.items[] | {id, nombre, codigo}'
```

---

## 📊 6. RESUMEN DE DATOS DISPONIBLES

### Productos en la base de datos:
```bash
# Contar total de productos
curl -s "http://localhost:3001/api/catalog/items?size=1" | jq '.meta.total'
```

### Categorías disponibles:
- `ANALGESICS` - Analgésicos
- `ANTIBIOTICS` - Antibióticos
- `CARDIOVASCULAR` - Cardiovasculares
- `DIABETES` - Diabetes
- `RESPIRATORY` - Respiratorios
- `GASTROINTESTINAL` - Gastrointestinales

### Países disponibles:
- `CO` - Colombia
- `MX` - México
- `PE` - Perú
- `CL` - Chile

### Bodegas disponibles:
- Colombia: `BOG_NORTE`, `MED_SUR`
- México: `CDMX_CENTRO`, `GDL_ESTE`
- Perú: `LIM_CALLAO`
- Chile: `SCL_OESTE`

---

## 🚀 7. SCRIPT COMPLETO DE VALIDACIÓN

Copia y pega este script para probar todos los endpoints de una vez:

```bash
#!/bin/bash

BASE_URL="http://localhost:3001"

echo "========================================="
echo "   PRUEBA COMPLETA CATALOGO-SERVICE"
echo "========================================="
echo ""

echo "1️⃣  Health Check..."
curl -s "$BASE_URL/health" | jq '.'
echo ""

echo "2️⃣  Listar todos los productos (primeras 5)..."
curl -s "$BASE_URL/api/catalog/items?size=5" | jq '.meta'
echo ""

echo "3️⃣  Buscar Ibuprofeno..."
curl -s "$BASE_URL/api/catalog/items?q=ibuprofeno" | jq '.items[0].nombre'
echo ""

echo "4️⃣  Filtrar por categoría ANALGESICS..."
curl -s "$BASE_URL/api/catalog/items?categoriaId=ANALGESICS&size=3" | jq '.items[].nombre'
echo ""

echo "5️⃣  Productos en Colombia..."
curl -s "$BASE_URL/api/catalog/items?pais=CO&size=3" | jq '.items[].nombre'
echo ""

echo "6️⃣  Detalle del producto PROD006..."
curl -s "$BASE_URL/api/catalog/items/PROD006" | jq '.'
echo ""

echo "7️⃣  Inventario del producto PROD006..."
curl -s "$BASE_URL/api/catalog/items/PROD006/inventario?size=3" | jq '.items[0:2]'
echo ""

echo "8️⃣  Ordenar por precio..."
curl -s "$BASE_URL/api/catalog/items?sort=precio&size=3" | jq '.items[] | {nombre, precioUnitario}'
echo ""

echo "✅ PRUEBAS COMPLETADAS"
```

---

## 💡 TIPS PARA PROBAR

1. **Instalar jq** (si no lo tienes):
   ```bash
   # macOS
   brew install jq
   
   # Linux
   sudo apt-get install jq
   ```

2. **Sin jq** (respuesta sin formato):
   ```bash
   curl "http://localhost:3001/api/catalog/items"
   ```

3. **Ver solo headers**:
   ```bash
   curl -I "http://localhost:3001/health"
   ```

4. **Ver tiempo de respuesta**:
   ```bash
   time curl -s "http://localhost:3001/api/catalog/items?q=ibuprofeno" > /dev/null
   ```

5. **Guardar respuesta en archivo**:
   ```bash
   curl -s "http://localhost:3001/api/catalog/items" > respuesta.json
   ```

---

## ✅ CHECKLIST DE VALIDACIÓN

- [ ] Health check responde con status 200
- [ ] Listar productos devuelve array de items
- [ ] Meta incluye: page, size, total, tookMs
- [ ] Búsqueda por query funciona
- [ ] Filtro por categoría funciona
- [ ] Filtro por país funciona
- [ ] Filtro por bodega funciona
- [ ] Filtro por código funciona
- [ ] Ordenamiento por precio funciona
- [ ] Ordenamiento por cantidad funciona
- [ ] Paginación funciona correctamente
- [ ] Detalle de producto funciona
- [ ] Inventario de producto funciona
- [ ] Combinación de filtros funciona
- [ ] Cache mejora el performance (tookMs menor)
- [ ] Respuestas tienen formato JSON válido

