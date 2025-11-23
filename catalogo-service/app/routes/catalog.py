from fastapi import APIRouter, Depends, Query, Request, HTTPException, status, UploadFile
from app.db import get_session
from app.schemas import SearchResponse, ProductCreate, ProductUpdate
from app.repositories.catalog_repo import buscar_productos, detalle_inventario
from app.config import settings
from sqlalchemy import select, update, delete
from app.models.catalogo_model import Producto
import time
import logging

router = APIRouter(tags=["catalog"])
logger = logging.getLogger(__name__)

@router.get("/items", response_model=SearchResponse)
async def list_items(
    request: Request,
    q: str | None = None,
    categoriaId: str | None = None,
    codigo: str | None = None,
    pais: str | None = None,
    bodegaId: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(settings.page_size_default, ge=1, le=settings.page_size_max),
    sort: str | None = Query(None, pattern="^(relevancia|precio|cantidad|vencimiento)?$"),
    session = Depends(get_session)
):
    """
    Lista productos del catálogo con filtros opcionales.
    Consulta directamente desde la base de datos.
    """
    logger.info(f"🔍 Búsqueda: q={q}, categoriaId={categoriaId}, codigo={codigo}, pais={pais}, bodegaId={bodegaId}, page={page}, size={size}")
    
    started = time.perf_counter_ns()
    
    # Consulta directa a la base de datos
    rows, total, inv_map = await buscar_productos(
        session, 
        q=q, 
        categoriaId=categoriaId, 
        codigo=codigo,
        pais=pais, 
        bodegaId=bodegaId, 
        page=page, 
        size=size, 
        sort=sort
    )
    
    # Construir respuesta
    items = []
    for r in rows:
        # DEBUG: Log valores de campos de proveedor
        if hasattr(r, 'id') and r.id.startswith('PROD_BULK'):
            logger.info(f"   DEBUG: {r.id} -> cert={getattr(r, 'certificado_sanitario', 'NO ATTR')}, dias={getattr(r, 'tiempo_entrega_dias', 'NO ATTR')}, prov={getattr(r, 'proveedor_id', 'NO ATTR')}")
        
        item = {
            "id": r.id,
            "nombre": r.nombre,
            "codigo": r.codigo,
            "categoria": r.categoria_id,
            "presentacion": r.presentacion,
            "precioUnitario": float(r.precio_unitario),
            "requisitosAlmacenamiento": r.requisitos_almacenamiento,
            # HU021 - Campos de proveedor
            "certificadoSanitario": r.certificado_sanitario,
            "tiempoEntregaDias": r.tiempo_entrega_dias,
            "proveedorId": r.proveedor_id,
        }
        
        # Agregar resumen de inventario si existe
        if r.id in inv_map:
            item["inventarioResumen"] = {
                "cantidadTotal": inv_map[r.id]["cantidad"],
                "paises": sorted(inv_map[r.id]["paises"]),  # Ordenar para consistencia
                "bodegas": inv_map[r.id].get("bodegas", [])  # Incluir info de bodegas
            }
        else:
            item["inventarioResumen"] = None
        
        items.append(item)

    took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
    
    logger.info(f"✅ Búsqueda completada: {len(items)} items de {total} en {took_ms}ms")
    
    return {
        "items": items, 
        "meta": {
            "page": page, 
            "size": size, 
            "total": total, 
            "tookMs": took_ms
        }
    }

@router.get("/items/{id}")
async def get_product(id: str, session=Depends(get_session)):
    # …consulta sencilla por id (similar al repo)
    from sqlalchemy import select
    from app.models.catalogo_model import Producto
    row = (await session.execute(select(Producto).where(Producto.id==id))).scalar_one_or_none()
    if not row:
        return {"detail":"Not found"}, 404
    return {
        "id": row.id, "nombre": row.nombre, "codigo": row.codigo, "categoria": row.categoria_id,
        "presentacion": row.presentacion, "precioUnitario": float(row.precio_unitario),
        "requisitosAlmacenamiento": row.requisitos_almacenamiento,
        # HU021 - Campos de proveedor
        "certificadoSanitario": row.certificado_sanitario,
        "tiempoEntregaDias": row.tiempo_entrega_dias,
        "proveedorId": row.proveedor_id
    }

