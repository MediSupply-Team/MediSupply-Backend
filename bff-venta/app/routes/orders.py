from flask import Blueprint, request, jsonify, current_app
import requests

bp = Blueprint("orders", __name__)


def get_orders_service_url():
    """URL del servicio FastAPI de ordenes"""
    url = current_app.config.get("ORDERS_SERVICE_URL")
    if not url:
        current_app.logger.error("ORDERS_SERVICE_URL no esta configurada")
        return None
    return url.rstrip('/')


@bp.post("/api/v1/orders")
def create_order():
    """
    Crear nueva orden (proxy a orders-service)
    ---
    tags:
      - Orders
    summary: Crear nueva orden
    description: |
      Crea una nueva orden en el sistema con soporte de idempotencia.
      
      El servicio de ordenes maneja:
      - Validacion de datos
      - Idempotencia (evita duplicados)
      - Persistencia en base de datos
      - Eventos outbox para procesamiento asíncrono
    
    parameters:
      - in: header
        name: Idempotency-Key
        type: string
        required: false
        description: UUID v4 para idempotencia (opcional, se genera si no se provee)
        example: "550e8400-e29b-41d4-a716-446655440000"
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - customer_id
            - items
          properties:
            customer_id:
              type: string
              description: ID del cliente
              example: "Hospital San José"
            items:
              type: array
              description: Items de la orden
              items:
                type: object
                properties:
                  sku:
                    type: string
                  qty:
                    type: integer
              example:
                - sku: "PROD-A"
                  qty: 2
                - sku: "PROD-B"
                  qty: 1
            user_name:
              type: string
              description: Usuario que crea la orden
              example: "juan.perez"
            address:
              type: object
              description: Direccion de entrega
              properties:
                street:
                  type: string
                city:
                  type: string
                state:
                  type: string
                zip_code:
                  type: string
                country:
                  type: string
    
    responses:
      202:
        description: Orden aceptada para procesamiento
        schema:
          type: object
          properties:
            request_id:
              type: string
              description: ID de la peticion (hash del Idempotency-Key)
            message:
              type: string
        examples:
          application/json:
            request_id: "abc123..."
            message: "Orden aceptada"
      
      400:
        description: Error de validacion
      
      409:
        description: Conflicto - Idempotency-Key ya usado con payload diferente
      
      503:
        description: Servicio no disponible
    """
    orders_url = get_orders_service_url()
    if not orders_url:
        return jsonify(error="Servicio de ordenes no disponible"), 503
    
    data = request.get_json(silent=True)
    if data is None:
        return jsonify(error="Body JSON requerido"), 400
    
    # Enriquecer con metadata del BFF
    enriched_data = {
        **data,
        "created_by_role": "vendor",
        "source": "bff-venta"
    }
    
    # Copiar Idempotency-Key header si existe
    headers = {}
    if "Idempotency-Key" in request.headers:
        headers["Idempotency-Key"] = request.headers["Idempotency-Key"]
    
    try:
        response = requests.post(
            f"{orders_url}/orders",
            json=enriched_data,
            headers=headers,
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
        return jsonify(error="Error creando orden"), 500
        
    except requests.exceptions.Timeout:
        return jsonify(error="Timeout creando orden"), 504
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error: {e}")
        return jsonify(error="Error conectando con servicio de ordenes"), 503


@bp.get("/api/v1/orders")
def get_orders():
    """
    Obtener lista de ordenes con paginacion
    ---
    tags:
      - Orders
    summary: Listar ordenes
    description: Obtiene todas las ordenes del sistema con soporte de paginacion
    
    parameters:
      - in: query
        name: limit
        type: integer
        default: 100
        description: Numero maximo de resultados
      - in: query
        name: offset
        type: integer
        default: 0
        description: Numero de resultados a saltar (para paginacion)
    
    responses:
      200:
        description: Lista de ordenes
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: string
              customer_id:
                type: string
              items:
                type: array
              status:
                type: string
              created_by_role:
                type: string
              source:
                type: string
              user_name:
                type: string
              address:
                type: object
              created_at:
                type: string
      503:
        description: Servicio no disponible
    """
    orders_url = get_orders_service_url()
    if not orders_url:
        return jsonify(error="Servicio de ordenes no disponible"), 503
    
    try:
        response = requests.get(
            f"{orders_url}/orders",
            params=request.args,  # Pasar limit y offset
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
        return jsonify(error="Error obteniendo ordenes"), 500
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error: {e}")
        return jsonify(error="Error conectando con servicio de ordenes"), 503


@bp.get("/api/v1/orders/<order_id>")
def get_order_by_id(order_id: str):
    """
    Obtener detalle de una orden específica
    ---
    tags:
      - Orders
    summary: Detalle de orden
    description: Obtiene toda la informacion de una orden por su ID
    
    parameters:
      - in: path
        name: order_id
        type: string
        required: true
        description: UUID de la orden
    
    responses:
      200:
        description: Detalle de la orden
        schema:
          type: object
          properties:
            id:
              type: string
            customer_id:
              type: string
            items:
              type: array
            status:
              type: string
            created_by_role:
              type: string
            source:
              type: string
            user_name:
              type: string
            address:
              type: object
            created_at:
              type: string
      
      400:
        description: ID de orden invalido
      
      404:
        description: Orden no encontrada
      
      503:
        description: Servicio no disponible
    """
    orders_url = get_orders_service_url()
    if not orders_url:
        return jsonify(error="Servicio de ordenes no disponible"), 503
    
    try:
        response = requests.get(
            f"{orders_url}/orders/{order_id}",
            timeout=10
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.HTTPError as e:
        if e.response is not None:
            if e.response.status_code == 404:
                return jsonify(error="Orden no encontrada"), 404
            if e.response.status_code == 400:
                return jsonify(error="ID de orden invalido"), 400
            try:
                return jsonify(e.response.json()), e.response.status_code
            except:
                return jsonify(error=e.response.text), e.response.status_code
        return jsonify(error="Error obteniendo orden"), 500
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error: {e}")
        return jsonify(error="Error conectando con servicio de ordenes"), 503


@bp.get("/api/v1/orders/health")
def orders_health_check():
    """
    Health check del servicio de ordenes
    ---
    tags:
      - Orders
    summary: Estado del servicio
    responses:
      200:
        description: Servicio saludable
      503:
        description: Servicio no disponible
    """
    orders_url = get_orders_service_url()
    
    if not orders_url:
        return jsonify(
            status="unhealthy",
            reason="ORDERS_SERVICE_URL no configurada"
        ), 503
    
    try:
        response = requests.get(
            f"{orders_url}/health",
            timeout=5
        )
        
        if response.status_code == 200:
            health_data = response.json()
            return jsonify(
                status="healthy",
                orders_service="connected",
                orders_url=orders_url,
                service_health=health_data
            ), 200
        else:
            return jsonify(
                status="degraded",
                status_code=response.status_code
            ), 503
            
    except Exception as e:
        return jsonify(
            status="unhealthy",
            error=str(e)
        ), 503