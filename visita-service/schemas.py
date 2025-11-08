"""
Schemas Pydantic para validación y documentación de API
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class EstadoVisitaEnum(str, Enum):
    """Estados posibles de una visita"""
    EXITOSA = "exitosa"
    PENDIENTE = "pendiente"
    CANCELADA = "cancelada"


class VideoAnalysisStatusEnum(str, Enum):
    """Estados posibles de un análisis de video"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoAnalysisResponse(BaseModel):
    """Respuesta de análisis de video"""
    id: int
    visita_id: int
    video_url: str
    status: VideoAnalysisStatusEnum
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class VideoAnalysisRequest(BaseModel):
    """Request para análisis manual de video"""
    visita_id: int = Field(..., description="ID de la visita asociada")
    video_url: str = Field(..., description="URL del video a analizar")


class HallazgoResponse(BaseModel):
    """Respuesta de un hallazgo"""
    id: int
    tipo: str
    descripcion: Optional[str]
    url_descarga: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class VisitaResponse(BaseModel):
    """Respuesta completa de una visita"""
    id: int
    vendedor_id: int
    cliente_id: int
    nombre_contacto: str
    observaciones: Optional[str]
    estado: EstadoVisitaEnum
    fecha_visita: datetime
    created_at: datetime
    hallazgos: List[HallazgoResponse] = []
    video_analyses: List[VideoAnalysisResponse] = []
    
    class Config:
        from_attributes = True


class VideoServiceStatusResponse(BaseModel):
    """Estado del servicio de análisis de video"""
    service: str = "video-analysis"
    status: str
    gemini_configured: bool
    model: str
    message: str
