# app/websockets/ws_catalog_router.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.db import get_session
from app.repositories.catalog_repo import buscar_productos
import asyncio
import json
import hashlib
import logging
import time

# Configuración
router = APIRouter(tags=["WebSocket - Catalog"])
logger = logging.getLogger(__name__)

@router.websocket("/items/ws")
async def catalog_websocket(websocket: WebSocket, session = Depends(get_session)):
    """
    WebSocket para catálogo en tiempo real.
    
    El cliente envía:
    {
        "q": "busqueda",           # Opcional
        "categoriaId": "...",      # Opcional
        "codigo": "...",           # Opcional
        "pais": "...",             # Opcional
        "bodegaId": "...",         # Opcional
        "page": 1,                 # Default: 1
        "size": 20,                # Default: 20
        "sort": "relevancia"       # Opcional
    }
    
    El servidor responde:
    {
        "items": [...],
        "meta": {
            "page": 1,
            "size": 20,
            "total": 156,
            "tookMs": 45
        }
    }
    """
    await websocket.accept()
    # Obtener host de forma segura (starlette/uvicorn puede exponer websocket.client como tupla)
    try:
        client_host = websocket.client.host
    except Exception:
        try:
            client_host = websocket.client[0]
        except Exception:
            client_host = "desconocido"

    logger.info(f"✅ Cliente WebSocket conectado: {client_host}")
    
    # Parámetros por defecto
    query_params = {
        "q": None,
        "categoriaId": None,
        "codigo": None,
        "pais": None,
        "bodegaId": None,
        "page": 1,
        "size": 20,
        "sort": None
    }
    
    last_payload_hash = None  # Para evitar envios duplicados
    
    # Leer parametros iniciales del cliente (timeout 2 segundos)
    try:
        initial_data = await asyncio.wait_for(websocket.receive_text(), timeout=2.0)
        initial_params = json.loads(initial_data)
        query_params.update(initial_params)
        logger.info(f"📥 Parametros iniciales: {query_params}")
    except asyncio.TimeoutError:
        logger.info("⏱️ Sin parametros iniciales, usando valores por defecto")
    except json.JSONDecodeError:
        logger.warning("⚠️ JSON invalido en parametros iniciales")
    except WebSocketDisconnect:
        logger.info(f"❌ Cliente desconectado durante inicializacion: {client_host}")
        return
    
    try:
        while True:
            # 1️⃣ Consultar productos con los parametros actuales
            started = time.perf_counter_ns()
            
            rows, total, inv_map = await buscar_productos(
                session, 
                q=query_params.get("q"), 
                categoriaId=query_params.get("categoriaId"), 
                codigo=query_params.get("codigo"),
                pais=query_params.get("pais"), 
                bodegaId=query_params.get("bodegaId"), 
                page=query_params.get("page", 1), 
                size=query_params.get("size", 20), 
                sort=query_params.get("sort")
            )
            
            # 2️⃣ Construir respuesta (igual que el endpoint REST)
            items = []
            for r in rows:
                item = {
                    "id": r.id,
                    "nombre": r.nombre,
                    "codigo": r.codigo,
                    "categoria": r.categoria_id,
                    "presentacion": r.presentacion,
                    "precioUnitario": float(r.precio_unitario),
                    "requisitosAlmacenamiento": r.requisitos_almacenamiento,
                    "certificadoSanitario": r.certificado_sanitario,
                    "tiempoEntregaDias": r.tiempo_entrega_dias,
                    "proveedorId": r.proveedor_id,
                }
                
                # Agregar inventario si existe
                if r.id in inv_map:
                    item["inventarioResumen"] = {
                        "cantidadTotal": inv_map[r.id]["cantidad"],
                        "paises": sorted(inv_map[r.id]["paises"])
                    }
                else:
                    item["inventarioResumen"] = None
                
                items.append(item)
            
            took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
            
            response_payload = {
                "items": items,
                "meta": {
                    "page": query_params.get("page", 1),
                    "size": query_params.get("size", 20),
                    "total": total,
                    "tookMs": took_ms
                }
            }
            
            # 3️⃣ Calcular hash para detectar cambios
            response_str = json.dumps(response_payload, sort_keys=True, default=str)
            current_hash = hashlib.md5(response_str.encode()).hexdigest()
            
            # 4️⃣ Solo enviar si los datos cambiaron
            if current_hash != last_payload_hash:
                await websocket.send_text(response_str)
                last_payload_hash = current_hash
                logger.info(
                    f"📤 Datos enviados: {len(items)} items, page={query_params.get('page')}, "
                    f"total={total}, took={took_ms}ms"
                )
            
            # 5️⃣ Esperar 3 segundos o nuevos parametros del cliente
            sleep_task = asyncio.create_task(asyncio.sleep(3))
            receive_task = asyncio.create_task(websocket.receive_text())
            
            done, pending = await asyncio.wait(
                [sleep_task, receive_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancelar tareas pendientes y esperar su finalizacion para evitar warnings
            for task in pending:
                task.cancel()
            if pending:
                # Esperar para limpiar tareas canceladas y evitar 'Task was destroyed but it is pending'
                await asyncio.gather(*pending, return_exceptions=True)
            
            # 6️⃣ Si el cliente envio nuevos parametros, actualizarlos
            if receive_task in done:
                try:
                    updated_data = receive_task.result()
                    updated_params = json.loads(updated_data)
                    query_params.update(updated_params)
                    logger.info(f"🔄 Parametros actualizados: {query_params}")
                except WebSocketDisconnect:
                    # Reenviar para que el handler exterior cierre la conexion
                    raise
                except json.JSONDecodeError:
                    logger.warning("⚠️ JSON invalido recibido del cliente")
                except Exception as e:
                    logger.warning(f"⚠️ Error procesando parametros: {e}")
            
    except WebSocketDisconnect:
        logger.info(f"❌ Cliente desconectado: {websocket.client.host}")
    except Exception as e:
        logger.error(f"❌ Error en WebSocket: {e}")
        try:
            await websocket.close(code=1011)
        except:
            pass