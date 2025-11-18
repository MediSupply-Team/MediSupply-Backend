"""
Rutas de inventario para el BFF-Venta
Proxy hacia catalogo-service endpoints de inventario
"""
from flask import Blueprint, jsonify, request, current_app
import requests
from requests.exceptions import RequestException, Timeout
import os

bp = Blueprint('inventory', __name__)


def get_catalogo_service_url():
    """Obtener la URL del servicio de catálogo desde variables de entorno"""
    url = os.getenv("CATALOGO_SERVICE_URL")
    if not url:
        current_app.logger.error("CATALOGO_SERVICE_URL no está configurada")
        return None
    return url.rstrip('/')  # Remover trailing slash si existe


@bp.route('/api/v1/inventory/movements', methods=['POST'])
def create_inventory_movement():
    """
    Registra un movimiento de inventario (ingreso/salida)
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Obtener datos del body
        movement_data = request.get_json()
        if not movement_data:
            return jsonify(error="Request body required"), 400
        
        # Construir URL
        url = f"{catalogo_url}/api/v1/inventory/movements"
        
        current_app.logger.info(f"📦 Creating inventory movement: {url}")
        current_app.logger.info(f"   Producto: {movement_data.get('producto_id')}, Tipo: {movement_data.get('tipo_movimiento')}")
        
        response = requests.post(
            url,
            json=movement_data,
            timeout=15,
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
                "Content-Type": "application/json"
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Inventory movement error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al registrar movimiento",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"✅ Movement registered: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de catálogo: {catalogo_url}")
        return jsonify(error="Timeout al registrar movimiento"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de catálogo: {e}")
        return jsonify(error="Error de conexión con servicio de catálogo"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en inventory endpoint: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/inventory/transfers', methods=['POST'])
def create_inventory_transfer():
    """
    Registra una transferencia entre bodegas
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Obtener datos del body
        transfer_data = request.get_json()
        if not transfer_data:
            return jsonify(error="Request body required"), 400
        
        # Construir URL
        url = f"{catalogo_url}/api/v1/inventory/transfers"
        
        current_app.logger.info(f"🔄 Creating inventory transfer: {url}")
        current_app.logger.info(
            f"   {transfer_data.get('bodega_origen_id')} → {transfer_data.get('bodega_destino_id')}"
        )
        
        response = requests.post(
            url,
            json=transfer_data,
            timeout=15,
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
                "Content-Type": "application/json"
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Transfer error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al registrar transferencia",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"✅ Transfer registered: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de catálogo: {catalogo_url}")
        return jsonify(error="Timeout al registrar transferencia"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de catálogo: {e}")
        return jsonify(error="Error de conexión con servicio de catálogo"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en inventory endpoint: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/inventory/movements/kardex', methods=['GET'])
def get_kardex():
    """
    Consulta el kardex (historial de movimientos) de un producto
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Construir parámetros de query
        params = {}
        
        # Parámetros requeridos/opcionales
        if request.args.get('producto_id'):
            params['producto_id'] = request.args.get('producto_id')
        if request.args.get('bodega_id'):
            params['bodega_id'] = request.args.get('bodega_id')
        if request.args.get('pais'):
            params['pais'] = request.args.get('pais')
        if request.args.get('tipo_movimiento'):
            params['tipo_movimiento'] = request.args.get('tipo_movimiento')
        if request.args.get('fecha_desde'):
            params['fecha_desde'] = request.args.get('fecha_desde')
        if request.args.get('fecha_hasta'):
            params['fecha_hasta'] = request.args.get('fecha_hasta')
        if request.args.get('page'):
            params['page'] = request.args.get('page')
        if request.args.get('size'):
            params['size'] = request.args.get('size')
        
        # Construir URL del kardex
        url = f"{catalogo_url}/api/v1/inventory/movements/kardex"
        
        current_app.logger.info(f"📊 Getting kardex: {url} with params: {params}")
        
        response = requests.get(
            url,
            params=params,
            timeout=10,
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Kardex error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al consultar kardex",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"✅ Kardex retrieved: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de catálogo: {catalogo_url}")
        return jsonify(error="Timeout al consultar kardex"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de catálogo: {e}")
        return jsonify(error="Error de conexión con servicio de catálogo"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en inventory endpoint: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/inventory/movements/<int:movimiento_id>/anular', methods=['PUT'])
def cancel_movement(movimiento_id: int):
    """
    Anula un movimiento de inventario
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Obtener datos del body
        cancel_data = request.get_json()
        if not cancel_data:
            return jsonify(error="Request body required (usuario_id, motivo_anulacion)"), 400
        
        # Construir URL
        url = f"{catalogo_url}/catalog/api/v1/inventory/movements/{movimiento_id}/anular"
        
        current_app.logger.info(f"🚫 Cancelling movement {movimiento_id}: {url}")
        
        response = requests.put(
            url,
            json=cancel_data,
            timeout=15,
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
                "Content-Type": "application/json"
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Cancel movement error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al anular movimiento",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"✅ Movement cancelled: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de catálogo: {catalogo_url}")
        return jsonify(error="Timeout al anular movimiento"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de catálogo: {e}")
        return jsonify(error="Error de conexión con servicio de catálogo"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en inventory endpoint: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/inventory/alerts', methods=['GET'])
def get_alerts():
    """
    Lista las alertas de inventario
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Construir parámetros de query
        params = {}
        
        if request.args.get('producto_id'):
            params['producto_id'] = request.args.get('producto_id')
        if request.args.get('bodega_id'):
            params['bodega_id'] = request.args.get('bodega_id')
        if request.args.get('pais'):
            params['pais'] = request.args.get('pais')
        if request.args.get('tipo_alerta'):
            params['tipo_alerta'] = request.args.get('tipo_alerta')
        if request.args.get('nivel'):
            params['nivel'] = request.args.get('nivel')
        if request.args.get('incluir_leidas'):
            params['incluir_leidas'] = request.args.get('incluir_leidas')
        if request.args.get('page'):
            params['page'] = request.args.get('page')
        if request.args.get('size'):
            params['size'] = request.args.get('size')
        
        # Construir URL
        url = f"{catalogo_url}/catalog/api/v1/inventory/alerts"
        
        current_app.logger.info(f"⚠️  Getting alerts: {url} with params: {params}")
        
        response = requests.get(
            url,
            params=params,
            timeout=10,
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Alerts error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al consultar alertas",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"✅ Alerts retrieved: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de catálogo: {catalogo_url}")
        return jsonify(error="Timeout al consultar alertas"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de catálogo: {e}")
        return jsonify(error="Error de conexión con servicio de catálogo"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en inventory endpoint: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/inventory/alerts/<int:alerta_id>/marcar-leida', methods=['PUT'])
def mark_alert_read(alerta_id: int):
    """
    Marca una alerta como leída
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Obtener usuario_id de query params
        usuario_id = request.args.get('usuario_id')
        if not usuario_id:
            return jsonify(error="usuario_id query parameter required"), 400
        
        # Construir URL con query params
        url = f"{catalogo_url}/catalog/api/v1/inventory/alerts/{alerta_id}/marcar-leida"
        
        current_app.logger.info(f"✓ Marking alert {alerta_id} as read: {url}")
        
        response = requests.put(
            url,
            params={"usuario_id": usuario_id},
            timeout=10,
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Mark alert read error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al marcar alerta como leída",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"✅ Alert marked as read: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de catálogo: {catalogo_url}")
        return jsonify(error="Timeout al marcar alerta"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de catálogo: {e}")
        return jsonify(error="Error de conexión con servicio de catálogo"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en inventory endpoint: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/inventory/reports/saldos', methods=['GET'])
def get_stock_report():
    """
    Genera reporte de saldos de inventario por bodega
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Construir parámetros de query
        params = {}
        
        if request.args.get('producto_id'):
            params['producto_id'] = request.args.get('producto_id')
        if request.args.get('bodega_id'):
            params['bodega_id'] = request.args.get('bodega_id')
        if request.args.get('pais'):
            params['pais'] = request.args.get('pais')
        if request.args.get('estado_stock'):
            params['estado_stock'] = request.args.get('estado_stock')
        if request.args.get('page'):
            params['page'] = request.args.get('page')
        if request.args.get('size'):
            params['size'] = request.args.get('size')
        
        # Construir URL
        url = f"{catalogo_url}/catalog/api/v1/inventory/reports/saldos"
        
        current_app.logger.info(f"📈 Getting stock report: {url} with params: {params}")
        
        response = requests.get(
            url,
            params=params,
            timeout=15,
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Stock report error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al generar reporte de saldos",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"✅ Stock report generated: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de catálogo: {catalogo_url}")
        return jsonify(error="Timeout al generar reporte"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de catálogo: {e}")
        return jsonify(error="Error de conexión con servicio de catálogo"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en inventory endpoint: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/inventory/bodega/<bodega_id>/productos', methods=['GET'])
def get_productos_en_bodega(bodega_id: str):
    """
    Lista todos los productos disponibles en una bodega específica
    Proxy hacia catalogo-service
    
    Query params:
    - pais: Filtrar por país (opcional)
    - con_stock: Solo productos con stock > 0 (default: true)
    - page: Número de página (default: 1)
    - size: Items por página (default: 50)
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Construir parámetros de query
        params = {}
        
        if request.args.get('pais'):
            params['pais'] = request.args.get('pais')
        if request.args.get('con_stock'):
            params['con_stock'] = request.args.get('con_stock')
        if request.args.get('page'):
            params['page'] = request.args.get('page')
        if request.args.get('size'):
            params['size'] = request.args.get('size')
        
        # Construir URL
        url = f"{catalogo_url}/catalog/api/v1/inventory/bodega/{bodega_id}/productos"
        
        current_app.logger.info(f"🏢 Getting productos en bodega {bodega_id}: {url}")
        
        response = requests.get(
            url,
            params=params,
            timeout=10,
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Get productos en bodega error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al consultar productos en bodega",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"✅ Productos en bodega retrieved: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de catálogo: {catalogo_url}")
        return jsonify(error="Timeout al consultar productos en bodega"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de catálogo: {e}")
        return jsonify(error="Error de conexión con servicio de catálogo"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en inventory endpoint: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/inventory/health', methods=['GET'])
def inventory_health_check():
    """
    Health check del módulo de inventario
    """
    catalogo_url = get_catalogo_service_url()
    
    if not catalogo_url:
        return jsonify(
            status="unhealthy",
            reason="CATALOG_SERVICE_URL no configurada"
        ), 503
    
    try:
        response = requests.get(
            f"{catalogo_url}/health",
            timeout=5
        )
        
        if response.status_code == 200:
            return jsonify(
                status="healthy",
                inventory_module="connected",
                catalog_service_url=catalogo_url
            ), 200
        else:
            return jsonify(
                status="degraded",
                inventory_module="error",
                status_code=response.status_code,
                catalog_service_url=catalogo_url
            ), 503
            
    except Timeout:
        return jsonify(
            status="unhealthy",
            inventory_module="timeout",
            catalog_service_url=catalogo_url
        ), 503
    except Exception as e:
        return jsonify(
            status="unhealthy",
            inventory_module="disconnected",
            error=str(e),
            catalog_service_url=catalogo_url
        ), 503

