"""
Rutas de catálogo para el BFF-Venta
Proxy hacia catalogo-service con manejo de errores
"""
from flask import Blueprint, jsonify, request, current_app
import requests
from requests.exceptions import RequestException, Timeout
import os

bp = Blueprint('catalog', __name__)


def get_catalogo_service_url():
    """
    Obtener la URL del servicio de catálogo desde variables de entorno.
    Remueve el sufijo /catalog si existe, ya que el ALB lo maneja automáticamente.
    """
    url = os.getenv("CATALOGO_SERVICE_URL")
    if not url:
        current_app.logger.error("CATALOGO_SERVICE_URL no está configurada")
        return None
    
    url = url.rstrip('/')  # Remover trailing slash si existe
    
    # Remover /catalog del final si existe, porque el ALB ya lo maneja
    if url.endswith('/catalog'):
        url = url.rsplit('/catalog', 1)[0]
    
    return url


@bp.route('/api/v1/catalog/items', methods=['GET'])
def get_catalog_items():
    """
    Obtiene la lista de items del catálogo
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Construir parámetros de query
        params = {}
        
        # Soportar tanto 'category' como 'categoriaId' para compatibilidad
        categoria = request.args.get('category') or request.args.get('categoriaId')
        if categoria:
            params['categoriaId'] = categoria
        
        # Otros parámetros
        if request.args.get('q'):
            params['q'] = request.args.get('q')
        if request.args.get('codigo'):
            params['codigo'] = request.args.get('codigo')
        if request.args.get('pais'):
            params['pais'] = request.args.get('pais')
        if request.args.get('bodegaId') or request.args.get('bodega_id'):
            params['bodegaId'] = request.args.get('bodegaId') or request.args.get('bodega_id')
        if request.args.get('page'):
            params['page'] = request.args.get('page')
        if request.args.get('size'):
            params['size'] = request.args.get('size')
        if request.args.get('sort'):
            params['sort'] = request.args.get('sort')
        
        # Construir URL
        url = f"{catalogo_url}/api/v1/catalog/items"
        
        current_app.logger.info(f"🔍 Llamando a catalogo-service: {url}")
        
        response = requests.get(
            url,
            params=params,
            timeout=10,
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Catalog service error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al consultar catálogo",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"Catalog service success: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de catálogo: {catalogo_url}")
        return jsonify(error="Timeout al consultar catálogo"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de catálogo: {e}")
        return jsonify(error="Error de conexión con servicio de catálogo"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en catalog endpoint: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/catalog/items/<string:item_id>', methods=['GET'])
def get_catalog_item(item_id: str):
    """
    Obtiene un item específico del catálogo
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Construir URL
        url = f"{catalogo_url}/api/v1/catalog/items/{item_id}"
        
        current_app.logger.info(f"Calling catalog service: {url}")
        
        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Catalog service error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al consultar producto",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"Catalog service success: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de catálogo: {catalogo_url}")
        return jsonify(error="Timeout al consultar producto"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de catálogo: {e}")
        return jsonify(error="Error de conexión con servicio de catálogo"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en catalog endpoint: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/catalog/items/<string:item_id>/inventario', methods=['GET'])
def get_item_inventory(item_id: str):
    """
    Obtiene el inventario de un item específico
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Construir parámetros
        params = {
            'page': request.args.get('page', 1),
            'size': request.args.get('size', 50)
        }
        
        # Construir URL
        url = f"{catalogo_url}/api/v1/catalog/items/{item_id}/inventario"
        
        current_app.logger.info(f"Calling catalog service: {url} with params: {params}")
        
        response = requests.get(
            url,
            params=params,
            timeout=10,
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Catalog service error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al consultar inventario",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"Catalog service success: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de catálogo: {catalogo_url}")
        return jsonify(error="Timeout al consultar inventario"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de catálogo: {e}")
        return jsonify(error="Error de conexión con servicio de catálogo"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en catalog endpoint: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/catalog/items', methods=['POST'])
def create_catalog_item():
    """
    Crea un nuevo item en el catálogo
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Obtener datos del body
        item_data = request.get_json()
        if not item_data:
            return jsonify(error="Request body required"), 400
        
        # Construir URL
        url = f"{catalogo_url}/api/v1/catalog/items"
        
        current_app.logger.info(f"Calling catalog service: {url}")
        
        response = requests.post(
            url,
            json=item_data,
            timeout=10,
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
                "Content-Type": "application/json"
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Catalog service error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al crear producto",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"Catalog service success: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de catálogo: {catalogo_url}")
        return jsonify(error="Timeout al crear producto"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de catálogo: {e}")
        return jsonify(error="Error de conexión con servicio de catálogo"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en catalog endpoint: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/catalog/items/<string:item_id>', methods=['PUT'])
def update_catalog_item(item_id: str):
    """
    Actualiza un item existente del catálogo
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Obtener datos del body
        item_data = request.get_json()
        if not item_data:
            return jsonify(error="Request body required"), 400
        
        # Construir URL
        url = f"{catalogo_url}/api/v1/catalog/items/{item_id}"
        
        current_app.logger.info(f"Calling catalog service: {url}")
        
        response = requests.put(
            url,
            json=item_data,
            timeout=10,
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
                "Content-Type": "application/json"
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Catalog service error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al actualizar producto",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"Catalog service success: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de catálogo: {catalogo_url}")
        return jsonify(error="Timeout al actualizar producto"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de catálogo: {e}")
        return jsonify(error="Error de conexión con servicio de catálogo"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en catalog endpoint: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/catalog/items/<string:item_id>', methods=['DELETE'])
def delete_catalog_item(item_id: str):
    """
    Elimina un item del catálogo
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Construir URL
        url = f"{catalogo_url}/api/v1/catalog/items/{item_id}"
        
        current_app.logger.info(f"Calling catalog service: {url}")
        
        response = requests.delete(
            url,
            timeout=10,
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Catalog service error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error al eliminar producto",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"Catalog service success: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout al conectar con servicio de catálogo: {catalogo_url}")
        return jsonify(error="Timeout al eliminar producto"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error conectando con servicio de catálogo: {e}")
        return jsonify(error="Error de conexión con servicio de catálogo"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en catalog endpoint: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/catalog/health', methods=['GET'])
def catalog_health_check():
    """
    Health check del servicio de catálogo
    """
    catalogo_url = get_catalogo_service_url()
    
    if not catalogo_url:
        return jsonify(
            status="unhealthy",
            reason="CATALOG_SERVICE_URL no configurada"
        ), 503
    
    try:
        response = requests.get(
            f"{catalogo_url}/health",
            timeout=5
        )
        
        if response.status_code == 200:
            return jsonify(
                status="healthy",
                catalog_service="connected",
                catalog_url=catalogo_url
            ), 200
        else:
            return jsonify(
                status="degraded",
                catalog_service="error",
                status_code=response.status_code,
                catalog_url=catalogo_url
            ), 503
            
    except Timeout:
        return jsonify(
            status="unhealthy",
            catalog_service="timeout",
            catalog_url=catalogo_url
        ), 503
    except Exception as e:
        return jsonify(
            status="unhealthy",
            catalog_service="disconnected",
            error=str(e),
            catalog_url=catalogo_url
        ), 503


@bp.route('/api/v1/catalog/items/bulk-upload', methods=['POST'])
def bulk_upload_products():
    """
    Carga masiva de productos desde Excel o CSV
    HU021 - Proxy hacia catalogo-service
    
    Permite a proveedores registrar productos médicos de manera masiva.
    
    Query params:
    - proveedor_id: ID del proveedor (requerido)
    - reemplazar_duplicados: Si es true, reemplaza productos duplicados (default: false)
    
    Body:
    - file: Archivo Excel (.xlsx) o CSV (.csv)
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Verificar que se envió un archivo
        if 'file' not in request.files:
            return jsonify(error="No se envió ningún archivo"), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify(error="No se seleccionó ningún archivo"), 400
        
        # Obtener parámetros de query
        proveedor_id = request.args.get('proveedor_id')
        if not proveedor_id:
            return jsonify(error="proveedor_id es requerido"), 400
        
        reemplazar_duplicados = request.args.get('reemplazar_duplicados', 'false').lower() == 'true'
        
        # Construir URL con parámetros
        url = f"{catalogo_url}/api/v1/catalog/items/bulk-upload"
        params = {
            'proveedor_id': proveedor_id,
            'reemplazar_duplicados': reemplazar_duplicados
        }
        
        current_app.logger.info(f"📤 Bulk upload: {url} (proveedor: {proveedor_id})")
        
        # Reenviar archivo al servicio de catálogo
        files = {
            'file': (file.filename, file.stream, file.content_type)
        }
        
        response = requests.post(
            url,
            params=params,
            files=files,
            timeout=60,  # 60 segundos para carga masiva
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Bulk upload error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error en carga masiva",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"✅ Bulk upload success: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout en bulk upload: {catalogo_url}")
        return jsonify(error="Timeout en carga masiva"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error en bulk upload: {e}")
        return jsonify(error="Error de conexión con servicio de catálogo"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en bulk upload: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


@bp.route('/api/v1/catalog/bulk-upload/status/<string:task_id>', methods=['GET'])
def get_bulk_upload_status(task_id: str):
    """
    Consulta el estado de una carga masiva asíncrona
    HU021 - Proxy hacia catalogo-service
    
    Retorna el estado actual de la tarea con progreso y resultados.
    
    Estados posibles:
    - pending: En cola esperando procesamiento
    - processing: Siendo procesado por el worker
    - completed: Completado con éxito
    - failed: Falló el procesamiento
    
    Response:
    - task_id: ID de la tarea
    - status: Estado actual
    - progress: {total, processed, successful, failed}
    - result: Resultado final (solo si completed)
    - error: Mensaje de error (solo si failed)
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        url = f"{catalogo_url}/api/v1/catalog/bulk-upload/status/{task_id}"
        
        current_app.logger.info(f"📊 Getting bulk upload status: {task_id}")
        
        response = requests.get(
            url,
            timeout=5,
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Get status error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error consultando estado de tarea",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"✅ Status retrieved: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout consultando estado: {task_id}")
        return jsonify(error="Timeout consultando estado de tarea"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error consultando estado: {e}")
        return jsonify(error="Error de conexión con servicio de catálogo"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado consultando estado: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500


# ============================================================================
# ENDPOINTS DE PROVEEDORES (CRUD)
# ============================================================================

@bp.route('/api/v1/catalog/proveedores', methods=['GET'])
def listar_proveedores():
    """
    Lista todos los proveedores
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Construir parámetros de query
        params = {}
        if request.args.get('page'):
            params['page'] = request.args.get('page')
        if request.args.get('size'):
            params['size'] = request.args.get('size')
        if request.args.get('activo'):
            params['activo'] = request.args.get('activo')
        
        # Construir URL (sin /catalog ya que proveedores está en /api/v1/proveedores/ del ALB)
        # Remover /catalog del catalogo_url si existe para proveedores
        base_url = catalogo_url.replace('/catalog', '')
        url = f"{base_url}/api/v1/proveedores/"
        
        current_app.logger.info(f"Calling catalog service: {url}")
        
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
        current_app.logger.error("Timeout al listar proveedores")
        return jsonify(error="Timeout al conectar con servicio de catálogo"), 504
    except RequestException as e:
        current_app.logger.error(f"Error al listar proveedores: {str(e)}")
        return jsonify(error="Error al conectar con servicio de catálogo"), 503


@bp.route('/api/v1/catalog/proveedores', methods=['POST'])
def crear_proveedor():
    """
    Crea un nuevo proveedor
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Obtener datos del body
        data = request.get_json()
        if not data:
            return jsonify(error="Body vacío"), 400
        
        # Construir URL (sin /catalog ya que proveedores está en /api/v1/proveedores/ del ALB)
        base_url = catalogo_url.replace('/catalog', '')
        url = f"{base_url}/api/v1/proveedores/"
        
        current_app.logger.info(f"Creating proveedor at: {url}")
        
        # Hacer request al servicio
        response = requests.post(
            url,
            json=data,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        # Retornar respuesta del servicio
        return jsonify(response.json()), response.status_code
        
    except Timeout:
        current_app.logger.error("Timeout al crear proveedor")
        return jsonify(error="Timeout al conectar con servicio de catálogo"), 504
    except RequestException as e:
        current_app.logger.error(f"Error al crear proveedor: {str(e)}")
        return jsonify(error="Error al conectar con servicio de catálogo"), 503


@bp.route('/api/v1/catalog/proveedores/<string:proveedor_id>', methods=['GET'])
def obtener_proveedor(proveedor_id):
    """
    Obtiene un proveedor por ID
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Construir URL (sin /catalog ya que proveedores está en /api/v1/proveedores/ del ALB)
        base_url = catalogo_url.replace('/catalog', '')
        url = f"{base_url}/api/v1/proveedores/{proveedor_id}"
        
        current_app.logger.info(f"Getting proveedor: {url}")
        
        # Hacer request al servicio
        response = requests.get(
            url,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        # Retornar respuesta del servicio
        return jsonify(response.json()), response.status_code
        
    except Timeout:
        current_app.logger.error("Timeout al obtener proveedor")
        return jsonify(error="Timeout al conectar con servicio de catálogo"), 504
    except RequestException as e:
        current_app.logger.error(f"Error al obtener proveedor: {str(e)}")
        return jsonify(error="Error al conectar con servicio de catálogo"), 503


@bp.route('/api/v1/catalog/proveedores/<string:proveedor_id>', methods=['PUT'])
def actualizar_proveedor(proveedor_id):
    """
    Actualiza un proveedor existente
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Obtener datos del body
        data = request.get_json()
        if not data:
            return jsonify(error="Body vacío"), 400
        
        # Construir URL (sin /catalog ya que proveedores está en /api/v1/proveedores/ del ALB)
        base_url = catalogo_url.replace('/catalog', '')
        url = f"{base_url}/api/v1/proveedores/{proveedor_id}"
        
        current_app.logger.info(f"Updating proveedor: {url}")
        
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
        current_app.logger.error("Timeout al actualizar proveedor")
        return jsonify(error="Timeout al conectar con servicio de catálogo"), 504
    except RequestException as e:
        current_app.logger.error(f"Error al actualizar proveedor: {str(e)}")
        return jsonify(error="Error al conectar con servicio de catálogo"), 503


@bp.route('/api/v1/catalog/proveedores/<string:proveedor_id>', methods=['DELETE'])
def eliminar_proveedor(proveedor_id):
    """
    Elimina (soft delete) un proveedor
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Construir URL (sin /catalog ya que proveedores está en /api/v1/proveedores/ del ALB)
        base_url = catalogo_url.replace('/catalog', '')
        url = f"{base_url}/api/v1/proveedores/{proveedor_id}"
        
        current_app.logger.info(f"Deleting proveedor: {url}")
        
        # Hacer request al servicio
        response = requests.delete(
            url,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        # Retornar respuesta del servicio
        return jsonify(response.json()), response.status_code
        
    except Timeout:
        current_app.logger.error("Timeout al eliminar proveedor")
        return jsonify(error="Timeout al conectar con servicio de catálogo"), 504
    except RequestException as e:
        current_app.logger.error(f"Error al eliminar proveedor: {str(e)}")
        return jsonify(error="Error al conectar con servicio de catálogo"), 503


@bp.route('/api/v1/catalog/proveedores/<string:proveedor_id>/productos', methods=['GET'])
def listar_productos_proveedor(proveedor_id):
    """
    Lista los productos de un proveedor
    Proxy hacia catalogo-service
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Construir parámetros de query
        params = {}
        if request.args.get('page'):
            params['page'] = request.args.get('page')
        if request.args.get('size'):
            params['size'] = request.args.get('size')
        
        # Construir URL (sin /catalog ya que proveedores está en /api/v1/proveedores/ del ALB)
        base_url = catalogo_url.replace('/catalog', '')
        url = f"{base_url}/api/v1/proveedores/{proveedor_id}/productos"
        
        current_app.logger.info(f"Getting productos for proveedor: {url}")
        
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
        current_app.logger.error("Timeout al listar productos del proveedor")
        return jsonify(error="Timeout al conectar con servicio de catálogo"), 504
    except RequestException as e:
        current_app.logger.error(f"Error al listar productos del proveedor: {str(e)}")
        return jsonify(error="Error al conectar con servicio de catálogo"), 503


# ============================================================================
# ENDPOINTS DE CARGA MASIVA DE PROVEEDORES
# ============================================================================

@bp.route('/api/v1/catalog/proveedores/bulk-upload', methods=['POST'])
def bulk_upload_proveedores():
    """
    Carga masiva de proveedores desde Excel o CSV
    Proxy hacia catalogo-service
    
    Permite registrar proveedores de manera masiva desde un archivo.
    
    Query params:
    - reemplazar_duplicados: Si es true, reemplaza proveedores duplicados (default: false)
    
    Body:
    - file: Archivo Excel (.xlsx) o CSV (.csv)
    
    Expected columns:
    - nombre: Nombre del proveedor (requerido)
    - nit: NIT del proveedor (requerido, único)
    - email: Email de contacto (requerido)
    - telefono: Teléfono de contacto
    - direccion: Dirección física
    - pais: País de origen (código ISO)
    - ciudad: Ciudad
    - activo: Estado activo (true/false, default: true)
    """
    catalogo_url = get_catalogo_service_url()
    if not catalogo_url:
        return jsonify(error="Servicio de catálogo no disponible"), 503
    
    try:
        # Verificar que se envió un archivo
        if 'file' not in request.files:
            return jsonify(error="No se envió ningún archivo"), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify(error="No se seleccionó ningún archivo"), 400
        
        # Verificar extensión del archivo
        import os as os_module
        allowed_extensions = {'.xlsx', '.xls', '.csv'}
        file_ext = os_module.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return jsonify(
                error="Formato de archivo no válido",
                message="Use archivos Excel (.xlsx, .xls) o CSV (.csv)"
            ), 400
        
        # Obtener parámetros de query
        reemplazar_duplicados = request.args.get('reemplazar_duplicados', 'false').lower() == 'true'
        
        # Construir URL con parámetros (sin /catalog ya que proveedores está en /api/v1/proveedores/ del ALB)
        base_url = catalogo_url.replace('/catalog', '')
        url = f"{base_url}/api/v1/proveedores/bulk-upload"
        params = {
            'reemplazar_duplicados': reemplazar_duplicados
        }
        
        current_app.logger.info(f"📤 Bulk upload proveedores: {url}")
        current_app.logger.info(f"   Archivo: {file.filename}, Reemplazar: {reemplazar_duplicados}")
        
        # Reenviar archivo al servicio de catálogo
        files = {
            'file': (file.filename, file.stream, file.content_type)
        }
        
        response = requests.post(
            url,
            params=params,
            files=files,
            timeout=60,  # 60 segundos para carga masiva
            headers={
                "User-Agent": "BFF-Venta/1.0",
                "X-Request-ID": request.headers.get("X-Request-ID", "no-id"),
            }
        )
        
        # Si el servicio responde con error, propagar el error
        if response.status_code >= 400:
            current_app.logger.warning(
                f"Bulk upload error: {response.status_code} - {response.text[:200]}"
            )
            
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text[:200]}
            
            return jsonify(
                error="Error en carga masiva de proveedores",
                details=error_data
            ), response.status_code
        
        # Respuesta exitosa
        current_app.logger.info(f"✅ Bulk upload proveedores success: {response.status_code}")
        
        try:
            return jsonify(response.json()), response.status_code
        except:
            return jsonify({"data": response.text}), response.status_code
        
    except Timeout:
        current_app.logger.error(f"Timeout en bulk upload proveedores: {catalogo_url}")
        return jsonify(error="Timeout en carga masiva"), 504
    
    except RequestException as e:
        current_app.logger.error(f"Error en bulk upload proveedores: {e}")
        return jsonify(error="Error de conexión con servicio de catálogo"), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en bulk upload proveedores: {e}", exc_info=True)
        return jsonify(error="Error interno del servidor"), 500