"""
Rutas de cliente para el BFF-Cliente
Proxy hacia cliente-service con llamadas directas usando requests
Siguiendo el patrón de bff-venta/catalog.py
"""
from flask import Blueprint, jsonify, request, current_app
import requests
from requests.exceptions import Timeout, RequestException
import os
import logging

bp = Blueprint('client', __name__)
logger = logging.getLogger(__name__)


def get_cliente_service_url():
    """Obtiene la URL del cliente-service desde variables de entorno"""
    url = os.getenv('CLIENTE_SERVICE_URL')
    if not url:
        current_app.logger.error("CLIENTE_SERVICE_URL no está configurada")
        return None
    return url.rstrip('/')


@bp.route('/api/v1/client/', methods=['GET'])
def listar_clientes():
    """
    Lista todos los clientes con filtros opcionales
    Proxy hacia cliente-service
    """
    cliente_url = get_cliente_service_url()
    if not cliente_url:
        return jsonify(error="Servicio de clientes no disponible"), 503
    
    try:
        # Construir parámetros de query
        params = {}
        if request.args.get('limite'):
            params['limite'] = request.args.get('limite')
        if request.args.get('offset'):
            params['offset'] = request.args.get('offset')
        if request.args.get('activos_solo'):
            params['activos_solo'] = request.args.get('activos_solo')
        if request.args.get('ordenar_por'):
            params['ordenar_por'] = request.args.get('ordenar_por')
        if request.args.get('vendedor_id'):
            params['vendedor_id'] = request.args.get('vendedor_id')
        
        # Construir URL
        url = f"{cliente_url}/api/cliente/"
        
        current_app.logger.info(f"Calling cliente service: {url} with params: {params}")
        
        response = requests.get(
            url,
            params=params,
            timeout=10,
            headers={
                "User-Agent": "BFF-Cliente/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Cliente service error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al consultar clientes",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"Cliente service success: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de clientes: {cliente_url}")
        return jsonify(error="Timeout al consultar clientes"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de clientes: {e}")
        return jsonify(error="Error de conexión con servicio de clientes"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en client endpoint: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/client/sin-vendedor', methods=['GET'])
def listar_clientes_sin_vendedor():
    """
    Lista todos los clientes que NO tienen vendedor asociado
    Proxy hacia cliente-service GET /api/cliente/sin-vendedor
    """
    cliente_url = get_cliente_service_url()
    if not cliente_url:
        return jsonify(error="Servicio de clientes no disponible"), 503
    
    try:
        # Construir parámetros de query
        params = {}
        if request.args.get('limite'):
            params['limite'] = request.args.get('limite')
        if request.args.get('offset'):
            params['offset'] = request.args.get('offset')
        if request.args.get('activos_solo'):
            params['activos_solo'] = request.args.get('activos_solo')
        
        # Construir URL
        url = f"{cliente_url}/api/cliente/sin-vendedor"
        
        current_app.logger.info(f"Calling cliente service sin-vendedor: {url} with params: {params}")
        
        response = requests.get(
            url,
            params=params,
            timeout=10,
            headers={
                "User-Agent": "BFF-Cliente/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Cliente service error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al listar clientes sin vendedor",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"Cliente service sin-vendedor success: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de clientes: {cliente_url}")
        return jsonify(error="Timeout al listar clientes sin vendedor"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de clientes: {e}")
        return jsonify(error="Error de conexión con servicio de clientes"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado listando clientes sin vendedor: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/client/', methods=['POST'])
def crear_cliente():
    """
    Crea un nuevo cliente
    Proxy hacia cliente-service POST /api/cliente/
    """
    cliente_url = get_cliente_service_url()
    if not cliente_url:
        return jsonify(error="Servicio de clientes no disponible"), 503
    
    try:
        # Obtener el body del request
        data = request.get_json()
        
        if not data:
            return jsonify(error="Body JSON requerido"), 400
        
        # Construir URL
        url = f"{cliente_url}/api/cliente/"
        
        current_app.logger.info(f"Creating cliente: POST {url}")
        
        response = requests.post(
            url,
            json=data,
            timeout=10,
            headers={
                "User-Agent": "BFF-Cliente/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
                "Content-Type": "application/json"
            }
        )
        
        # Propagar respuesta del servicio
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Cliente service error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al crear cliente",
                details=error_data
            ), response.status_code
        
        current_app.logger.info(f"Cliente created successfully: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de clientes: {cliente_url}")
        return jsonify(error="Timeout al crear cliente"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de clientes: {e}")
        return jsonify(error="Error de conexión con servicio de clientes"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado creando cliente: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/client/<string:cliente_id>', methods=['PUT'])
def actualizar_cliente(cliente_id):
    """
    Actualiza un cliente existente
    Proxy hacia cliente-service PUT /api/cliente/{cliente_id}
    """
    cliente_url = get_cliente_service_url()
    if not cliente_url:
        return jsonify(error="Servicio de clientes no disponible"), 503
    
    try:
        # Obtener el body del request
        data = request.get_json()
        
        if not data:
            return jsonify(error="Body JSON requerido"), 400
        
        # Construir URL
        url = f"{cliente_url}/api/cliente/{cliente_id}"
        
        current_app.logger.info(f"Updating cliente: PUT {url}")
        
        response = requests.put(
            url,
            json=data,
            timeout=10,
            headers={
                "User-Agent": "BFF-Cliente/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
                "Content-Type": "application/json"
            }
        )
        
        # Propagar respuesta del servicio
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Cliente service error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al actualizar cliente",
                details=error_data
            ), response.status_code
        
        current_app.logger.info(f"Cliente updated successfully: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de clientes: {cliente_url}")
        return jsonify(error="Timeout al actualizar cliente"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de clientes: {e}")
        return jsonify(error="Error de conexión con servicio de clientes"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado actualizando cliente: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/client/search', methods=['GET'])
def buscar_cliente():
    """
    Busca un cliente por NIT, nombre o código único
    Proxy hacia cliente-service
    """
    cliente_url = get_cliente_service_url()
    if not cliente_url:
        return jsonify(error="Servicio de clientes no disponible"), 503
    
    try:
        # Obtener parámetros de query
        params = {}
        if request.args.get('q'):
            params['q'] = request.args.get('q')
        if request.args.get('vendedor_id'):
            params['vendedor_id'] = request.args.get('vendedor_id')
        
        # Validar parámetro requerido
        if not params.get('q'):
            return jsonify(error="Parámetro 'q' es requerido"), 400
        
        # Construir URL
        url = f"{cliente_url}/api/cliente/search"
        
        current_app.logger.info(f"Searching cliente: {url} with params: {params}")
        
        response = requests.get(
            url,
            params=params,
            timeout=10,
            headers={
                "User-Agent": "BFF-Cliente/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
            }
        )
        
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Cliente service error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al buscar cliente",
                details=error_data
            ), response.status_code
        
        current_app.logger.info(f"Cliente search success: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de clientes: {cliente_url}")
        return jsonify(error="Timeout al buscar cliente"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de clientes: {e}")
        return jsonify(error="Error de conexión con servicio de clientes"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado buscando cliente: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/client/<string:cliente_id>/historico', methods=['GET'])
def obtener_historico_cliente(cliente_id):
    """
    Obtiene el histórico completo de un cliente
    Proxy hacia cliente-service
    """
    cliente_url = get_cliente_service_url()
    if not cliente_url:
        return jsonify(error="Servicio de clientes no disponible"), 503
    
    try:
        # Obtener parámetros de query
        params = {}
        if request.args.get('vendedor_id'):
            params['vendedor_id'] = request.args.get('vendedor_id')
        if request.args.get('limite_meses'):
            params['limite_meses'] = request.args.get('limite_meses')
        if request.args.get('incluir_devoluciones'):
            params['incluir_devoluciones'] = request.args.get('incluir_devoluciones')
        
        # Construir URL
        url = f"{cliente_url}/api/cliente/{cliente_id}/historico"
        
        current_app.logger.info(f"Getting cliente history: {url} with params: {params}")
        
        response = requests.get(
            url,
            params=params,
            timeout=10,
            headers={
                "User-Agent": "BFF-Cliente/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
            }
        )
        
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Cliente service error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al obtener histórico del cliente",
                details=error_data
            ), response.status_code
        
        current_app.logger.info(f"Cliente history success: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de clientes: {cliente_url}")
        return jsonify(error="Timeout al obtener histórico"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de clientes: {e}")
        return jsonify(error="Error de conexión con servicio de clientes"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado obteniendo histórico: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/client/health', methods=['GET'])
def client_service_health():
    """
    Health check del cliente-service
    """
    cliente_url = get_cliente_service_url()
    if not cliente_url:
        return jsonify(
            status="unhealthy",
            service="cliente-service",
            message="URL no configurada"
        ), 503
    
    try:
        url = f"{cliente_url}/api/cliente/health"
        
        response = requests.get(url, timeout=5)
        
        if response.status_code >= 400:
            return jsonify(
                status="unhealthy",
                service="cliente-service",
                message="Health check failed"
            ), 503
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"status": "healthy", "data": response.text}), response.status_code
        
    except Exception as e:
        current_app.logger.error(f"Error en health check: {e}")
        return jsonify(
            status="unhealthy",
            service="cliente-service",
            message="Health check exception",
            error=str(e)
        ), 503


@bp.route('/api/v1/client/metrics', methods=['GET'])
def obtener_metricas():
    """
    Obtiene las métricas del cliente-service
    """
    cliente_url = get_cliente_service_url()
    if not cliente_url:
        return jsonify(error="Servicio de clientes no disponible"), 503
    
    try:
        url = f"{cliente_url}/api/cliente/metrics"
        
        current_app.logger.info(f"Getting metrics: {url}")
        
        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "BFF-Cliente/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
            }
        )
        
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Cliente service error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al obtener métricas",
                details=error_data
            ), response.status_code
        
        current_app.logger.info(f"Metrics success: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de clientes: {cliente_url}")
        return jsonify(error="Timeout al obtener métricas"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de clientes: {e}")
        return jsonify(error="Error de conexión con servicio de clientes"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado obteniendo métricas: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/client/seed-data', methods=['POST'])
def seed_clientes():
    """
    Carga datos de clientes de ejemplo
    Proxy hacia cliente-service /seed-data
    """
    cliente_url = get_cliente_service_url()
    if not cliente_url:
        return jsonify(error="Servicio de clientes no disponible"), 503
    
    try:
        url = f"{cliente_url}/seed-data"
        
        current_app.logger.info(f"Cargando datos de ejemplo en clientes: POST {url}")
        
        response = requests.post(
            url,
            timeout=30
        )
        
        current_app.logger.info(f"Respuesta de seed-data: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al cargar datos de ejemplo")
        return jsonify(error="Timeout al cargar datos"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de clientes: {e}")
        return jsonify(error="Error de conexión"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado cargando datos: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500
