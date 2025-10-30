# 🧪 ENDPOINTS CLIENTE-SERVICE - Pruebas Manuales

**Base URL Local:** `http://localhost:3003`  
**API Prefix:** `/api`  
**Router Prefix:** `/cliente`

---

## ✅ 1. HEALTH CHECK

```bash
# Health check completo
curl http://localhost:3003/api/cliente/health

# Con formato JSON
curl -s http://localhost:3003/api/cliente/health | jq '.'
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "service": "cliente-service",
  "version": "1.0.0",
  "timestamp": "2025-10-23T22:12:46Z",
  "sla_max_response_ms": 2000,
  "database": "connected"
}
```

---

## 📊 2. MÉTRICAS DEL SERVICIO (GET /api/cliente/metrics)

```bash
# Obtener métricas del servicio
curl -s "http://localhost:3003/api/cliente/metrics" | jq '.'
```

**Respuesta esperada:**
```json
{
  "service": "cliente-service",
  "version": "1.0.0",
  "timestamp": "2025-10-23T22:13:26.521430",
  "stats": {
    "total_clientes": 5,
    "clientes_activos": 5,
    "clientes_inactivos": 0,
    "consultas_realizadas_hoy": 0
  },
  "sla": {
    "max_response_time_ms": 2000,
    "description": "Todas las consultas deben responder en ≤ 2 segundos"
  }
}
```

---

## 📋 3. LISTAR CLIENTES (GET /api/cliente/)

### 3.1 Sin filtros (todos los clientes activos)
```bash
curl -s "http://localhost:3003/api/cliente/" | jq '.'
```

### 3.2 Con paginación
```bash
# Primeros 3 clientes
curl -s "http://localhost:3003/api/cliente/?limite=3" | jq '.[] | {nombre, nit}'

# Con offset (saltar primeros 2)
curl -s "http://localhost:3003/api/cliente/?limite=3&offset=2" | jq '.[] | {nombre, nit}'

# Limitar a 10 clientes
curl -s "http://localhost:3003/api/cliente/?limite=10" | jq 'length'

# Grandes volúmenes (hasta 500)
curl -s "http://localhost:3003/api/cliente/?limite=100" | jq 'length'
```

### 3.3 Incluir clientes inactivos
```bash
# Solo clientes activos (default: true)
curl -s "http://localhost:3003/api/cliente/?activos_solo=true&limite=10" | jq '.[] | {nombre, activo}'

# Todos los clientes (activos e inactivos)
curl -s "http://localhost:3003/api/cliente/?activos_solo=false" | jq '.[] | {nombre, activo}'
```

### 3.4 Ordenamiento
```bash
# Ordenar por nombre (default)
curl -s "http://localhost:3003/api/cliente/?ordenar_por=nombre&limite=5" | jq '.[] | .nombre'

# Ordenar por NIT
curl -s "http://localhost:3003/api/cliente/?ordenar_por=nit&limite=5" | jq '.[] | {nit, nombre}'

# Ordenar por código único
curl -s "http://localhost:3003/api/cliente/?ordenar_por=codigo_unico&limite=5" | jq '.[] | {codigo_unico, nombre}'

# Ordenar por fecha de creación
curl -s "http://localhost:3003/api/cliente/?ordenar_por=created_at&limite=5" | jq '.[] | {created_at, nombre}'
```

### 3.5 Con vendedor_id (trazabilidad)
```bash
# Registrar consulta de vendedor
curl -s "http://localhost:3003/api/cliente/?limite=5&vendedor_id=VEND001" | jq '.[] | {nombre, nit}'
```

### 3.6 Combinación de filtros
```bash
# Activos, ordenados por NIT, con paginación
curl -s "http://localhost:3003/api/cliente/?activos_solo=true&ordenar_por=nit&limite=3&offset=0" | jq '.'

# Todos los clientes, ordenados por fecha de creación
curl -s "http://localhost:3003/api/cliente/?activos_solo=false&ordenar_por=created_at" | jq '.[] | {nombre, created_at}'
```

**Respuesta esperada (array de clientes):**
```json
[
  {
    "id": "CLI001",
    "nit": "900123456-7",
    "nombre": "Farmacia San José",
    "codigo_unico": "FSJ001",
    "email": "contacto@farmaciasanjose.com",
    "telefono": "+57-1-2345678",
    "direccion": "Calle 45 #12-34",
    "ciudad": "Bogotá",
    "pais": "CO",
    "activo": true,
    "created_at": "2025-10-13T00:12:08.743569",
    "updated_at": "2025-10-13T00:12:08.743569"
  }
]
```

