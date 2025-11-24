from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from app.models.catalogo_model import Producto, Inventario, Bodega
from typing import Optional, Dict, List

async def buscar_productos(session: AsyncSession, *,
                           q: Optional[str], categoriaId: Optional[str], codigo: Optional[str],
                           pais: Optional[str], bodegaId: Optional[str],
                           page: int, size: int, sort: Optional[str]):

    stmt = select(Producto).where(Producto.activo.is_(True))
    if q:
        stmt = stmt.where(func.lower(Producto.nombre).like(f"%{q.lower()}%"))
    if categoriaId:
        stmt = stmt.where(Producto.categoria_id == categoriaId)
    if codigo:
        stmt = stmt.where(Producto.codigo == codigo)

    # Para contar, crear consulta separada SIN order by
    count_stmt = select(func.count()).select_from(Producto).where(Producto.activo.is_(True))
    if q:
        count_stmt = count_stmt.where(func.lower(Producto.nombre).like(f"%{q.lower()}%"))
    if categoriaId:
        count_stmt = count_stmt.where(Producto.categoria_id == categoriaId)
    if codigo:
        count_stmt = count_stmt.where(Producto.codigo == codigo)
    
    total = (await session.execute(count_stmt)).scalar_one()

    # Orden para la consulta de datos
    if sort == "precio":
        stmt = stmt.order_by(Producto.precio_unitario.asc())
    else:
        stmt = stmt.order_by(Producto.nombre.asc())

    rows = (await session.execute(stmt.offset((page-1)*size).limit(size))).scalars().all()

    # inventario resumen con información de bodegas
    ids = [r.id for r in rows]
    if not ids:
        return rows, 0, {}

    # Query para obtener inventario agrupado por producto con info de bodegas
    # Primero obtener la suma total y países únicos
    inv_summary = select(
        Inventario.producto_id,
        func.sum(Inventario.cantidad).label("cantidad_total"),
        func.array_agg(func.distinct(Inventario.pais)).label("paises")
    ).where(Inventario.producto_id.in_(ids))
    
    if pais:
        inv_summary = inv_summary.where(Inventario.pais == pais)
    if bodegaId:
        inv_summary = inv_summary.where(Inventario.bodega_id == bodegaId)
    
    inv_summary = inv_summary.group_by(Inventario.producto_id)
    summary_rows = (await session.execute(inv_summary)).all()
    
    # Query para obtener detalle de bodegas por producto
    inv_bodegas = select(
        Inventario.producto_id,
        Inventario.bodega_id,
        Bodega.id.label("bodega_uuid"),  # UUID de la bodega
        Bodega.codigo.label("bodega_codigo"),  # Código de la bodega
        Bodega.nombre.label("bodega_nombre"),
        Bodega.ciudad,
        Bodega.pais,
        func.sum(Inventario.cantidad).label("cantidad")
    ).join(
        Bodega, Inventario.bodega_id == Bodega.id
    ).where(
        Inventario.producto_id.in_(ids),
        Inventario.cantidad > 0  # Solo bodegas con stock
    )
    
    if pais:
        inv_bodegas = inv_bodegas.where(Inventario.pais == pais)
    if bodegaId:
        inv_bodegas = inv_bodegas.where(Inventario.bodega_id == bodegaId)
    
    inv_bodegas = inv_bodegas.group_by(
        Inventario.producto_id,
        Inventario.bodega_id,
        Bodega.id,
        Bodega.codigo,
        Bodega.nombre,
        Bodega.ciudad,
        Bodega.pais
    ).order_by(
        Inventario.producto_id,
        func.sum(Inventario.cantidad).desc()  # Ordenar por mayor cantidad
    )
    
    bodega_rows = (await session.execute(inv_bodegas)).all()
    
    # Construir mapa de inventario con bodegas
    inv_map: Dict[str, Dict] = {}
    
    # Agregar resumen (cantidad total y países)
    for r in summary_rows:
        inv_map[r.producto_id] = {
            "cantidad": int(r.cantidad_total or 0),
            "paises": list(r.paises or []),
            "bodegas": []
        }
    
    # Agregar información de bodegas
    for r in bodega_rows:
        if r.producto_id in inv_map:
            inv_map[r.producto_id]["bodegas"].append({
                "id": r.bodega_uuid,  # UUID de la bodega
                "codigo": r.bodega_codigo,  # Código de negocio
                "nombre": r.bodega_nombre,
                "ciudad": r.ciudad,
                "pais": r.pais,
                "cantidad": int(r.cantidad or 0)
            })
    
    return rows, total, inv_map

async def detalle_inventario(session: AsyncSession, producto_id: str, page:int, size:int):
    base = select(Inventario).where(Inventario.producto_id == producto_id)
    total = (await session.execute(base.with_only_columns(func.count()))).scalar_one()
    rows = (await session.execute(base.order_by(Inventario.vence.asc())
                        .offset((page-1)*size).limit(size))).scalars().all()
    return rows, total
