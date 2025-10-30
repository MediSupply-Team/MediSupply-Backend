"""
Endpoints de API para gestión de movimientos de inventario.

Este módulo expone todos los endpoints necesarios para:
- Registrar ingresos y salidas
- Gestionar transferencias entre bodegas
- Consultar kardex (historial de movimientos)
- Anular movimientos
- Consultar alertas
- Generar reportes de saldos
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from typing import Optional
from datetime import datetime

from app.db import get_session
from app.schemas import (
    MovimientoCreate, MovimientoResponse, TransferenciaCreate, TransferenciaResponse,
    AnularMovimientoRequest, KardexResponse, KardexItem, Meta,
    AlertasListResponse, AlertaResponse, ReporteSaldosResponse, SaldoBodega,
    TipoMovimiento, MotivoMovimiento
)
from app.services.inventario_service import InventarioService
from app.models.movimiento_model import MovimientoInventario, AlertaInventario
from app.models.catalogo_model import Producto, Inventario

import logging

router = APIRouter(prefix="/inventory", tags=["inventory-movements"])
logger = logging.getLogger(__name__)


@router.post("/movements", response_model=MovimientoResponse, status_code=status.HTTP_201_CREATED)
async def registrar_movimiento_inventario(
    movimiento: MovimientoCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    **Registra un movimiento de inventario (ingreso o salida)**
    
    ### Tipos de Movimiento:
    - `INGRESO`: Entrada de producto (compra, devolución, producción)
    - `SALIDA`: Salida de producto (venta, merma, ajuste)
    - `TRANSFERENCIA_SALIDA`: Salida por transferencia (usar endpoint /transfers)
    - `TRANSFERENCIA_INGRESO`: Ingreso por transferencia (usar endpoint /transfers)
    
    ### Validaciones:
    - ✅ Producto debe existir
    - ✅ Si el producto requiere lote, debe especificarse
    - ✅ Si el producto requiere fecha de vencimiento, debe especificarse
    - ✅ No permite stock negativo (excepto con permiso explícito)
    - ✅ Genera alertas automáticas si el stock queda bajo
    
    ### Actualización en Tiempo Real:
    - El stock se actualiza inmediatamente en la misma transacción
    - El saldo actualizado es visible de inmediato
    
    ### Respuesta:
    - **201**: Movimiento registrado exitosamente con saldos antes/después
    - **400**: Error de validación o stock insuficiente
    - **404**: Producto no encontrado
    - **500**: Error interno del servidor
    """
    try:
        async with session.begin():
            mov, alertas = await InventarioService.registrar_movimiento(session, movimiento)
            
            # Log de alertas generadas
            for alerta in alertas:
                logger.warning(f"⚠️ {alerta.tipo_alerta}: {alerta.mensaje}")
        
        await session.refresh(mov)
        
        response = MovimientoResponse.model_validate(mov)
        
        if alertas:
            logger.info(f"✅ Movimiento creado con {len(alertas)} alerta(s)")
        else:
            logger.info("✅ Movimiento creado sin alertas")
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error registrando movimiento: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "Error interno al registrar movimiento",
                "details": str(e)
            }
        )


