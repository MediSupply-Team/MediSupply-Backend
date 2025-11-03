# 🎨 Guía de Integración Frontend - MediSupply

## 📋 Tabla de Contenidos

1. [Configuración Inicial](#configuración-inicial)
2. [Vista: Productos (Catálogo)](#vista-productos-catálogo)
3. [Vista: Inventario](#vista-inventario)
4. [Registrar Venta (Salida)](#registrar-venta-salida)
5. [Registrar Ingreso](#registrar-ingreso)
6. [Ver Kardex/Historial](#ver-kardexhistorial)
7. [Manejo de Errores](#manejo-de-errores)

---

## 🔧 Configuración Inicial

### Variables de Entorno

```javascript
// .env o config.js
const API_BASE_URL = 'http://localhost:8001/api/v1'; // BFF-Venta (recomendado)
// O directamente:
// const API_BASE_URL = 'http://localhost:3001/api'; // Catalog Service
```

### Helper de API

```javascript
// utils/api.js
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001/api/v1';

export const api = {
  // GET request
  get: async (endpoint, params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    const url = `${API_BASE_URL}${endpoint}${queryString ? '?' + queryString : ''}`;
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}` // Si usas auth
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Error en la petición');
    }
    
    return response.json();
  },
  
  // POST request
  post: async (endpoint, data) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.details?.message || error.message || 'Error en la petición');
    }
    
    return response.json();
  }
};
```

---

## 📦 Vista: Productos (Catálogo)

### ¿Qué Mostrar?

Esta vista muestra el **catálogo general de productos** (todos los productos disponibles en el sistema).

### Endpoint a Usar

```
GET /api/v1/catalog/items
```

### Implementación React

```jsx
// pages/ProductosPage.jsx
import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';

export default function ProductosPage() {
  const [productos, setProductos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Filtros
  const [searchTerm, setSearchTerm] = useState('');
  const [categoria, setCategoria] = useState('');
  
  useEffect(() => {
    cargarProductos();
  }, [searchTerm, categoria]);
  
  const cargarProductos = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = {};
      if (searchTerm) params.q = searchTerm;
      if (categoria) params.categoriaId = categoria;
      
      const data = await api.get('/catalog/items', params);
      setProductos(data.items || []);
    } catch (err) {
      setError(err.message);
      console.error('Error cargando productos:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const verDetalleProducto = async (productoId) => {
    try {
      // Ver dónde está disponible este producto
      const inventario = await api.get(`/catalog/items/${productoId}/inventario`);
      console.log('Inventario del producto:', inventario);
      
      // Mostrar modal o navegar a detalle
      // inventario.items = [{bodegaId, pais, cantidad, lote, vence}, ...]
    } catch (err) {
      console.error('Error:', err);
    }
  };
  
  return (
    <div className="productos-page">
      <header>
        <h1>Inventario de Productos</h1>
        <p>Busca y gestiona productos en el inventario</p>
      </header>
      
      {/* Filtros */}
      <div className="filtros">
        <input
          type="text"
          placeholder="Buscar por nombre, SKU, código de barras..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        
        <select 
          value={categoria} 
          onChange={(e) => setCategoria(e.target.value)}
        >
          <option value="">Todas las categorías</option>
          <option value="ANTIBIOTICS">Antibióticos</option>
          <option value="ANALGESICS">Analgésicos</option>
          <option value="VACCINES">Vacunas</option>
        </select>
      </div>
      
      {/* Resultados */}
      {loading && <p>Cargando productos...</p>}
      {error && <p className="error">Error: {error}</p>}
      
      {!loading && productos.length === 0 && (
        <p>Se encontraron 0 productos</p>
      )}
      
      {!loading && productos.length > 0 && (
        <div className="productos-grid">
          {productos.map(producto => (
            <div key={producto.id} className="producto-card">
              <h3>{producto.nombre}</h3>
              <p>Código: {producto.codigo}</p>
              <p>Categoría: {producto.categoria}</p>
              <p>Precio: ${producto.precioUnitario}</p>
              
              <button onClick={() => verDetalleProducto(producto.id)}>
                Ver dónde está disponible
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

### Ver Inventario de un Producto Específico

```javascript
// components/ModalInventarioProducto.jsx
const ModalInventarioProducto = ({ productoId, onClose }) => {
  const [inventario, setInventario] = useState([]);
  
  useEffect(() => {
    cargarInventarioProducto();
  }, [productoId]);
  
  const cargarInventarioProducto = async () => {
    const data = await api.get(`/catalog/items/${productoId}/inventario`);
    setInventario(data.items);
  };
  
  return (
    <div className="modal">
      <h3>Disponibilidad por Bodega</h3>
      
      <table>
        <thead>
          <tr>
            <th>País</th>
            <th>Bodega</th>
            <th>Lote</th>
            <th>Cantidad</th>
            <th>Vencimiento</th>
          </tr>
        </thead>
        <tbody>
          {inventario.map((item, idx) => (
            <tr key={idx}>
              <td>{item.pais}</td>
              <td>{item.bodegaId}</td>
              <td>{item.lote}</td>
              <td>{item.cantidad}</td>
              <td>{item.vence}</td>
            </tr>
          ))}
        </tbody>
      </table>
      
      <p>Total en todas las bodegas: {inventario.reduce((sum, i) => sum + i.cantidad, 0)}</p>
      
      <button onClick={onClose}>Cerrar</button>
    </div>
  );
};
```

---

## 📊 Vista: Inventario

### ¿Qué Mostrar?

Esta vista muestra **QUÉ productos hay en una bodega específica** (vista de bodega).

**✨ NUEVO ENDPOINT - Úsalo aquí**

### Endpoint a Usar

```
GET /api/v1/inventory/bodega/{bodega_id}/productos
```

### Implementación React

```jsx
// pages/InventarioPage.jsx
import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';

export default function InventarioPage() {
  const [productos, setProductos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Filtros
  const [bodegaSeleccionada, setBodegaSeleccionada] = useState('BOG_CENTRAL');
  const [paisSeleccionado, setPaisSeleccionado] = useState('');
  const [conStock, setConStock] = useState(true); // Solo productos con stock
  const [ordenamiento, setOrdenamiento] = useState('nombre');
  
  // Bodegas disponibles (puedes traerlas de una API)
  const bodegas = [
    { id: 'BOG_CENTRAL', nombre: 'Bogotá Central', pais: 'CO' },
    { id: 'MED_SUR', nombre: 'Medellín Sur', pais: 'CO' },
    { id: 'CDMX_NORTE', nombre: 'CDMX Norte', pais: 'MX' },
    { id: 'LIM_CALLAO', nombre: 'Lima Callao', pais: 'PE' }
  ];
  
  useEffect(() => {
    if (bodegaSeleccionada) {
      cargarProductosEnBodega();
    }
  }, [bodegaSeleccionada, paisSeleccionado, conStock]);
  
  const cargarProductosEnBodega = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = {
        con_stock: conStock,
        size: 100
      };
      
      if (paisSeleccionado) {
        params.pais = paisSeleccionado;
      }
      
      const data = await api.get(
        `/inventory/bodega/${bodegaSeleccionada}/productos`,
        params
      );
      
      setProductos(data.items || []);
    } catch (err) {
      setError(err.message);
      console.error('Error cargando inventario:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Filtros rápidos
  const filtrarStockBajo = () => {
    return productos.filter(p => p.estado_stock === 'BAJO');
  };
  
  const filtrarStockCritico = () => {
    return productos.filter(p => p.estado_stock === 'CRITICO');
  };
  
  return (
    <div className="inventario-page">
      <header>
        <h1>Inventario</h1>
        <p>Gestión de medicamentos y suministros médicos</p>
      </header>
      
      {/* Selector de Bodega */}
      <div className="selector-bodega">
        <label>📍 Ubicación:</label>
        <select 
          value={bodegaSeleccionada}
          onChange={(e) => setBodegaSeleccionada(e.target.value)}
        >
          {bodegas.map(bodega => (
            <option key={bodega.id} value={bodega.id}>
              {bodega.nombre} ({bodega.pais})
            </option>
          ))}
        </select>
      </div>
      
      {/* Filtros */}
      <div className="filtros-rapidos">
        <button 
          className={conStock ? 'active' : ''}
          onClick={() => setConStock(!conStock)}
        >
          {conStock ? '✓ Con stock' : 'Todos'}
        </button>
        
        <button onClick={() => console.log('Stock bajo:', filtrarStockBajo())}>
          🟡 Stock Bajo ({filtrarStockBajo().length})
        </button>
        
        <button onClick={() => console.log('Stock crítico:', filtrarStockCritico())}>
          🔴 Stock Crítico ({filtrarStockCritico().length})
        </button>
      </div>
      
      {/* Resultados */}
      {loading && <p>Cargando productos...</p>}
      {error && <p className="error">Error: {error}</p>}
      
      {!loading && productos.length === 0 && (
        <p>No hay productos {conStock ? 'con stock' : ''} en esta bodega</p>
      )}
      
      {!loading && productos.length > 0 && (
        <div>
          <p>Se encontraron {productos.length} productos</p>
          
          <table className="inventario-tabla">
            <thead>
              <tr>
                <th>Producto</th>
                <th>Código</th>
                <th>Lote</th>
                <th>Cantidad</th>
                <th>Estado</th>
                <th>Vencimiento</th>
                <th>Precio Unit.</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {productos.map((producto, idx) => (
                <tr 
                  key={idx}
                  className={`estado-${producto.estado_stock.toLowerCase()}`}
                >
                  <td>
                    <strong>{producto.producto_nombre}</strong>
                    <br />
                    <small>{producto.categoria}</small>
                  </td>
                  <td>{producto.producto_codigo}</td>
                  <td>{producto.lote}</td>
                  <td>
                    <span className="cantidad">
                      {producto.cantidad}
                    </span>
                  </td>
                  <td>
                    <span className={`badge badge-${producto.estado_stock.toLowerCase()}`}>
                      {producto.estado_stock}
                    </span>
                  </td>
                  <td>{producto.fecha_vencimiento}</td>
                  <td>${producto.precio_unitario.toFixed(2)}</td>
                  <td>
                    <button 
                      className="btn-vender"
                      onClick={() => abrirModalVenta(producto)}
                    >
                      Vender
                    </button>
                    <button onClick={() => verKardex(producto.producto_id)}>
                      Historial
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
```

### CSS para Estados de Stock

```css
/* styles/inventario.css */
.estado-normal {
  background-color: #f0f9ff;
}

.estado-bajo {
  background-color: #fffbeb;
}

.estado-critico {
  background-color: #fef2f2;
}

.badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.badge-normal {
  background-color: #10b981;
  color: white;
}

.badge-bajo {
  background-color: #f59e0b;
  color: white;
}

.badge-critico {
  background-color: #ef4444;
  color: white;
}
```

---

## 💰 Registrar Venta (Salida)

### ¿Dónde Usar?

En la **Vista de Inventario**, cuando el usuario hace clic en "Vender" un producto.

### Endpoint a Usar

```
POST /api/v1/inventory/movements
```

### Flujo Completo

```jsx
// components/ModalVenta.jsx
import React, { useState } from 'react';
import { api } from '../utils/api';

const ModalVenta = ({ producto, bodegaId, onVentaExitosa, onClose }) => {
  const [cantidad, setCantidad] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Información del usuario (obtener de tu contexto de auth)
  const usuarioId = localStorage.getItem('userId') || 'VENDEDOR_001';
  
  const handleVenta = async (e) => {
    e.preventDefault();
    
    // Validación básica
    if (cantidad <= 0) {
      setError('La cantidad debe ser mayor a 0');
      return;
    }
    
    if (cantidad > producto.cantidad) {
      setError(`Stock insuficiente. Disponible: ${producto.cantidad}`);
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const movimiento = {
        producto_id: producto.producto_id,
        bodega_id: bodegaId,
        pais: producto.pais,
        lote: producto.lote,
        tipo_movimiento: 'SALIDA',
        motivo: 'VENTA',
        cantidad: cantidad,
        usuario_id: usuarioId,
        referencia_documento: `VENTA-${Date.now()}`, // Generar ID único
        observaciones: `Venta de ${cantidad} unidades de ${producto.producto_nombre}`
      };
      
      const resultado = await api.post('/inventory/movements', movimiento);
      
      console.log('✅ Venta registrada:', resultado);
      
      // Mostrar mensaje de éxito
      alert(`✅ Venta registrada exitosamente!
      
Producto: ${producto.producto_nombre}
Cantidad vendida: ${cantidad}
Stock anterior: ${resultado.saldo_anterior}
Stock nuevo: ${resultado.saldo_nuevo}
      `);
      
      // Callback para recargar inventario
      onVentaExitosa();
      
      // Cerrar modal
      onClose();
      
    } catch (err) {
      console.error('Error registrando venta:', err);
      setError(err.message || 'Error al registrar la venta');
    } finally {
      setLoading(false);
    }
  };
  
  const calcularTotal = () => {
    return (cantidad * producto.precio_unitario).toFixed(2);
  };
  
  return (
    <div className="modal-overlay">
      <div className="modal-venta">
        <h2>🛒 Registrar Venta</h2>
        
        <div className="producto-info">
          <h3>{producto.producto_nombre}</h3>
          <p>Código: {producto.producto_codigo}</p>
          <p>Lote: {producto.lote}</p>
          <p>Stock disponible: <strong>{producto.cantidad}</strong> unidades</p>
          <p>Precio unitario: <strong>${producto.precio_unitario.toFixed(2)}</strong></p>
        </div>
        
        <form onSubmit={handleVenta}>
          <div className="form-group">
            <label>Cantidad a vender:</label>
            <input
              type="number"
              min="1"
              max={producto.cantidad}
              value={cantidad}
              onChange={(e) => setCantidad(parseInt(e.target.value) || 0)}
              required
            />
            <small>Máximo: {producto.cantidad}</small>
          </div>
          
          <div className="total">
            <strong>Total: ${calcularTotal()}</strong>
          </div>
          
          {error && <p className="error">{error}</p>}
          
          <div className="modal-actions">
            <button 
              type="submit" 
              disabled={loading || cantidad <= 0 || cantidad > producto.cantidad}
              className="btn-primary"
            >
              {loading ? 'Procesando...' : '✓ Confirmar Venta'}
            </button>
            
            <button 
              type="button" 
              onClick={onClose}
              className="btn-secondary"
              disabled={loading}
            >
              Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ModalVenta;
```

### Uso en la Vista de Inventario

```jsx
// En InventarioPage.jsx
const [modalVentaAbierto, setModalVentaAbierto] = useState(false);
const [productoSeleccionado, setProductoSeleccionado] = useState(null);

const abrirModalVenta = (producto) => {
  setProductoSeleccionado(producto);
  setModalVentaAbierto(true);
};

const handleVentaExitosa = () => {
  // Recargar lista de productos
  cargarProductosEnBodega();
};

return (
  <div>
    {/* ... tabla de productos ... */}
    
    {modalVentaAbierto && (
      <ModalVenta
        producto={productoSeleccionado}
        bodegaId={bodegaSeleccionada}
        onVentaExitosa={handleVentaExitosa}
        onClose={() => setModalVentaAbierto(false)}
      />
    )}
  </div>
);
```

---

## 📥 Registrar Ingreso

### ¿Dónde Usar?

- Al recibir mercancía de proveedores
- Al realizar ajustes de inventario
- Al procesar devoluciones

### Endpoint a Usar

```
POST /api/v1/inventory/movements
```

### Implementación

```jsx
// components/ModalIngreso.jsx
const ModalIngreso = ({ productoId, bodegaId, onIngresoExitoso, onClose }) => {
  const [formData, setFormData] = useState({
    cantidad: 0,
    lote: '',
    fecha_vencimiento: '',
    motivo: 'COMPRA',
    referencia_documento: '',
    observaciones: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const motivos = [
    { value: 'COMPRA', label: 'Compra a Proveedor' },
    { value: 'DEVOLUCION', label: 'Devolución de Cliente' },
    { value: 'AJUSTE', label: 'Ajuste de Inventario' },
    { value: 'PRODUCCION', label: 'Producción Interna' }
  ];
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const movimiento = {
        producto_id: productoId,
        bodega_id: bodegaId,
        pais: 'CO', // Obtener del contexto
        lote: formData.lote || `LOTE-${Date.now()}`,
        tipo_movimiento: 'INGRESO',
        motivo: formData.motivo,
        cantidad: formData.cantidad,
        fecha_vencimiento: formData.fecha_vencimiento || null,
        usuario_id: localStorage.getItem('userId'),
        referencia_documento: formData.referencia_documento,
        observaciones: formData.observaciones
      };
      
      const resultado = await api.post('/inventory/movements', movimiento);
      
      alert(`✅ Ingreso registrado!
      
Stock anterior: ${resultado.saldo_anterior}
Stock nuevo: ${resultado.saldo_nuevo}
      `);
      
      onIngresoExitoso();
      onClose();
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="modal-overlay">
      <div className="modal-ingreso">
        <h2>📥 Registrar Ingreso</h2>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Cantidad: *</label>
            <input
              type="number"
              min="1"
              required
              value={formData.cantidad}
              onChange={(e) => setFormData({...formData, cantidad: parseInt(e.target.value)})}
            />
          </div>
          
          <div className="form-group">
            <label>Lote:</label>
            <input
              type="text"
              placeholder="Se generará automáticamente si está vacío"
              value={formData.lote}
              onChange={(e) => setFormData({...formData, lote: e.target.value})}
            />
          </div>
          
          <div className="form-group">
            <label>Fecha de Vencimiento:</label>
            <input
              type="date"
              value={formData.fecha_vencimiento}
              onChange={(e) => setFormData({...formData, fecha_vencimiento: e.target.value})}
            />
          </div>
          
          <div className="form-group">
            <label>Motivo: *</label>
            <select
              required
              value={formData.motivo}
              onChange={(e) => setFormData({...formData, motivo: e.target.value})}
            >
              {motivos.map(m => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>
          
          <div className="form-group">
            <label>Documento de Referencia:</label>
            <input
              type="text"
              placeholder="Ej: PO-2024-001"
              value={formData.referencia_documento}
              onChange={(e) => setFormData({...formData, referencia_documento: e.target.value})}
            />
          </div>
          
          <div className="form-group">
            <label>Observaciones:</label>
            <textarea
              rows="3"
              value={formData.observaciones}
              onChange={(e) => setFormData({...formData, observaciones: e.target.value})}
            />
          </div>
          
          {error && <p className="error">{error}</p>}
          
          <div className="modal-actions">
            <button type="submit" disabled={loading}>
              {loading ? 'Procesando...' : '✓ Registrar Ingreso'}
            </button>
            <button type="button" onClick={onClose}>Cancelar</button>
          </div>
        </form>
      </div>
    </div>
  );
};
```

---

## 📜 Ver Kardex/Historial

### Endpoint a Usar

```
GET /api/v1/inventory/movements/kardex
```

### Implementación

```jsx
// components/ModalKardex.jsx
const ModalKardex = ({ productoId, productoNombre, onClose }) => {
  const [movimientos, setMovimientos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filtros, setFiltros] = useState({
    tipo: '', // INGRESO, SALIDA, TRANSFERENCIA
    motivo: '',
    fecha_desde: '',
    fecha_hasta: ''
  });
  
  useEffect(() => {
    cargarKardex();
  }, [filtros]);
  
  const cargarKardex = async () => {
    setLoading(true);
    
    try {
      const params = {
        producto_id: productoId,
        size: 50,
        ...filtros
      };
      
      // Limpiar parámetros vacíos
      Object.keys(params).forEach(key => {
        if (params[key] === '') delete params[key];
      });
      
      const data = await api.get('/inventory/movements/kardex', params);
      setMovimientos(data.items || []);
    } catch (err) {
      console.error('Error cargando kardex:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const getTipoColor = (tipo) => {
    switch (tipo) {
      case 'INGRESO': return 'green';
      case 'SALIDA': return 'red';
      case 'TRANSFERENCIA': return 'blue';
      default: return 'gray';
    }
  };
  
  return (
    <div className="modal-overlay">
      <div className="modal-kardex">
        <h2>📜 Kardex - {productoNombre}</h2>
        
        {/* Filtros */}
        <div className="filtros-kardex">
          <select 
            value={filtros.tipo}
            onChange={(e) => setFiltros({...filtros, tipo: e.target.value})}
          >
            <option value="">Todos los tipos</option>
            <option value="INGRESO">Ingresos</option>
            <option value="SALIDA">Salidas</option>
            <option value="TRANSFERENCIA">Transferencias</option>
          </select>
          
          <input
            type="date"
            placeholder="Desde"
            value={filtros.fecha_desde}
            onChange={(e) => setFiltros({...filtros, fecha_desde: e.target.value})}
          />
          
          <input
            type="date"
            placeholder="Hasta"
            value={filtros.fecha_hasta}
            onChange={(e) => setFiltros({...filtros, fecha_hasta: e.target.value})}
          />
        </div>
        
        {/* Tabla de movimientos */}
        {loading ? (
          <p>Cargando historial...</p>
        ) : (
          <table className="kardex-tabla">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Tipo</th>
                <th>Motivo</th>
                <th>Cantidad</th>
                <th>Saldo Anterior</th>
                <th>Saldo Nuevo</th>
                <th>Usuario</th>
                <th>Documento</th>
              </tr>
            </thead>
            <tbody>
              {movimientos.map(mov => (
                <tr key={mov.id}>
                  <td>{new Date(mov.created_at).toLocaleString()}</td>
                  <td>
                    <span 
                      className="badge"
                      style={{ backgroundColor: getTipoColor(mov.tipo_movimiento) }}
                    >
                      {mov.tipo_movimiento}
                    </span>
                  </td>
                  <td>{mov.motivo}</td>
                  <td className={mov.tipo_movimiento === 'SALIDA' ? 'negativo' : 'positivo'}>
                    {mov.tipo_movimiento === 'SALIDA' ? '-' : '+'}{mov.cantidad}
                  </td>
                  <td>{mov.saldo_anterior}</td>
                  <td><strong>{mov.saldo_nuevo}</strong></td>
                  <td>{mov.usuario_id}</td>
                  <td>{mov.referencia_documento || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        
        {!loading && movimientos.length === 0 && (
          <p>No hay movimientos registrados</p>
        )}
        
        <button onClick={onClose}>Cerrar</button>
      </div>
    </div>
  );
};
```

---

## ⚠️ Manejo de Errores

### Errores Comunes

```javascript
// utils/errorHandler.js
export const handleInventoryError = (error) => {
  // Parsear mensaje de error del backend
  const message = error.message || error.toString();
  
  // Errores conocidos
  if (message.includes('STOCK_INSUFICIENTE')) {
    return {
      title: 'Stock Insuficiente',
      message: 'No hay suficiente stock para realizar esta operación',
      type: 'warning'
    };
  }
  
  if (message.includes('PRODUCTO_NO_EXISTE')) {
    return {
      title: 'Producto No Encontrado',
      message: 'El producto no existe en el sistema',
      type: 'error'
    };
  }
  
  if (message.includes('BODEGA_NO_EXISTE')) {
    return {
      title: 'Bodega No Encontrada',
      message: 'La bodega especificada no existe',
      type: 'error'
    };
  }
  
  if (message.includes('Network')) {
    return {
      title: 'Error de Conexión',
      message: 'No se pudo conectar con el servidor. Verifica tu conexión.',
      type: 'error'
    };
  }
  
  // Error genérico
  return {
    title: 'Error',
    message: message || 'Ocurrió un error inesperado',
    type: 'error'
  };
};
```

### Uso en Componentes

```jsx
import { handleInventoryError } from '../utils/errorHandler';

// En tu catch:
catch (err) {
  const errorInfo = handleInventoryError(err);
  
  // Mostrar con tu librería de notificaciones
  toast.error(errorInfo.title, {
    description: errorInfo.message
  });
  
  // O con alert
  alert(`${errorInfo.title}\n\n${errorInfo.message}`);
}
```

---

## 📊 Resumen de Uso por Vista

### Vista "Productos" (Catálogo General)

```javascript
// ✅ Usar estos endpoints:
GET /api/v1/catalog/items                           // Listar todos los productos
GET /api/v1/catalog/items/{id}                      // Ver detalle de producto
GET /api/v1/catalog/items/{id}/inventario           // Ver dónde está disponible
POST /api/v1/catalog/items                          // Crear nuevo producto
```

**Objetivo:** Gestionar el catálogo general de productos (CRUD de productos).

---

### Vista "Inventario" (Vista de Bodega)

```javascript
// ✅ Usar estos endpoints:
GET /api/v1/inventory/bodega/{bodega_id}/productos  // ⭐ NUEVO - QUÉ hay en esta bodega
POST /api/v1/inventory/movements                    // Registrar VENTA (salida)
POST /api/v1/inventory/movements                    // Registrar INGRESO
GET /api/v1/inventory/movements/kardex              // Ver historial
GET /api/v1/inventory/alerts                        // Ver alertas de stock
```

**Objetivo:** Gestionar movimientos de inventario (ingresos, ventas, transferencias).

---

## 🎯 Flujo Completo: De la Búsqueda a la Venta

```
1. Usuario entra a "Inventario"
   └─> Selecciona bodega: "BOG_CENTRAL"
   └─> GET /inventory/bodega/BOG_CENTRAL/productos
   └─> Ve lista de productos disponibles

2. Usuario busca producto "Amoxicilina"
   └─> Filtra localmente la lista o hace nueva llamada con filtro

3. Usuario hace clic en "Vender"
   └─> Abre modal con info del producto
   └─> Ingresa cantidad: 50

4. Usuario confirma venta
   └─> POST /inventory/movements
       {
         producto_id: "PROD007",
         bodega_id: "BOG_CENTRAL",
         tipo_movimiento: "SALIDA",
         motivo: "VENTA",
         cantidad: 50
       }
   └─> Backend actualiza stock automáticamente
   └─> Retorna: saldo_anterior: 100, saldo_nuevo: 50

5. Sistema recarga inventario
   └─> GET /inventory/bodega/BOG_CENTRAL/productos
   └─> Ahora muestra: cantidad: 50 ✅

6. Usuario puede ver historial
   └─> GET /inventory/movements/kardex?producto_id=PROD007
   └─> Ve la venta recién registrada
```

---

## 📚 Recursos Adicionales

### Documentación Completa

- `ACLARACION-ENDPOINTS-INVENTARIO.md` - Diferencia entre endpoints
- `ENDPOINTS-INVENTARIO.md` - Documentación técnica completa
- `GUIA-INVENTARIO-INICIAL.md` - Crear productos con inventario

### Swagger/OpenAPI

Visita: `http://localhost:3001/docs`

### Testing

```bash
# Probar endpoints directamente
curl http://localhost:3001/api/inventory/bodega/BOG_CENTRAL/productos
curl http://localhost:3001/api/catalog/items/PROD007/inventario
```

---

## 🎉 ¡Todo Listo!

Ahora tienes:
- ✅ Configuración de API
- ✅ Vista de Productos (Catálogo)
- ✅ Vista de Inventario (Por Bodega) ⭐ NUEVO
- ✅ Registrar Ventas
- ✅ Registrar Ingresos
- ✅ Ver Kardex
- ✅ Manejo de Errores

**Empieza por implementar la Vista de Inventario usando el NUEVO endpoint** `/inventory/bodega/{id}/productos` 🚀

