from flask import Blueprint, request, jsonify, current_app
import requests
from requests.exceptions import RequestException, Timeout
import os

bp = Blueprint("rutas", __name__)

def get_rutas_service_url():
    """Obtener la URL del servicio de rutas desde variables de entorno"""
    url = os.getenv("RUTAS_SERVICE_URL")
    if not url:
        current_app.logger.error("RUTAS_SERVICE_URL no esta configurada")
        return None
    return url.rstrip('/')  # Remover trailing slash si existe


# ==================== GESTION DE RUTAS ====================

@bp.post("/api/v1/rutas")
def create_ruta():
    """
    Crear una nueva ruta optimizada
    ---
    tags:
      - Rutas
    parameters:
      - in: body
        name: body
        required: true
        description: Datos de la ruta optimizada (del servicio optimizador)
        schema:
          type: object
          required:
            - secuencia_entregas
            - resumen
          properties:
            id_cliente:
              type: string
              description: UUID del cliente que solicita la ruta
              example: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
            fecha_entrega:
              type: string
              format: date
              description: Fecha programada de entrega (YYYY-MM-DD)
              example: "2024-05-05"
            secuencia_entregas:
              type: array
              items:
                type: object
                properties:
                  orden:
                    type: integer
                  id_pedido:
                    type: string
                  descripcion:
                    type: string
                  cliente:
                    type: string
                  direccion:
                    type: string
                  lat:
                    type: number
                  lon:
                    type: number
                  ventana_inicio:
                    type: string
                    example: "10:00"
                  ventana_fin:
                    type: string
                    example: "11:00"
                  hora_estimada:
                    type: string
                  cajas:
                    type: integer
                  urgencia:
                    type: string
            resumen:
              type: object
              properties:
                distancia_total_km:
                  type: number
                tiempo_total_min:
                  type: integer
                total_entregas:
                  type: integer
                costo_estimado:
                  type: number
            geometria:
              type: object
              description: GeoJSON opcional
            alertas:
              type: array
            optimized_by:
              type: string
            notes:
              type: string
    responses:
      201:
        description: Ruta creada exitosamente
        schema:
          type: object
          properties:
            id:
              type: string
            created_at:
              type: string
            message:
              type: string
      400:
        description: Datos invalidos
      503:
        description: Servicio no disponible
    """
    rutas_url = get_rutas_service_url()
    if not rutas_url:
        return jsonify(error="Servicio de rutas no disponible"), 503
    
    try:
        # Obtener datos del body
        data = request.get_json()
        if not data:
            return jsonify(error="Datos requeridos"), 400
        
        # Validar campos minimos
        if 'secuencia_entregas' not in data or 'resumen' not in data:
            return jsonify(error="secuencia_entregas y resumen son requeridos"), 400
        
        # ✅ NUEVO: Validar formato de fecha_entrega si está presente
        if 'fecha_entrega' in data and data['fecha_entrega']:
            from datetime import datetime
            try:
                datetime.strptime(data['fecha_entrega'], '%Y-%m-%d')
            except ValueError:
                return jsonify(error="fecha_entrega debe estar en formato YYYY-MM-DD"), 400
        
        # Enviar al ruta-service
        url = f"{rutas_url}/rutas"
        current_app.logger.info(f"Creating route at: {url}")
        
        response = requests.post(
            url,
            json=data,
            timeout=10,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
            }
        )
        
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Rutas service error: {response.status_code} - {response.text[:200]}"
            )
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al crear ruta",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"Route created successfully: {response.status_code}")
        return jsonify(response.json()), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de rutas: {rutas_url}")
        return jsonify(error="Timeout al crear ruta"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de rutas: {e}")
        return jsonify(error="Error de conexion con servicio de rutas"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado al crear ruta: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.get("/api/v1/rutas")
def list_rutas():
    """
    Listar rutas con paginacion y filtros
    ---
    tags:
      - Rutas
    parameters:
      - in: query
        name: skip
        type: integer
        required: false
        description: Registros a saltar
        default: 0
      - in: query
        name: limit
        type: integer
        required: false
        description: Cantidad maxima a retornar
        default: 10
      - in: query
        name: status
        type: string
        required: false
        description: Filtrar por estado (pending, in_progress, completed, cancelled)
      - in: query
        name: id_cliente
        type: string
        required: false
        description: Filtrar por ID de cliente
      - in: query
        name: fecha_entrega
        type: string
        format: date
        required: false
        description: Filtrar por fecha de entrega exacta (YYYY-MM-DD)
        example: "2024-05-05"
      - in: query
        name: fecha_desde
        type: string
        format: date
        required: false
        description: Filtrar rutas desde esta fecha de entrega (YYYY-MM-DD)
      - in: query
        name: fecha_hasta
        type: string
        format: date
        required: false
        description: Filtrar rutas hasta esta fecha de entrega (YYYY-MM-DD)
    responses:
      200:
        description: Lista de rutas
        schema:
          type: object
          properties:
            total:
              type: integer
            routes:
              type: array
      503:
        description: Servicio no disponible
    """
    rutas_url = get_rutas_service_url()
    if not rutas_url:
        return jsonify(error="Servicio de rutas no disponible"), 503
    
    try:
        # Construir query params
        params = {
            'skip': request.args.get('skip', 0, type=int),
            'limit': request.args.get('limit', 10, type=int)
        }
        
        # ✅ Filtros existentes
        status = request.args.get('status')
        if status:
            params['status'] = status
        
        # ✅ NUEVO: Filtros por cliente
        id_cliente = request.args.get('id_cliente')
        if id_cliente:
            params['id_cliente'] = id_cliente
        
        # ✅ NUEVO: Filtros por fecha de entrega
        fecha_entrega = request.args.get('fecha_entrega')
        if fecha_entrega:
            params['fecha_entrega'] = fecha_entrega
        
        fecha_desde = request.args.get('fecha_desde')
        if fecha_desde:
            params['fecha_desde'] = fecha_desde
        
        fecha_hasta = request.args.get('fecha_hasta')
        if fecha_hasta:
            params['fecha_hasta'] = fecha_hasta
        
        url = f"{rutas_url}/rutas"
        current_app.logger.info(f"Listing routes: {url} with params: {params}")
        
        response = requests.get(
            url,
            params=params,
            timeout=10,
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
            }
        )
        
        if response.status_code >= 400:
            current_app.logger.warning(f"Rutas service error: {response.status_code}")
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(error="Error al listar rutas", details=error_data), response.status_code
        
        return jsonify(response.json()), response.status_code
        
    except Timeout:
        return jsonify(error="Timeout al listar rutas"), 504
    except RequestException as e:
        current_app.logger.error(f"Error al listar rutas: {e}")
        return jsonify(error="Error de conexion"), 503
    except Exception as e:
        current_app.logger.error(f"Error inesperado: {e}", exc_info=True)
        return jsonify(error="Error interno"), 500


@bp.get("/api/v1/rutas/<ruta_id>")
def get_ruta(ruta_id):
    """
    Obtener ruta por ID
    ---
    tags:
      - Rutas
    parameters:
      - in: path
        name: ruta_id
        type: string
        required: true
        description: ID de la ruta
    responses:
      200:
        description: Ruta encontrada
        schema:
          type: object
          properties:
            id:
              type: string
            id_cliente:
              type: string
            fecha_entrega:
              type: string
              format: date
            secuencia_entregas:
              type: array
            resumen:
              type: object
            geometria:
              type: object
            status:
              type: string
      404:
        description: Ruta no encontrada
      503:
        description: Servicio no disponible
    """
    rutas_url = get_rutas_service_url()
    if not rutas_url:
        return jsonify(error="Servicio de rutas no disponible"), 503
    
    try:
        url = f"{rutas_url}/rutas/{ruta_id}"
        current_app.logger.info(f"Getting route: {url}")
        
        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "BFF-Venta/1.0",
            }
        )
        
        if response.status_code >= 400:
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(error="Error al obtener ruta", details=error_data), response.status_code
        
        return jsonify(response.json()), response.status_code
        
    except Timeout:
        return jsonify(error="Timeout"), 504
    except RequestException as e:
        current_app.logger.error(f"Error: {e}")
        return jsonify(error="Error de conexion"), 503
    except Exception as e:
        current_app.logger.error(f"Error: {e}", exc_info=True)
        return jsonify(error="Error interno"), 500


