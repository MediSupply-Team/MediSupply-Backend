from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, Date, ForeignKey, DECIMAL
from app.db import Base
from typing import Optional

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
    proveedor_id: Mapped[Optional[str]] = mapped_column(String(64))

class Inventario(Base):
    __tablename__ = "inventario"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    producto_id: Mapped[str] = mapped_column(ForeignKey("producto.id"), index=True, nullable=False)
    pais: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    bodega_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    lote: Mapped[str] = mapped_column(String(64), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    vence: Mapped[str] = mapped_column(Date, nullable=False, index=True)
    condiciones: Mapped[Optional[str]] = mapped_column(String(128))