@router.post("/transfers", response_model=TransferenciaResponse, status_code=status.HTTP_201_CREATED)
async def registrar_transferencia(
    transferencia: TransferenciaCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    **Registra una transferencia entre bodegas**
    
    ### Proceso:
    1. Valida stock disponible en bodega origen
    2. Registra SALIDA en bodega origen
    3. Registra INGRESO en bodega destino
    4. Vincula ambos movimientos para trazabilidad
    5. Genera alertas si es necesario
    
    ### Validaciones:
    - ✅ Debe haber stock suficiente en origen
    - ✅ Ambos movimientos se crean en la misma transacción (atomic)
    - ✅ Si falla alguno, se revierten ambos
    
    ### Respuesta:
    - **201**: Transferencia completada exitosamente
    - **400**: Stock insuficiente o validación fallida
    - **404**: Producto no encontrado
    - **500**: Error interno
    """
    try:
        async with session.begin():
            mov_salida, mov_ingreso, alertas = await InventarioService.registrar_transferencia(
                session, transferencia
            )
        
        for alerta in alertas:
            logger.warning(f"⚠️ {alerta.tipo_alerta}: {alerta.mensaje}")
        
        return TransferenciaResponse(
            message="Transferencia registrada exitosamente",
            movimiento_salida_id=mov_salida.id,
            movimiento_ingreso_id=mov_ingreso.id,
            saldo_origen=mov_salida.saldo_nuevo,
            saldo_destino=mov_ingreso.saldo_nuevo
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en transferencia: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "Error interno al registrar transferencia",
                "details": str(e)
            }
        )


@router.get("/movements/kardex", response_model=KardexResponse)
async def consultar_kardex(
    producto_id: Optional[str] = Query(None, description="Filtrar por producto"),
    bodega_id: Optional[str] = Query(None, description="Filtrar por bodega"),
    pais: Optional[str] = Query(None, description="Filtrar por país"),
    tipo_movimiento: Optional[str] = Query(None, description="Filtrar por tipo (INGRESO, SALIDA, etc)"),
    motivo: Optional[str] = Query(None, description="Filtrar por motivo (COMPRA, VENTA, etc)"),
    usuario_id: Optional[str] = Query(None, description="Filtrar por usuario"),
    referencia_documento: Optional[str] = Query(None, description="Filtrar por referencia"),
    fecha_desde: Optional[datetime] = Query(None, description="Fecha desde (ISO 8601)"),
    fecha_hasta: Optional[datetime] = Query(None, description="Fecha hasta (ISO 8601)"),
    estado: Optional[str] = Query("ACTIVO", description="Estado (ACTIVO, ANULADO, o null para ambos)"),
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(50, ge=1, le=200, description="Tamaño de página"),
    session: AsyncSession = Depends(get_session)
):
    """
    **Consulta el kardex (historial de movimientos) con filtros**
    
    ### Filtros Disponibles:
    - `producto_id`: Ver movimientos de un producto específico
    - `bodega_id`: Ver movimientos de una bodega
    - `pais`: Ver movimientos de un país
    - `tipo_movimiento`: INGRESO, SALIDA, TRANSFERENCIA_SALIDA, TRANSFERENCIA_INGRESO
    - `motivo`: COMPRA, VENTA, AJUSTE, DEVOLUCION, MERMA, etc.
    - `usuario_id`: Ver movimientos registrados por un usuario
    - `referencia_documento`: Buscar por número de documento
    - `fecha_desde` / `fecha_hasta`: Rango de fechas
    - `estado`: ACTIVO (default), ANULADO, o null para ambos
    
    ### Paginación:
    - `page`: Número de página (default: 1)
    - `size`: Items por página (1-200, default: 50)
    
    ### Respuesta:
    Retorna lista de movimientos con información del producto y metadatos de paginación.
    """
    import time
    started = time.perf_counter_ns()
    
    # Construir query base
    query = (
        select(
            MovimientoInventario,
            Producto.nombre.label("producto_nombre")
        )
        .join(Producto, MovimientoInventario.producto_id == Producto.id)
    )
    
    # Aplicar filtros
    filtros = []
    
    if producto_id:
        filtros.append(MovimientoInventario.producto_id == producto_id)
    
    if bodega_id:
        filtros.append(MovimientoInventario.bodega_id == bodega_id)
    
    if pais:
        filtros.append(MovimientoInventario.pais == pais)
    
    if tipo_movimiento:
        filtros.append(MovimientoInventario.tipo_movimiento == tipo_movimiento)
    
    if motivo:
        filtros.append(MovimientoInventario.motivo == motivo)
    
    if usuario_id:
        filtros.append(MovimientoInventario.usuario_id == usuario_id)
    
    if referencia_documento:
        filtros.append(MovimientoInventario.referencia_documento.like(f"%{referencia_documento}%"))
    
    if fecha_desde:
        filtros.append(MovimientoInventario.created_at >= fecha_desde)
    
    if fecha_hasta:
        filtros.append(MovimientoInventario.created_at <= fecha_hasta)
    
    if estado:
        filtros.append(MovimientoInventario.estado == estado)
    
    if filtros:
        query = query.where(and_(*filtros))
    
    # Contar total
    count_query = select(func.count()).select_from(MovimientoInventario)
    if filtros:
        count_query = count_query.where(and_(*filtros))
    
    total = (await session.execute(count_query)).scalar_one()
    
    # Aplicar ordenamiento y paginación
    query = query.order_by(MovimientoInventario.created_at.desc())
    query = query.offset((page - 1) * size).limit(size)
    
    # Ejecutar query
    result = await session.execute(query)
    rows = result.all()
    
    # Construir respuesta
    items = [
        KardexItem(
            id=row.MovimientoInventario.id,
            producto_id=row.MovimientoInventario.producto_id,
            producto_nombre=row.producto_nombre,
            bodega_id=row.MovimientoInventario.bodega_id,
            pais=row.MovimientoInventario.pais,
            lote=row.MovimientoInventario.lote,
            tipo_movimiento=row.MovimientoInventario.tipo_movimiento,
            motivo=row.MovimientoInventario.motivo,
            cantidad=row.MovimientoInventario.cantidad,
            saldo_anterior=row.MovimientoInventario.saldo_anterior,
            saldo_nuevo=row.MovimientoInventario.saldo_nuevo,
            usuario_id=row.MovimientoInventario.usuario_id,
            referencia_documento=row.MovimientoInventario.referencia_documento,
            created_at=row.MovimientoInventario.created_at,
            estado=row.MovimientoInventario.estado
        )
        for row in rows
    ]
    
    took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
    
    logger.info(f"📋 Kardex consultado: {len(items)} movimientos de {total} en {took_ms}ms")
    
    return KardexResponse(
        items=items,
        meta=Meta(page=page, size=size, total=total, tookMs=took_ms)
    )


@router.put("/movements/{movimiento_id}/anular", response_model=MovimientoResponse)
async def anular_movimiento(
    movimiento_id: int,
    anulacion: AnularMovimientoRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    **Anula un movimiento de inventario**
    
    ### Proceso:
    1. Valida que el movimiento exista y no esté anulado
    2. Crea un movimiento inverso para revertir el impacto en stock
    3. Marca el movimiento original como ANULADO
    4. Registra usuario, fecha y motivo de anulación
    
    ### Restricciones:
    - ❌ No se puede anular un movimiento ya anulado
    - ❌ Las transferencias no se pueden anular individualmente
    - ✅ Solo usuarios autorizados deben poder anular
    
    ### Trazabilidad:
    - El movimiento original NO se borra (trazabilidad completa)
    - Se crea un movimiento reverso que ajusta el inventario
    - Queda registrado quién, cuándo y por qué se anuló
    
    ### Respuesta:
    - **200**: Movimiento anulado exitosamente
    - **400**: Movimiento ya anulado o es una transferencia
    - **404**: Movimiento no encontrado
    """
    try:
        async with session.begin():
            movimiento = await InventarioService.anular_movimiento(
                session, movimiento_id, anulacion
            )
        
        await session.refresh(movimiento)
        
        logger.info(f"✅ Movimiento {movimiento_id} anulado por {anulacion.usuario_id}")
        
        return MovimientoResponse.model_validate(movimiento)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error anulando movimiento: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "Error interno al anular movimiento"
            }
        )