@router.get("/items/{id}/inventario")
async def get_inventory(id: str, page:int=1, size:int=50, session=Depends(get_session)):
    rows, total = await detalle_inventario(session, id, page, size)
    items = [{
        "pais": r.pais, "bodegaId": r.bodega_id, "lote": r.lote,
        "cantidad": r.cantidad, "vence": r.vence.isoformat(), "condiciones": r.condiciones
    } for r in rows]
    return {"items": items, "meta": {"page": page, "size": size, "total": total, "tookMs": 0}}

@router.post("/items", status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, session=Depends(get_session)):
    """
    Crea un nuevo producto en el catálogo.
    
    **Nuevo**: Ahora puedes especificar las bodegas iniciales donde estará disponible el producto.
    Si se especifican, se crearán registros de inventario con stock inicial en 0.
    
    **Campos de Inventario**:
    - `stockMinimo`: Stock mínimo antes de generar alerta (default: 10)
    - `stockCritico`: Stock crítico para alertas críticas (default: 5)
    - `requiereLote`: Si el producto requiere número de lote (default: False)
    - `requiereVencimiento`: Si el producto requiere fecha de vencimiento (default: True)
    
    **Bodegas Iniciales** (opcional):
    - Lista de bodegas donde se habilitará el producto con stock 0
    - Facilita el primer movimiento de INGRESO
    - Si no se especifica, el inventario se crea en el primer INGRESO
    """
    # Generar UUID automáticamente si no se proporciona
    import uuid
    product_id = product.id if product.id else str(uuid.uuid4())
    
    logger.info(f"📝 Creando producto: {product_id}")
    
    try:
        # Verificar si el producto ya existe
        existing = (await session.execute(
            select(Producto).where(Producto.id == product_id)
        )).scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Producto con id {product_id} ya existe"
            )
        
        # Validar proveedorId si se proporciona
        if product.proveedorId:
            try:
                from uuid import UUID
                UUID(product.proveedorId)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "INVALID_PROVEEDOR_ID",
                        "message": f"proveedorId '{product.proveedorId}' no es un UUID válido. Debe tener formato: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                        "field": "proveedorId",
                        "received": product.proveedorId
                    }
                )
        
        # Crear nuevo producto con campos de inventario
        new_product = Producto(
            id=product_id,
            nombre=product.nombre,
            codigo=product.codigo,
            categoria_id=product.categoria,
            presentacion=product.presentacion,
            precio_unitario=product.precioUnitario,
            requisitos_almacenamiento=product.requisitosAlmacenamiento,
            stock_minimo=product.stockMinimo or 10,
            stock_critico=product.stockCritico or 5,
            requiere_lote=product.requiereLote or False,
            requiere_vencimiento=product.requiereVencimiento if product.requiereVencimiento is not None else True,
            certificado_sanitario=product.certificadoSanitario,
            tiempo_entrega_dias=product.tiempoEntregaDias,
            proveedor_id=product.proveedorId
        )
        
        session.add(new_product)
        await session.flush()  # Flush para que el producto exista antes de crear inventarios
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creando producto {product_id}: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "PRODUCT_CREATION_FAILED",
                "message": f"Error al crear producto: {str(e)}",
                "product_id": product_id
            }
        )
    
    # Crear inventarios iniciales si se especificaron bodegas
    bodegas_creadas = []
    if product.bodegasIniciales:
        from app.models.catalogo_model import Inventario
        from datetime import date, datetime
        
        logger.info(f"   📦 Creando {len(product.bodegasIniciales)} registros de inventario inicial")
        
        for bodega in product.bodegasIniciales:
            # Generar lote si no se proporcionó
            lote = bodega.lote or f"INICIAL-{datetime.now().strftime('%Y%m%d')}"
            
            # Usar fecha de vencimiento proporcionada o una fecha muy lejana
            fecha_vence = bodega.fecha_vencimiento or date(2099, 12, 31)
            
            # Crear registro de inventario con cantidad = 0
            inventario_inicial = Inventario(
                producto_id=product_id,
                pais=bodega.pais,
                bodega_id=bodega.bodega_id,
                lote=lote,
                cantidad=0,  # Stock inicial en 0
                vence=fecha_vence,
                condiciones="Producto habilitado - stock inicial en 0"
            )
            
            session.add(inventario_inicial)
            bodegas_creadas.append(f"{bodega.bodega_id} ({bodega.pais})")
            
            logger.info(f"      ✓ Inventario inicial creado en {bodega.bodega_id} ({bodega.pais})")
    
    # Commit para guardar los cambios
    await session.commit()
    await session.refresh(new_product)
    
    log_msg = f"✅ Producto creado: {product_id}"
    if bodegas_creadas:
        log_msg += f" con inventario inicial en: {', '.join(bodegas_creadas)}"
    logger.info(log_msg)
    
    response = {
        "id": new_product.id,
        "nombre": new_product.nombre,
        "codigo": new_product.codigo,
        "categoria": new_product.categoria_id,
        "presentacion": new_product.presentacion,
        "precioUnitario": float(new_product.precio_unitario),
        "requisitosAlmacenamiento": new_product.requisitos_almacenamiento,
        "stockMinimo": new_product.stock_minimo,
        "stockCritico": new_product.stock_critico,
        "requiereLote": new_product.requiere_lote,
        "requiereVencimiento": new_product.requiere_vencimiento
    }
    
    # Agregar info de bodegas si se crearon
    if bodegas_creadas:
        response["bodegasIniciales"] = bodegas_creadas
    
    return response