@bp.patch("/api/v1/rutas/<ruta_id>")
def update_ruta(ruta_id):
    """
    Actualizar ruta
    ---
    tags:
      - Rutas
    parameters:
      - in: path
        name: ruta_id
        type: string
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            geometria:
              type: object
            alertas:
              type: array
            notes:
              type: string
    responses:
      200:
        description: Ruta actualizada
      404:
        description: Ruta no encontrada
      503:
        description: Servicio no disponible
    """
    rutas_url = get_rutas_service_url()
    if not rutas_url:
        return jsonify(error="Servicio de rutas no disponible"), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify(error="Datos requeridos"), 400
        
        url = f"{rutas_url}/rutas/{ruta_id}"
        current_app.logger.info(f"Updating route: {url}")
        
        response = requests.patch(
            url,
            json=data,
            timeout=10,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "BFF-Venta/1.0",
            }
        )
        
        if response.status_code >= 400:
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(error="Error al actualizar ruta", details=error_data), response.status_code
        
        return jsonify(response.json()), response.status_code
        
    except Timeout:
        return jsonify(error="Timeout"), 504
    except RequestException as e:
        current_app.logger.error(f"Error: {e}")
        return jsonify(error="Error de conexion"), 503
    except Exception as e:
        current_app.logger.error(f"Error: {e}", exc_info=True)
        return jsonify(error="Error interno"), 500


