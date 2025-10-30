# 📋 ENDPOINTS DE INVENTARIO - BFF-VENTA

**Base URL:** `http://localhost:8001` (local) o tu ALB de AWS

---

## 🟢 1. Health Check

```http
GET http://localhost:8001/api/v1/inventory/health
```

**Respuesta:**
```json
{
  "status": "healthy",
  "inventory_module": "connected",
  "catalog_service_url": "http://catalog-service:8000"
}
```

---

## 🟢 2. Registrar Movimiento de Inventario

**Registra un INGRESO o SALIDA de productos**

```http
POST http://localhost:8001/api/v1/inventory/movements
Content-Type: application/json

{
  "producto_id": "PROD001",
  "bodega_id": "BOG_CENTRAL",
  "pais": "CO",
  "lote": "LOTE-001",
  "tipo_movimiento": "INGRESO",
  "motivo": "COMPRA",
  "cantidad": 100,
  "fecha_vencimiento": "2025-12-31",
  "usuario_id": "USER001",
  "referencia_documento": "PO-12345",
  "observaciones": "Compra regular mensual"
}
```

**Tipos de Movimiento:**
- `INGRESO`: Entrada de producto (compra, devolución, producción)
- `SALIDA`: Salida de producto (venta, merma, ajuste)

**Motivos:**
- Para INGRESO: `COMPRA`, `DEVOLUCION`, `PRODUCCION`, `AJUSTE`
- Para SALIDA: `VENTA`, `MERMA`, `DEVOLUCION`, `AJUSTE`

**Respuesta (201 Created):**
```json
{
  "id": 9,
  "producto_id": "PROD001",
  "bodega_id": "BOG_CENTRAL",
  "pais": "CO",
  "lote": "LOTE-001",
  "tipo_movimiento": "INGRESO",
  "motivo": "COMPRA",
  "cantidad": 100,
  "saldo_anterior": 50,
  "saldo_nuevo": 150,
  "usuario_id": "USER001",
  "created_at": "2025-10-28T22:37:50.588926",
  "estado": "ACTIVO"
}
```

---

## 🟢 3. Registrar Transferencia entre Bodegas

**Transfiere productos de una bodega a otra**

```http
POST http://localhost:8001/api/v1/inventory/transfers
Content-Type: application/json

{
  "producto_id": "PROD001",
  "bodega_origen_id": "BOG_CENTRAL",
  "bodega_destino_id": "MED_CENTRAL",
  "pais_origen": "CO",
  "pais_destino": "CO",
  "lote": "LOTE-001",
  "cantidad": 50,
  "usuario_id": "USER001",
  "referencia_documento": "TR-2024-001",
  "observaciones": "Transferencia por alta demanda"
}
```

**Respuesta (201 Created):**
```json
{
  "message": "Transferencia registrada exitosamente",
  "movimiento_salida_id": 10,
  "movimiento_ingreso_id": 11,
  "saldo_origen": 100,
  "saldo_destino": 50
}
```

---

## 🟢 4. Consultar Kardex (Historial de Movimientos)

**Obtiene el historial de movimientos con filtros**

```http
GET http://localhost:8001/api/v1/inventory/movements/kardex?producto_id=PROD001&bodega_id=BOG_CENTRAL&pais=CO&page=1&size=5
```

**Query Parameters:**
- `producto_id` (opcional): Filtrar por producto
- `bodega_id` (opcional): Filtrar por bodega
- `pais` (opcional): Filtrar por país (CO, MX, etc.)
- `tipo_movimiento` (opcional): INGRESO, SALIDA, TRANSFERENCIA_SALIDA, TRANSFERENCIA_INGRESO
- `motivo` (opcional): COMPRA, VENTA, AJUSTE, etc.
- `usuario_id` (opcional): Filtrar por usuario
- `referencia_documento` (opcional): Buscar por número de documento
- `fecha_desde` (opcional): Fecha desde (ISO 8601: 2025-01-01T00:00:00)
- `fecha_hasta` (opcional): Fecha hasta
- `estado` (opcional): ACTIVO, ANULADO, o null para ambos
- `page` (default: 1): Número de página
- `size` (default: 50): Items por página (máx 200)

