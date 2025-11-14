"""
Modelos SQLAlchemy para catálogos de soporte en cliente-service
Catálogos necesarios para gestión de vendedores y planes de venta
"""
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, DECIMAL, JSON, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from datetime import datetime
from decimal import Decimal
from app.db import Base
from typing import Optional
from uuid import UUID, uuid4


class TipoRolVendedor(Base):
    """
    Catálogo de tipos de rol para vendedores
    Define roles jerárquicos con sus permisos
    """
    __tablename__ = "tipo_rol_vendedor"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    codigo: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nivel_jerarquia: Mapped[int] = mapped_column(Integer, nullable=False, default=5)  # 1=más alto, 5=más bajo
    permisos: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"ver_reportes": true, "aprobar_descuentos": true}
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)


class Territorio(Base):
    """
    Catálogo de territorios asignables a vendedores
    Define zonas geográficas de cobertura
    """
    __tablename__ = "territorio"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    codigo: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    pais: Mapped[str] = mapped_column(String(2), nullable=False, index=True)  # ISO 3166-1 alpha-2
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)


class TipoPlan(Base):
    """
    Catálogo de tipos de plan de venta
    Define categorías de planes con comisiones base
    """
    __tablename__ = "tipo_plan"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    codigo: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    comision_base_defecto: Mapped[Decimal] = mapped_column(DECIMAL(5,2), nullable=False, default=5.0)  # Porcentaje
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)


class Region(Base):
    """
    Catálogo de regiones principales para planes de venta
    Define regiones geográficas amplias (Norte, Sur, Este, Oeste, Centro)
    """
    __tablename__ = "region"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    codigo: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    pais: Mapped[str] = mapped_column(String(2), nullable=False, index=True)  # ISO 3166-1 alpha-2
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)


class Zona(Base):
    """
    Catálogo de zonas especiales para planes de venta
    Define zonas específicas por tipo de mercado (Industrial, Hospitalaria, Rural)
    """
    __tablename__ = "zona"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    codigo: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # industrial, hospitalaria, rural, etc.
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