---

## 🔍 4. BUSCAR CLIENTE (GET /api/cliente/search)

### 4.1 Buscar por NIT
```bash
# Farmacia San José (NIT: 900123456-7)
curl -s "http://localhost:3003/api/cliente/search?q=900123456-7&vendedor_id=VEND001" | jq '.'

# Droguería El Buen Pastor (NIT: 800987654-3)
curl -s "http://localhost:3003/api/cliente/search?q=800987654-3&vendedor_id=VEND001" | jq '{nombre, nit, ciudad}'

# Farmatodo Zona Norte (NIT: 700456789-1)
curl -s "http://localhost:3003/api/cliente/search?q=700456789-1&vendedor_id=VEND001" | jq '{nombre, telefono, email}'
```

### 4.2 Buscar por código único
```bash
# Código FSJ001 (Farmacia San José)
curl -s "http://localhost:3003/api/cliente/search?q=FSJ001&vendedor_id=VEND001" | jq '.'

# Código DBP002 (Droguería El Buen Pastor)
curl -s "http://localhost:3003/api/cliente/search?q=DBP002&vendedor_id=VEND001" | jq '{codigo_unico, nombre}'

# Código FZN003 (Farmatodo Zona Norte)
curl -s "http://localhost:3003/api/cliente/search?q=FZN003&vendedor_id=VEND001" | jq '.'
```

### 4.3 Buscar por nombre (parcial)
```bash
# Buscar "Farmacia"
curl -s "http://localhost:3003/api/cliente/search?q=Farmacia&vendedor_id=VEND001" | jq '{nombre, nit}'

# Buscar "San José"
curl -s "http://localhost:3003/api/cliente/search?q=San%20José&vendedor_id=VEND001" | jq '{nombre, ciudad}'

# Buscar "Droguería"
curl -s "http://localhost:3003/api/cliente/search?q=Droguería&vendedor_id=VEND001" | jq '.'

# Buscar "Popular"
curl -s "http://localhost:3003/api/cliente/search?q=Popular&vendedor_id=VEND001" | jq '{nombre, direccion}'
```

### 4.4 Casos de error
```bash
# Cliente no encontrado
curl -s "http://localhost:3003/api/cliente/search?q=NOEXISTE999&vendedor_id=VEND001" | jq '.'

# Query muy corta (mínimo 2 caracteres)
curl -s "http://localhost:3003/api/cliente/search?q=A&vendedor_id=VEND001" | jq '.'

# Sin vendedor_id (requerido)
curl -s "http://localhost:3003/api/cliente/search?q=900123456-7" | jq '.'
```

**Respuesta esperada (cliente único):**
```json
{
  "id": "CLI001",
  "nit": "900123456-7",
  "nombre": "Farmacia San José",
  "codigo_unico": "FSJ001",
  "email": "contacto@farmaciasanjose.com",
  "telefono": "+57-1-2345678",
  "direccion": "Calle 45 #12-34",
  "ciudad": "Bogotá",
  "pais": "CO",
  "activo": true,
  "created_at": "2025-10-13T00:12:08.743569",
  "updated_at": "2025-10-13T00:12:08.743569"
}
```

---

## 📜 5. HISTÓRICO COMPLETO DEL CLIENTE (GET /api/cliente/{cliente_id}/historico)

### 5.1 Histórico completo (12 meses)
```bash
# Cliente CLI001 (Farmacia San José)
curl -s "http://localhost:3003/api/cliente/CLI001/historico?vendedor_id=VEND001" | jq '.'

# Cliente CLI002 (Droguería El Buen Pastor)
curl -s "http://localhost:3003/api/cliente/CLI002/historico?vendedor_id=VEND001" | jq '.'

# Cliente CLI003 (Farmatodo Zona Norte)
curl -s "http://localhost:3003/api/cliente/CLI003/historico?vendedor_id=VEND001" | jq '.'

# Cliente CLI004 (Centro Médico Salud Total)
curl -s "http://localhost:3003/api/cliente/CLI004/historico?vendedor_id=VEND001" | jq '.'

# Cliente CLI005 (Farmacia Popular)
curl -s "http://localhost:3003/api/cliente/CLI005/historico?vendedor_id=VEND001" | jq '.'
```