**Respuesta (200 OK):**
```json
{
  "items": [
    {
      "id": 9,
      "producto_id": "PROD001",
      "producto_nombre": "Amoxicilina 500mg",
      "bodega_id": "BOG_CENTRAL",
      "pais": "CO",
      "lote": "LOTE-DOCKER-001",
      "tipo_movimiento": "INGRESO",
      "motivo": "COMPRA",
      "cantidad": 50,
      "saldo_anterior": 0,
      "saldo_nuevo": 50,
      "usuario_id": "DOCKER_TEST",
      "referencia_documento": null,
      "created_at": "2025-10-28T22:37:50.588926",
      "estado": "ACTIVO"
    }
  ],
  "meta": {
    "page": 1,
    "size": 5,
    "total": 8,
    "tookMs": 12
  }
}
```

---

## 🟢 5. Anular un Movimiento

**Revierte un movimiento de inventario**

```http
PUT http://localhost:8001/api/v1/inventory/movements/9/anular
Content-Type: application/json

{
  "usuario_id": "USER001",
  "motivo_anulacion": "Error de registro - cantidad incorrecta"
}
```

**Respuesta (200 OK):**
```json
{
  "id": 9,
  "producto_id": "PROD001",
  "estado": "ANULADO",
  "anulado_por": "USER001",
  "anulado_at": "2025-10-28T23:00:00",
  "motivo_anulacion": "Error de registro - cantidad incorrecta"
}
```

---

## 🟢 6. Listar Alertas de Inventario

**Obtiene las alertas activas del sistema**

```http
GET http://localhost:8001/api/v1/inventory/alerts?leida=false&nivel=WARNING&page=1&size=10
```

**Query Parameters:**
- `leida` (opcional): true (solo leídas), false (solo no leídas), null (ambas)
- `nivel` (opcional): INFO, WARNING, CRITICAL
- `tipo_alerta` (opcional): STOCK_MINIMO, STOCK_CRITICO, STOCK_NEGATIVO, PROXIMO_VENCER, VENCIDO
- `producto_id` (opcional): Filtrar por producto
- `bodega_id` (opcional): Filtrar por bodega
- `page` (default: 1)
- `size` (default: 50, máx 200)

**Respuesta (200 OK):**
```json
{
  "items": [
    {
      "id": 3,
      "producto_id": "PROD001",
      "producto_nombre": "Amoxicilina 500mg",
      "bodega_id": "BOG_CENTRAL",
      "pais": "CO",
      "tipo_alerta": "STOCK_MINIMO",
      "nivel": "WARNING",
      "mensaje": "⚡ Stock bajo para Amoxicilina 500mg en BOG_CENTRAL: 50 unidades (mínimo: 50)",
      "stock_actual": 50,
      "stock_minimo": 50,
      "leida": false,
      "created_at": "2025-10-28T22:37:50.603918"
    }
  ],
  "meta": {
    "page": 1,
    "size": 10,
    "total": 2,
    "tookMs": 17
  }
}
```

---

## 🟢 7. Marcar Alerta como Leída

```http
PUT http://localhost:8001/api/v1/inventory/alerts/3/marcar-leida?usuario_id=USER001
```

**Respuesta (200 OK):**
```json
{
  "message": "Alerta marcada como leída",
  "alerta_id": 3
}
```

---

## 🟢 8. Reporte de Saldos por Bodega

**Genera un reporte consolidado de inventario**

```http
GET http://localhost:8001/api/v1/inventory/reports/saldos?producto_id=PROD001&bodega_id=BOG_CENTRAL&page=1&size=50
```

**Query Parameters:**
- `producto_id` (opcional): Filtrar por producto
- `bodega_id` (opcional): Filtrar por bodega
- `pais` (opcional): Filtrar por país
- `estado_stock` (opcional): NORMAL, BAJO, CRITICO
- `page` (default: 1)
- `size` (default: 100, máx 500)

