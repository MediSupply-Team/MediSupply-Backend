"""
Rutas de catálogo para el BFF-Venta
Proxy hacia catalogo-service con manejo de errores
"""
from flask import Blueprint, jsonify, request, current_app
import requests
from requests.exceptions import RequestException, Timeout
import os

bp = Blueprint('catalog', __name__)


def get_catalogo_service_url():
    """Obtener la URL del servicio de catálogo desde variables de entorno"""
    url = os.getenv("CATALOGO_SERVICE_URL")
    if not url:
        current_app.logger.error("CATALOGO_SERVICE_URL no está configurada")
        return None
    return url.rstrip('/')  # Remover trailing slash si existe


@bp.route('/api/v1/catalog/items', methods=['GET'])
def get_catalog_items():
    """
    Obtiene la lista de items del catálogo
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Construir parámetros de query
        params = {}
        
        # Soportar tanto 'category' como 'categoriaId' para compatibilidad
        categoria = request.args.get('category') or request.args.get('categoriaId')
        if categoria:
            params['categoriaId'] = categoria
        
        # Otros parámetros
        if request.args.get('q'):
            params['q'] = request.args.get('q')
        if request.args.get('codigo'):
            params['codigo'] = request.args.get('codigo')
        if request.args.get('pais'):
            params['pais'] = request.args.get('pais')
        if request.args.get('bodegaId') or request.args.get('bodega_id'):
            params['bodegaId'] = request.args.get('bodegaId') or request.args.get('bodega_id')
        if request.args.get('page'):
            params['page'] = request.args.get('page')
        if request.args.get('size'):
            params['size'] = request.args.get('size')
        if request.args.get('sort'):
            params['sort'] = request.args.get('sort')
        
        # Construir URL
        url = f"{catalogo_url}/api/catalog/items"
        
        current_app.logger.info(f"Calling catalog service: {url} with params: {params}")
        
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
                f"Catalog service error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al consultar catálogo",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"Catalog service success: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de catálogo: {catalogo_url}")
        return jsonify(error="Timeout al consultar catálogo"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de catálogo: {e}")
        return jsonify(error="Error de conexión con servicio de catálogo"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en catalog endpoint: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/catalog/items/<string:item_id>', methods=['GET'])
def get_catalog_item(item_id: str):
    """
    Obtiene un item específico del catálogo
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Construir URL
        url = f"{catalogo_url}/api/catalog/items/{item_id}"
        
        current_app.logger.info(f"Calling catalog service: {url}")
        
        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Catalog service error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al consultar producto",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"Catalog service success: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de catálogo: {catalogo_url}")
        return jsonify(error="Timeout al consultar producto"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de catálogo: {e}")
        return jsonify(error="Error de conexión con servicio de catálogo"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en catalog endpoint: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/catalog/items/<string:item_id>/inventario', methods=['GET'])
def get_item_inventory(item_id: str):
    """
    Obtiene el inventario de un item específico
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Construir parámetros
        params = {
            'page': request.args.get('page', 1),
            'size': request.args.get('size', 50)
        }
        
        # Construir URL
        url = f"{catalogo_url}/api/catalog/items/{item_id}/inventario"
        
        current_app.logger.info(f"Calling catalog service: {url} with params: {params}")
        
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
                f"Catalog service error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al consultar inventario",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"Catalog service success: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de catálogo: {catalogo_url}")
        return jsonify(error="Timeout al consultar inventario"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de catálogo: {e}")
        return jsonify(error="Error de conexión con servicio de catálogo"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en catalog endpoint: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/catalog/items', methods=['POST'])
def create_catalog_item():
    """
    Crea un nuevo item en el catálogo
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Obtener datos del body
        item_data = request.get_json()
        if not item_data:
            return jsonify(error="Request body required"), 400
        
        # Construir URL
        url = f"{catalogo_url}/api/catalog/items"
        
        current_app.logger.info(f"Calling catalog service: {url}")
        
        response = requests.post(
            url,
            json=item_data,
            timeout=10,
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
                "Content-Type": "application/json"
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Catalog service error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al crear producto",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"Catalog service success: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de catálogo: {catalogo_url}")
        return jsonify(error="Timeout al crear producto"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de catálogo: {e}")
        return jsonify(error="Error de conexión con servicio de catálogo"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en catalog endpoint: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/catalog/items/<string:item_id>', methods=['PUT'])
def update_catalog_item(item_id: str):
    """
    Actualiza un item existente del catálogo
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Obtener datos del body
        item_data = request.get_json()
        if not item_data:
            return jsonify(error="Request body required"), 400
        
        # Construir URL
        url = f"{catalogo_url}/api/catalog/items/{item_id}"
        
        current_app.logger.info(f"Calling catalog service: {url}")
        
        response = requests.put(
            url,
            json=item_data,
            timeout=10,
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
                "Content-Type": "application/json"
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Catalog service error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al actualizar producto",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"Catalog service success: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de catálogo: {catalogo_url}")
        return jsonify(error="Timeout al actualizar producto"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de catálogo: {e}")
        return jsonify(error="Error de conexión con servicio de catálogo"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en catalog endpoint: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/catalog/items/<string:item_id>', methods=['DELETE'])
def delete_catalog_item(item_id: str):
    """
    Elimina un item del catálogo
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Construir URL
        url = f"{catalogo_url}/api/catalog/items/{item_id}"
        
        current_app.logger.info(f"Calling catalog service: {url}")
        
        response = requests.delete(
            url,
            timeout=10,
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Catalog service error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al eliminar producto",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"Catalog service success: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de catálogo: {catalogo_url}")
        return jsonify(error="Timeout al eliminar producto"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de catálogo: {e}")
        return jsonify(error="Error de conexión con servicio de catálogo"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en catalog endpoint: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/catalog/health', methods=['GET'])
def catalog_health_check():
    """
    Health check del servicio de catálogo
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
                catalog_service="connected",
                catalog_url=catalogo_url
            ), 200
        else:
            return jsonify(
                status="degraded",
                catalog_service="error",
                status_code=response.status_code,
                catalog_url=catalogo_url
            ), 503
            
    except Timeout:
        return jsonify(
            status="unhealthy",
            catalog_service="timeout",
            catalog_url=catalogo_url
        ), 503
    except Exception as e:
        return jsonify(
            status="unhealthy",
            catalog_service="disconnected",
            error=str(e),
            catalog_url=catalogo_url
        ), 503