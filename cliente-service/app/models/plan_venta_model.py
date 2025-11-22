"""
Modelos SQLAlchemy para Plan de Venta
FASE 3: Plan de Venta completo con productos, regiones, zonas y bonificaciones
"""
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, Date, DateTime, ForeignKey, DECIMAL, JSON, Text, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from datetime import date, datetime
from decimal import Decimal
from app.db import Base
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from app.models.client_model import Vendedor
    from app.models.catalogo_model import TipoPlan, Region, Zona


class PlanVenta(Base):
    """
    Modelo de Plan de Venta (1:1 con Vendedor)
    Contiene la información principal del plan de ventas asignado a un vendedor
    """
    __tablename__ = "plan_venta"
    
    # Campos principales
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    nombre_plan: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Relaciones
    vendedor_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vendedor.id"), unique=True, nullable=False, index=True)  # 1:1 con Vendedor
    tipo_plan_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tipo_plan.id"), nullable=True, index=True)
    
    # Fechas del plan
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Metas y comisiones
    meta_ventas: Mapped[Decimal] = mapped_column(DECIMAL(15,2), nullable=False, default=0)  # Meta en dinero
    comision_base: Mapped[Decimal] = mapped_column(DECIMAL(5,2), nullable=False, default=5.0)  # Porcentaje base
    
    # Estructura de bonificaciones (JSON: {70: 2, 90: 5, 100: 10})
    estructura_bonificaciones: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Campos adicionales
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Auditoría
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Relaciones (lazy="noload" por defecto, se cargan explícitamente en /detalle)
    vendedor: Mapped["Vendedor"] = relationship("Vendedor", back_populates="plan_venta", lazy="noload")
    tipo_plan: Mapped[Optional["TipoPlan"]] = relationship("TipoPlan", lazy="noload")
    productos_asignados: Mapped[List["PlanProducto"]] = relationship("PlanProducto", back_populates="plan_venta", cascade="all, delete-orphan", lazy="noload")
    regiones_asignadas: Mapped[List["PlanRegion"]] = relationship("PlanRegion", back_populates="plan_venta", cascade="all, delete-orphan", lazy="noload")
    zonas_asignadas: Mapped[List["PlanZona"]] = relationship("PlanZona", back_populates="plan_venta", cascade="all, delete-orphan", lazy="noload")


class PlanProducto(Base):
    """
    Relación M2M entre Plan de Venta y Productos
    Define los productos asignados al plan con sus metas
    SOLO guarda producto_id, el frontend consulta catalogo-service para obtener detalles
    """
    __tablename__ = "plan_producto"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_venta_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("plan_venta.id", ondelete="CASCADE"), nullable=False, index=True)
    producto_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # ID del producto desde catalogo-service
    
    # Metas específicas del producto
    meta_cantidad: Mapped[int] = mapped_column(nullable=False, default=0)  # Cantidad a vender
    precio_unitario: Mapped[Decimal] = mapped_column(DECIMAL(12,2), nullable=False, default=0)  # Precio en el plan
    
    # Auditoría
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    plan_venta: Mapped["PlanVenta"] = relationship("PlanVenta", back_populates="productos_asignados")
    
    # Constraint único: Un producto no puede estar duplicado en el mismo plan
    __table_args__ = (
        {'comment': 'Productos asignados a un plan de venta con sus metas'},
    )


class PlanRegion(Base):
    """
    Relación M2M entre Plan de Venta y Regiones
    Define las regiones asignadas al plan
    """
    __tablename__ = "plan_region"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_venta_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("plan_venta.id", ondelete="CASCADE"), nullable=False, index=True)
    region_id: Mapped[int] = mapped_column(Integer, ForeignKey("region.id"), nullable=False, index=True)
    
    # Auditoría
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    plan_venta: Mapped["PlanVenta"] = relationship("PlanVenta", back_populates="regiones_asignadas")
    region: Mapped["Region"] = relationship("Region", lazy="noload")
    
    # Constraint único: Una región no puede estar duplicada en el mismo plan
    __table_args__ = (
        {'comment': 'Regiones principales asignadas a un plan de venta'},
    )


class PlanZona(Base):
    """
    Relación M2M entre Plan de Venta y Zonas
    Define las zonas especiales asignadas al plan
    """
    __tablename__ = "plan_zona"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_venta_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("plan_venta.id", ondelete="CASCADE"), nullable=False, index=True)
    zona_id: Mapped[int] = mapped_column(Integer, ForeignKey("zona.id"), nullable=False, index=True)
    
    # Auditoría
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    plan_venta: Mapped["PlanVenta"] = relationship("PlanVenta", back_populates="zonas_asignadas")
    zona: Mapped["Zona"] = relationship("Zona", lazy="noload")
    
    # Constraint único: Una zona no puede estar duplicada en el mismo plan
    __table_args__ = (
        {'comment': 'Zonas especiales asignadas a un plan de venta'},
    )