@bp.delete("/api/v1/rutas/<ruta_id>")
def delete_ruta(ruta_id):
    """
    Eliminar ruta
    ---
    tags:
      - Rutas
    parameters:
      - in: path
        name: ruta_id
        type: string
        required: true
    responses:
      200:
        description: Ruta eliminada
      404:
        description: Ruta no encontrada
      503:
        description: Servicio no disponible
    """
    rutas_url = get_rutas_service_url()
    if not rutas_url:
        return jsonify(error="Servicio de rutas no disponible"), 503
    
    try:
        url = f"{rutas_url}/rutas/{ruta_id}"
        current_app.logger.info(f"Deleting route: {url}")
        
        response = requests.delete(
            url,
            timeout=10,
            headers={
                "User-Agent": "BFF-Venta/1.0",
            }
        )
        
        if response.status_code >= 400:
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(error="Error al eliminar ruta", details=error_data), response.status_code
        
        return jsonify(response.json()), response.status_code
        
    except Timeout:
        return jsonify(error="Timeout"), 504
    except RequestException as e:
        current_app.logger.error(f"Error: {e}")
        return jsonify(error="Error de conexion"), 503
    except Exception as e:
        current_app.logger.error(f"Error: {e}", exc_info=True)
        return jsonify(error="Error interno"), 500


@bp.patch("/api/v1/rutas/<ruta_id>/assign-driver")
def assign_driver(ruta_id):
    """
    Asignar conductor a ruta
    ---
    tags:
      - Rutas
    parameters:
      - in: path
        name: ruta_id
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - driver_id
          properties:
            driver_id:
              type: string
            driver_name:
              type: string
    responses:
      200:
        description: Conductor asignado
      400:
        description: Datos invalidos
      404:
        description: Ruta no encontrada
      503:
        description: Servicio no disponible
    """
    rutas_url = get_rutas_service_url()
    if not rutas_url:
        return jsonify(error="Servicio de rutas no disponible"), 503
    
    try:
        data = request.get_json()
        if not data or 'driver_id' not in data:
            return jsonify(error="driver_id es requerido"), 400
        
        url = f"{rutas_url}/rutas/{ruta_id}/assign-driver"
        current_app.logger.info(f"Assigning driver: {url}")
        
        response = requests.patch(
            url,
            json=data,
            timeout=10,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "BFF-Venta/1.0",
            }
        )
        
        if response.status_code >= 400:
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(error="Error al asignar conductor", details=error_data), response.status_code
        
        return jsonify(response.json()), response.status_code
        
    except Timeout:
        return jsonify(error="Timeout"), 504
    except RequestException as e:
        current_app.logger.error(f"Error: {e}")
        return jsonify(error="Error de conexion"), 503
    except Exception as e:
        current_app.logger.error(f"Error: {e}", exc_info=True)
        return jsonify(error="Error interno"), 500


