"""
Modelos SQLAlchemy para cliente-service siguiendo patrón catalogo-service
Definición de tablas para HU07: Consultar Cliente y HU: Registrar Vendedor
"""
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, Date, DateTime, ForeignKey, DECIMAL, JSON, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from datetime import date, datetime
from decimal import Decimal
from app.db import Base
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from app.models.plan_venta_model import PlanVenta


class Vendedor(Base):
    """
    Modelo de Vendedor para HU: Registrar Vendedor (Extendido - Fase 2)
    Representa los vendedores del sistema MediSupply con catálogos y jerarquía
    """
    __tablename__ = "vendedor"
    
    # Campos principales
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    identificacion: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    nombre_completo: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    telefono: Mapped[str] = mapped_column(String(32), nullable=False)
    pais: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    
    # Campos de credenciales y acceso
    username: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True, index=True)  # Para login
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Campos de rol y permisos
    rol: Mapped[str] = mapped_column(String(32), default="seller", nullable=False)  # seller para coincidir con orders
    rol_vendedor_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tipo_rol_vendedor.id"), nullable=True, index=True)  # FK a TipoRolVendedor
    
    # Campos de asignación geográfica y jerarquía
    territorio_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("territorio.id"), nullable=True, index=True)  # FK a Territorio
    supervisor_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vendedor.id"), nullable=True, index=True)  # FK a Vendedor (auto-referencia)
    
    # Campos adicionales
    fecha_ingreso: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # Fecha de ingreso al equipo
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Notas adicionales
    
    # Campos de auditoría
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Relación 1:1 con Plan de Venta (se carga solo en /vendedores/{id}/detalle)
    # NO se carga automáticamente para evitar queries innecesarios
    plan_venta: Mapped[Optional["PlanVenta"]] = relationship(
        "PlanVenta", 
        back_populates="vendedor",
        uselist=False,  # 1:1 relationship
        lazy="noload"  # NO cargar automáticamente, solo cuando se necesite explícitamente
    )


class Cliente(Base):
    """
    Modelo de Cliente principal
    Representa los clientes del sistema MediSupply
    """
    __tablename__ = "cliente"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    nit: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    codigo_unico: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    telefono: Mapped[str] = mapped_column(String(32), nullable=True)
    direccion: Mapped[str] = mapped_column(String(512), nullable=True)
    ciudad: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    pais: Mapped[str] = mapped_column(String(8), nullable=True, default="CO")
    vendedor_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)  # FK a vendedor
    rol: Mapped[str] = mapped_column(String(32), default="cliente", nullable=False)  # Rol del cliente
    # tipo_cliente: Mapped[str] = mapped_column(String(32), nullable=True, default="farmacia")  # Comentado: columna no existe en DB
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CompraHistorico(Base):
    """
    Modelo de Histórico de Compras
    Registra todas las compras realizadas por los clientes
    """
    __tablename__ = "compra_historico"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    cliente_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("cliente.id"), nullable=False, index=True)
    orden_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    producto_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    producto_nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    categoria_producto: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(DECIMAL(12,2), nullable=False)
    precio_total: Mapped[Decimal] = mapped_column(DECIMAL(12,2), nullable=False)
    fecha_compra: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    estado_orden: Mapped[str] = mapped_column(String(32), nullable=True, default="completada")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DevolucionHistorico(Base):
    """
    Modelo de Histórico de Devoluciones
    Registra todas las devoluciones realizadas por los clientes
    """
    __tablename__ = "devolucion_historico"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    cliente_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("cliente.id"), nullable=False, index=True)
    compra_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    compra_orden_id: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    producto_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    producto_nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    cantidad_devuelta: Mapped[int] = mapped_column(Integer, nullable=False)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    categoria_motivo: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    fecha_devolucion: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    estado: Mapped[str] = mapped_column(String(32), nullable=True, default="procesada")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ConsultaClienteLog(Base):
    """
    Modelo de Log de Consultas
    Para trazabilidad de todas las consultas realizadas (criterio HU07)
    """
    __tablename__ = "consulta_cliente_log"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # BIGSERIAL en SQL
    vendedor_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    cliente_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    tipo_consulta: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tipo_busqueda: Mapped[str] = mapped_column(String(32), nullable=True, index=True)
    termino_busqueda: Mapped[str] = mapped_column(String(255), nullable=True)
    took_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    metadatos: Mapped[dict] = mapped_column(JSON, nullable=True)
    fecha_consulta: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class ProductoPreferido(Base):
    """
    Modelo de Productos Preferidos (vista materializada o tabla calculada)
    Para optimizar consultas de productos preferidos
    """
    __tablename__ = "producto_preferido"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # BIGSERIAL en SQL
    cliente_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("cliente.id"), nullable=False, index=True)
    producto_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    producto_nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    categoria_producto: Mapped[str] = mapped_column(String(128), nullable=True)
    frecuencia_compra: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cantidad_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cantidad_promedio: Mapped[Decimal] = mapped_column(DECIMAL(8,2), nullable=False, default=0)
    ultima_compra: Mapped[date] = mapped_column(Date, nullable=True)
    meses_desde_ultima_compra: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EstadisticaCliente(Base):
    """
    Modelo de Estadísticas del Cliente (vista materializada o tabla calculada)
    Para optimizar consultas de estadísticas resumidas
    """
    __tablename__ = "estadistica_cliente"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # BIGSERIAL en SQL
    cliente_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("cliente.id"), nullable=False, unique=True, index=True)
    total_compras: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_productos_unicos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_devoluciones: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valor_total_compras: Mapped[Decimal] = mapped_column(DECIMAL(15,2), nullable=False, default=0)
    promedio_orden: Mapped[Decimal] = mapped_column(DECIMAL(12,2), nullable=False, default=0)
    frecuencia_compra_mensual: Mapped[Decimal] = mapped_column(DECIMAL(8,2), nullable=False, default=0)
    tasa_devolucion: Mapped[Decimal] = mapped_column(DECIMAL(5,2), nullable=False, default=0)
    cliente_desde: Mapped[date] = mapped_column(Date, nullable=True)
    ultima_compra: Mapped[date] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)