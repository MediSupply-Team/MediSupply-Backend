from pydantic import BaseModel
from typing import List, Optional

class Coordenadas(BaseModel):
    lat: float
    lon: float

class Parada(BaseModel):
    id: Optional[str] = None
    cliente: Optional[str] = None
    direccion: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    prioridad: str = "media"
    tiempo_estimado_entrega: int = 10

class OptimizarRequest(BaseModel):
    bodega: Parada
    paradas: List[Parada]
    retorna_bodega: bool = True

class GeocodeBatchRequest(BaseModel):
    direcciones: List[str]