@bp.patch("/api/v1/rutas/<ruta_id>/status")
def update_status(ruta_id):
    """
    Actualizar estado de ruta
    ---
    tags:
      - Rutas
    parameters:
      - in: path
        name: ruta_id
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
              enum: [pending, in_progress, completed, cancelled]
    responses:
      200:
        description: Estado actualizado
      400:
        description: Estado invalido
      404:
        description: Ruta no encontrada
      503:
        description: Servicio no disponible
    """
    rutas_url = get_rutas_service_url()
    if not rutas_url:
        return jsonify(error="Servicio de rutas no disponible"), 503
    
    try:
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify(error="status es requerido"), 400
        
        # Validar estado
        valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
        if data['status'] not in valid_statuses:
            return jsonify(error=f"status debe ser uno de: {', '.join(valid_statuses)}"), 400
        
        url = f"{rutas_url}/rutas/{ruta_id}/status"
        current_app.logger.info(f"Updating status: {url}")
        
        response = requests.patch(
            url,
            json=data,
            timeout=10,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "BFF-Venta/1.0",
            }
        )
        
        if response.status_code >= 400:
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(error="Error al actualizar estado", details=error_data), response.status_code
        
        return jsonify(response.json()), response.status_code
        
    except Timeout:
        return jsonify(error="Timeout"), 504
    except RequestException as e:
        current_app.logger.error(f"Error: {e}")
        return jsonify(error="Error de conexion"), 503
    except Exception as e:
        current_app.logger.error(f"Error: {e}", exc_info=True)
        return jsonify(error="Error interno"), 500


@bp.get("/api/v1/rutas/driver/<driver_id>")
def get_rutas_by_driver(driver_id):
    """
    Obtener todas las rutas de un conductor
    ---
    tags:
      - Rutas
    parameters:
      - in: path
        name: driver_id
        type: string
        required: true
        description: ID del conductor
    responses:
      200:
        description: Rutas del conductor
        schema:
          type: object
          properties:
            total:
              type: integer
            routes:
              type: array
      503:
        description: Servicio no disponible
    """
    rutas_url = get_rutas_service_url()
    if not rutas_url:
        return jsonify(error="Servicio de rutas no disponible"), 503
    
    try:
        url = f"{rutas_url}/rutas/driver/{driver_id}"
        current_app.logger.info(f"Getting driver routes: {url}")
        
        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "BFF-Venta/1.0",
            }
        )
        
        if response.status_code >= 400:
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(error="Error al obtener rutas del conductor", details=error_data), response.status_code
        
        return jsonify(response.json()), response.status_code
        
    except Timeout:
        return jsonify(error="Timeout"), 504
    except RequestException as e:
        current_app.logger.error(f"Error: {e}")
        return jsonify(error="Error de conexion"), 503
    except Exception as e:
        current_app.logger.error(f"Error: {e}", exc_info=True)
        return jsonify(error="Error interno"), 500


# ✅ NUEVO: Endpoint dedicado para rutas de un cliente
@bp.get("/api/v1/rutas/cliente/<cliente_id>")
def get_rutas_by_cliente(cliente_id):
    """
    Obtener todas las rutas de un cliente (para vista de calendario)
    ---
    tags:
      - Rutas
    parameters:
      - in: path
        name: cliente_id
        type: string
        required: true
        description: ID del cliente
      - in: query
        name: fecha_entrega
        type: string
        format: date
        required: false
        description: Filtrar por fecha de entrega exacta (YYYY-MM-DD)
        example: "2024-05-05"
      - in: query
        name: fecha_desde
        type: string
        format: date
        required: false
        description: Filtrar desde esta fecha de entrega (YYYY-MM-DD)
      - in: query
        name: fecha_hasta
        type: string
        format: date
        required: false
        description: Filtrar hasta esta fecha de entrega (YYYY-MM-DD)
      - in: query
        name: status
        type: string
        required: false
        description: Filtrar por estado (pending, in_progress, completed, cancelled)
    responses:
      200:
        description: Rutas del cliente
        schema:
          type: object
          properties:
            total:
              type: integer
            routes:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                  fecha_entrega:
                    type: string
                    format: date
                  secuencia_entregas:
                    type: array
                  status:
                    type: string
      503:
        description: Servicio no disponible
    """
    rutas_url = get_rutas_service_url()
    if not rutas_url:
        return jsonify(error="Servicio de rutas no disponible"), 503
    
    try:
        # Construir query params para filtros opcionales
        params = {}
        
        fecha_entrega = request.args.get('fecha_entrega')
        if fecha_entrega:
            params['fecha_entrega'] = fecha_entrega
        
        fecha_desde = request.args.get('fecha_desde')
        if fecha_desde:
            params['fecha_desde'] = fecha_desde
        
        fecha_hasta = request.args.get('fecha_hasta')
        if fecha_hasta:
            params['fecha_hasta'] = fecha_hasta
        
        status = request.args.get('status')
        if status:
            params['status'] = status
        
        url = f"{rutas_url}/rutas/cliente/{cliente_id}"
        current_app.logger.info(f"Getting cliente routes: {url} with params: {params}")
        
        response = requests.get(
            url,
            params=params,
            timeout=10,
            headers={
                "User-Agent": "BFF-Venta/1.0",
            }
        )
        
        if response.status_code >= 400:
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al obtener rutas del cliente", 
                details=error_data
            ), response.status_code
        
        return jsonify(response.json()), response.status_code
        
    except Timeout:
        return jsonify(error="Timeout"), 504
    except RequestException as e:
        current_app.logger.error(f"Error: {e}")
        return jsonify(error="Error de conexion"), 503
    except Exception as e:
        current_app.logger.error(f"Error: {e}", exc_info=True)
        return jsonify(error="Error interno"), 500


