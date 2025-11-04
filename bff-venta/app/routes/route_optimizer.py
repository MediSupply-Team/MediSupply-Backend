from flask import Blueprint, request, jsonify, current_app
import requests

bp = Blueprint("route_optimizer", __name__)


def get_optimizer_service_url():
    """
    Obtener la URL del servicio optimizador FastAPI desde configuración
    """
    url = current_app.config.get("OPTIMIZER_SERVICE_URL")
    if not url:
        current_app.logger.error("OPTIMIZER_SERVICE_URL no está configurada")
        return None
    return url.rstrip('/')


# ============================================
# ENDPOINTS QUE SÍ EXISTEN EN TU FASTAPI
# ============================================

@bp.post("/api/v1/routes/optimize")
def optimizar_pedidos():
    """
    Proxy a FastAPI optimizer - optimizar pedidos completo
    ---
    tags:
      - Route Optimizer
    summary: Optimizar ruta de entregas con pedidos
    description: |
      Endpoint completo para optimizar pedidos desde el frontend.
      
      Recibe configuración de ruta (bodega, camión, horarios) y lista de pedidos.
      Devuelve secuencia optimizada con horarios, resumen y geometría.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - configuracion
            - pedidos
          properties:
            configuracion:
              type: object
              properties:
                bodega_origen:
                  type: string
                hora_inicio:
                  type: string
                camion_capacidad_kg:
                  type: number
                camion_capacidad_m3:
                  type: number
            pedidos:
              type: array
              items:
                type: object
            costo_km:
              type: number
            costo_hora:
              type: number
    responses:
      200:
        description: Ruta optimizada exitosamente
      400:
        description: Error de validación
      500:
        description: Error interno
    """
    optimizer_url = get_optimizer_service_url()
    if not optimizer_url:
        return jsonify(error="Servicio optimizador no disponible"), 503
    
    data = request.get_json(silent=True)
    if data is None:
        return jsonify(error="Body JSON requerido"), 400
    
    try:
        response = requests.post(
            f"{optimizer_url}/api/v1/optimize/pedidos",
            json=data,
            timeout=60
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.HTTPError as e:
        if e.response is not None:
            try:
                return jsonify(e.response.json()), e.response.status_code
            except:
                return jsonify(error=e.response.text), e.response.status_code
        return jsonify(error="Error en optimización"), 500
    except requests.exceptions.Timeout:
        return jsonify(error="Timeout en optimización"), 504
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error: {e}")
        return jsonify(error="Error conectando con optimizador"), 503


@bp.post("/api/v1/optimize/route")
def optimizar_ruta():
    """
    Proxy a FastAPI optimizer - optimizar ruta simple
    ---
    tags:
      - Route Optimizer
    summary: Optimizar ruta de entregas
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - bodega
            - paradas
          properties:
            bodega:
              type: object
            paradas:
              type: array
            retorna_bodega:
              type: boolean
    """
    optimizer_url = get_optimizer_service_url()
    if not optimizer_url:
        return jsonify(error="Servicio optimizador no disponible"), 503
    
    data = request.get_json(silent=True)
    if data is None:
        return jsonify(error="Body JSON requerido"), 400
    
    try:
        response = requests.post(
            f"{optimizer_url}/api/v1/optimize/route",
            json=data,
            timeout=30
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.HTTPError as e:
        if e.response is not None:
            try:
                return jsonify(e.response.json()), e.response.status_code
            except:
                return jsonify(error=e.response.text), e.response.status_code
        return jsonify(error="Error optimizando ruta"), 500
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error: {e}")
        return jsonify(error="Error conectando con optimizador"), 503


@bp.post("/api/v1/optimize/from-service")
def optimizar_desde_servicio():
    """
    Proxy a FastAPI optimizer - obtener visitas de ruta-service y optimizar
    ---
    tags:
      - Route Optimizer
    summary: Optimizar desde servicio de rutas
    parameters:
      - in: query
        name: fecha
        type: string
        required: true
        description: Fecha en formato YYYY-MM-DD
      - in: query
        name: vendedor_id
        type: integer
        required: true
        description: ID del vendedor
    """
    optimizer_url = get_optimizer_service_url()
    if not optimizer_url:
        return jsonify(error="Servicio optimizador no disponible"), 503
    
    try:
        response = requests.post(
            f"{optimizer_url}/api/v1/optimize/from-service",
            params=request.args,
            timeout=30
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.HTTPError as e:
        if e.response is not None:
            try:
                return jsonify(e.response.json()), e.response.status_code
            except:
                return jsonify(error=e.response.text), e.response.status_code
        return jsonify(error="Error optimizando desde servicio"), 500
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error: {e}")
        return jsonify(error="Error conectando con optimizador"), 503


@bp.post("/api/v1/geocode")
def geocodificar():
    """
    Proxy a FastAPI optimizer - geocodificar dirección
    ---
    tags:
      - Route Optimizer
    summary: Convertir dirección a coordenadas
    parameters:
      - in: query
        name: direccion
        type: string
        required: true
        description: Dirección a geocodificar
      - in: query
        name: ciudad
        type: string
        description: Ciudad (default Bogotá)
    """
    optimizer_url = get_optimizer_service_url()
    if not optimizer_url:
        return jsonify(error="Servicio optimizador no disponible"), 503
    
    try:
        response = requests.post(
            f"{optimizer_url}/api/v1/geocode",
            params=request.args,
            timeout=10
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.HTTPError as e:
        if e.response is not None:
            try:
                return jsonify(e.response.json()), e.response.status_code
            except:
                return jsonify(error=e.response.text), e.response.status_code
        return jsonify(error="Error geocodificando"), 500
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error: {e}")
        return jsonify(error="Error conectando con optimizador"), 503


@bp.post("/api/v1/geocode/batch")
def geocodificar_batch():
    """
    Proxy a FastAPI optimizer - geocodificar múltiples direcciones
    ---
    tags:
      - Route Optimizer
    summary: Geocodificar batch de direcciones
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            direcciones:
              type: array
              items:
                type: string
    """
    optimizer_url = get_optimizer_service_url()
    if not optimizer_url:
        return jsonify(error="Servicio optimizador no disponible"), 503
    
    data = request.get_json(silent=True)
    if data is None:
        return jsonify(error="Body JSON requerido"), 400
    
    try:
        response = requests.post(
            f"{optimizer_url}/api/v1/geocode/batch",
            json=data,
            timeout=15
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.HTTPError as e:
        if e.response is not None:
            try:
                return jsonify(e.response.json()), e.response.status_code
            except:
                return jsonify(error=e.response.text), e.response.status_code
        return jsonify(error="Error geocodificando batch"), 500
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error: {e}")
        return jsonify(error="Error conectando con optimizador"), 503


@bp.post("/api/v1/route/calculate")
def calcular_ruta():
    """
    Proxy a FastAPI optimizer - calcular ruta entre dos puntos
    ---
    tags:
      - Route Optimizer
    summary: Calcular ruta entre origen y destino
    parameters:
      - in: query
        name: origen_lat
        type: number
        required: true
      - in: query
        name: origen_lon
        type: number
        required: true
      - in: query
        name: destino_lat
        type: number
        required: true
      - in: query
        name: destino_lon
        type: number
        required: true
    """
    optimizer_url = get_optimizer_service_url()
    if not optimizer_url:
        return jsonify(error="Servicio optimizador no disponible"), 503
    
    try:
        response = requests.post(
            f"{optimizer_url}/api/v1/route/calculate",
            params=request.args,
            timeout=10
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.HTTPError as e:
        if e.response is not None:
            try:
                return jsonify(e.response.json()), e.response.status_code
            except:
                return jsonify(error=e.response.text), e.response.status_code
        return jsonify(error="Error calculando ruta"), 500
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error: {e}")
        return jsonify(error="Error conectando con optimizador"), 503


@bp.post("/api/v1/route/matrix")
def calcular_matriz():
    """
    Proxy a FastAPI optimizer - calcular matriz de distancias
    ---
    tags:
      - Route Optimizer
    summary: Calcular matriz de distancias entre múltiples puntos
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: array
          items:
            type: object
    """
    optimizer_url = get_optimizer_service_url()
    if not optimizer_url:
        return jsonify(error="Servicio optimizador no disponible"), 503
    
    data = request.get_json(silent=True)
    if data is None:
        return jsonify(error="Body JSON requerido"), 400
    
    try:
        response = requests.post(
            f"{optimizer_url}/api/v1/route/matrix",
            json=data,
            timeout=15
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.HTTPError as e:
        if e.response is not None:
            try:
                return jsonify(e.response.json()), e.response.status_code
            except:
                return jsonify(error=e.response.text), e.response.status_code
        return jsonify(error="Error calculando matriz"), 500
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error: {e}")
        return jsonify(error="Error conectando con optimizador"), 503


@bp.get("/api/v1/optimize/health")
def optimizer_health_check():
    """
    Health check del servicio optimizador FastAPI
    ---
    tags:
      - Route Optimizer
    summary: Verificar estado del servicio
    responses:
      200:
        description: Servicio saludable
      503:
        description: Servicio no disponible
    """
    optimizer_url = get_optimizer_service_url()
    
    if not optimizer_url:
        return jsonify(
            status="unhealthy",
            reason="OPTIMIZER_SERVICE_URL no configurada"
        ), 503
    
    try:
        # FastAPI tiene /docs por defecto
        response = requests.get(
            f"{optimizer_url}/docs",
            timeout=5
        )
        
        if response.status_code == 200:
            return jsonify(
                status="healthy",
                optimizer_service="connected",
                optimizer_url=optimizer_url
            ), 200
        else:
            return jsonify(
                status="degraded",
                status_code=response.status_code
            ), 503
            
    except requests.exceptions.Timeout:
        return jsonify(
            status="unhealthy",
            optimizer_service="timeout"
        ), 503
    except Exception as e:
        return jsonify(
            status="unhealthy",
            error=str(e)
        ), 503