**Respuesta (200 OK):**
```json
{
  "items": [
    {
      "producto_id": "PROD001",
      "producto_nombre": "Amoxicilina 500mg",
      "producto_codigo": "MED-AMX-500",
      "bodega_id": "BOG_CENTRAL",
      "pais": "CO",
      "lote": "LOTE-001",
      "cantidad_total": 50,
      "fecha_vencimiento_proxima": "2025-12-31",
      "stock_minimo": 50,
      "stock_critico": 25,
      "estado_stock": "NORMAL"
    }
  ],
  "meta": {
    "page": 1,
    "size": 50,
    "total": 1,
    "tookMs": 23
  }
}
```

---

## 🔥 Ejemplos de Uso Común

### Registrar una Compra (Ingreso)
```bash
curl -X POST http://localhost:8001/api/v1/inventory/movements \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD001",
    "bodega_id": "BOG_CENTRAL",
    "pais": "CO",
    "lote": "LOTE-2025-001",
    "tipo_movimiento": "INGRESO",
    "motivo": "COMPRA",
    "cantidad": 500,
    "fecha_vencimiento": "2026-12-31",
    "usuario_id": "COMPRAS_USER",
    "referencia_documento": "PO-2025-001"
  }'
```

### Registrar una Venta (Salida)
```bash
curl -X POST http://localhost:8001/api/v1/inventory/movements \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD001",
    "bodega_id": "BOG_CENTRAL",
    "pais": "CO",
    "lote": "LOTE-2025-001",
    "tipo_movimiento": "SALIDA",
    "motivo": "VENTA",
    "cantidad": 50,
    "fecha_vencimiento": "2026-12-31",
    "usuario_id": "VENTAS_USER",
    "referencia_documento": "INV-2025-0001"
  }'
```

### Ver Kardex de un Producto
```bash
curl "http://localhost:8001/api/v1/inventory/movements/kardex?producto_id=PROD001&bodega_id=BOG_CENTRAL&pais=CO&page=1&size=10"
```

### Ver Alertas Críticas No Leídas
```bash
curl "http://localhost:8001/api/v1/inventory/alerts?leida=false&nivel=CRITICAL"
```

---

## ⚠️ Códigos de Error Comunes

- **400 Bad Request**: Datos inválidos o stock insuficiente
- **404 Not Found**: Producto, movimiento o alerta no encontrada
- **503 Service Unavailable**: Catalogo-service no disponible
- **504 Gateway Timeout**: Timeout al conectar con catalogo-service

---

## 🔐 Notas de Seguridad

- En producción, estos endpoints deben estar protegidos con autenticación JWT
- El `usuario_id` debe obtenerse del token de autenticación
- Se deben aplicar validaciones de permisos por rol (admin, ventas, compras, etc.)
- Las transferencias deben requerir aprobación en flujos críticos

---

## 📊 Tips para el Frontend

1. **Actualización en Tiempo Real**: Después de registrar un movimiento, consulta el kardex o reporte de saldos para mostrar el stock actualizado
2. **Notificaciones**: Consulta las alertas periódicamente (cada 1-2 minutos) para notificar al usuario
3. **Paginación**: Usa paginación para kardex y reportes, especialmente para productos con mucho movimiento
4. **Filtros**: Implementa filtros en el frontend para mejorar la experiencia de búsqueda
5. **Validación**: Valida que `cantidad > 0` y que las fechas de vencimiento sean futuras antes de enviar

---

## 🚀 Estado Actual

✅ **catalogo-service** corriendo en Docker (puerto 3001)
✅ **bff-venta** corriendo en Docker (puerto 8001)
✅ **catalog-db** (PostgreSQL) corriendo en Docker (puerto 5433)
✅ Todos los endpoints funcionando correctamente
✅ Datos de prueba disponibles (PROD001-PROD025)

