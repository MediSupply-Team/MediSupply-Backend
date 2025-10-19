"""
Rutas de catálogo para el BFF-Venta
Proxy hacia catalogo-service con manejo de errores y modo mock
"""
from flask import Blueprint, jsonify, request, current_app
import asyncio
import logging
from datetime import datetime

bp = Blueprint('catalog', __name__)
logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper para ejecutar corutinas async en Flask sincrono"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def log_request(endpoint: str, method: str, params: dict = None, body: dict = None):
    """Registra la petición para auditoría (síncono, no bloquea)"""
    try:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "endpoint": endpoint,
            "method": method,
            "user_agent": request.headers.get('User-Agent', 'unknown'),
            "ip": request.remote_addr
        }
        if params:
            log_data["query_params"] = params
        if body:
            log_data["body"] = body
            
        logger.info(f"Catalog API Request: {log_data}")
    except Exception as e:
        logger.warning(f"Error logging request: {e}")


@bp.route('/api/v1/catalog/items', methods=['GET'])
def get_catalog_items():
    """Obtiene la lista de items del catálogo"""
    try:
        # Obtener parámetros de query
        params = {
            'q': request.args.get('q'),
            'categoria_id': request.args.get('categoria_id'),
            'codigo': request.args.get('codigo'),
            'pais': request.args.get('pais'),
            'bodega_id': request.args.get('bodega_id'),
            'page': int(request.args.get('page', 1)),
            'size': int(request.args.get('size', 20)),
            'sort': request.args.get('sort')
        }
        
        # Filtrar parámetros None
        filtered_params = {k: v for k, v in params.items() if v is not None}
        
        # Log de la petición
        log_request("/api/v1/catalog/items", "GET", filtered_params)
        
        # Obtener cliente de catálogo
        catalogo_client = current_app.extensions.get("catalogo")
        if not catalogo_client:
            return jsonify({"error": "Catalogo client not initialized"}), 500
        
        # Obtener datos del catalogo-service
        result = run_async(catalogo_client.get_items(**filtered_params))
        
        # Verificar si hay error
        if "error" in result:
            status_code = 500 if result.get("status", 500) != 404 else 404
            return jsonify(result), status_code
            
        return jsonify(result), 200
        
    except ValueError as e:
        logger.error(f"Error de validación en get_catalog_items: {e}")
        return jsonify({"error": "Invalid parameters", "details": str(e)}), 400
    except Exception as e:
        logger.error(f"Error en get_catalog_items: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@bp.route('/api/v1/catalog/items/<string:item_id>', methods=['GET'])
def get_catalog_item(item_id: str):
    """Obtiene un item específico del catálogo"""
    try:
        # Log de la petición
        log_request(f"/api/v1/catalog/items/{item_id}", "GET")
        
        # Obtener cliente de catálogo
        catalogo_client = current_app.extensions.get("catalogo")
        if not catalogo_client:
            return jsonify({"error": "Catalogo client not initialized"}), 500
        
        # Obtener datos del catalogo-service
        result = run_async(catalogo_client.get_item(item_id))
        
        # Verificar si hay error
        if "error" in result:
            status_code = 500 if result.get("status", 500) != 404 else 404
            return jsonify(result), status_code
            
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error en get_catalog_item: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@bp.route('/api/v1/catalog/items/<string:item_id>/inventario', methods=['GET'])
def get_item_inventory(item_id: str):
    """Obtiene el inventario de un item específico"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 50))
        
        # Log de la petición
        log_request(f"/api/v1/catalog/items/{item_id}/inventario", "GET", {"page": page, "size": size})
        
        # Obtener cliente de catálogo
        catalogo_client = current_app.extensions.get("catalogo")
        if not catalogo_client:
            return jsonify({"error": "Catalogo client not initialized"}), 500
        
        # Obtener datos del catalogo-service
        result = run_async(catalogo_client.get_item_inventory(item_id, page, size))
        
        # Verificar si hay error
        if "error" in result:
            status_code = 500 if result.get("status", 500) != 404 else 404
            return jsonify(result), status_code
            
        return jsonify(result), 200
        
    except ValueError as e:
        logger.error(f"Error de validación en get_item_inventory: {e}")
        return jsonify({"error": "Invalid parameters", "details": str(e)}), 400
    except Exception as e:
        logger.error(f"Error en get_item_inventory: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@bp.route('/api/v1/catalog/items', methods=['POST'])
def create_catalog_item():
    """Crea un nuevo item en el catálogo"""
    try:
        # Obtener datos del body
        item_data = request.get_json()
        if not item_data:
            return jsonify({"error": "Request body required"}), 400
        
        # Log de la petición
        log_request("/api/v1/catalog/items", "POST", body=item_data)
        
        # Obtener cliente de catálogo
        catalogo_client = current_app.extensions.get("catalogo")
        if not catalogo_client:
            return jsonify({"error": "Catalogo client not initialized"}), 500
        
        # Crear item en el catalogo-service
        result = run_async(catalogo_client.create_item(item_data))
        
        # Verificar si hay error
        if "error" in result:
            return jsonify(result), 500
            
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"Error en create_catalog_item: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@bp.route('/api/v1/catalog/items/<string:item_id>', methods=['PUT'])
def update_catalog_item(item_id: str):
    """Actualiza un item existente del catálogo"""
    try:
        # Obtener datos del body
        item_data = request.get_json()
        if not item_data:
            return jsonify({"error": "Request body required"}), 400
        
        # Log de la petición
        log_request(f"/api/v1/catalog/items/{item_id}", "PUT", body=item_data)
        
        # Obtener cliente de catálogo
        catalogo_client = current_app.extensions.get("catalogo")
        if not catalogo_client:
            return jsonify({"error": "Catalogo client not initialized"}), 500
        
        # Actualizar item en el catalogo-service
        result = run_async(catalogo_client.update_item(item_id, item_data))
        
        # Verificar si hay error
        if "error" in result:
            status_code = 500 if result.get("status", 500) != 404 else 404
            return jsonify(result), status_code
            
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error en update_catalog_item: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@bp.route('/api/v1/catalog/items/<string:item_id>', methods=['DELETE'])
def delete_catalog_item(item_id: str):
    """Elimina un item del catálogo"""
    try:
        # Log de la petición
        log_request(f"/api/v1/catalog/items/{item_id}", "DELETE")
        
        # Obtener cliente de catálogo
        catalogo_client = current_app.extensions.get("catalogo")
        if not catalogo_client:
            return jsonify({"error": "Catalogo client not initialized"}), 500
        
        # Eliminar item del catalogo-service
        result = run_async(catalogo_client.delete_item(item_id))
        
        # Verificar si hay error
        if "error" in result:
            status_code = 500 if result.get("status", 500) != 404 else 404
            return jsonify(result), status_code
            
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error en delete_catalog_item: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500