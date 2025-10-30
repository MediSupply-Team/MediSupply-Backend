# 📦 Documentación de Endpoints - Gestión de Inventario

## 🎯 Resumen

Esta API permite gestionar movimientos de inventario en tiempo real, incluyendo ingresos, salidas, transferencias entre bodegas, consulta de kardex, alertas y reportes.

**Base URL (local):** `http://localhost:8000/api/inventory`
**Base URL (AWS):** `http://<alb-url>/api/inventory`

---

## 📋 Índice de Endpoints

1. [Registrar Movimiento (Ingreso/Salida)](#1-registrar-movimiento-ingresosalida)
2. [Registrar Transferencia](#2-registrar-transferencia)
3. [Consultar Kardex (Historial)](#3-consultar-kardex-historial)
4. [Anular Movimiento](#4-anular-movimiento)
5. [Consultar Alertas](#5-consultar-alertas)
6. [Marcar Alerta como Leída](#6-marcar-alerta-como-leída)
7. [Reporte de Saldos](#7-reporte-de-saldos)

---

## 1. Registrar Movimiento (Ingreso/Salida)

### `POST /api/inventory/movements`

Registra un movimiento de inventario (ingreso o salida) y actualiza el stock en tiempo real.

### Headers
```
Content-Type: application/json
```

### Request Body

```json
{
  "producto_id": "PROD001",
  "bodega_id": "BOG_CENTRAL",
  "pais": "CO",
  "lote": "AMX001_2024",
  "tipo_movimiento": "INGRESO",
  "motivo": "COMPRA",
  "cantidad": 100,
  "fecha_vencimiento": "2025-12-31",
  "usuario_id": "USER001",
  "referencia_documento": "PO-2024-100",
  "observaciones": "Compra a proveedor XYZ",
  "permitir_stock_negativo": false
}
```

### Campos del Request

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `producto_id` | string | ✅ | ID del producto (ej: "PROD001") |
| `bodega_id` | string | ✅ | ID de la bodega (ej: "BOG_CENTRAL") |
| `pais` | string | ✅ | Código de país (2 letras, ej: "CO") |
| `lote` | string | ❌ | Número de lote (requerido si el producto lo exige) |
| `tipo_movimiento` | enum | ✅ | **INGRESO**, **SALIDA**, TRANSFERENCIA_SALIDA, TRANSFERENCIA_INGRESO |
| `motivo` | enum | ✅ | **COMPRA**, **VENTA**, **AJUSTE**, **DEVOLUCION**, **MERMA**, TRANSFERENCIA, PRODUCCION, INVENTARIO_INICIAL |
| `cantidad` | integer | ✅ | Cantidad a mover (debe ser > 0) |
| `fecha_vencimiento` | date | ❌ | Fecha de vencimiento (formato: YYYY-MM-DD) |
| `usuario_id` | string | ✅ | ID del usuario que registra el movimiento |
| `referencia_documento` | string | ❌ | N° de documento (PO, factura, orden, etc) |
| `observaciones` | string | ❌ | Observaciones adicionales |
| `permitir_stock_negativo` | boolean | ❌ | Permite dejar stock negativo (default: false) |

### Response Success (201)

```json
{
  "id": 12,
  "producto_id": "PROD001",
  "bodega_id": "BOG_CENTRAL",
  "pais": "CO",
  "lote": "AMX001_2024",
  "tipo_movimiento": "INGRESO",
  "motivo": "COMPRA",
  "cantidad": 100,
  "fecha_vencimiento": "2025-12-31",
  "saldo_anterior": 500,
  "saldo_nuevo": 600,
  "usuario_id": "USER001",
  "referencia_documento": "PO-2024-100",
  "observaciones": "Compra a proveedor XYZ",
  "created_at": "2024-10-28T10:30:00Z",
  "estado": "ACTIVO"
}
```

### Response Error (400 - Stock Insuficiente)

```json
{
  "detail": {
    "error": "STOCK_INSUFICIENTE",
    "message": "Stock insuficiente en BOG_CENTRAL",
    "saldo_actual": 50,
    "cantidad_requerida": 100,
    "faltante": 50,
    "producto_id": "PROD001",
    "producto_nombre": "Amoxicilina 500mg",
    "bodega_id": "BOG_CENTRAL",
    "pais": "CO"
  }
}
```

### Ejemplo de Uso (JavaScript/Axios)

```javascript
// Registrar un ingreso (compra)
const registrarIngreso = async () => {
  try {
    const response = await axios.post('/api/inventory/movements', {
      producto_id: 'PROD001',
      bodega_id: 'BOG_CENTRAL',
      pais: 'CO',
      lote: 'AMX001_2024',
      tipo_movimiento: 'INGRESO',
      motivo: 'COMPRA',
      cantidad: 100,
      fecha_vencimiento: '2025-12-31',
      usuario_id: getCurrentUserId(),
      referencia_documento: 'PO-2024-100',
      observaciones: 'Compra a proveedor XYZ'
    });
    
    console.log('Saldo anterior:', response.data.saldo_anterior);
    console.log('Saldo nuevo:', response.data.saldo_nuevo);
    
    // Mostrar mensaje de éxito
    alert(`Movimiento registrado. Stock actualizado: ${response.data.saldo_nuevo} unidades`);
  } catch (error) {
    if (error.response?.status === 400) {
      // Error de validación o stock insuficiente
      alert(error.response.data.detail.message);
    }
  }
};

// Registrar una salida (venta)
const registrarSalida = async () => {
  try {
    const response = await axios.post('/api/inventory/movements', {
      producto_id: 'PROD001',
      bodega_id: 'BOG_CENTRAL',
      pais: 'CO',
      lote: 'AMX001_2024',
      tipo_movimiento: 'SALIDA',
      motivo: 'VENTA',
      cantidad: 50,
      usuario_id: getCurrentUserId(),
      referencia_documento: 'ORD-2024-500'
    });
    
    console.log('Stock después de venta:', response.data.saldo_nuevo);
  } catch (error) {
    if (error.response?.data.detail?.error === 'STOCK_INSUFICIENTE') {
      const detail = error.response.data.detail;
      alert(`Stock insuficiente. Disponible: ${detail.saldo_actual}, Requerido: ${detail.cantidad_requerida}`);
    }
  }
};
```

---

## 2. Registrar Transferencia

### `POST /api/inventory/transfers`

Registra una transferencia entre dos bodegas (puede ser entre países diferentes).

### Request Body

```json
{
  "producto_id": "PROD001",
  "lote": "AMX001_2024",
  "cantidad": 50,
  "bodega_origen_id": "BOG_CENTRAL",
  "pais_origen": "CO",
  "bodega_destino_id": "MED_SUR",
  "pais_destino": "CO",
  "usuario_id": "USER001",
  "referencia_documento": "TRANS-2024-001",
  "observaciones": "Transferencia por demanda"
}
```

### Response Success (201)

```json
{
  "message": "Transferencia registrada exitosamente",
  "movimiento_salida_id": 15,
  "movimiento_ingreso_id": 16,
  "saldo_origen": 450,
  "saldo_destino": 50
}
```

### Ejemplo de Uso

```javascript
const registrarTransferencia = async (productoId, cantidad, origenBodega, destinoBodega) => {
  try {
    const response = await axios.post('/api/inventory/transfers', {
      producto_id: productoId,
      cantidad: cantidad,
      bodega_origen_id: origenBodega,
      pais_origen: 'CO',
      bodega_destino_id: destinoBodega,
      pais_destino: 'CO',
      usuario_id: getCurrentUserId(),
      referencia_documento: `TRANS-${Date.now()}`,
      observaciones: 'Transferencia solicitada desde el sistema'
    });
    
    console.log('Transferencia completada:');
    console.log('- Saldo en origen:', response.data.saldo_origen);
    console.log('- Saldo en destino:', response.data.saldo_destino);
    
    return response.data;
  } catch (error) {
    console.error('Error en transferencia:', error.response?.data);
    throw error;
  }
};
```

---

## 3. Consultar Kardex (Historial)

### `GET /api/inventory/movements/kardex`

Consulta el historial de movimientos (kardex) con múltiples filtros disponibles.

### Query Parameters

| Parámetro | Tipo | Descripción | Ejemplo |
|-----------|------|-------------|---------|
| `producto_id` | string | Filtrar por producto | PROD001 |
| `bodega_id` | string | Filtrar por bodega | BOG_CENTRAL |
| `pais` | string | Filtrar por país | CO |
| `tipo_movimiento` | string | INGRESO, SALIDA, etc | INGRESO |
| `motivo` | string | COMPRA, VENTA, etc | COMPRA |
| `usuario_id` | string | Filtrar por usuario | USER001 |
| `referencia_documento` | string | Buscar por referencia | PO-2024 |
| `fecha_desde` | datetime | Desde (ISO 8601) | 2024-10-01T00:00:00Z |
| `fecha_hasta` | datetime | Hasta (ISO 8601) | 2024-10-31T23:59:59Z |
| `estado` | string | ACTIVO, ANULADO, null | ACTIVO |
| `page` | integer | Página (default: 1) | 1 |
| `size` | integer | Tamaño (1-200, default: 50) | 50 |

### Response Success (200)

```json
{
  "items": [
    {
      "id": 12,
      "producto_id": "PROD001",
      "producto_nombre": "Amoxicilina 500mg",
      "bodega_id": "BOG_CENTRAL",
      "pais": "CO",
      "lote": "AMX001_2024",
      "tipo_movimiento": "INGRESO",
      "motivo": "COMPRA",
      "cantidad": 100,
      "saldo_anterior": 500,
      "saldo_nuevo": 600,
      "usuario_id": "USER001",
      "referencia_documento": "PO-2024-100",
      "created_at": "2024-10-28T10:30:00Z",
      "estado": "ACTIVO"
    }
  ],
  "meta": {
    "page": 1,
    "size": 50,
    "total": 150,
    "tookMs": 45
  }
}
```

### Ejemplo de Uso

```javascript
// Obtener kardex de un producto
const obtenerKardexProducto = async (productoId, page = 1) => {
  try {
    const response = await axios.get('/api/inventory/movements/kardex', {
      params: {
        producto_id: productoId,
        page: page,
        size: 50,
        estado: 'ACTIVO'  // Solo movimientos activos
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error obteniendo kardex:', error);
    throw error;
  }
};

// Obtener movimientos de una bodega en un rango de fechas
const obtenerMovimientosBodega = async (bodegaId, fechaDesde, fechaHasta) => {
  try {
    const response = await axios.get('/api/inventory/movements/kardex', {
      params: {
        bodega_id: bodegaId,
        fecha_desde: fechaDesde,  // '2024-10-01T00:00:00Z'
        fecha_hasta: fechaHasta,  // '2024-10-31T23:59:59Z'
        page: 1,
        size: 100
      }
    });
    
    console.log(`Total de movimientos: ${response.data.meta.total}`);
    return response.data.items;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
};

// Ejemplo de tabla en React
const KardexTable = ({ productoId }) => {
  const [kardex, setKardex] = useState([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  
  useEffect(() => {
    const fetchKardex = async () => {
      const data = await obtenerKardexProducto(productoId, page);
      setKardex(data.items);
      setTotal(data.meta.total);
    };
    
    fetchKardex();
  }, [productoId, page]);
  
  return (
    <div>
      <h2>Kardex</h2>
      <table>
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Tipo</th>
            <th>Motivo</th>
            <th>Cantidad</th>
            <th>Saldo Anterior</th>
            <th>Saldo Nuevo</th>
            <th>Usuario</th>
          </tr>
        </thead>
        <tbody>
          {kardex.map(mov => (
            <tr key={mov.id}>
              <td>{new Date(mov.created_at).toLocaleString()}</td>
              <td>{mov.tipo_movimiento}</td>
              <td>{mov.motivo}</td>
              <td>{mov.cantidad}</td>
              <td>{mov.saldo_anterior}</td>
              <td>{mov.saldo_nuevo}</td>
              <td>{mov.usuario_id}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <Pagination page={page} total={total} size={50} onPageChange={setPage} />
    </div>
  );
};
```

---

## 4. Anular Movimiento

### `PUT /api/inventory/movements/{movimiento_id}/anular`

Anula un movimiento de inventario, revirtiendo su impacto en el stock.

### Request Body

```json
{
  "motivo_anulacion": "Error en la cantidad registrada, se duplicó el movimiento",
  "usuario_id": "ADMIN001"
}
```

### Response Success (200)

```json
{
  "id": 12,
  "producto_id": "PROD001",
  "bodega_id": "BOG_CENTRAL",
  "pais": "CO",
  "lote": "AMX001_2024",
  "tipo_movimiento": "INGRESO",
  "motivo": "COMPRA",
  "cantidad": 100,
  "saldo_anterior": 500,
  "saldo_nuevo": 600,
  "usuario_id": "USER001",
  "referencia_documento": "PO-2024-100",
  "observaciones": "Compra a proveedor XYZ",
  "created_at": "2024-10-28T10:30:00Z",
  "estado": "ANULADO"
}
```

### Ejemplo de Uso

```javascript
const anularMovimiento = async (movimientoId, motivo) => {
  try {
    const response = await axios.put(
      `/api/inventory/movements/${movimientoId}/anular`,
      {
        motivo_anulacion: motivo,
        usuario_id: getCurrentUserId()
      }
    );
    
    alert('Movimiento anulado exitosamente');
    return response.data;
  } catch (error) {
    if (error.response?.data.detail?.error === 'MOVIMIENTO_YA_ANULADO') {
      alert('Este movimiento ya fue anulado previamente');
    } else {
      alert('Error al anular movimiento');
    }
    throw error;
  }
};
```

---

## 5. Consultar Alertas

### `GET /api/inventory/alerts`

Obtiene las alertas de inventario (stock bajo, crítico, negativo, etc).

### Query Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `leida` | boolean | true (leídas), false (no leídas), null (ambas) |
| `nivel` | string | INFO, WARNING, CRITICAL |
| `tipo_alerta` | string | STOCK_MINIMO, STOCK_CRITICO, STOCK_NEGATIVO, etc |
| `producto_id` | string | Filtrar por producto |
| `bodega_id` | string | Filtrar por bodega |
| `page` | integer | Página (default: 1) |
| `size` | integer | Tamaño (1-200, default: 50) |

### Response Success (200)

```json
{
  "items": [
    {
      "id": 5,
      "producto_id": "PROD016",
      "producto_nombre": "Salbutamol 100mcg",
      "bodega_id": "LIM_CALLAO",
      "pais": "PE",
      "tipo_alerta": "STOCK_MINIMO",
      "nivel": "WARNING",
      "mensaje": "⚡ Stock bajo para Salbutamol 100mcg en LIM_CALLAO: 100 unidades (mínimo: 50)",
      "stock_actual": 100,
      "stock_minimo": 50,
      "leida": false,
      "created_at": "2024-10-28T09:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "size": 50,
    "total": 8,
    "tookMs": 25
  }
}
```

### Ejemplo de Uso

```javascript
// Obtener alertas no leídas y críticas
const obtenerAlertasCriticas = async () => {
  try {
    const response = await axios.get('/api/inventory/alerts', {
      params: {
        leida: false,
        nivel: 'CRITICAL'
      }
    });
    
    return response.data.items;
  } catch (error) {
    console.error('Error obteniendo alertas:', error);
    throw error;
  }
};

// Componente de alertas en React
const AlertasBadge = () => {
  const [alertas, setAlertas] = useState([]);
  
  useEffect(() => {
    const fetchAlertas = async () => {
      const data = await obtenerAlertasCriticas();
      setAlertas(data);
    };
    
    fetchAlertas();
    
    // Actualizar cada 5 minutos
    const interval = setInterval(fetchAlertas, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);
  
  return (
    <div className="alertas-badge">
      {alertas.length > 0 && (
        <span className="badge badge-danger">
          {alertas.length} alertas críticas
        </span>
      )}
    </div>
  );
};
```

---

## 6. Marcar Alerta como Leída

### `PUT /api/inventory/alerts/{alerta_id}/marcar-leida`

### Query Parameters

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `usuario_id` | string | ✅ | ID del usuario que marca como leída |

### Response Success (200)

```json
{
  "message": "Alerta marcada como leída",
  "alerta_id": 5
}
```

### Ejemplo de Uso

```javascript
const marcarAlertaLeida = async (alertaId) => {
  try {
    await axios.put(
      `/api/inventory/alerts/${alertaId}/marcar-leida`,
      null,
      {
        params: {
          usuario_id: getCurrentUserId()
        }
      }
    );
    
    // Actualizar estado local
    setAlertas(prev => prev.filter(a => a.id !== alertaId));
  } catch (error) {
    console.error('Error marcando alerta:', error);
  }
};
```

---

## 7. Reporte de Saldos

### `GET /api/inventory/reports/saldos`

Genera un reporte consolidado de saldos actuales por bodega.

### Query Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `producto_id` | string | Filtrar por producto |
| `bodega_id` | string | Filtrar por bodega |
| `pais` | string | Filtrar por país |
| `estado_stock` | string | NORMAL, BAJO, CRITICO |
| `page` | integer | Página (default: 1) |
| `size` | integer | Tamaño (1-500, default: 100) |

### Response Success (200)

```json
{
  "items": [
    {
      "producto_id": "PROD001",
      "producto_nombre": "Amoxicilina 500mg",
      "producto_codigo": "AMX500",
      "bodega_id": "BOG_CENTRAL",
      "pais": "CO",
      "lote": "AMX001_2024",
      "cantidad_total": 600,
      "fecha_vencimiento_proxima": "2025-12-31",
      "stock_minimo": 50,
      "stock_critico": 20,
      "estado_stock": "NORMAL"
    }
  ],
  "meta": {
    "page": 1,
    "size": 100,
    "total": 45,
    "tookMs": 67
  }
}
```

### Ejemplo de Uso

```javascript
// Obtener productos con stock bajo
const obtenerProductosBajoStock = async () => {
  try {
    const response = await axios.get('/api/inventory/reports/saldos', {
      params: {
        estado_stock: 'BAJO',
        page: 1,
        size: 100
      }
    });
    
    return response.data.items;
  } catch (error) {
    console.error('Error obteniendo reporte:', error);
    throw error;
  }
};

// Tabla de saldos
const SaldosTable = ({ bodegaId }) => {
  const [saldos, setSaldos] = useState([]);
  
  useEffect(() => {
    const fetchSaldos = async () => {
      const response = await axios.get('/api/inventory/reports/saldos', {
        params: {
          bodega_id: bodegaId
        }
      });
      setSaldos(response.data.items);
    };
    
    fetchSaldos();
  }, [bodegaId]);
  
  const getEstadoColor = (estado) => {
    switch(estado) {
      case 'CRITICO': return 'red';
      case 'BAJO': return 'orange';
      case 'NORMAL': return 'green';
      default: return 'gray';
    }
  };
  
  return (
    <table>
      <thead>
        <tr>
          <th>Producto</th>
          <th>Bodega</th>
          <th>Cantidad</th>
          <th>Estado</th>
          <th>Vence</th>
        </tr>
      </thead>
      <tbody>
        {saldos.map(saldo => (
          <tr key={`${saldo.producto_id}-${saldo.bodega_id}-${saldo.lote}`}>
            <td>{saldo.producto_nombre}</td>
            <td>{saldo.bodega_id}</td>
            <td>{saldo.cantidad_total}</td>
            <td style={{ color: getEstadoColor(saldo.estado_stock) }}>
              {saldo.estado_stock}
            </td>
            <td>{new Date(saldo.fecha_vencimiento_proxima).toLocaleDateString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};
```

---

## 🔧 Configuración de Axios

```javascript
// api/inventario.js
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const inventarioAPI = axios.create({
  baseURL: `${API_BASE_URL}/api/inventory`,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Interceptor para agregar token de autenticación
inventarioAPI.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const InventarioService = {
  // Movimientos
  registrarMovimiento: (data) => inventarioAPI.post('/movements', data),
  registrarTransferencia: (data) => inventarioAPI.post('/transfers', data),
  anularMovimiento: (id, data) => inventarioAPI.put(`/movements/${id}/anular`, data),
  
  // Consultas
  obtenerKardex: (params) => inventarioAPI.get('/movements/kardex', { params }),
  obtenerAlertas: (params) => inventarioAPI.get('/alerts', { params }),
  obtenerSaldos: (params) => inventarioAPI.get('/reports/saldos', { params }),
  
  // Acciones
  marcarAlertaLeida: (id, usuarioId) => 
    inventarioAPI.put(`/alerts/${id}/marcar-leida`, null, { params: { usuario_id: usuarioId } })
};
```

---

## 📝 Notas Importantes

### Validaciones Automáticas

1. **Stock Negativo**: Por defecto NO permite stock negativo. Para permitirlo, enviar `"permitir_stock_negativo": true`

2. **Lote y Vencimiento**: Algunos productos REQUIEREN lote y fecha de vencimiento. El sistema valida automáticamente.

3. **Transacciones Atómicas**: Todos los movimientos se ejecutan en transacciones. Si falla algo, TODO se revierte.

4. **Alertas Automáticas**: Las alertas se generan automáticamente cuando:
   - Stock ≤ stock_critico → Alerta CRITICAL
   - Stock ≤ stock_minimo → Alerta WARNING
   - Stock < 0 → Alerta CRITICAL

### Mejores Prácticas

1. **Siempre capturar `saldo_anterior` y `saldo_nuevo`** en las respuestas para mostrar al usuario
2. **Usar `referencia_documento`** para vincular movimientos con órdenes/facturas
3. **Consultar alertas periódicamente** (cada 5-10 minutos)
4. **Filtrar kardex por fechas** para mejorar performance
5. **Usar paginación** en todas las consultas de listado

---

## 🧪 Testing con cURL

```bash
# 1. Registrar un ingreso
curl -X POST http://localhost:8000/api/inventory/movements \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD001",
    "bodega_id": "BOG_CENTRAL",
    "pais": "CO",
    "tipo_movimiento": "INGRESO",
    "motivo": "COMPRA",
    "cantidad": 100,
    "usuario_id": "USER001"
  }'

# 2. Registrar una salida
curl -X POST http://localhost:8000/api/inventory/movements \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD001",
    "bodega_id": "BOG_CENTRAL",
    "pais": "CO",
    "tipo_movimiento": "SALIDA",
    "motivo": "VENTA",
    "cantidad": 50,
    "usuario_id": "USER001",
    "referencia_documento": "ORD-2024-500"
  }'

# 3. Consultar kardex
curl "http://localhost:8000/api/inventory/movements/kardex?producto_id=PROD001&page=1&size=10"

# 4. Obtener alertas no leídas
curl "http://localhost:8000/api/inventory/alerts?leida=false&nivel=CRITICAL"

# 5. Reporte de saldos
curl "http://localhost:8000/api/inventory/reports/saldos?bodega_id=BOG_CENTRAL"
```

---

## ❓ FAQ

### ¿Cómo saber si un producto requiere lote?
Consulta el endpoint de productos `/api/catalog/items/{id}` y revisa el campo `requiere_lote`.

### ¿Puedo anular una transferencia?
No directamente. Las transferencias generan 2 movimientos vinculados que deben anularse por separado.

### ¿Qué pasa si intento una salida sin stock suficiente?
El sistema retorna un error 400 con detalles del stock disponible y la cantidad faltante.

### ¿Las alertas se eliminan automáticamente?
No. Debes marcarlas como leídas manualmente con el endpoint correspondiente.

### ¿Cómo exportar el kardex a Excel?
Por ahora puedes consultar el endpoint y procesar los datos en el frontend. Un endpoint de exportación está en desarrollo.

---

**Versión:** 2.0.0  
**Última Actualización:** Octubre 2024  
**Autor:** MediSupply Team