### 5.2 Con límite de meses personalizado
```bash
# Últimos 6 meses
curl -s "http://localhost:3003/api/cliente/CLI001/historico?vendedor_id=VEND001&limite_meses=6" | jq '.'

# Últimos 3 meses
curl -s "http://localhost:3003/api/cliente/CLI001/historico?vendedor_id=VEND001&limite_meses=3" | jq '.'

# Últimos 24 meses (2 años)
curl -s "http://localhost:3003/api/cliente/CLI001/historico?vendedor_id=VEND001&limite_meses=24" | jq '.'

# Máximo: 60 meses (5 años)
curl -s "http://localhost:3003/api/cliente/CLI001/historico?vendedor_id=VEND001&limite_meses=60" | jq '.'
```

### 5.3 Excluir devoluciones
```bash
# Sin incluir devoluciones
curl -s "http://localhost:3003/api/cliente/CLI001/historico?vendedor_id=VEND001&incluir_devoluciones=false" | jq '.'

# Solo ver compras y productos preferidos
curl -s "http://localhost:3003/api/cliente/CLI001/historico?vendedor_id=VEND001&incluir_devoluciones=false" | jq '{cliente, historico_compras, productos_preferidos}'
```

### 5.4 Ver secciones específicas del histórico
```bash
# Solo información del cliente
curl -s "http://localhost:3003/api/cliente/CLI001/historico?vendedor_id=VEND001" | jq '.cliente'

# Solo histórico de compras
curl -s "http://localhost:3003/api/cliente/CLI001/historico?vendedor_id=VEND001" | jq '.historico_compras'

# Solo productos preferidos
curl -s "http://localhost:3003/api/cliente/CLI001/historico?vendedor_id=VEND001" | jq '.productos_preferidos'

# Solo devoluciones
curl -s "http://localhost:3003/api/cliente/CLI001/historico?vendedor_id=VEND001" | jq '.devoluciones'

# Solo estadísticas
curl -s "http://localhost:3003/api/cliente/CLI001/historico?vendedor_id=VEND001" | jq '.estadisticas'

# Resumen completo
curl -s "http://localhost:3003/api/cliente/CLI001/historico?vendedor_id=VEND001" | jq '{
  cliente: .cliente.nombre,
  total_compras: (.historico_compras | length),
  productos_preferidos: (.productos_preferidos | length),
  devoluciones: (.devoluciones | length),
  estadisticas: .estadisticas
}'
```

### 5.5 Casos de error
```bash
# Cliente no existe
curl -s "http://localhost:3003/api/cliente/CLI999/historico?vendedor_id=VEND001" | jq '.'

# Sin vendedor_id (requerido)
curl -s "http://localhost:3003/api/cliente/CLI001/historico" | jq '.'

# Límite de meses inválido (< 1)
curl -s "http://localhost:3003/api/cliente/CLI001/historico?vendedor_id=VEND001&limite_meses=0" | jq '.'

# Límite de meses excede máximo (> 60)
curl -s "http://localhost:3003/api/cliente/CLI001/historico?vendedor_id=VEND001&limite_meses=100" | jq '.'
```

**Respuesta esperada:**
```json
{
  "cliente": {
    "id": "CLI001",
    "nit": "900123456-7",
    "nombre": "Farmacia San José",
    "codigo_unico": "FSJ001",
    "email": "contacto@farmaciasanjose.com",
    "telefono": "+57-1-2345678",
    "direccion": "Calle 45 #12-34",
    "ciudad": "Bogotá",
    "pais": "CO",
    "activo": true
  },
  "historico_compras": [
    {
      "id": "COMP001",
      "fecha": "2024-09-15T10:30:00",
      "producto_id": "PROD006",
      "producto_nombre": "Ibuprofeno 400mg",
      "cantidad": 100,
      "precio_unitario": 320.0,
      "total": 32000.0
    }
  ],
  "productos_preferidos": [
    {
      "producto_id": "PROD006",
      "producto_nombre": "Ibuprofeno 400mg",
      "categoria": "ANALGESICS",
      "frecuencia_compra": 5,
      "cantidad_total": 500,
      "ultima_compra": "2024-10-01T14:20:00"
    }
  ],
  "devoluciones": [
    {
      "id": "DEV001",
      "fecha": "2024-10-05T09:15:00",
      "producto_id": "PROD007",
      "producto_nombre": "Acetaminofén 500mg",
      "cantidad": 10,
      "motivo": "Producto defectuoso",
      "estado": "APROBADA"
    }
  ],
  "estadisticas": {
    "total_compras": 15,
    "monto_total_comprado": 1500000.0,
    "promedio_compra": 100000.0,
    "ultima_compra": "2024-10-20T11:45:00",
    "productos_unicos": 8,
    "total_devoluciones": 2
  },
  "metadata": {
    "limite_meses": 12,
    "fecha_desde": "2023-10-23",
    "fecha_hasta": "2024-10-23",
    "incluye_devoluciones": true,
    "vendedor_id": "VEND001",
    "timestamp": "2024-10-23T15:30:00"
  }
}
```

