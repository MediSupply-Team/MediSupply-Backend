"""
Modelos SQLAlchemy para gestión de movimientos de inventario y alertas.

Este módulo contiene:
- MovimientoInventario: Kardex completo de entradas/salidas
- AlertaInventario: Alertas automáticas por condiciones de stock
"""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, Date, ForeignKey, Text, DateTime, CheckConstraint, BigInteger
from app.db import Base
from datetime import datetime
from typing import Optional


class MovimientoInventario(Base):
    """
    Modelo para registrar todos los movimientos de inventario (kardex).
    
    Cada movimiento registra:
    - Tipo: INGRESO, SALIDA, TRANSFERENCIA_SALIDA, TRANSFERENCIA_INGRESO
    - Motivo: COMPRA, VENTA, AJUSTE, DEVOLUCION, MERMA, TRANSFERENCIA, etc.
    - Snapshot de saldos antes/después
    - Trazabilidad completa (usuario, fecha, referencia)
    - Posibilidad de anulación
    """
    
    __tablename__ = "movimiento_inventario"
    
    # Identificador único
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # Identificación del producto y ubicación
    producto_id: Mapped[str] = mapped_column(
        String(64), 
        ForeignKey("producto.id", ondelete="RESTRICT"), 
        index=True, 
        nullable=False
    )
    bodega_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    pais: Mapped[str] = mapped_column(String(2), index=True, nullable=False)
    lote: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Tipo y motivo del movimiento
    tipo_movimiento: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    motivo: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Datos de la transacción
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_vencimiento: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    
    # Snapshot de saldos (permite auditoría histórica)
    saldo_anterior: Mapped[int] = mapped_column(Integer, nullable=False)
    saldo_nuevo: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Auditoría y trazabilidad
    usuario_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    referencia_documento: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamp de creación
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        index=True,
        nullable=False
    )
    
    # Estado (para permitir anulación sin borrar registros)
    estado: Mapped[str] = mapped_column(
        String(20), 
        default="ACTIVO", 
        index=True,
        nullable=False
    )
    anulado_por: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    anulado_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    motivo_anulacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relación para transferencias (vincula movimiento salida con ingreso)
    movimiento_relacionado_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("movimiento_inventario.id"),
        nullable=True
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint('cantidad > 0', name='check_cantidad_positiva'),
        CheckConstraint(
            "tipo_movimiento IN ('INGRESO', 'SALIDA', 'TRANSFERENCIA_SALIDA', 'TRANSFERENCIA_INGRESO')",
            name='check_tipo_movimiento_valido'
        ),
        CheckConstraint(
            "motivo IN ('COMPRA', 'AJUSTE', 'VENTA', 'DEVOLUCION', 'MERMA', 'TRANSFERENCIA', 'PRODUCCION', 'INVENTARIO_INICIAL')",
            name='check_motivo_valido'
        ),
        CheckConstraint(
            "estado IN ('ACTIVO', 'ANULADO')",
            name='check_estado_valido'
        ),
    )
    
    def __repr__(self):
        return (
            f"<MovimientoInventario("
            f"id={self.id}, "
            f"producto={self.producto_id}, "
            f"tipo={self.tipo_movimiento}, "
            f"cantidad={self.cantidad}, "
            f"saldo={self.saldo_anterior}→{self.saldo_nuevo}"
            f")>"
        )


class AlertaInventario(Base):
    """
    Modelo para alertas automáticas de inventario.
    
    Se generan automáticamente cuando:
    - Stock cae por debajo del mínimo (WARNING)
    - Stock cae por debajo del crítico (CRITICAL)
    - Productos próximos a vencer (INFO/WARNING)
    - Productos vencidos (CRITICAL)
    - Stock negativo (CRITICAL)
    """
    
    __tablename__ = "alerta_inventario"
    
    # Identificador único
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # Identificación
    producto_id: Mapped[str] = mapped_column(
        String(64), 
        ForeignKey("producto.id", ondelete="CASCADE"), 
        index=True, 
        nullable=False
    )
    bodega_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    pais: Mapped[str] = mapped_column(String(2), nullable=False)
    
    # Tipo y nivel de alerta
    tipo_alerta: Mapped[str] = mapped_column(String(30), nullable=False)
    nivel: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    
    # Información de la alerta
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    stock_actual: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stock_minimo: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Control de lectura
    leida: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    leida_por: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    leida_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Timestamp de creación
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        index=True,
        nullable=False
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "tipo_alerta IN ('STOCK_MINIMO', 'STOCK_CRITICO', 'PROXIMO_VENCER', 'VENCIDO', 'STOCK_NEGATIVO')",
            name='check_tipo_alerta_valido'
        ),
        CheckConstraint(
            "nivel IN ('INFO', 'WARNING', 'CRITICAL')",
            name='check_nivel_valido'
        ),
    )
    
    def __repr__(self):
        return (
            f"<AlertaInventario("
            f"id={self.id}, "
            f"tipo={self.tipo_alerta}, "
            f"nivel={self.nivel}, "
            f"leida={self.leida}"
            f")>"
        )

