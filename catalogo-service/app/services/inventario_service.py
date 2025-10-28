"""
Servicio de gestión de movimientos de inventario.

Este módulo contiene toda la lógica de negocio para:
- Registrar ingresos y salidas
- Validar stock y requisitos de lote/vencimiento
- Gestionar transferencias entre bodegas
- Generar alertas automáticas
- Anular movimientos
- Consultar kardex (historial)
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func, or_
from app.models.catalogo_model import Producto, Inventario
from app.models.movimiento_model import MovimientoInventario, AlertaInventario
from app.schemas import (
    MovimientoCreate, TransferenciaCreate, TipoMovimiento, 
    MotivoMovimiento, AnularMovimientoRequest
)
from fastapi import HTTPException, status
from typing import Optional, Tuple, List
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)


class InventarioService:
    """
    Servicio para gestión completa de inventario.
    
    Implementa todas las operaciones de kardex con:
    - Validaciones de negocio
    - Actualización en tiempo real
    - Trazabilidad completa
    - Generación de alertas
    """
    
    @staticmethod
    async def validar_producto_lote_vencimiento(
        session: AsyncSession,
        producto_id: str,
        lote: Optional[str],
        fecha_vencimiento: Optional[date],
        tipo_movimiento: TipoMovimiento,
        motivo: Optional[str] = None
    ) -> Producto:
        """
        Valida que el producto exista y cumpla requisitos de lote/vencimiento.
        
        Args:
            session: Sesión de base de datos
            producto_id: ID del producto
            lote: Número de lote (opcional)
            fecha_vencimiento: Fecha de vencimiento (opcional)
            tipo_movimiento: Tipo de movimiento (INGRESO requiere validaciones adicionales)
            motivo: Motivo del movimiento (opcional, AJUSTE excluido de validaciones estrictas)
            
        Returns:
            Producto validado
            
        Raises:
            HTTPException 404: Producto no encontrado
            HTTPException 400: Falta lote o fecha de vencimiento requerida
        """
        producto = (await session.execute(
            select(Producto).where(Producto.id == producto_id)
        )).scalar_one_or_none()
        
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "PRODUCTO_NO_ENCONTRADO",
                    "message": f"Producto {producto_id} no encontrado",
                    "producto_id": producto_id
                }
            )
        
        # Validar lote/vencimiento (solo para ingresos NO de ajuste/anulación)
        es_ajuste = motivo == "AJUSTE"
        if tipo_movimiento in [TipoMovimiento.INGRESO, TipoMovimiento.TRANSFERENCIA_INGRESO] and not es_ajuste:
            if producto.requiere_lote and not lote:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "LOTE_REQUERIDO",
                        "message": f"El producto {producto.nombre} requiere especificar el número de lote",
                        "producto_id": producto_id,
                        "requiere_lote": True
                    }
                )
            
            if producto.requiere_vencimiento and not fecha_vencimiento:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "VENCIMIENTO_REQUERIDO",
                        "message": f"El producto {producto.nombre} requiere especificar fecha de vencimiento",
                        "producto_id": producto_id,
                        "requiere_vencimiento": True
                    }
                )
        
        return producto
    
    @staticmethod
    async def obtener_saldo_actual(
        session: AsyncSession,
        producto_id: str,
        bodega_id: str,
        pais: str,
        lote: Optional[str] = None
    ) -> int:
        """
        Obtiene el saldo actual de un producto en una bodega.
        
        Args:
            session: Sesión de base de datos
            producto_id: ID del producto
            bodega_id: ID de la bodega
            pais: Código del país
            lote: Número de lote específico (opcional)
            
        Returns:
            Saldo actual (0 si no existe inventario)
        """
        query = select(func.sum(Inventario.cantidad)).where(
            and_(
                Inventario.producto_id == producto_id,
                Inventario.bodega_id == bodega_id,
                Inventario.pais == pais
            )
        )
        
        if lote:
            query = query.where(Inventario.lote == lote)
        
        saldo = (await session.execute(query)).scalar_one_or_none()
        return int(saldo or 0)
    
    @staticmethod
    async def registrar_movimiento(
        session: AsyncSession,
        movimiento: MovimientoCreate
    ) -> Tuple[MovimientoInventario, List[AlertaInventario]]:
        """
        Registra un movimiento de inventario y actualiza el stock en tiempo real.
        
        Este método implementa la lógica completa:
        1. Valida el producto y requisitos
        2. Obtiene saldo actual
        3. Calcula nuevo saldo
        4. Valida stock negativo
        5. Crea registro de movimiento
        6. Actualiza inventario
        7. Genera alertas si es necesario
        
        Args:
            session: Sesión de base de datos (debe estar en una transacción)
            movimiento: Datos del movimiento a registrar
            
        Returns:
            Tupla con (movimiento_creado, lista_de_alertas)
            
        Raises:
            HTTPException 400: Validación fallida o stock insuficiente
            HTTPException 404: Producto no encontrado
        """
        logger.info(
            f"📦 Registrando movimiento: {movimiento.tipo_movimiento.value} "
            f"- {movimiento.producto_id} - {movimiento.cantidad} unidades"
        )
        
        # 1. Validar producto
        producto = await InventarioService.validar_producto_lote_vencimiento(
            session, 
            movimiento.producto_id, 
            movimiento.lote, 
            movimiento.fecha_vencimiento,
            movimiento.tipo_movimiento,
            movimiento.motivo
        )
        
        # 2. Obtener saldo actual
        saldo_anterior = await InventarioService.obtener_saldo_actual(
            session,
            movimiento.producto_id,
            movimiento.bodega_id,
            movimiento.pais,
            movimiento.lote
        )
        
        logger.info(f"   Saldo anterior: {saldo_anterior}")
        
        # 3. Calcular nuevo saldo
        if movimiento.tipo_movimiento in [TipoMovimiento.INGRESO, TipoMovimiento.TRANSFERENCIA_INGRESO]:
            saldo_nuevo = saldo_anterior + movimiento.cantidad
            logger.info(f"   ➕ Ingreso: {saldo_anterior} + {movimiento.cantidad} = {saldo_nuevo}")
        else:  # SALIDA o TRANSFERENCIA_SALIDA
            saldo_nuevo = saldo_anterior - movimiento.cantidad
            logger.info(f"   ➖ Salida: {saldo_anterior} - {movimiento.cantidad} = {saldo_nuevo}")
        
        # 4. Validar stock negativo
        if saldo_nuevo < 0 and not movimiento.permitir_stock_negativo:
            logger.warning(
                f"   ❌ Stock insuficiente: disponible={saldo_anterior}, "
                f"requerido={movimiento.cantidad}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "STOCK_INSUFICIENTE",
                    "message": f"Stock insuficiente en {movimiento.bodega_id}",
                    "saldo_actual": saldo_anterior,
                    "cantidad_requerida": movimiento.cantidad,
                    "faltante": abs(saldo_nuevo),
                    "producto_id": movimiento.producto_id,
                    "producto_nombre": producto.nombre,
                    "bodega_id": movimiento.bodega_id,
                    "pais": movimiento.pais
                }
            )
        
        # 5. Crear el movimiento
        nuevo_movimiento = MovimientoInventario(
            producto_id=movimiento.producto_id,
            bodega_id=movimiento.bodega_id,
            pais=movimiento.pais,
            lote=movimiento.lote,
            tipo_movimiento=movimiento.tipo_movimiento.value,
            motivo=movimiento.motivo.value,
            cantidad=movimiento.cantidad,
            fecha_vencimiento=movimiento.fecha_vencimiento,
            saldo_anterior=saldo_anterior,
            saldo_nuevo=saldo_nuevo,
            usuario_id=movimiento.usuario_id,
            referencia_documento=movimiento.referencia_documento,
            observaciones=movimiento.observaciones
        )
        
        session.add(nuevo_movimiento)
        
        # 6. Actualizar inventario
        await InventarioService.actualizar_inventario(
            session,
            movimiento,
            saldo_nuevo
        )
        
        # 7. Generar alertas si es necesario
        alertas = await InventarioService.verificar_alertas(
            session,
            producto,
            movimiento.bodega_id,
            movimiento.pais,
            saldo_nuevo
        )
        
        await session.flush()
        
        logger.info(
            f"✅ Movimiento registrado: ID={nuevo_movimiento.id}, "
            f"Saldo: {saldo_anterior} → {saldo_nuevo}"
        )
        if alertas:
            logger.warning(f"   ⚠️  Se generaron {len(alertas)} alertas")
        
        return nuevo_movimiento, alertas
    
    @staticmethod
    async def actualizar_inventario(
        session: AsyncSession,
        movimiento: MovimientoCreate,
        saldo_nuevo: int
    ):
        """
        Actualiza o crea registro de inventario según el movimiento.
        
        Args:
            session: Sesión de base de datos
            movimiento: Datos del movimiento
            saldo_nuevo: Nuevo saldo calculado
        """
        # Buscar registro existente
        inv = (await session.execute(
            select(Inventario).where(
                and_(
                    Inventario.producto_id == movimiento.producto_id,
                    Inventario.bodega_id == movimiento.bodega_id,
                    Inventario.pais == movimiento.pais,
                    Inventario.lote == (movimiento.lote or "")
                )
            )
        )).scalar_one_or_none()
        
        if inv:
            # Actualizar existente
            if saldo_nuevo <= 0:
                # Si el saldo es 0 o negativo, eliminar el registro
                await session.delete(inv)
                logger.info(f"   🗑️  Registro de inventario eliminado (saldo={saldo_nuevo})")
            else:
                inv.cantidad = saldo_nuevo
                logger.info(f"   📝 Inventario actualizado: {inv.cantidad} unidades")
        else:
            # Crear nuevo (solo si es ingreso y el saldo es positivo)
            if saldo_nuevo > 0 and movimiento.tipo_movimiento in [
                TipoMovimiento.INGRESO, 
                TipoMovimiento.TRANSFERENCIA_INGRESO
            ]:
                nuevo_inv = Inventario(
                    producto_id=movimiento.producto_id,
                    pais=movimiento.pais,
                    bodega_id=movimiento.bodega_id,
                    lote=movimiento.lote or f"LOTE-{datetime.now().strftime('%Y%m%d')}",
                    cantidad=saldo_nuevo,
                    vence=movimiento.fecha_vencimiento or date(2099, 12, 31),
                    condiciones="Normal"
                )
                session.add(nuevo_inv)
                logger.info(f"   ➕ Nuevo registro de inventario creado: {nuevo_inv.cantidad} unidades")
    
    @staticmethod
    async def verificar_alertas(
        session: AsyncSession,
        producto: Producto,
        bodega_id: str,
        pais: str,
        saldo_nuevo: int
    ) -> List[AlertaInventario]:
        """
        Verifica y genera alertas según el saldo del producto.
        
        Genera alertas cuando:
        - Stock ≤ stock_critico: CRITICAL
        - Stock ≤ stock_minimo: WARNING
        - Stock < 0: CRITICAL
        
        Args:
            session: Sesión de base de datos
            producto: Producto a evaluar
            bodega_id: ID de la bodega
            pais: Código del país
            saldo_nuevo: Nuevo saldo del producto
            
        Returns:
            Lista de alertas generadas
        """
        alertas = []
        
        # Alerta de stock negativo (más grave)
        if saldo_nuevo < 0:
            alerta = AlertaInventario(
                producto_id=producto.id,
                bodega_id=bodega_id,
                pais=pais,
                tipo_alerta="STOCK_NEGATIVO",
                nivel="CRITICAL",
                mensaje=(
                    f"🚨 STOCK NEGATIVO para {producto.nombre} en {bodega_id}: "
                    f"{saldo_nuevo} unidades (requiere atención inmediata)"
                ),
                stock_actual=saldo_nuevo,
                stock_minimo=producto.stock_minimo
            )
            session.add(alerta)
            alertas.append(alerta)
            logger.warning(f"   🚨 Alerta CRÍTICA: Stock negativo ({saldo_nuevo})")
        
        # Alerta de stock crítico
        elif saldo_nuevo <= producto.stock_critico:
            alerta = AlertaInventario(
                producto_id=producto.id,
                bodega_id=bodega_id,
                pais=pais,
                tipo_alerta="STOCK_CRITICO",
                nivel="CRITICAL",
                mensaje=(
                    f"⚠️  Stock crítico para {producto.nombre} en {bodega_id}: "
                    f"{saldo_nuevo} unidades (crítico: {producto.stock_critico}, mínimo: {producto.stock_minimo})"
                ),
                stock_actual=saldo_nuevo,
                stock_minimo=producto.stock_minimo
            )
            session.add(alerta)
            alertas.append(alerta)
            logger.warning(
                f"   ⚠️  Alerta CRÍTICA: Stock crítico "
                f"({saldo_nuevo} ≤ {producto.stock_critico})"
            )
        
        # Alerta de stock mínimo
        elif saldo_nuevo <= producto.stock_minimo:
            alerta = AlertaInventario(
                producto_id=producto.id,
                bodega_id=bodega_id,
                pais=pais,
                tipo_alerta="STOCK_MINIMO",
                nivel="WARNING",
                mensaje=(
                    f"⚡ Stock bajo para {producto.nombre} en {bodega_id}: "
                    f"{saldo_nuevo} unidades (mínimo: {producto.stock_minimo})"
                ),
                stock_actual=saldo_nuevo,
                stock_minimo=producto.stock_minimo
            )
            session.add(alerta)
            alertas.append(alerta)
            logger.warning(
                f"   ⚡ Alerta WARNING: Stock bajo "
                f"({saldo_nuevo} ≤ {producto.stock_minimo})"
            )
        
        return alertas
    
    @staticmethod
    async def registrar_transferencia(
        session: AsyncSession,
        transferencia: TransferenciaCreate
    ) -> Tuple[MovimientoInventario, MovimientoInventario, List[AlertaInventario]]:
        """
        Registra una transferencia entre bodegas.
        
        Genera dos movimientos vinculados:
        1. Salida en bodega origen
        2. Ingreso en bodega destino
        
        Ambos movimientos mantienen referencia cruzada para trazabilidad.
        
        Args:
            session: Sesión de base de datos (debe estar en una transacción)
            transferencia: Datos de la transferencia
            
        Returns:
            Tupla con (movimiento_salida, movimiento_ingreso, alertas_generadas)
        """
        logger.info(
            f"🔄 Registrando transferencia: {transferencia.producto_id} "
            f"desde {transferencia.bodega_origen_id} → {transferencia.bodega_destino_id}"
        )
        
        todas_alertas = []
        
        # 1. Salida de bodega origen
        salida = MovimientoCreate(
            producto_id=transferencia.producto_id,
            bodega_id=transferencia.bodega_origen_id,
            pais=transferencia.pais_origen,
            lote=transferencia.lote,
            tipo_movimiento=TipoMovimiento.TRANSFERENCIA_SALIDA,
            motivo=MotivoMovimiento.TRANSFERENCIA,
            cantidad=transferencia.cantidad,
            usuario_id=transferencia.usuario_id,
            referencia_documento=transferencia.referencia_documento,
            observaciones=(
                f"Transferencia a {transferencia.bodega_destino_id}. "
                f"{transferencia.observaciones or ''}"
            ).strip()
        )
        
        mov_salida, alertas_salida = await InventarioService.registrar_movimiento(session, salida)
        todas_alertas.extend(alertas_salida)
        
        # 2. Ingreso a bodega destino
        # Obtener fecha de vencimiento del lote de origen si existe
        fecha_vence = None
        if transferencia.lote:
            inv_origen = (await session.execute(
                select(Inventario).where(
                    and_(
                        Inventario.producto_id == transferencia.producto_id,
                        Inventario.bodega_id == transferencia.bodega_origen_id,
                        Inventario.lote == transferencia.lote
                    )
                )
            )).scalar_one_or_none()
            if inv_origen:
                fecha_vence = inv_origen.vence
        
        ingreso = MovimientoCreate(
            producto_id=transferencia.producto_id,
            bodega_id=transferencia.bodega_destino_id,
            pais=transferencia.pais_destino,
            lote=transferencia.lote,
            tipo_movimiento=TipoMovimiento.TRANSFERENCIA_INGRESO,
            motivo=MotivoMovimiento.TRANSFERENCIA,
            cantidad=transferencia.cantidad,
            fecha_vencimiento=fecha_vence,
            usuario_id=transferencia.usuario_id,
            referencia_documento=transferencia.referencia_documento,
            observaciones=(
                f"Transferencia desde {transferencia.bodega_origen_id}. "
                f"{transferencia.observaciones or ''}"
            ).strip()
        )
        
        mov_ingreso, alertas_ingreso = await InventarioService.registrar_movimiento(session, ingreso)
        todas_alertas.extend(alertas_ingreso)
        
        # 3. Vincular movimientos
        mov_salida.movimiento_relacionado_id = mov_ingreso.id
        mov_ingreso.movimiento_relacionado_id = mov_salida.id
        
        await session.flush()
        
        logger.info(
            f"✅ Transferencia completada: "
            f"Salida ID={mov_salida.id} ↔ Ingreso ID={mov_ingreso.id}"
        )
        
        return mov_salida, mov_ingreso, todas_alertas
    
    @staticmethod
    async def anular_movimiento(
        session: AsyncSession,
        movimiento_id: int,
        anulacion: AnularMovimientoRequest
    ) -> MovimientoInventario:
        """
        Anula un movimiento de inventario, revirtiendo su impacto en el stock.
        
        La anulación:
        - No borra el movimiento original (trazabilidad)
        - Crea un movimiento inverso
        - Marca el original como ANULADO
        - Registra usuario y motivo
        
        Args:
            session: Sesión de base de datos
            movimiento_id: ID del movimiento a anular
            anulacion: Datos de la anulación (motivo y usuario)
            
        Returns:
            Movimiento anulado
            
        Raises:
            HTTPException 404: Movimiento no encontrado
            HTTPException 400: Movimiento ya está anulado o es una transferencia
        """
        logger.info(f"🔄 Anulando movimiento: ID={movimiento_id}")
        
        # Buscar el movimiento
        movimiento = (await session.execute(
            select(MovimientoInventario).where(MovimientoInventario.id == movimiento_id)
        )).scalar_one_or_none()
        
        if not movimiento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "MOVIMIENTO_NO_ENCONTRADO",
                    "message": f"Movimiento {movimiento_id} no encontrado"
                }
            )
        
        if movimiento.estado == "ANULADO":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "MOVIMIENTO_YA_ANULADO",
                    "message": "Este movimiento ya fue anulado previamente",
                    "anulado_por": movimiento.anulado_por,
                    "anulado_at": movimiento.anulado_at.isoformat() if movimiento.anulado_at else None
                }
            )
        
        # No permitir anular transferencias directamente (debe anularse ambos movimientos)
        if movimiento.movimiento_relacionado_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "TRANSFERENCIA_NO_ANULABLE",
                    "message": "Las transferencias deben anularse como conjunto",
                    "movimiento_relacionado_id": movimiento.movimiento_relacionado_id
                }
            )
        
        # Crear movimiento inverso para revertir el impacto
        tipo_inverso = (
            TipoMovimiento.SALIDA if movimiento.tipo_movimiento == "INGRESO"
            else TipoMovimiento.INGRESO
        )
        
        movimiento_reverso = MovimientoCreate(
            producto_id=movimiento.producto_id,
            bodega_id=movimiento.bodega_id,
            pais=movimiento.pais,
            lote=movimiento.lote,
            tipo_movimiento=tipo_inverso,
            motivo=MotivoMovimiento.AJUSTE,
            cantidad=movimiento.cantidad,
            fecha_vencimiento=movimiento.fecha_vencimiento,  # Tomar del movimiento original
            usuario_id=anulacion.usuario_id,
            referencia_documento=f"ANUL-{movimiento.id}",
            observaciones=f"Anulación de movimiento {movimiento.id}: {anulacion.motivo_anulacion}",
            permitir_stock_negativo=True  # Permitir para revertir
        )
        
        # Registrar el movimiento reverso
        await InventarioService.registrar_movimiento(session, movimiento_reverso)
        
        # Marcar el movimiento original como anulado
        movimiento.estado = "ANULADO"
        movimiento.anulado_por = anulacion.usuario_id
        movimiento.anulado_at = datetime.utcnow()
        movimiento.motivo_anulacion = anulacion.motivo_anulacion
        
        await session.flush()
        
        logger.info(f"✅ Movimiento {movimiento_id} anulado exitosamente")
        
        return movimiento