@router.get("/alerts", response_model=AlertasListResponse)
async def obtener_alertas(
    leida: Optional[bool] = Query(None, description="Filtrar por estado de lectura"),
    nivel: Optional[str] = Query(None, description="Filtrar por nivel (INFO, WARNING, CRITICAL)"),
    tipo_alerta: Optional[str] = Query(None, description="Tipo de alerta"),
    producto_id: Optional[str] = Query(None, description="Filtrar por producto"),
    bodega_id: Optional[str] = Query(None, description="Filtrar por bodega"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session)
):
    """
    **Obtiene las alertas de inventario**
    
    ### Tipos de Alertas:
    - `STOCK_MINIMO`: Stock por debajo del mínimo (WARNING)
    - `STOCK_CRITICO`: Stock por debajo del crítico (CRITICAL)
    - `STOCK_NEGATIVO`: Stock negativo (CRITICAL)
    - `PROXIMO_VENCER`: Producto próximo a vencer (WARNING)
    - `VENCIDO`: Producto vencido (CRITICAL)
    
    ### Filtros:
    - `leida`: true (solo leídas), false (solo no leídas), null (ambas)
    - `nivel`: INFO, WARNING, CRITICAL
    - `tipo_alerta`: Tipo específico
    - `producto_id`: Alertas de un producto
    - `bodega_id`: Alertas de una bodega
    """
    import time
    started = time.perf_counter_ns()
    
    # Query base
    query = (
        select(
            AlertaInventario,
            Producto.nombre.label("producto_nombre")
        )
        .join(Producto, AlertaInventario.producto_id == Producto.id)
    )
    
    # Aplicar filtros
    filtros = []
    
    if leida is not None:
        filtros.append(AlertaInventario.leida == leida)
    
    if nivel:
        filtros.append(AlertaInventario.nivel == nivel)
    
    if tipo_alerta:
        filtros.append(AlertaInventario.tipo_alerta == tipo_alerta)
    
    if producto_id:
        filtros.append(AlertaInventario.producto_id == producto_id)
    
    if bodega_id:
        filtros.append(AlertaInventario.bodega_id == bodega_id)
    
    if filtros:
        query = query.where(and_(*filtros))
    
    # Contar total
    count_query = select(func.count()).select_from(AlertaInventario)
    if filtros:
        count_query = count_query.where(and_(*filtros))
    
    total = (await session.execute(count_query)).scalar_one()
    
    # Ordenar y paginar
    query = query.order_by(AlertaInventario.created_at.desc())
    query = query.offset((page - 1) * size).limit(size)
    
    # Ejecutar
    result = await session.execute(query)
    rows = result.all()
    
    # Construir respuesta
    items = [
        AlertaResponse(
            id=row.AlertaInventario.id,
            producto_id=row.AlertaInventario.producto_id,
            producto_nombre=row.producto_nombre,
            bodega_id=row.AlertaInventario.bodega_id,
            pais=row.AlertaInventario.pais,
            tipo_alerta=row.AlertaInventario.tipo_alerta,
            nivel=row.AlertaInventario.nivel,
            mensaje=row.AlertaInventario.mensaje,
            stock_actual=row.AlertaInventario.stock_actual,
            stock_minimo=row.AlertaInventario.stock_minimo,
            leida=row.AlertaInventario.leida,
            created_at=row.AlertaInventario.created_at
        )
        for row in rows
    ]
    
    took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
    
    logger.info(f"🔔 Alertas consultadas: {len(items)} de {total} en {took_ms}ms")
    
    return AlertasListResponse(
        items=items,
        meta=Meta(page=page, size=size, total=total, tookMs=took_ms)
    )


