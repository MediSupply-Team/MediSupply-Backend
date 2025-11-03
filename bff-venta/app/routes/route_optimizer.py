from flask import Blueprint, request, jsonify, current_app
import requests
import uuid
from concurrent.futures import ThreadPoolExecutor

bp = Blueprint("route_optimizer", __name__)

# Thread pool para operaciones pesadas
executor = ThreadPoolExecutor(max_workers=10)


def get_optimizer_service_url():
    """
    Obtener la URL del servicio optimizador desde configuración
    """
    url = current_app.config.get("OPTIMIZER_SERVICE_URL")
    if not url:
        current_app.logger.error("OPTIMIZER_SERVICE_URL no está configurada")
        return None
    return url.rstrip('/')


@bp.post("/api/v1/routes/optimize")
def optimize_routes():
    """
    Proxy asíncrono a Route Optimizer - optimización de rutas
    Devuelve 202 inmediatamente y procesa en background
    ---
    tags:
      - Route Optimizer
    parameters:
      - in: body
        name: body
        required: true
        description: Parámetros de optimización (según microservicio)
    responses:
      202:
        description: Request accepted, processing in background
        schema:
          type: object
          properties:
            request_id:
              type: string
            status:
              type: string
      400:
        description: Validation error
      503:
        description: Service unavailable
    """
    optimizer_url = get_optimizer_service_url()
    if not optimizer_url:
        return jsonify(error="Servicio optimizador no disponible"), 503
    
    data = request.get_json(silent=True)
    
    if data is None:
        return jsonify(error="Body JSON requerido"), 400
    
    # Generar request_id para tracking
    request_id = str(uuid.uuid4())
    
    # Enviar en background
    executor.submit(
        call_optimizer_async,
        optimizer_url,
        data,
        request_id
    )
    
    # Respuesta inmediata
    return jsonify(
        request_id=request_id,
        status="processing",
        message="Route optimization in progress"
    ), 202


@bp.post("/api/v1/routes/<route_id>/assign-driver")
def assign_driver_to_route(route_id: str):
    """
    Proxy síncrono - asignar conductor
    ---
    tags:
      - Route Optimizer
    parameters:
      - in: path
        name: route_id
        type: string
        required: true
      - in: body
        name: body
        required: true
    responses:
      200:
        description: Driver assigned successfully
      404:
        description: Route not found
      503:
        description: Service unavailable
    """
    optimizer_url = get_optimizer_service_url()
    if not optimizer_url:
        return jsonify(error="Servicio optimizador no disponible"), 503
    
    data = request.get_json(silent=True)
    
    if data is None:
        return jsonify(error="Body JSON requerido"), 400
    
    try:
        response = requests.post(
            f"{optimizer_url}/routes/{route_id}/assign-driver",
            json=data,
            timeout=10
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.HTTPError as e:
        if e.response is not None:
            if e.response.status_code == 404:
                return jsonify(error="Route not found"), 404
            try:
                return jsonify(e.response.json()), e.response.status_code
            except:
                return jsonify(error=e.response.text), e.response.status_code
        return jsonify(error="Error asignando conductor"), 500
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error calling route optimizer: {e}")
        return jsonify(error="Error conectando con optimizador"), 503


@bp.get("/api/v1/routes")
def get_routes():
    """
    Proxy síncrono - lista de rutas
    ---
    tags:
      - Route Optimizer
    """
    optimizer_url = get_optimizer_service_url()
    if not optimizer_url:
        return jsonify(error="Servicio optimizador no disponible"), 503
    
    try:
        response = requests.get(
            f"{optimizer_url}/routes",
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
        return jsonify(error="Error obteniendo rutas"), 500
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error calling route optimizer: {e}")
        return jsonify(error="Error conectando con optimizador"), 503


@bp.get("/api/v1/routes/<route_id>")
def get_route_detail(route_id: str):
    """
    Proxy síncrono - detalle de ruta
    ---
    tags:
      - Route Optimizer
    """
    optimizer_url = get_optimizer_service_url()
    if not optimizer_url:
        return jsonify(error="Servicio optimizador no disponible"), 503
    
    try:
        response = requests.get(
            f"{optimizer_url}/routes/{route_id}",
            timeout=10
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.HTTPError as e:
        if e.response is not None:
            if e.response.status_code == 404:
                return jsonify(error="Route not found"), 404
            try:
                return jsonify(e.response.json()), e.response.status_code
            except:
                return jsonify(error=e.response.text), e.response.status_code
        return jsonify(error="Error obteniendo ruta"), 500
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error calling route optimizer: {e}")
        return jsonify(error="Error conectando con optimizador"), 503


@bp.patch("/api/v1/routes/<route_id>/status")
def update_route_status(route_id: str):
    """
    Proxy síncrono - actualizar estado
    ---
    tags:
      - Route Optimizer
    """
    optimizer_url = get_optimizer_service_url()
    if not optimizer_url:
        return jsonify(error="Servicio optimizador no disponible"), 503
    
    data = request.get_json(silent=True)
    
    if data is None:
        return jsonify(error="Body JSON requerido"), 400
    
    try:
        response = requests.patch(
            f"{optimizer_url}/routes/{route_id}/status",
            json=data,
            timeout=10
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.HTTPError as e:
        if e.response is not None:
            if e.response.status_code == 404:
                return jsonify(error="Route not found"), 404
            try:
                return jsonify(e.response.json()), e.response.status_code
            except:
                return jsonify(error=e.response.text), e.response.status_code
        return jsonify(error="Error actualizando ruta"), 500
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error calling route optimizer: {e}")
        return jsonify(error="Error conectando con optimizador"), 503


# ============================================
# FUNCIÓN ASYNC (solo para /optimize)
# ============================================

def call_optimizer_async(
    optimizer_url: str,
    data: dict,
    request_id: str
):
    """
    Llama al microservicio en background
    No devuelve nada al cliente (ya recibió 202)
    """
    try:
        response = requests.post(
            f"{optimizer_url}/routes/optimize",
            json=data,
            timeout=60  # Timeout largo para optimización
        )
        response.raise_for_status()
        
        current_app.logger.info(
            f"Route optimization successful. Request ID: {request_id}"
        )
        
    except requests.exceptions.Timeout:
        current_app.logger.error(
            f"Timeout calling route optimizer. Request ID: {request_id}"
        )
    except requests.exceptions.RequestException as e:
        current_app.logger.error(
            f"Error calling route optimizer. Request ID: {request_id}, Error: {e}"
        )


@bp.get("/api/v1/routes/health")
def optimizer_health_check():
    """
    Health check del servicio optimizador
    ---
    tags:
      - Route Optimizer
    """
    optimizer_url = get_optimizer_service_url()
    
    if not optimizer_url:
        return jsonify(
            status="unhealthy",
            reason="OPTIMIZER_SERVICE_URL no configurada"
        ), 503
    
    try:
        response = requests.get(
            f"{optimizer_url}/health",
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
                optimizer_service="error",
                status_code=response.status_code,
                optimizer_url=optimizer_url
            ), 503
            
    except requests.exceptions.Timeout:
        return jsonify(
            status="unhealthy",
            optimizer_service="timeout",
            optimizer_url=optimizer_url
        ), 503
    except Exception as e:
        return jsonify(
            status="unhealthy",
            optimizer_service="disconnected",
            error=str(e),
            optimizer_url=optimizer_url
        ), 503