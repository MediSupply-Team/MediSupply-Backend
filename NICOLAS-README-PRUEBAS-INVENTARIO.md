# 🧪 Guía de Pruebas: Nuevas Funcionalidades de Inventario

## 📋 Resumen

Este documento explica cómo ejecutar las pruebas completas de las nuevas funcionalidades implementadas:

1. **Inventario Inicial al Crear Productos**
2. **Consultar Productos en Bodega**

---

## 🚀 Inicio Rápido

### Prerequisitos

- Docker Desktop instalado y corriendo
- Docker Compose instalado
- `jq` instalado (para parsear JSON): `brew install jq`

### Ejecución Simple

```bash
# 1. Asegúrate de que Docker está corriendo
# En macOS: Abre Docker Desktop

# 2. Dale permisos de ejecución al script
chmod +x test-completo-inventario.sh

# 3. Ejecuta el script
./test-completo-inventario.sh
```

El script hará automáticamente:
- ✅ Levantar servicios necesarios (catalog-service, bff-venta, bases de datos, redis)
- ✅ Esperar a que estén listos
- ✅ Ejecutar migraciones si es necesario
- ✅ Ejecutar todas las pruebas
- ✅ Mostrar resultados detallados
- ✅ Opción de detener servicios al final

---

## 🔍 Qué Prueba el Script

### Test 1: Retrocompatibilidad
Crea un producto SIN especificar `bodegasIniciales` para verificar que el comportamiento anterior sigue funcionando.

**Esperado:** ✅ Producto creado sin inventario inicial

### Test 2: Inventario Inicial en UNA Bodega
Crea un producto especificando una bodega inicial.

**Esperado:** ✅ Producto creado con 1 registro de inventario en cantidad = 0

### Test 3: Inventario Inicial en MÚLTIPLES Bodegas
Crea un producto especificando 3 bodegas iniciales.

**Esperado:** ✅ Producto creado con 3 registros de inventario en cantidad = 0

### Test 4: Registrar Ingreso
Registra un movimiento de INGRESO en un producto con inventario inicial.

**Esperado:** ✅ Stock actualiza de 0 → 100

### Test 5: Consultar Productos en Bodega (Directo)
Consulta productos disponibles en BOG_CENTRAL usando el endpoint directo.

**Esperado:** ✅ Endpoint retorna productos con stock

### Test 6: Consultar Productos en Bodega (BFF)
Consulta productos a través del BFF-Venta.

**Esperado:** ✅ BFF funciona como proxy correctamente

### Test 7: Filtrar por País
Consulta productos filtrando por país (CO).

**Esperado:** ✅ Solo retorna productos de Colombia

### Test 8: Incluir Productos Sin Stock
Consulta usando `con_stock=false`.

**Esperado:** ✅ Retorna más productos que con `con_stock=true`

---

## 📊 Salida Esperada

```
╔════════════════════════════════════════════════════════════════════╗
║       🧪 Pruebas Completas: Inventario y Productos en Bodega     ║
╚════════════════════════════════════════════════════════════════════╝

📦 PASO 1: Levantando servicios con Docker Compose
────────────────────────────────────────────────────────────────────

Levantando servicios: catalog-service, bff-venta y sus dependencias...
✅ Servicios levantados

⏳ PASO 2: Esperando a que los servicios estén listos
────────────────────────────────────────────────────────────────────

Esperando catalog-service (puerto 3001)... ✓
Esperando bff-venta (puerto 8001)... ✓
✅ Todos los servicios están listos

...

╔════════════════════════════════════════════════════════════════════╗
║                        📊 RESUMEN DE PRUEBAS                       ║
╚════════════════════════════════════════════════════════════════════╝

Total de pruebas:      13
Pruebas exitosas:      13
Pruebas fallidas:      0

🎉 ¡Todas las pruebas pasaron exitosamente!
```

---

## 🛠️ Solución de Problemas

### Error: "Cannot connect to the Docker daemon"

**Problema:** Docker no está corriendo

**Solución:**
```bash
# En macOS
open -a Docker

# Espera a que Docker Desktop esté completamente iniciado
# Verás el ícono de Docker en la barra de menú
```

### Error: "no such service: catalog-service"

**Problema:** Los servicios requieren el perfil `dev`

**Solución:** El script ya exporta `APP_PROFILE=dev` automáticamente.

Si ejecutas manualmente:
```bash
export APP_PROFILE=dev
docker-compose up -d catalog-service bff-venta
```

### Error: "Connection refused" al ejecutar pruebas

**Problema:** Los servicios aún no están listos

**Solución:** El script espera automáticamente. Si ejecutas manualmente:
```bash
# Esperar 30 segundos y reintentar
sleep 30
./test-completo-inventario.sh
```

### Error: Migraciones no aplicadas

**Problema:** La tabla `movimiento_inventario` no existe

**Solución:** Ejecutar migración manualmente:
```bash
docker exec -i catalog-db psql -U catalog_user -d catalogo < catalogo-service/data/002_movimientos.sql
```

---

## 🔧 Comandos Manuales Útiles