@router.put("/items/{id}")
async def update_product(id: str, product: ProductUpdate, session=Depends(get_session)):
    """
    Actualiza un producto existente
    """
    logger.info(f"📝 Actualizando producto: {id}")
    
    # Buscar el producto
    existing = (await session.execute(
        select(Producto).where(Producto.id == id)
    )).scalar_one_or_none()
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto {id} no encontrado"
        )
    
    # Actualizar solo los campos proporcionados
    update_data = product.dict(exclude_unset=True)
    
    if update_data:
        # Mapear campos de la API a campos de la base de datos
        db_update_data = {}
        if "nombre" in update_data:
            db_update_data["nombre"] = update_data["nombre"]
        if "codigo" in update_data:
            db_update_data["codigo"] = update_data["codigo"]
        if "categoria" in update_data:
            db_update_data["categoria_id"] = update_data["categoria"]
        if "presentacion" in update_data:
            db_update_data["presentacion"] = update_data["presentacion"]
        if "precioUnitario" in update_data:
            db_update_data["precio_unitario"] = update_data["precioUnitario"]
        if "requisitosAlmacenamiento" in update_data:
            db_update_data["requisitos_almacenamiento"] = update_data["requisitosAlmacenamiento"]
        
        await session.execute(
            update(Producto).where(Producto.id == id).values(**db_update_data)
        )
        await session.commit()
        
        # Recargar el producto actualizado
        await session.refresh(existing)
    
    logger.info(f"✅ Producto actualizado: {id}")
    
    return {
        "id": existing.id,
        "nombre": existing.nombre,
        "codigo": existing.codigo,
        "categoria": existing.categoria_id,
        "presentacion": existing.presentacion,
        "precioUnitario": float(existing.precio_unitario),
        "requisitosAlmacenamiento": existing.requisitos_almacenamiento
    }

@router.delete("/items/{id}")
async def delete_product(id: str, session=Depends(get_session)):
    """
    Elimina un producto del catálogo
    """
    logger.info(f"🗑️ Eliminando producto: {id}")
    
    # Buscar el producto
    existing = (await session.execute(
        select(Producto).where(Producto.id == id)
    )).scalar_one_or_none()
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto {id} no encontrado"
        )
    
    # Eliminar el producto
    await session.execute(
        delete(Producto).where(Producto.id == id)
    )
    await session.commit()
    
    logger.info(f"✅ Producto eliminado: {id}")
    
    return {"message": f"Producto {id} eliminado exitosamente"}


