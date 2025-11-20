"""
Rutas de vendedor para el BFF-Cliente
Proxy hacia cliente-service para gestión de vendedores
"""
from flask import Blueprint, jsonify, request, current_app
import requests
from requests.exceptions import Timeout, RequestException
import os
import logging

bp = Blueprint('vendedor', __name__)
logger = logging.getLogger(__name__)


def get_cliente_service_url():
    """Obtiene la URL del cliente-service desde variables de entorno"""
    url = os.getenv('CLIENTE_SERVICE_URL')
    if not url:
        current_app.logger.error("CLIENTE_SERVICE_URL no está configurada")
        return None
    return url.rstrip('/')


@bp.route('/api/v1/vendedores/', methods=['GET'])
def listar_vendedores():
    """
    Lista todos los vendedores con paginación
    Proxy hacia cliente-service
    """
    cliente_url = get_cliente_service_url()
    if not cliente_url:
        return jsonify(error="Servicio de clientes no disponible"), 503
    
    try:
        # Construir parámetros de query
        params = {}
        if request.args.get('page'):
            params['page'] = request.args.get('page')
        if request.args.get('size'):
            params['size'] = request.args.get('size')
        if request.args.get('activo'):
            params['activo'] = request.args.get('activo')
        
        # Construir URL
        url = f"{cliente_url}/api/vendedores/"
        
        current_app.logger.info(f"Calling cliente-service: {url} with params: {params}")
        
        # Hacer request al servicio
        response = requests.get(
            url,
            params=params,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        # Retornar respuesta del servicio
        return jsonify(response.json()), response.status_code
        
    except Timeout:
        current_app.logger.error("Timeout al llamar cliente-service")
        return jsonify(error="Timeout al conectar con servicio de clientes"), 504
    except RequestException as e:
        current_app.logger.error(f"Error al llamar cliente-service: {str(e)}")
        return jsonify(error="Error al conectar con servicio de clientes"), 503


@bp.route('/api/v1/vendedores/', methods=['POST'])
def crear_vendedor():
    """
    Crea un nuevo vendedor (con o sin plan de venta)
    Proxy hacia cliente-service
    """
    cliente_url = get_cliente_service_url()
    if not cliente_url:
        return jsonify(error="Servicio de clientes no disponible"), 503
    
    try:
        # Obtener datos del body
        data = request.get_json()
        if not data:
            return jsonify(error="Body vacío"), 400
        
        # Construir URL
        url = f"{cliente_url}/api/vendedores/"
        
        current_app.logger.info(f"Creating vendedor at: {url}")
        
        # Hacer request al servicio
        response = requests.post(
            url,
            json=data,
            timeout=15,  # Mayor timeout para creación
            headers={'Content-Type': 'application/json'}
        )
        
        # Retornar respuesta del servicio
        return jsonify(response.json()), response.status_code
        
    except Timeout:
        current_app.logger.error("Timeout al crear vendedor")
        return jsonify(error="Timeout al conectar con servicio de clientes"), 504
    except RequestException as e:
        current_app.logger.error(f"Error al crear vendedor: {str(e)}")
        return jsonify(error="Error al conectar con servicio de clientes"), 503


@bp.route('/api/v1/vendedores/<string:vendedor_id>', methods=['GET'])
def obtener_vendedor(vendedor_id):
    """
    Obtiene un vendedor por ID (básico, con plan_venta_id)
    Proxy hacia cliente-service
    """
    cliente_url = get_cliente_service_url()
    if not cliente_url:
        return jsonify(error="Servicio de clientes no disponible"), 503
    
    try:
        # Construir URL
        url = f"{cliente_url}/api/vendedores/{vendedor_id}"
        
        current_app.logger.info(f"Getting vendedor: {url}")
        
        # Hacer request al servicio
        response = requests.get(
            url,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        # Retornar respuesta del servicio
        return jsonify(response.json()), response.status_code
        
    except Timeout:
        current_app.logger.error("Timeout al obtener vendedor")
        return jsonify(error="Timeout al conectar con servicio de clientes"), 504
    except RequestException as e:
        current_app.logger.error(f"Error al obtener vendedor: {str(e)}")
        return jsonify(error="Error al conectar con servicio de clientes"), 503


@bp.route('/api/v1/vendedores/<string:vendedor_id>/detalle', methods=['GET'])
def obtener_vendedor_detalle(vendedor_id):
    """
    Obtiene el detalle completo de un vendedor con plan de venta nested
    Proxy hacia cliente-service
    """
    cliente_url = get_cliente_service_url()
    if not cliente_url:
        return jsonify(error="Servicio de clientes no disponible"), 503
    
    try:
        # Construir URL
        url = f"{cliente_url}/api/vendedores/{vendedor_id}/detalle"
        
        current_app.logger.info(f"Getting vendedor detalle: {url}")
        
        # Hacer request al servicio
        response = requests.get(
            url,
            timeout=15,  # Mayor timeout para detalle completo
            headers={'Content-Type': 'application/json'}
        )
        
        # Retornar respuesta del servicio
        return jsonify(response.json()), response.status_code
        
    except Timeout:
        current_app.logger.error("Timeout al obtener vendedor detalle")
        return jsonify(error="Timeout al conectar con servicio de clientes"), 504
    except RequestException as e:
        current_app.logger.error(f"Error al obtener vendedor detalle: {str(e)}")
        return jsonify(error="Error al conectar con servicio de clientes"), 503


@bp.route('/api/v1/vendedores/<string:vendedor_id>', methods=['PUT'])
def actualizar_vendedor(vendedor_id):
    """
    Actualiza un vendedor existente
    Proxy hacia cliente-service
    """
    cliente_url = get_cliente_service_url()
    if not cliente_url:
        return jsonify(error="Servicio de clientes no disponible"), 503
    
    try:
        # Obtener datos del body
        data = request.get_json()
        if not data:
            return jsonify(error="Body vacío"), 400
        
        # Construir URL
        url = f"{cliente_url}/api/vendedores/{vendedor_id}"
        
        current_app.logger.info(f"Updating vendedor: {url}")
        
        # Hacer request al servicio
        response = requests.put(
            url,
            json=data,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        # Retornar respuesta del servicio
        return jsonify(response.json()), response.status_code
        
    except Timeout:
        current_app.logger.error("Timeout al actualizar vendedor")
        return jsonify(error="Timeout al conectar con servicio de clientes"), 504
    except RequestException as e:
        current_app.logger.error(f"Error al actualizar vendedor: {str(e)}")
        return jsonify(error="Error al conectar con servicio de clientes"), 503


@bp.route('/api/v1/vendedores/<string:vendedor_id>', methods=['DELETE'])
def eliminar_vendedor(vendedor_id):
    """
    Elimina (soft delete) un vendedor
    Proxy hacia cliente-service
    """
    cliente_url = get_cliente_service_url()
    if not cliente_url:
        return jsonify(error="Servicio de clientes no disponible"), 503
    
    try:
        # Construir URL
        url = f"{cliente_url}/api/vendedores/{vendedor_id}"
        
        current_app.logger.info(f"Deleting vendedor: {url}")
        
        # Hacer request al servicio
        response = requests.delete(
            url,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        # Retornar respuesta del servicio
        return jsonify(response.json()), response.status_code
        
    except Timeout:
        current_app.logger.error("Timeout al eliminar vendedor")
        return jsonify(error="Timeout al conectar con servicio de clientes"), 504
    except RequestException as e:
        current_app.logger.error(f"Error al eliminar vendedor: {str(e)}")
        return jsonify(error="Error al conectar con servicio de clientes"), 503


@bp.route('/api/v1/vendedores/<string:vendedor_id>/clientes', methods=['GET'])
def listar_clientes_vendedor(vendedor_id):
    """
    Lista los clientes asociados a un vendedor
    Proxy hacia cliente-service
    """
    cliente_url = get_cliente_service_url()
    if not cliente_url:
        return jsonify(error="Servicio de clientes no disponible"), 503
    
    try:
        # Construir parámetros de query
        params = {}
        if request.args.get('page'):
            params['page'] = request.args.get('page')
        if request.args.get('size'):
            params['size'] = request.args.get('size')
        
        # Construir URL
        url = f"{cliente_url}/api/vendedores/{vendedor_id}/clientes"
        
        current_app.logger.info(f"Getting clientes for vendedor: {url}")
        
        # Hacer request al servicio
        response = requests.get(
            url,
            params=params,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        # Retornar respuesta del servicio
        return jsonify(response.json()), response.status_code
        
    except Timeout:
        current_app.logger.error("Timeout al listar clientes del vendedor")
        return jsonify(error="Timeout al conectar con servicio de clientes"), 504
    except RequestException as e:
        current_app.logger.error(f"Error al listar clientes del vendedor: {str(e)}")
        return jsonify(error="Error al conectar con servicio de clientes"), 503


@bp.route('/api/v1/vendedores/<string:vendedor_id>/clientes/asociar', methods=['POST'])
def asociar_clientes_a_vendedor(vendedor_id):
    """
    Asocia múltiples clientes a un vendedor
    Proxy hacia cliente-service POST /api/vendedores/{vendedor_id}/clientes/asociar
    """
    cliente_url = get_cliente_service_url()
    if not cliente_url:
        return jsonify(error="Servicio de clientes no disponible"), 503
    
    try:
        # Obtener datos del body
        data = request.get_json()
        if not data:
            return jsonify(error="Body vacío"), 400
        
        if not data.get('clientes_ids'):
            return jsonify(error="Campo 'clientes_ids' es requerido"), 400
        
        # Construir URL
        url = f"{cliente_url}/api/vendedores/{vendedor_id}/clientes/asociar"
        
        current_app.logger.info(f"Asociando clientes a vendedor: POST {url}")
        current_app.logger.info(f"Clientes a asociar: {len(data['clientes_ids'])}")
        
        # Hacer request al servicio
        response = requests.post(
            url,
            json=data,
            timeout=15,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'BFF-Cliente/1.0',
                'X-Request-ID': request.headers.get("X-Request-ID", "no-id"),
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
                error="Error al asociar clientes",
                details=error_data
            ), response.status_code
        
        current_app.logger.info(f"Clientes asociados exitosamente: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error("Timeout al asociar clientes")
        return jsonify(error="Timeout al conectar con servicio de clientes"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error al asociar clientes: {str(e)}")
        return jsonify(error="Error al conectar con servicio de clientes"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado al asociar clientes: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


# ====== ENDPOINTS DE CATÁLOGOS DE SOPORTE ======

@bp.route('/api/v1/catalogos/tipos-rol', methods=['GET', 'POST'])
def catalogos_tipos_rol():
    """Proxy para tipos de rol de vendedor"""
    cliente_url = get_cliente_service_url()
    if not cliente_url:
        return jsonify(error="Servicio de clientes no disponible"), 503
    
    try:
        url = f"{cliente_url}/api/catalogos/tipos-rol"
        
        if request.method == 'GET':
            response = requests.get(url, timeout=10, headers={'Content-Type': 'application/json'})
        else:  # POST
            data = request.get_json()
            response = requests.post(url, json=data, timeout=10, headers={'Content-Type': 'application/json'})
        
        return jsonify(response.json()), response.status_code
    except Exception as e:
        current_app.logger.error(f"Error en catalogos tipos-rol: {str(e)}")
        return jsonify(error="Error al conectar con servicio de clientes"), 503


@bp.route('/api/v1/catalogos/territorios', methods=['GET', 'POST'])
def catalogos_territorios():
    """Proxy para territorios"""
    cliente_url = get_cliente_service_url()
    if not cliente_url:
        return jsonify(error="Servicio de clientes no disponible"), 503
    
    try:
        url = f"{cliente_url}/api/catalogos/territorios"
        
        if request.method == 'GET':
            response = requests.get(url, timeout=10, headers={'Content-Type': 'application/json'})
        else:  # POST
            data = request.get_json()
            response = requests.post(url, json=data, timeout=10, headers={'Content-Type': 'application/json'})
        
        return jsonify(response.json()), response.status_code
    except Exception as e:
        current_app.logger.error(f"Error en catalogos territorios: {str(e)}")
        return jsonify(error="Error al conectar con servicio de clientes"), 503


@bp.route('/api/v1/catalogos/tipos-plan', methods=['GET', 'POST'])
def catalogos_tipos_plan():
    """Proxy para tipos de plan"""
    cliente_url = get_cliente_service_url()
    if not cliente_url:
        return jsonify(error="Servicio de clientes no disponible"), 503
    
    try:
        url = f"{cliente_url}/api/catalogos/tipos-plan"
        
        if request.method == 'GET':
            response = requests.get(url, timeout=10, headers={'Content-Type': 'application/json'})
        else:  # POST
            data = request.get_json()
            response = requests.post(url, json=data, timeout=10, headers={'Content-Type': 'application/json'})
        
        return jsonify(response.json()), response.status_code
    except Exception as e:
        current_app.logger.error(f"Error en catalogos tipos-plan: {str(e)}")
        return jsonify(error="Error al conectar con servicio de clientes"), 503


@bp.route('/api/v1/catalogos/regiones', methods=['GET', 'POST'])
def catalogos_regiones():
    """Proxy para regiones"""
    cliente_url = get_cliente_service_url()
    if not cliente_url:
        return jsonify(error="Servicio de clientes no disponible"), 503
    
    try:
        url = f"{cliente_url}/api/catalogos/regiones"
        
        if request.method == 'GET':
            response = requests.get(url, timeout=10, headers={'Content-Type': 'application/json'})
        else:  # POST
            data = request.get_json()
            response = requests.post(url, json=data, timeout=10, headers={'Content-Type': 'application/json'})
        
        return jsonify(response.json()), response.status_code
    except Exception as e:
        current_app.logger.error(f"Error en catalogos regiones: {str(e)}")
        return jsonify(error="Error al conectar con servicio de clientes"), 503


@bp.route('/api/v1/catalogos/zonas', methods=['GET', 'POST'])
def catalogos_zonas():
    """Proxy para zonas"""
    cliente_url = get_cliente_service_url()
    if not cliente_url:
        return jsonify(error="Servicio de clientes no disponible"), 503
    
    try:
        url = f"{cliente_url}/api/catalogos/zonas"
        
        if request.method == 'GET':
            response = requests.get(url, timeout=10, headers={'Content-Type': 'application/json'})
        else:  # POST
            data = request.get_json()
            response = requests.post(url, json=data, timeout=10, headers={'Content-Type': 'application/json'})
        
        return jsonify(response.json()), response.status_code
    except Exception as e:
        current_app.logger.error(f"Error en catalogos zonas: {str(e)}")
        return jsonify(error="Error al conectar con servicio de clientes"), 503