# ==================== RUTAS DE VISITA (legacy) ====================

@bp.get("/api/v1/rutas/visita/<fecha>")
def get_ruta_by_fecha(fecha):
    """
    Obtener ruta de visita por fecha (legacy endpoint)
    ---
    tags:
      - Rutas
    parameters:
      - in: path
        name: fecha
        type: string
        required: true
        description: Fecha en formato YYYY-MM-DD
        example: "2025-10-10"
      - in: query
        name: vendedor_id
        type: integer
        required: false
        description: ID del vendedor (opcional, default 1)
        example: 1
    responses:
      200:
        description: Ruta encontrada exitosamente
      404:
        description: Ruta no encontrada
      503:
        description: Servicio no disponible
    """
    rutas_url = get_rutas_service_url()
    if not rutas_url:
        return jsonify(error="Servicio de rutas no disponible"), 503
    
    try:
        vendedor_id = request.args.get('vendedor_id', 1, type=int)
        url = f"{rutas_url}/api/ruta?fecha={fecha}&vendedor_id={vendedor_id}"
        
        current_app.logger.info(f"Calling rutas service: {url}")
        
        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
            }
        )
        
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Rutas service error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al consultar ruta",
                details=error_data
            ), response.status_code
        
        current_app.logger.info(f"Rutas service success: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de rutas: {rutas_url}")
        return jsonify(error="Timeout al consultar ruta"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de rutas: {e}")
        return jsonify(error="Error de conexion con servicio de rutas"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en rutas endpoint: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


# ==================== HEALTH CHECK ====================

@bp.get("/api/v1/rutas/health")
def rutas_health_check():
    """
    Health check del servicio de rutas
    ---
    tags:
      - Rutas
    responses:
      200:
        description: Servicio conectado
        schema:
          type: object
          properties:
            status:
              type: string
              example: "healthy"
            rutas_service:
              type: string
              example: "connected"
            rutas_url:
              type: string
      503:
        description: Servicio no disponible
    """
    rutas_url = get_rutas_service_url()
    
    if not rutas_url:
        return jsonify(
            status="unhealthy",
            reason="RUTAS_SERVICE_URL no configurada"
        ), 503
    
    try:
        response = requests.get(
            f"{rutas_url}/health",
            timeout=5
        )
        
        if response.status_code == 200:
            return jsonify(
                status="healthy",
                rutas_service="connected",
                rutas_url=rutas_url
            ), 200
        else:
            return jsonify(
                status="degraded",
                rutas_service="error",
                status_code=response.status_code,
                rutas_url=rutas_url
            ), 503
            
    except Timeout:
        return jsonify(
            status="unhealthy",
            rutas_service="timeout",
            rutas_url=rutas_url
        ), 503
    except Exception as e:
        return jsonify(
            status="unhealthy",
            rutas_service="disconnected",
            error=str(e),
            rutas_url=rutas_url
        ), 503