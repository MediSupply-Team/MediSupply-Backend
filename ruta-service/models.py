from sqlmodel import SQLModel, Field, Column, JSON
from datetime import date, datetime
from typing import Optional, List, Dict, Any
import uuid


class Visita(SQLModel, table=True):
    """Modelo para visitas de vendedores"""
    id: int | None = Field(default=None, primary_key=True)
    vendedor_id: str  # UUID del vendedor
    cliente: str  # Nombre del cliente (mantener nombre original)
    direccion: str  # Dirección completa (mantener nombre original)
    fecha: date
    hora: str
    lat: float
    lng: float
    # Campos adicionales internos (no se exponen en el endpoint actual)
    cliente_id: Optional[str] = None  # UUID real del cliente en cliente-service
    ciudad: Optional[str] = None
    estado: str = Field(default="pendiente")
    observaciones: Optional[str] = None


class Ruta(SQLModel, table=True):
    """
    Modelo para rutas optimizadas
    Estructura adaptada a la respuesta del optimizador-rutas-service
    """
    __tablename__ = "rutas"
    
    # Primary key y timestamps
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Datos del optimizador (JSONB completo)
    secuencia_entregas: List[Dict[str, Any]] = Field(
        sa_column=Column(JSON),
        description="Array de entregas optimizadas"
    )
    resumen: Dict[str, Any] = Field(
        sa_column=Column(JSON),
        description="Resumen: distancia, tiempo, costo, etc"
    )
    geometria: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="GeoJSON con coordenadas de la ruta"
    )
    alertas: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Alertas de la optimización"
    )
    
    # Gestion
    status: str = Field(default='pending', max_length=20)
    driver_id: Optional[str] = Field(default=None)
    driver_name: Optional[str] = Field(default=None, max_length=255)
    optimized_by: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)
