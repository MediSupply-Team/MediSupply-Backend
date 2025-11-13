from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class RutaCreate(BaseModel):
    """Recibe directamente la respuesta del optimizador"""
    secuencia_entregas: List[Dict[str, Any]]
    resumen: Dict[str, Any]
    geometria: Optional[Dict[str, Any]] = None
    alertas: Optional[List[Dict[str, Any]]] = None
    optimized_by: Optional[str] = None
    notes: Optional[str] = None


class RutaUpdate(BaseModel):
    notes: Optional[str] = None


class AssignDriver(BaseModel):
    driver_id: str
    driver_name: str


class UpdateStatus(BaseModel):
    status: str = Field(..., pattern="^(pending|in_progress|completed|cancelled)$")


class RutaResponse(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
    secuencia_entregas: List[Dict[str, Any]]
    resumen: Dict[str, Any]
    geometria: Optional[Dict[str, Any]]
    alertas: Optional[List[Dict[str, Any]]]
    status: str
    driver_id: Optional[str]
    driver_name: Optional[str]
    optimized_by: Optional[str]
    notes: Optional[str]

    model_config = {"from_attributes": True}


class RutaCreatedResponse(BaseModel):
    id: str
    created_at: datetime
    message: str = "Route created successfully"

    model_config = {"from_attributes": True}


class RutaListResponse(BaseModel):
    total: int
    routes: List[RutaResponse]
