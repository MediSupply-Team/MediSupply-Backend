from flask import Blueprint, request, jsonify, current_app
import uuid
from concurrent.futures import ThreadPoolExecutor
import requests
from typing import Dict, Any
import time

bp = Blueprint("routes", __name__)

# Thread pool para operaciones async
executor = ThreadPoolExecutor(max_workers=10)

# URL del microservicio (configurar en variables de entorno)
ROUTE_OPTIMIZER_URL = "http://route-optimizer-service:8000"  # o desde env


@bp.post("/api/v1/routes/optimize")
def optimize_routes():
    """
    Solicita optimización de rutas al microservicio Route Optimizer
    ---
    tags:
      - Routes
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            date:
              type: string
              format: date
              example: "2025-11-03"
            max_orders_per_route:
              type: integer
              example: 15
            max_duration_hours:
              type: integer
              example: 8
    responses:
      202:
        description: Route optimization request accepted
        schema:
          type: object
          properties:
            request_id:
              type: string
            status:
              type: string
              example: "processing"
      400:
        description: Validation error
    """
    data = request.get_json(silent=True) or {}
    
    # Validación básica
    if not data.get("date"):
        return jsonify(error="Falta 'date' en el JSON"), 400
    
    request_id = str(uuid.uuid4())
    
    # Preparar request para el microservicio
    optimization_request = {
        "date": data["date"],
        "max_orders_per_route": data.get("max_orders_per_route", 15),
        "max_duration_hours": data.get("max_duration_hours", 8),
        "warehouse_location": data.get("warehouse_location", {
            "lat": 4.6097,
            "lng": -74.0817,
            "address": "Bodega Central MediSupply, Bogotá"
        })
    }
    
    # Llamar al microservicio de forma asíncrona
    future = executor.submit(
        call_route_optimizer_async,
        optimization_request,
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
    Asigna un conductor a una ruta optimizada
    ---
    tags:
      - Routes
    parameters:
      - in: path
        name: route_id
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - driver_id
            - driver_name
            - vehicle_plate
          properties:
            driver_id:
              type: string
            driver_name:
              type: string
            vehicle_plate:
              type: string
            vehicle_type:
              type: string
    responses:
      200:
        description: Driver assigned successfully
      400:
        description: Validation error
      404:
        description: Route not found
    """
    data = request.get_json(silent=True) or {}
    
    required_fields = ["driver_id", "driver_name", "vehicle_plate"]
    for field in required_fields:
        if not data.get(field):
            return jsonify(error=f"Falta '{field}' en el JSON"), 400
    
    # Llamar al microservicio de forma asíncrona
    future = executor.submit(
        assign_driver_async,
        route_id,
        data
    )
    
    return jsonify(
        route_id=route_id,
        status="assigned",
        driver_name=data["driver_name"]
    ), 200


@bp.get("/api/v1/routes")
def get_routes():
    """
    Obtiene lista de rutas
    ---
    tags:
      - Routes
    parameters:
      - in: query
        name: status
        type: string
        enum: [PENDING, ASSIGNED, IN_PROGRESS, COMPLETED, CANCELLED]
      - in: query
        name: date
        type: string
        format: date
      - in: query
        name: driver_id
        type: string
    responses:
      200:
        description: List of routes
    """
    params = {}
    if request.args.get("status"):
        params["status"] = request.args.get("status")
    if request.args.get("date"):
        params["date"] = request.args.get("date")
    if request.args.get("driver_id"):
        params["driver_id"] = request.args.get("driver_id")
    
    try:
        response = requests.get(
            f"{ROUTE_OPTIMIZER_URL}/routes",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error calling route optimizer: {e}")
        return jsonify(error="Error connecting to route optimizer service"), 503


@bp.get("/api/v1/routes/<route_id>")
def get_route_detail(route_id: str):
    """
    Obtiene detalle de una ruta específica
    ---
    tags:
      - Routes
    parameters:
      - in: path
        name: route_id
        type: string
        required: true
    responses:
      200:
        description: Route details
      404:
        description: Route not found
    """
    try:
        response = requests.get(
            f"{ROUTE_OPTIMIZER_URL}/routes/{route_id}",
            timeout=10
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify(error="Route not found"), 404
        current_app.logger.error(f"Error calling route optimizer: {e}")
        return jsonify(error="Error fetching route"), 503
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error calling route optimizer: {e}")
        return jsonify(error="Error connecting to route optimizer service"), 503


@bp.patch("/api/v1/routes/<route_id>/status")
def update_route_status(route_id: str):
    """
    Actualiza el estado de una ruta
    ---
    tags:
      - Routes
    parameters:
      - in: path
        name: route_id
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - status
          properties:
            status:
              type: string
              enum: [IN_PROGRESS, COMPLETED, CANCELLED]
    responses:
      200:
        description: Status updated
      400:
        description: Invalid status
      404:
        description: Route not found
    """
    data = request.get_json(silent=True) or {}
    
    if not data.get("status"):
        return jsonify(error="Falta 'status' en el JSON"), 400
    
    try:
        response = requests.patch(
            f"{ROUTE_OPTIMIZER_URL}/routes/{route_id}/status",
            json=data,
            timeout=10
        )
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify(error="Route not found"), 404
        current_app.logger.error(f"Error calling route optimizer: {e}")
        return jsonify(error="Error updating route"), 503
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error calling route optimizer: {e}")
        return jsonify(error="Error connecting to route optimizer service"), 503


# ============================================
# FUNCIONES ASYNC (background)
# ============================================

def call_route_optimizer_async(optimization_request: Dict[str, Any], request_id: str):
    """
    Llama al microservicio Route Optimizer de forma asíncrona
    Similar a send_sqs_message_async en orders.py
    """
    try:
        response = requests.post(
            f"{ROUTE_OPTIMIZER_URL}/routes/optimize",
            json=optimization_request,
            timeout=30
        )
        response.raise_for_status()
        
        current_app.logger.info(
            f"Route optimization successful. Request ID: {request_id}, "
            f"Routes created: {len(response.json())}"
        )
        return response.json()
        
    except requests.exceptions.Timeout:
        current_app.logger.error(f"Timeout calling route optimizer. Request ID: {request_id}")
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error calling route optimizer: {e}")


def assign_driver_async(route_id: str, driver_data: Dict[str, Any]):
    """
    Asigna conductor de forma asíncrona
    """
    try:
        response = requests.post(
            f"{ROUTE_OPTIMIZER_URL}/routes/{route_id}/assign-driver",
            json=driver_data,
            timeout=10
        )
        response.raise_for_status()
        
        current_app.logger.info(
            f"Driver assigned to route {route_id}: {driver_data['driver_name']}"
        )
        return response.json()
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error assigning driver: {e}")
