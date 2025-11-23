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
    
    Returns:
        JSON con lista de bodegas y sus estadísticas
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    # Remover /catalog del catalogo_url para bodegas (similar a proveedores)
    # El ALB debe tener una regla para /api/v1/bodegas/*
    base_url = catalogo_url.replace('/catalog', '')
    url = f"{base_url}/api/v1/bodegas"
    
    # Extraer query parameters
    params = {}
    if 'pais' in request.args:
        params['pais'] = request.args.get('pais')
    
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

