from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List
from enum import Enum

class EstadoVisita(str, Enum):
    EXITOSA = "exitosa"
    PENDIENTE = "pendiente"
    CANCELADA = "cancelada"

class Visita(SQLModel, table=True):
    """Modelo de Visita a cliente"""
    __tablename__ = "visitas"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    vendedor_id: int = Field(index=True)
    cliente_id: int = Field(index=True)
    nombre_contacto: str
    observaciones: Optional[str] = None
    estado: EstadoVisita = Field(default=EstadoVisita.PENDIENTE)
    fecha_visita: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relación con hallazgos (fotos/videos)
    hallazgos: List["Hallazgo"] = Relationship(back_populates="visita")


class Hallazgo(SQLModel, table=True):
    """Hallazgos técnicos o clínicos: fotos, videos, textos"""
    __tablename__ = "hallazgos"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    visita_id: int = Field(foreign_key="visitas.id", index=True)
    tipo: str  # "foto", "video", "texto"
    contenido: str  # ruta del archivo o texto plano
    descripcion: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relación inversa
    visita: Optional[Visita] = Relationship(back_populates="hallazgos")
