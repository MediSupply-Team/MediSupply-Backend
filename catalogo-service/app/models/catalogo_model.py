from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, Date, ForeignKey, DECIMAL, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.db import Base
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4

class Proveedor(Base):
    """
    Modelo de Proveedor para HU: Registrar Proveedor
    Representa los proveedores de productos médicos
    """
    __tablename__ = "proveedor"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    nit: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    empresa: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contacto_nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    contacto_email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    contacto_telefono: Mapped[Optional[str]] = mapped_column(String(32))
    contacto_cargo: Mapped[Optional[str]] = mapped_column(String(128))
    direccion: Mapped[Optional[str]] = mapped_column(String(512))
    pais: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    notas: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id: Mapped[Optional[str]] = mapped_column(String(64))


class Bodega(Base):
    """
    Modelo de Bodega (Warehouse) para gestión de almacenes.
    Representa los almacenes/bodegas donde se guarda el inventario.
    """
    __tablename__ = "bodega"
    
    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # UUID como PK
    codigo: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)  # Código de negocio único
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    pais: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    direccion: Mapped[Optional[str]] = mapped_column(String(512))
    ciudad: Mapped[Optional[str]] = mapped_column(String(128))
    responsable: Mapped[Optional[str]] = mapped_column(String(255))
    telefono: Mapped[Optional[str]] = mapped_column(String(32))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    capacidad_m3: Mapped[Optional[float]] = mapped_column(DECIMAL(10,2))  # Capacidad en metros cúbicos
    tipo: Mapped[Optional[str]] = mapped_column(String(64))  # PRINCIPAL, SECUNDARIA, TRANSITO
    notas: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id: Mapped[Optional[str]] = mapped_column(String(64))


class Producto(Base):
    __tablename__ = "producto"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    codigo: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    categoria_id: Mapped[str] = mapped_column(String(64), nullable=False)
    presentacion: Mapped[Optional[str]] = mapped_column(String(128))
    precio_unitario: Mapped[float] = mapped_column(DECIMAL(12,2), nullable=False)
    requisitos_almacenamiento: Mapped[Optional[str]] = mapped_column(String(128))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Nuevos campos para gestión de inventario
    stock_minimo: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    stock_critico: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    requiere_lote: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requiere_vencimiento: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Campos para HU021 - Carga masiva y gestión de proveedores
    certificado_sanitario: Mapped[Optional[str]] = mapped_column(String(255))
    tiempo_entrega_dias: Mapped[Optional[int]] = mapped_column(Integer)
    proveedor_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)  # FK a proveedor

class Inventario(Base):
    __tablename__ = "inventario"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    producto_id: Mapped[str] = mapped_column(ForeignKey("producto.id"), index=True, nullable=False)
    pais: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    bodega_id: Mapped[str] = mapped_column(ForeignKey("bodega.id", ondelete="RESTRICT"), nullable=False, index=True)
    lote: Mapped[str] = mapped_column(String(64), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    vence: Mapped[str] = mapped_column(Date, nullable=False, index=True)
    condiciones: Mapped[Optional[str]] = mapped_column(String(128))
