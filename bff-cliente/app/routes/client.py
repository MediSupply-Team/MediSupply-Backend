"""
Rutas de cliente para el BFF-Cliente
Proxy hacia cliente-service con manejo de errores y modo mock
"""
from flask import Blueprint, jsonify, request, current_app
import asyncio
import logging
from datetime import datetime

bp = Blueprint('client', __name__)
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
            
        logger.info(f"Client API Request: {log_data}")
    except Exception as e:
        logger.warning(f"Error logging request: {e}")


@bp.route('/api/v1/client/', methods=['GET'])
def listar_clientes():
    """Lista todos los clientes con filtros opcionales"""
    try:
        # Obtener parámetros de query
        params = {
            'limite': request.args.get('limite', type=int),
            'offset': request.args.get('offset', type=int),
            'activos_solo': request.args.get('activos_solo', type=bool),
            'ordenar_por': request.args.get('ordenar_por'),
            'vendedor_id': request.args.get('vendedor_id')
        }
        
        # Remover parámetros None
        params = {k: v for k, v in params.items() if v is not None}
        
        log_request('/api/v1/client/', 'GET', params)
        
        # Obtener cliente del cliente-service
        cliente_client = current_app.extensions.get("cliente")
        if not cliente_client:
            logger.error("Cliente service client not initialized")
            return jsonify({
                "error": "SERVICE_UNAVAILABLE",
                "message": "Client service is not available"
            }), 503
        
        # Llamar al cliente-service
        result = run_async(cliente_client.listar_clientes(params))
        
        if isinstance(result, dict) and "error" in result:
            logger.error(f"Error from cliente-service: {result}")
            return jsonify({
                "error": "BACKEND_ERROR", 
                "message": "Error retrieving clients",
                "details": result
            }), 500
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in listar_clientes: {e}")
        return jsonify({
            "error": "INTERNAL_ERROR",
            "message": "Internal server error"
        }), 500


@bp.route('/api/v1/client/search', methods=['GET'])
def buscar_cliente():
    """Busca un cliente por NIT, nombre o código único"""
    try:
        # Obtener parámetros de query
        params = {
            'q': request.args.get('q'),
            'vendedor_id': request.args.get('vendedor_id')
        }
        
        # Remover parámetros None
        params = {k: v for k, v in params.items() if v is not None}
        
        log_request('/api/v1/client/search', 'GET', params)
        
        # Validar que se proporcione el parámetro de búsqueda
        if not params.get('q'):
            return jsonify({
                "error": "MISSING_PARAMETER",
                "message": "Query parameter 'q' is required for search"
            }), 400
        
        # Obtener cliente del cliente-service
        cliente_client = current_app.extensions.get("cliente")
        if not cliente_client:
            logger.error("Cliente service client not initialized")
            return jsonify({
                "error": "SERVICE_UNAVAILABLE",
                "message": "Client service is not available"
            }), 503
        
        # Llamar al cliente-service
        result = run_async(cliente_client.buscar_cliente(params))
        
        if isinstance(result, dict) and "error" in result:
            if result.get("status") == 404:
                return jsonify({
                    "error": "CLIENT_NOT_FOUND",
                    "message": "No client found with the provided search criteria"
                }), 404
            
            logger.error(f"Error from cliente-service: {result}")
            return jsonify({
                "error": "BACKEND_ERROR",
                "message": "Error searching client",
                "details": result
            }), 500
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in buscar_cliente: {e}")
        return jsonify({
            "error": "INTERNAL_ERROR",
            "message": "Internal server error"
        }), 500


@bp.route('/api/v1/client/<string:cliente_id>/historico', methods=['GET'])
def obtener_historico_cliente(cliente_id):
    """Obtiene el histórico completo de un cliente"""
    try:
        # Obtener parámetros de query
        params = {
            'vendedor_id': request.args.get('vendedor_id'),
            'limite_meses': request.args.get('limite_meses', type=int)
        }
        
        # Remover parámetros None
        params = {k: v for k, v in params.items() if v is not None}
        
        log_request(f'/api/v1/client/{cliente_id}/historico', 'GET', params)
        
        # Validar que se proporcione vendedor_id (requerido según el cliente-service)
        if not params.get('vendedor_id'):
            return jsonify({
                "error": "MISSING_PARAMETER",
                "message": "Query parameter 'vendedor_id' is required"
            }), 400
        
        # Obtener cliente del cliente-service
        cliente_client = current_app.extensions.get("cliente")
        if not cliente_client:
            logger.error("Cliente service client not initialized")
            return jsonify({
                "error": "SERVICE_UNAVAILABLE",
                "message": "Client service is not available"
            }), 503
        
        # Llamar al cliente-service
        result = run_async(cliente_client.obtener_historico_cliente(cliente_id, params))
        
        if isinstance(result, dict) and "error" in result:
            if result.get("status") == 404:
                return jsonify({
                    "error": "CLIENT_NOT_FOUND",
                    "message": f"Client with id {cliente_id} not found"
                }), 404
            
            logger.error(f"Error from cliente-service: {result}")
            return jsonify({
                "error": "BACKEND_ERROR",
                "message": "Error retrieving client history",
                "details": result
            }), 500
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in obtener_historico_cliente: {e}")
        return jsonify({
            "error": "INTERNAL_ERROR",
            "message": "Internal server error"
        }), 500


@bp.route('/api/v1/client/health', methods=['GET'])
def client_service_health():
    """Health check del cliente-service"""
    try:
        log_request('/api/v1/client/health', 'GET')
        
        # Obtener cliente del cliente-service
        cliente_client = current_app.extensions.get("cliente")
        if not cliente_client:
            return jsonify({
                "status": "unhealthy",
                "service": "cliente-service",
                "message": "Client service client not initialized"
            }), 503
        
        # Llamar al cliente-service
        result = run_async(cliente_client.health_check())
        
        if isinstance(result, dict) and "error" in result:
            return jsonify({
                "status": "unhealthy",
                "service": "cliente-service", 
                "message": "Client service health check failed",
                "details": result
            }), 503
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in client_service_health: {e}")
        return jsonify({
            "status": "unhealthy",
            "service": "cliente-service",
            "message": "Health check failed with exception",
            "error": str(e)
        }), 503


@bp.route('/api/v1/client/metrics', methods=['GET'])
def obtener_metricas():
    """Obtiene las métricas del cliente-service"""
    try:
        log_request('/api/v1/client/metrics', 'GET')
        
        # Obtener cliente del cliente-service
        cliente_client = current_app.extensions.get("cliente")
        if not cliente_client:
            logger.error("Cliente service client not initialized")
            return jsonify({
                "error": "SERVICE_UNAVAILABLE",
                "message": "Client service is not available"
            }), 503
        
        # Llamar al cliente-service
        result = run_async(cliente_client.obtener_metricas())
        
        if isinstance(result, dict) and "error" in result:
            logger.error(f"Error from cliente-service: {result}")
            return jsonify({
                "error": "BACKEND_ERROR",
                "message": "Error retrieving metrics",
                "details": result
            }), 500
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in obtener_metricas: {e}")
        return jsonify({
            "error": "INTERNAL_ERROR",
            "message": "Internal server error"
        }), 500