@router.put("/alerts/{alerta_id}/marcar-leida")
async def marcar_alerta_leida(
    alerta_id: int,
    usuario_id: str = Query(..., description="ID del usuario que marca como leída"),
    session: AsyncSession = Depends(get_session)
):
    """
    **Marca una alerta como leída**
    
    Registra qué usuario la leyó y cuándo.
    """
    async with session.begin():
        alerta = (await session.execute(
            select(AlertaInventario).where(AlertaInventario.id == alerta_id)
        )).scalar_one_or_none()
        
        if not alerta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alerta no encontrada"
            )
        
        alerta.leida = True
        alerta.leida_por = usuario_id
        alerta.leida_at = datetime.utcnow()
    
    return {"message": "Alerta marcada como leída", "alerta_id": alerta_id}


@router.get("/bodega/{bodega_id}/productos")
async def listar_productos_en_bodega(
    bodega_id: str,
    pais: Optional[str] = Query(None, description="Filtrar por país"),
    con_stock: bool = Query(True, description="Solo productos con stock > 0"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session)
):
    """
    **Lista todos los productos disponibles en una bodega específica**
    
    Este endpoint es útil para:
    - Ver qué productos están disponibles en una bodega
    - Consultar stock actual por bodega antes de una venta
    - Verificar disponibilidad para transferencias
    
    ### Parámetros:
    - `bodega_id`: ID de la bodega a consultar (requerido)
    - `pais`: Filtrar por país (opcional)
    - `con_stock`: Si es True, solo muestra productos con cantidad > 0 (default: True)
    - `page`: Número de página (default: 1)
    - `size`: Items por página (1-200, default: 50)
    
    ### Respuesta:
    Lista de productos con información de inventario:
    - Datos del producto (nombre, código, categoría, precio)
    - Stock actual en la bodega
    - Lote y fecha de vencimiento
    - Alertas de stock (si aplica)
    """
    import time
    started = time.perf_counter_ns()
    
    logger.info(f"🏢 Consultando productos en bodega: {bodega_id} (pais: {pais}, con_stock: {con_stock})")
    
    # Construir query base con JOIN entre inventario y producto
    query = (
        select(
            Inventario.producto_id,
            Producto.nombre.label("producto_nombre"),
            Producto.codigo.label("producto_codigo"),
            Producto.categoria_id,
            Producto.precio_unitario,
            Inventario.pais,
            Inventario.lote,
            Inventario.cantidad,
            Inventario.vence,
            Inventario.condiciones,
            Producto.stock_minimo,
            Producto.stock_critico
        )
        .join(Producto, Inventario.producto_id == Producto.id)
        .where(Inventario.bodega_id == bodega_id)
    )
    
    # Aplicar filtros adicionales
    if pais:
        query = query.where(Inventario.pais == pais)
    
    if con_stock:
        query = query.where(Inventario.cantidad > 0)
    
    # Ordenar por nombre de producto
    query = query.order_by(Producto.nombre)
    
    # Contar total
    count_query = (
        select(func.count())
        .select_from(Inventario)
        .join(Producto, Inventario.producto_id == Producto.id)
        .where(Inventario.bodega_id == bodega_id)
    )
    
    if pais:
        count_query = count_query.where(Inventario.pais == pais)
    
    if con_stock:
        count_query = count_query.where(Inventario.cantidad > 0)
    
    total = (await session.execute(count_query)).scalar_one()
    
    # Aplicar paginación
    query = query.offset((page - 1) * size).limit(size)
    
    # Ejecutar query
    result = await session.execute(query)
    rows = result.all()
    
    # Construir respuesta
    items = []
    for row in rows:
        # Determinar estado del stock
        if row.cantidad <= row.stock_critico:
            estado_stock = "CRITICO"
        elif row.cantidad <= row.stock_minimo:
            estado_stock = "BAJO"
        else:
            estado_stock = "NORMAL"
        
        item = {
            "producto_id": row.producto_id,
            "producto_nombre": row.producto_nombre,
            "producto_codigo": row.producto_codigo,
            "categoria": row.categoria_id,
            "precio_unitario": float(row.precio_unitario),
            "bodega_id": bodega_id,
            "pais": row.pais,
            "lote": row.lote,
            "cantidad": row.cantidad,
            "fecha_vencimiento": row.vence.isoformat() if row.vence else None,
            "condiciones": row.condiciones,
            "stock_minimo": row.stock_minimo,
            "stock_critico": row.stock_critico,
            "estado_stock": estado_stock
        }
        items.append(item)
    
    took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
    
    logger.info(f"✅ Productos en bodega {bodega_id}: {len(items)} de {total} en {took_ms}ms")
    
    return {
        "items": items,
        "meta": {
            "page": page,
            "size": size,
            "total": total,
            "bodega_id": bodega_id,
            "pais": pais,
            "con_stock": con_stock,
            "tookMs": took_ms
        }
    }


