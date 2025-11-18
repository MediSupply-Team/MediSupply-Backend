from flask import Blueprint, request, jsonify, current_app
import requests
import uuid
from concurrent.futures import ThreadPoolExecutor
import threading
import time

bp = Blueprint("orders", __name__)

# Thread pool global para operaciones I/O
executor = ThreadPoolExecutor(max_workers=10)


def get_orders_service_url():
    """URL del servicio FastAPI de ordenes"""
    url = current_app.config.get("ORDERS_SERVICE_URL")
    if not url:
        current_app.logger.error("ORDERS_SERVICE_URL no esta configurada")
        return None
    return url.rstrip('/')


@bp.post("/api/v1/orders")
def post_message():
    """
    Create a new order (async via SQS)
    ---
    tags:
      - Orders
    parameters:
      - in: body
        name: body
        description: Order data
        required: true
        schema:
          type: object
          required:
            - body
          properties:
            body:
              type: object
              description: Order details
              example:
                customer_id: "123"
                items:
                  - product_id: "ABC"
                    quantity: 2
            group_id:
              type: string
              description: SQS Message Group ID
              example: "customer-123"
            dedup_id:
              type: string
              description: Deduplication ID
              example: "order-456"
    responses:
      202:
        description: Order accepted
        schema:
          type: object
          properties:
            messageId:
              type: string
              example: "async-uuid-here"
            event_id:
              type: string
              example: "uuid-here"
            status:
              type: string
              example: "accepted"
      400:
        description: Validation error
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Falta 'body' en el JSON"
    """
    data = request.get_json(silent=True) or {}
    body = data.get("body")
    if not body:
        return jsonify(error="Falta 'body' en el JSON"), 400
    
    enriched_body = {
    **body,  # Mantener todos los campos originales
    "created_by_role": "seller", 
    "source": "bff-venta"
    }
    event_id = str(uuid.uuid4())
    sqs_message = {
        "event_id": event_id,
        "order": enriched_body,
        "timestamps": {
            "bff_received": time.time(),
            "sqs_sent": time.time()
        }
    }

    group_id = data.get("group_id")
    dedup_id = data.get("dedup_id", event_id)

    sqs: "SQSService" = current_app.extensions["sqs"]
    
    # Enviar a SQS de forma asincrona (no bloqueante)
    future = executor.submit(
        send_sqs_message_async, 
        sqs, 
        sqs_message, 
        group_id, 
        dedup_id
    )
    
    # Respuesta inmediata sin esperar SQS
    return jsonify(
        messageId=f"async-{event_id}",  # ID temporal
        event_id=event_id,
        status="accepted"
    ), 202

def send_sqs_message_async(sqs, message, group_id, dedup_id):
    """Función para enviar mensaje a SQS en background"""
    try:
        resp = sqs.send_message(body=message, group_id=group_id, dedup_id=dedup_id)
        current_app.logger.info(f"SQS message sent: {resp['MessageId']}")
        return resp
    except Exception as e:
        current_app.logger.error(f"Error sending SQS message: {e}")
        # Aquí podrías implementar retry logic o DLQ

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

@bp.post("/api/v1/orders/seed-data")
def seed_orders_data():
    """
    Cargar datos de prueba en Orders Service
    ---
    tags:
      - Orders
    summary: Cargar datos de prueba
    responses:
      201:
        description: Datos cargados exitosamente
        schema:
          type: object
          properties:
            message:
              type: string
            count:
              type: integer
      503:
        description: Servicio no disponible
    """
    orders_url = get_orders_service_url()
    if not orders_url:
        return jsonify(error="Servicio de ordenes no disponible"), 503
    
    try:
        response = requests.post(
            f"{orders_url}/seed-data",
            timeout=10
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error: {e}")
        return jsonify(error="Error cargando datos de prueba"), 503


@bp.delete("/api/v1/orders/clear-all")
def clear_all_orders():
    """
    Borrar TODOS los registros de Orders Service
    ---
    tags:
      - Orders
    summary: Limpiar base de datos
    description: CUIDADO - Borra todos los registros
    responses:
      200:
        description: Datos eliminados
        schema:
          type: object
          properties:
            message:
              type: string
            tables_cleared:
              type: array
              items:
                type: string
      503:
        description: Servicio no disponible
    """
    orders_url = get_orders_service_url()
    if not orders_url:
        return jsonify(error="Servicio de ordenes no disponible"), 503
    
    try:
        response = requests.delete(
            f"{orders_url}/clear-all",
            timeout=10
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error: {e}")
        return jsonify(error="Error limpiando datos"), 503