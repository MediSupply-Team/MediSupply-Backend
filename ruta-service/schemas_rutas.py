from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List, Dict, Any


# ==================== REQUEST SCHEMAS ====================

class RutaCreate(BaseModel):
    """Schema para crear una ruta (del optimizador)"""
    id_cliente: Optional[str] = Field(None, description="UUID del cliente que solicita la ruta")
    fecha_entrega: Optional[date] = Field(None, description="Fecha programada de entrega (YYYY-MM-DD)")
    secuencia_entregas: List[Dict[str, Any]] = Field(..., description="Array de entregas optimizadas")
    resumen: Dict[str, Any] = Field(..., description="Resumen con distancia, tiempo, costo, etc")
    geometria: Optional[Dict[str, Any]] = Field(None, description="GeoJSON con coordenadas de la ruta")
    alertas: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Alertas de la optimización")
    optimized_by: Optional[str] = Field(None, description="Usuario que solicitó la optimización")
    notes: Optional[str] = Field(None, description="Notas adicionales")


class RutaUpdate(BaseModel):
    """Schema para actualizar notas de una ruta"""
    notes: Optional[str] = None


class AssignDriver(BaseModel):
    """Schema para asignar conductor"""
    driver_id: str = Field(..., description="ID del conductor")
    driver_name: str = Field(..., description="Nombre completo del conductor")


class UpdateStatus(BaseModel):
    """Schema para actualizar estado"""
    status: str = Field(..., description="Nuevo estado: pending, in_progress, completed, cancelled")


# ==================== RESPONSE SCHEMAS ====================

class RutaListItemResponse(BaseModel):
    """
    Schema para items en listas de rutas.
    SIN geometría para optimizar tamaño de respuesta.
    """
    id: str
    created_at: datetime
    updated_at: datetime
    
    # ✅ ID del cliente y fecha de entrega
    id_cliente: Optional[str] = None
    fecha_entrega: Optional[date] = None
    
    # Datos principales (sin geometría)
    secuencia_entregas: List[Dict[str, Any]]
    resumen: Dict[str, Any]
    alertas: Optional[List[Dict[str, Any]]] = None
    
    # Estado y gestión
    status: str
    driver_id: Optional[str] = None
    driver_name: Optional[str] = None
    optimized_by: Optional[str] = None
    notes: Optional[str] = None
    
    model_config = {"from_attributes": True}


class RutaResponse(BaseModel):
    """
    Schema para una ruta individual completa.
    CON geometría para visualización en mapa.
    """
    id: str
    created_at: datetime
    updated_at: datetime
    
    # ✅ ID del cliente y fecha de entrega
    id_cliente: Optional[str] = None
    fecha_entrega: Optional[date] = None
    
    # Datos completos (con geometría)
    secuencia_entregas: List[Dict[str, Any]]
    resumen: Dict[str, Any]
    geometria: Optional[Dict[str, Any]] = None  # ✅ Incluida aquí
    alertas: Optional[List[Dict[str, Any]]] = None
    
    # Estado y gestión
    status: str
    driver_id: Optional[str] = None
    driver_name: Optional[str] = None
    optimized_by: Optional[str] = None
    notes: Optional[str] = None
    
    model_config = {"from_attributes": True}


class RutaCreatedResponse(BaseModel):
    """Schema de respuesta al crear una ruta"""
    id: str
    created_at: datetime
    message: str


class RutaListResponse(BaseModel):
    """Schema para lista paginada de rutas"""
    total: int
    routes: List[RutaListItemResponse]  # ✅ Usa versión sin geometría