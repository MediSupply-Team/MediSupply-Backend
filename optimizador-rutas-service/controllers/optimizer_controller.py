from fastapi import APIRouter, HTTPException, Query
from models.schemas import OptimizarRequest
from services.geocoder_service import geocoder_service
from services.osrm_service import osrm_service
from services.optimizador_service import optimizador_service
from services.ruta_service_client import ruta_service_client
from typing import List
from models.schemas import GeocodeBatchRequest

router = APIRouter(prefix="/api", tags=["Optimizador"])

@router.post("/optimize/route")
async def optimizar_ruta(request: OptimizarRequest):
    """Optimizar ruta de entregas"""
    try:
        resultado = optimizador_service.optimizar_entregas(
            bodega=request.bodega.dict(),
            paradas=[p.dict() for p in request.paradas],
            retorna_bodega=request.retorna_bodega
        )
        return resultado
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/optimize/from-service")
async def optimizar_desde_servicio(
    fecha: str = Query(..., description="Fecha en formato YYYY-MM-DD"),
    vendedor_id: int = Query(..., description="ID del vendedor")
):
    """Obtener visitas de ruta-service y optimizar"""
    try:
        visitas = ruta_service_client.obtener_visitas(fecha, vendedor_id)
        
        if not visitas:
            raise HTTPException(status_code=404, detail="No se encontraron visitas")
        
        bodega = {
            "direccion": visitas[0].get("direccion"),
            "lat": visitas[0].get("lat"),
            "lon": visitas[0].get("lng")
        }
        
        paradas = []
        for v in visitas[1:]:
            paradas.append({
                "id": str(v.get("id")),
                "cliente": v.get("cliente"),
                "direccion": v.get("direccion"),
                "lat": v.get("lat"),
                "lon": v.get("lng"),
                "prioridad": "media",
                "tiempo_estimado_entrega": 15
            })
        
        resultado = optimizador_service.optimizar_entregas(
            bodega=bodega,
            paradas=paradas,
            retorna_bodega=False
        )
        
        return resultado
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/geocode")
async def geocodificar(
    direccion: str = Query(..., description="Direccion a geocodificar"),
    ciudad: str = Query(default="Bogota", description="Ciudad")
):
    """Convertir direccion a coordenadas"""
    try:
        resultado = geocoder_service.geocodificar(direccion, ciudad)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/geocode/batch")
async def geocodificar_batch(request: GeocodeBatchRequest):
    """Geocodificar multiples direcciones"""
    try:
        resultados = geocoder_service.geocodificar_multiple(request.direcciones)
        return {"resultados": resultados}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/route/calculate")
async def calcular_ruta(
    origen_lat: float = Query(...),
    origen_lon: float = Query(...),
    destino_lat: float = Query(...),
    destino_lon: float = Query(...)
):
    """Calcular ruta entre dos puntos"""
    try:
        origen = {"lat": origen_lat, "lon": origen_lon}
        destino = {"lat": destino_lat, "lon": destino_lon}
        
        resultado = osrm_service.calcular_ruta(origen, destino)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/route/matrix")
async def calcular_matriz(puntos: List[dict]):
    """Calcular matriz de distancias"""
    try:
        resultado = osrm_service.calcular_matriz(puntos)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))