@router.get("/reports/saldos", response_model=ReporteSaldosResponse)
async def reporte_saldos(
    producto_id: Optional[str] = Query(None, description="Filtrar por producto"),
    bodega_id: Optional[str] = Query(None, description="Filtrar por bodega"),
    pais: Optional[str] = Query(None, description="Filtrar por país"),
    estado_stock: Optional[str] = Query(None, description="Filtrar por estado (NORMAL, BAJO, CRITICO)"),
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session)
):
    """
    **Genera reporte de saldos actuales por bodega**
    
    Utiliza la vista `v_saldos_bodega` para obtener información consolidada.
    
    ### Campos del Reporte:
    - Producto (ID, nombre, código)
    - Ubicación (bodega, país, lote)
    - Cantidad total
    - Fecha de vencimiento más próxima
    - Stock mínimo y crítico
    - Estado del stock (NORMAL, BAJO, CRITICO)
    """
    import time
    started = time.perf_counter_ns()
    
    # Construir filtros dinámicos
    filtros_sql = []
    params = {"size": size, "offset": (page - 1) * size}
    
    if producto_id:
        filtros_sql.append("AND producto_id = :producto_id")
        params["producto_id"] = producto_id
    
    if bodega_id:
        filtros_sql.append("AND bodega_id = :bodega_id")
        params["bodega_id"] = bodega_id
    
    if pais:
        filtros_sql.append("AND pais = :pais")
        params["pais"] = pais
    
    if estado_stock:
        filtros_sql.append("AND estado_stock = :estado_stock")
        params["estado_stock"] = estado_stock
    
    filtros_str = " ".join(filtros_sql)
    
    # Usar la vista creada en SQL - construir query con f-string
    query = text(f"""
        SELECT 
            producto_id, producto_nombre, producto_codigo,
            bodega_id, pais, lote, cantidad_total,
            fecha_vencimiento_proxima, stock_minimo, stock_critico, estado_stock
        FROM v_saldos_bodega
        WHERE 1=1
        {filtros_str}
        ORDER BY estado_stock DESC, cantidad_total ASC
        LIMIT :size OFFSET :offset
    """)
    
    count_query = text(f"SELECT COUNT(*) FROM v_saldos_bodega WHERE 1=1 {filtros_str}")
    
    # Ejecutar queries
    total = (await session.execute(
        count_query, 
        params
    )).scalar_one()
    
    result = await session.execute(
        query,
        params
    )
    rows = result.fetchall()
    
    # Construir respuesta
    items = [
        SaldoBodega(
            producto_id=row.producto_id,
            producto_nombre=row.producto_nombre,
            producto_codigo=row.producto_codigo,
            bodega_id=row.bodega_id,
            pais=row.pais,
            lote=row.lote,
            cantidad_total=row.cantidad_total,
            fecha_vencimiento_proxima=row.fecha_vencimiento_proxima,
            stock_minimo=row.stock_minimo,
            stock_critico=row.stock_critico,
            estado_stock=row.estado_stock
        )
        for row in rows
    ]
    
    took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
    
    logger.info(f"📊 Reporte de saldos: {len(items)} registros de {total} en {took_ms}ms")
    
    return ReporteSaldosResponse(
        items=items,
        meta=Meta(page=page, size=size, total=total, tookMs=took_ms)
    )

