"""
Blueprint para gestión de bodegas (warehouses).
Actúa como proxy hacia el catalogo-service.
"""

from flask import Blueprint, request, jsonify, current_app
import requests
import os
from app.utils.logger import logger

bp = Blueprint('bodega', __name__)


def get_catalogo_service_url():
    """Obtener la URL del servicio de catálogo desde variables de entorno"""
    url = os.getenv("CATALOGO_SERVICE_URL")
    if not url:
        current_app.logger.error("CATALOGO_SERVICE_URL no está configurada")
        return None
    return url.rstrip('/')  # Remover trailing slash si existe


@bp.route('/api/v1/bodegas', methods=['GET'])
def listar_bodegas():
    """
    Proxy para listar todas las bodegas desde catalogo-service.
    
    Query Parameters:
        - pais (opcional): Filtrar por país (código ISO 2 letras)
        - activo (opcional): Filtrar por estado activo/inactivo
        - tipo (opcional): Filtrar por tipo (PRINCIPAL, SECUNDARIA, TRANSITO)
        - page (opcional): Número de página (default: 1)
        - size (opcional): Tamaño de página (default: 50)
    
    Returns:
        JSON con lista de bodegas y paginación
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    # Remover /catalog del catalogo_url para bodegas (similar a proveedores)
    base_url = catalogo_url.replace('/catalog', '')
    url = f"{base_url}/api/v1/bodegas"
    
    # Extraer todos los query parameters
    params = {key: value for key, value in request.args.items()}
    
    try:
        logger.info(f"[BFF-Venta] Proxy GET bodegas → {url}")
        logger.debug(f"[BFF-Venta] Query params: {params}")
        
        response = requests.get(
            url,
            params=params,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        logger.info(f"[BFF-Venta] Response status: {response.status_code}")
        
        return jsonify(response.json()), response.status_code
    
    except requests.exceptions.Timeout:
        logger.error("[BFF-Venta] Timeout al conectar con catalogo-service")
        return jsonify(
            error="TIMEOUT",
            message="El servicio de catálogo no respondió a tiempo"
        ), 504
    
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[BFF-Venta] Error de conexión: {str(e)}")
        return jsonify(
            error="CONNECTION_ERROR",
            message="No se pudo conectar con el servicio de catálogo"
        ), 503
    
    except requests.exceptions.RequestException as e:
        logger.error(f"[BFF-Venta] Error en request: {str(e)}")
        return jsonify(
            error="REQUEST_ERROR",
            message=f"Error al comunicarse con catalogo-service: {str(e)}"
        ), 500
    
    except Exception as e:
        logger.error(f"[BFF-Venta] Error inesperado: {str(e)}", exc_info=True)
        return jsonify(
            error="INTERNAL_ERROR",
            message="Error interno del servidor"
        ), 500


@bp.route('/api/v1/bodegas', methods=['POST'])
def crear_bodega():
    """
    Proxy para crear una nueva bodega en catalogo-service.
    
    Body (JSON):
        {
            "codigo": "BOG_SUR",
            "nombre": "Bodega Sur Bogotá",
            "pais": "CO",
            "direccion": "Av. Boyacá #45-78",
            "ciudad": "Bogotá",
            "responsable": "Juan Pérez",
            "telefono": "+57 301 555 0123",
            "email": "bodega.sur@medisupply.com",
            "tipo": "PRINCIPAL",
            "notas": "Bodega principal para zona sur"
        }
    
    Returns:
        JSON con los datos de la bodega creada
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    # Remover /catalog del catalogo_url
    base_url = catalogo_url.replace('/catalog', '')
    url = f"{base_url}/api/v1/bodegas"
    
    # Obtener datos del body
    try:
        data = request.get_json()
        if not data:
            return jsonify(
                error="INVALID_REQUEST",
                message="El body debe ser un JSON válido"
            ), 400
    except Exception as e:
        return jsonify(
            error="INVALID_JSON",
            message=f"Error al parsear JSON: {str(e)}"
        ), 400
    
    try:
        logger.info(f"[BFF-Venta] Proxy POST bodega → {url}")
        logger.debug(f"[BFF-Venta] Data: {data}")
        
        response = requests.post(
            url,
            json=data,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        logger.info(f"[BFF-Venta] Response status: {response.status_code}")
        
        return jsonify(response.json()), response.status_code
    
    except requests.exceptions.Timeout:
        logger.error("[BFF-Venta] Timeout al conectar con catalogo-service")
        return jsonify(
            error="TIMEOUT",
            message="El servicio de catálogo no respondió a tiempo"
        ), 504
    
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[BFF-Venta] Error de conexión: {str(e)}")
        return jsonify(
            error="CONNECTION_ERROR",
            message="No se pudo conectar con el servicio de catálogo"
        ), 503
    
    except requests.exceptions.RequestException as e:
        logger.error(f"[BFF-Venta] Error en request: {str(e)}")
        return jsonify(
            error="REQUEST_ERROR",
            message=f"Error al comunicarse con catalogo-service: {str(e)}"
        ), 500
    
    except Exception as e:
        logger.error(f"[BFF-Venta] Error inesperado: {str(e)}", exc_info=True)
        return jsonify(
            error="INTERNAL_ERROR",
            message="Error interno del servidor"
        ), 500
