from pydantic import BaseModel
from typing import List, Optional
from datetime import time, date

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

# NUEVOS SCHEMAS PARA TU FRONTEND
class Pedido(BaseModel):
    id_pedido: str
    cliente: str
    direccion: str
    fecha: str
    cajas: int
    urgencia: str  # "alta", "media", "baja"
    zona: str  # "norte", "centro", "sur"
    peso_kg: Optional[float] = None
    volumen_m3: Optional[float] = None

class ConfiguracionRuta(BaseModel):
    bodega_origen: str  # Dirección de la bodega
    hora_inicio: str  # "07:30 AM"
    camion_capacidad_kg: float
    camion_capacidad_m3: float
    retornar_bodega: bool = True
    max_paradas: int = 10
    tiempo_maximo_ruta: str = "08:00 AM"  # Tiempo máximo en formato HH:MM AM/PM

class OptimizarPedidosRequest(BaseModel):
    configuracion: ConfiguracionRuta
    pedidos: List[Pedido]
    costo_km: Optional[float] = 2000  # Costo por kilómetro (COP)
    costo_hora: Optional[float] = 15000  # Costo por hora (COP)

class EntregaOptimizada(BaseModel):
    orden: int
    id_pedido: str
    cliente: str
    direccion: str
    direccion_formateada: str
    lat: float
    lon: float
    hora_estimada: str
    cajas: int
    urgencia: str
    zona: str
    distancia_desde_anterior_km: float
    tiempo_desde_anterior_min: float

class ResumenRuta(BaseModel):
    total_entregas: int
    distancia_total_km: float
    tiempo_total_min: float
    tiempo_conduccion_min: float
    tiempo_entregas_min: float
    total_cajas: int
    costo_estimado: float
    hora_inicio: str
    hora_fin_estimada: str
    capacidad_peso_usada_pct: float
    capacidad_volumen_usada_pct: float

class OptimizarPedidosResponse(BaseModel):
    secuencia_entregas: List[EntregaOptimizada]
    resumen: ResumenRuta
    geometria: dict
    alertas: List[str]