@router.post("/items/bulk-upload", status_code=status.HTTP_202_ACCEPTED)
async def bulk_upload_products(
    file: UploadFile,
    proveedor_id: str = Query(..., description="ID del proveedor que carga los productos"),
    reemplazar_duplicados: bool = Query(False, description="Si es true, reemplaza productos duplicados; si es false, los ignora")
):
    """
    **HU021 - Carga masiva de productos desde Excel o CSV (ASÍNCRONO con SQS)**
    
    Permite a un proveedor registrar productos médicos de manera masiva.
    El archivo se sube a S3 y se procesa de forma asíncrona mediante SQS.
    
    **Retorna inmediatamente** con un task_id para consultar el estado.
    
    ### Formato del archivo:
    
    **Columnas requeridas:**
    - `id`: ID único del producto
    - `nombre`: Nombre del producto (obligatorio)
    - `codigo`: Código o referencia (obligatorio, único)
    - `categoria`: Categoría del producto (obligatorio)
    - `precio_unitario`: Precio unitario (obligatorio)
    - `certificado_sanitario`: Número del certificado sanitario (obligatorio)
    - `condiciones_almacenamiento`: Condiciones de almacenamiento (obligatorio)
    - `tiempo_entrega_dias`: Tiempo estimado de entrega en días (obligatorio)
    
    **Columnas opcionales:**
    - `presentacion`: Presentación del producto
    - `stock_minimo`: Stock mínimo (default: 10)
    - `stock_critico`: Stock crítico (default: 5)
    - `requiere_lote`: Si requiere lote (true/false, default: false)
    - `requiere_vencimiento`: Si requiere fecha de vencimiento (true/false, default: true)
    
    ### Parámetros:
    - `file`: Archivo Excel (.xlsx) o CSV (.csv)
    - `proveedor_id`: ID del proveedor
    - `reemplazar_duplicados`: Si es true, actualiza productos existentes; si es false, los ignora
    
    ### Respuesta:
    - `total`: Total de productos en el archivo
    - `exitosos`: Productos cargados exitosamente
    - `rechazados`: Productos rechazados
    - `duplicados`: Productos duplicados encontrados
    - `errores`: Lista de errores por fila
    - `productos_creados`: Lista de IDs de productos creados
    
    ### Procesamiento Asíncrono:
    1. Archivo se sube a S3
    2. Se crea tarea en Redis
    3. Se envía mensaje a SQS
    4. Worker procesa en background
    5. Consultar estado en GET /bulk-upload/status/{task_id}
    """
    import uuid
    from app.services.aws_service import aws_service
    from app.services.task_service import task_service
    
    logger.info(f"📤 Carga masiva asíncrona - Proveedor: {proveedor_id}, Archivo: {file.filename}")
    
    # Validar tipo de archivo
    if not file.filename.endswith(('.xlsx', '.csv')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de archivo no soportado. Use Excel (.xlsx) o CSV (.csv)"
        )
    
    try:
        # Generar task_id único
        task_id = str(uuid.uuid4())
        
        # Leer archivo en memoria
        file_content = await file.read()
        
        # Subir archivo a S3
        s3_key = await aws_service.upload_file_to_s3(
            file_content=file_content,
            filename=file.filename,
            content_type=file.content_type
        )
        
        # Crear tarea en Redis
        await task_service.create_task(
            task_id=task_id,
            filename=file.filename,
            proveedor_id=proveedor_id,
            s3_key=s3_key
        )
        
        # Enviar mensaje a SQS para procesamiento asíncrono
        await aws_service.send_sqs_message(
            task_id=task_id,
            s3_key=s3_key,
            filename=file.filename,
            proveedor_id=proveedor_id,
            reemplazar_duplicados=reemplazar_duplicados
        )
        
        logger.info(f"✅ Tarea de carga masiva encolada - Task ID: {task_id}")
        
        return {
            "message": "Archivo recibido y encolado para procesamiento",
            "task_id": task_id,
            "status": "pending",
            "status_url": f"/api/catalog/bulk-upload/status/{task_id}",
            "filename": file.filename,
            "proveedor_id": proveedor_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en carga masiva: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando el archivo: {str(e)}"
        )


@router.get("/bulk-upload/status/{task_id}")
async def get_bulk_upload_status(task_id: str):
    """
    Consulta el estado de una carga masiva asíncrona
    
    Args:
        task_id: ID de la tarea retornado por POST /bulk-upload
    
    Returns:
        Estado actual de la tarea con progreso y resultados
    """
    from app.services.task_service import task_service
    
    task = await task_service.get_task(task_id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarea {task_id} no encontrada"
        )
    
    return task
