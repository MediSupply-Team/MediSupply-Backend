# models.py
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

class Vendedor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str

class Producto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    stock: int = 0

class Venta(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha: datetime
    vendedor_id: int = Field(foreign_key="vendedor.id")
    producto_id: int = Field(foreign_key="producto.id")
    cantidad: int
    monto_total: float
    estado: str  # "completado" | "pendiente"