---

## 🧪 6. CASOS DE PRUEBA AVANZADOS

### 6.1 Verificar estructura de respuesta
```bash
# Listar clientes - verificar estructura
curl -s "http://localhost:3003/api/cliente/?limite=1" | jq '.[0] | keys'
# Debe tener: ["activo", "ciudad", "codigo_unico", "created_at", "direccion", "email", "id", "nit", "nombre", "pais", "telefono", "updated_at"]

# Health check - verificar estructura
curl -s "http://localhost:3003/api/cliente/health" | jq 'keys'
# Debe tener: ["database", "service", "sla_max_response_ms", "status", "timestamp", "version"]

# Métricas - verificar estructura
curl -s "http://localhost:3003/api/cliente/metrics" | jq 'keys'
# Debe tener: ["service", "sla", "stats", "timestamp", "version"]
```

### 6.2 Pruebas de límites y validación
```bash
# Límite muy grande (máximo 500)
curl -s "http://localhost:3003/api/cliente/?limite=1000" | jq 'length'

# Offset mayor que total de registros
curl -s "http://localhost:3003/api/cliente/?limite=10&offset=1000" | jq 'length'

# Ordenar por campo inválido (debería fallar)
curl -s "http://localhost:3003/api/cliente/?ordenar_por=campo_invalido" | jq '.'

# Query de búsqueda con un solo carácter (debería fallar)
curl -s "http://localhost:3003/api/cliente/search?q=a&vendedor_id=VEND001" | jq '.'
```

### 6.3 Verificar performance (SLA ≤ 2000ms)
```bash
# Medir tiempo de respuesta - Listar
time curl -s "http://localhost:3003/api/cliente/?limite=50" > /dev/null

# Medir tiempo de respuesta - Buscar
time curl -s "http://localhost:3003/api/cliente/search?q=900123456-7&vendedor_id=VEND001" > /dev/null

# Medir tiempo de respuesta - Histórico
time curl -s "http://localhost:3003/api/cliente/CLI001/historico?vendedor_id=VEND001" > /dev/null
```

### 6.4 Pruebas de trazabilidad
```bash
# Listar con vendedor_id
curl -s "http://localhost:3003/api/cliente/?limite=5&vendedor_id=VEND001" | jq 'length'

# Buscar con vendedor_id
curl -s "http://localhost:3003/api/cliente/search?q=FSJ001&vendedor_id=VEND002" | jq '.nombre'

# Histórico con vendedor_id
curl -s "http://localhost:3003/api/cliente/CLI001/historico?vendedor_id=VEND003" | jq '.metadata.vendedor_id'
```

---

## 📊 7. RESUMEN DE DATOS DISPONIBLES

### Clientes en la base de datos:
```bash
# Contar total de clientes
curl -s "http://localhost:3003/api/cliente/metrics" | jq '.stats.total_clientes'
```

### Clientes disponibles:
1. **CLI001** - Farmacia San José
   - NIT: `900123456-7`
   - Código: `FSJ001`
   - Ciudad: Bogotá, CO

2. **CLI002** - Droguería El Buen Pastor
   - NIT: `800987654-3`
   - Código: `DBP002`
   - Ciudad: Medellín, CO

3. **CLI003** - Farmatodo Zona Norte
   - NIT: `700456789-1`
   - Código: `FZN003`
   - Ciudad: Cali, CO

4. **CLI004** - Centro Médico Salud Total
   - NIT: `600345678-9`
   - Código: `CMST004`
   - Ciudad: Cartagena, CO

5. **CLI005** - Farmacia Popular
   - NIT: `500234567-5`
   - Código: `FP005`
   - Ciudad: Barranquilla, CO

---

## 🚀 8. SCRIPT COMPLETO DE VALIDACIÓN

Copia y pega este script para probar todos los endpoints de una vez:

```bash
#!/bin/bash

BASE_URL="http://localhost:3003"

echo "========================================="
echo "   PRUEBA COMPLETA CLIENTE-SERVICE"
echo "========================================="
echo ""

echo "1️⃣  Health Check..."
curl -s "$BASE_URL/api/cliente/health" | jq '.status'
echo ""

echo "2️⃣  Métricas del servicio..."
curl -s "$BASE_URL/api/cliente/metrics" | jq '.stats'
echo ""

echo "3️⃣  Listar primeros 5 clientes..."
curl -s "$BASE_URL/api/cliente/?limite=5" | jq '.[] | {nombre, nit}'
echo ""

echo "4️⃣  Buscar cliente por NIT (900123456-7)..."
curl -s "$BASE_URL/api/cliente/search?q=900123456-7&vendedor_id=VEND001" | jq '{nombre, ciudad, email}'
echo ""

echo "5️⃣  Buscar cliente por código (FSJ001)..."
curl -s "$BASE_URL/api/cliente/search?q=FSJ001&vendedor_id=VEND001" | jq '{nombre, telefono}'
echo ""

echo "6️⃣  Buscar cliente por nombre (Farmacia)..."
curl -s "$BASE_URL/api/cliente/search?q=Farmacia&vendedor_id=VEND001" | jq '.nombre'
echo ""

echo "7️⃣  Histórico del cliente CLI001..."
curl -s "$BASE_URL/api/cliente/CLI001/historico?vendedor_id=VEND001&limite_meses=12" | jq '{
  cliente: .cliente.nombre,
  compras: (.historico_compras | length),
  preferidos: (.productos_preferidos | length),
  devoluciones: (.devoluciones | length)
}'
echo ""

echo "8️⃣  Clientes ordenados por NIT..."
curl -s "$BASE_URL/api/cliente/?ordenar_por=nit&limite=3" | jq '.[] | {nit, nombre}'
echo ""

echo "9️⃣  Paginación (offset 2, límite 3)..."
curl -s "$BASE_URL/api/cliente/?limite=3&offset=2" | jq '.[] | .nombre'
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
   curl "http://localhost:3003/api/cliente/"
   ```

3. **Ver solo headers**:
   ```bash
   curl -I "http://localhost:3003/api/cliente/health"
   ```

4. **Ver tiempo de respuesta detallado**:
   ```bash
   curl -w "\nTime Total: %{time_total}s\n" -s "http://localhost:3003/api/cliente/search?q=900123456-7&vendedor_id=VEND001" -o /dev/null
   ```

5. **Guardar respuesta en archivo**:
   ```bash
   curl -s "http://localhost:3003/api/cliente/CLI001/historico?vendedor_id=VEND001" > historico_cli001.json
   ```

---

## ✅ CHECKLIST DE VALIDACIÓN

- [ ] Health check responde con status 200
- [ ] Métricas muestran total de clientes correcto
- [ ] Listar clientes devuelve array de clientes
- [ ] Paginación (limite, offset) funciona correctamente
- [ ] Filtro de activos_solo funciona
- [ ] Ordenamiento por nombre/nit/codigo/fecha funciona
- [ ] Búsqueda por NIT funciona
- [ ] Búsqueda por código único funciona
- [ ] Búsqueda por nombre funciona
- [ ] Histórico completo funciona
- [ ] Límite de meses en histórico funciona
- [ ] Incluir/excluir devoluciones funciona
- [ ] vendedor_id es obligatorio en búsqueda e histórico
- [ ] Validaciones rechazan parámetros inválidos
- [ ] Respuestas cumplen SLA (≤ 2000ms)
- [ ] Respuestas tienen formato JSON válido
- [ ] Errores devuelven estructura apropiada

---

## ⚠️ NOTAS IMPORTANTES

1. **Trazabilidad**: Los endpoints de búsqueda e histórico requieren `vendedor_id` obligatorio para auditoría.

2. **SLA**: Todas las consultas deben responder en ≤ 2 segundos según criterios de aceptación.

3. **Paginación**: 
   - `limite`: Máximo 500 registros por petición
   - `offset`: Para saltar registros (paginación manual)

4. **Ordenamiento**: Solo valores válidos: `nombre`, `nit`, `codigo_unico`, `created_at`

5. **Búsqueda**: Requiere mínimo 2 caracteres en el query parameter `q`

6. **Histórico**: 
   - Límite máximo: 60 meses (5 años)
   - Incluye: compras, productos preferidos, devoluciones, estadísticas

