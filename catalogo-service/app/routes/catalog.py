from fastapi import APIRouter, Depends, Query, Request, HTTPException, status
from app.db import get_session
from app.schemas import SearchResponse, ProductCreate, ProductUpdate
from app.repositories.catalog_repo import buscar_productos, detalle_inventario
from app.config import settings
from sqlalchemy import select, update, delete
from app.models.catalogo_model import Producto
import time
import logging

router = APIRouter(prefix="/catalog", tags=["catalog"])
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
        item = {
            "id": r.id,
            "nombre": r.nombre,
            "codigo": r.codigo,
            "categoria": r.categoria_id,
            "presentacion": r.presentacion,
            "precioUnitario": float(r.precio_unitario),
            "requisitosAlmacenamiento": r.requisitos_almacenamiento,
        }
        
        # Agregar resumen de inventario si existe
        if r.id in inv_map:
            item["inventarioResumen"] = {
                "cantidadTotal": inv_map[r.id]["cantidad"],
                "paises": sorted(inv_map[r.id]["paises"])  # Ordenar para consistencia
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
        "requisitosAlmacenamiento": row.requisitos_almacenamiento
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
    Crea un nuevo producto en el catálogo
    """
    logger.info(f"📝 Creando producto: {product.id}")
    
    # Verificar si el producto ya existe
    existing = (await session.execute(
        select(Producto).where(Producto.id == product.id)
    )).scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Producto con id {product.id} ya existe"
        )
    
    # Crear nuevo producto
    new_product = Producto(
        id=product.id,
        nombre=product.nombre,
        codigo=product.codigo,
        categoria_id=product.categoria,
        presentacion=product.presentacion,
        precio_unitario=product.precioUnitario,
        requisitos_almacenamiento=product.requisitosAlmacenamiento
    )
    
    session.add(new_product)
    await session.commit()
    await session.refresh(new_product)
    
    logger.info(f"✅ Producto creado: {product.id}")
    
    return {
        "id": new_product.id,
        "nombre": new_product.nombre,
        "codigo": new_product.codigo,
        "categoria": new_product.categoria_id,
        "presentacion": new_product.presentacion,
        "precioUnitario": float(new_product.precio_unitario),
        "requisitosAlmacenamiento": new_product.requisitos_almacenamiento
    }

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
