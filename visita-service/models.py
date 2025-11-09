from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import JSON
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
    # Relación con análisis de video
    video_analyses: List["VideoAnalysis"] = Relationship(back_populates="visita")


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


class VideoAnalysis(SQLModel, table=True):
    """Análisis de video usando Gemini AI"""
    __tablename__ = "video_analysis"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    visita_id: int = Field(foreign_key="visitas.id", index=True)
    video_url: str  # URL del video en S3 o path local
    summary: Optional[str] = None  # Resumen del video generado por Gemini
    tags: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))  # Etiquetas generadas
    recommendations: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))  # Recomendaciones de productos
    status: str = Field(default="pending")  # pending, processing, completed, failed
    error_message: Optional[str] = None  # Mensaje de error si falla el análisis
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Relación inversa
    visita: Optional[Visita] = Relationship(back_populates="video_analyses")