### Levantar solo los servicios necesarios

```bash
export APP_PROFILE=dev
docker-compose up -d redis catalog-db catalog-service bff-venta
```

### Ver logs de un servicio

```bash
# Catalog Service
docker-compose logs -f catalog-service

# BFF-Venta
docker-compose logs -f bff-venta
```

### Verificar que servicios están corriendo

```bash
docker-compose ps
```

### Detener servicios

```bash
docker-compose down
```

### Detener y limpiar todo

```bash
docker-compose down -v  # ⚠️ Esto borra los datos de las bases de datos
```

---

## 🌐 URLs de los Servicios

Una vez levantados, los servicios están disponibles en:

| Servicio | URL | Puerto |
|----------|-----|--------|
| Catalog Service (API) | http://localhost:3001/api | 3001 |
| Catalog Service (Swagger) | http://localhost:3001/docs | 3001 |
| BFF-Venta (API) | http://localhost:8001/api/v1 | 8001 |
| PostgreSQL (Catalog) | localhost:5433 | 5433 |
| Redis | localhost:6379 | 6379 |

---

## 📝 Pruebas Manuales

Si prefieres ejecutar pruebas manualmente:

### 1. Crear Producto con Inventario Inicial

```bash
curl -X POST "http://localhost:3001/api/catalog/items" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "PROD_MANUAL_001",
    "nombre": "Producto Manual",
    "codigo": "MAN001",
    "categoria": "TEST",
    "precioUnitario": 1000.00,
    "bodegasIniciales": [
      {"bodega_id": "BOG_CENTRAL", "pais": "CO"}
    ]
  }'
```

### 2. Verificar Inventario

```bash
curl "http://localhost:3001/api/catalog/items/PROD_MANUAL_001/inventario"
```

### 3. Consultar Productos en Bodega

```bash
# Directo
curl "http://localhost:3001/api/inventory/bodega/BOG_CENTRAL/productos?con_stock=true" | jq '.'

# A través del BFF
curl "http://localhost:8001/api/v1/inventory/bodega/BOG_CENTRAL/productos" | jq '.'
```

### 4. Registrar Ingreso

```bash
curl -X POST "http://localhost:3001/api/inventory/movements" \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD_MANUAL_001",
    "bodega_id": "BOG_CENTRAL",
    "pais": "CO",
    "tipo_movimiento": "INGRESO",
    "motivo": "COMPRA",
    "cantidad": 50,
    "usuario_id": "ADMIN001"
  }'
```

### 5. Verificar Stock Actualizado

```bash
curl "http://localhost:3001/api/inventory/bodega/BOG_CENTRAL/productos" | \
  jq '.items[] | select(.producto_id == "PROD_MANUAL_001")'
```

---

## 📚 Documentación Relacionada

- **GUIA-INVENTARIO-INICIAL.md** - Guía completa sobre inventario inicial
- **ENDPOINT-PRODUCTOS-BODEGA.md** - Documentación del endpoint de productos en bodega
- **RESUMEN-CAMBIOS-INVENTARIO.md** - Resumen ejecutivo de todos los cambios
- **ENDPOINTS-INVENTARIO.md** - Documentación completa de todos los endpoints

---

## ✅ Checklist Pre-Ejecución

Antes de ejecutar las pruebas, verifica:

- [ ] Docker Desktop está instalado y corriendo
- [ ] Tienes permisos de ejecución en el script (`chmod +x`)
- [ ] `jq` está instalado (para parsear JSON)
- [ ] Puerto 3001 está libre (catalog-service)
- [ ] Puerto 8001 está libre (bff-venta)
- [ ] Puerto 5433 está libre (postgres catalog)
- [ ] Puerto 6379 está libre (redis)

---

## 🎯 Resultados Esperados

Al finalizar las pruebas exitosamente deberías ver:

```
📊 RESUMEN DE PRUEBAS

Total de pruebas:      13
Pruebas exitosas:      13
Pruebas fallidas:      0

🎉 ¡Todas las pruebas pasaron exitosamente!
```

Y se habrán creado 3 productos de prueba:
- `TEST_{timestamp}_1` - Sin inventario inicial
- `TEST_{timestamp}_2` - Con 1 bodega inicial
- `TEST_{timestamp}_3` - Con 3 bodegas iniciales

---

## 🔄 Próximos Pasos

Después de las pruebas exitosas:

1. **Revisar Logs** - Verificar que no hay errores en los logs
2. **Explorar Swagger** - Visitar http://localhost:3001/docs
3. **Probar Endpoints** - Usar Swagger o Postman
4. **Revisar Base de Datos** - Conectarse a PostgreSQL y ver los datos

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa los logs: `docker-compose logs catalog-service`
2. Verifica que Docker tiene suficientes recursos (memoria/CPU)
3. Asegúrate que las migraciones se ejecutaron correctamente
4. Consulta la documentación en los archivos .md mencionados

---

**Fecha:** 29 de Enero de 2025  
**Versión:** 1.0  
**Autor:** Sistema de Pruebas Automatizadas MediSupply

