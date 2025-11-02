from fastapi import APIRouter, HTTPException, Query
from models.schemas import OptimizarRequest
from services.geocoder_service import geocoder_service
from services.osrm_service import osrm_service
from services.optimizador_service import optimizador_service
from services.ruta_service_client import ruta_service_client
from services.pedidos_service import pedidos_service
from typing import List
from models.schemas import OptimizarRequest, GeocodeBatchRequest, OptimizarPedidosRequest
router = APIRouter(prefix="/api/v1", tags=["Optimizador"])

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

@router.post(
    "/optimize/pedidos",
    tags=["Optimizador"],
    summary="🎯 Optimizar Ruta de Entregas",
    description="""
    ## 📦 Optimización Inteligente de Rutas de Entrega
    
    Este endpoint procesa pedidos pendientes y genera la ruta óptima considerando múltiples factores.
    
    ### 🔄 Proceso Automático:
    
    1. **Geocodificación**: Convierte todas las direcciones a coordenadas GPS usando Mapbox
    2. **Priorización**: Ordena entregas por urgencia (Alta → Media → Baja)
    3. **Optimización TSP**: Calcula la secuencia más eficiente usando OSRM
    4. **Cálculo de Horarios**: Estima tiempos de llegada considerando tráfico
    5. **Validación de Capacidad**: Verifica límites de peso y volumen del camión
    6. **Estimación de Costos**: Calcula gastos de combustible y tiempo
    
    ### 📊 Datos que Retorna:
    
    - ✅ **Secuencia Optimizada**: Lista ordenada de entregas con horarios estimados
    - ✅ **Resumen Ejecutivo**: Distancia total, tiempo, costos y capacidades
    - ✅ **Geometría GeoJSON**: Para visualización en mapas (Leaflet, Mapbox, etc.)
    - ✅ **Alertas**: Avisos si hay problemas de capacidad o restricciones
    
    ### 🚛 Parámetros de Configuración:
    
    | Campo | Descripción | Ejemplo |
    |-------|-------------|---------|
    | `bodega_origen` | Dirección del punto de partida | "Calle 100 #15-20, Bogotá" |
    | `hora_inicio` | Hora de salida | "07:30 AM" |
    | `camion_capacidad_kg` | Capacidad máxima en peso | 500 |
    | `camion_capacidad_m3` | Capacidad máxima en volumen | 12 |
    | `retornar_bodega` | Si regresa al punto de origen | true |
    | `max_paradas` | Número máximo de entregas | 10 |
    
    ### 📦 Información por Pedido:
    
    | Campo | Descripción | Valores |
    |-------|-------------|---------|
    | `urgencia` | Prioridad de entrega | "alta", "media", "baja" |
    | `zona` | Zona geográfica | "norte", "centro", "sur" |
    | `cajas` | Número de unidades | Número entero |
    | `peso_kg` | Peso en kilogramos | Número decimal |
    | `volumen_m3` | Volumen en metros cúbicos | Número decimal |
    
    ### 💰 Cálculo de Costos:
    
    - **Costo por KM**: Valor predeterminado $2,000 COP/km
    - **Costo por Hora**: Valor predeterminado $15,000 COP/hora
    - **Costo Total**: (Distancia × CostoKM) + (Tiempo × CostoHora)
    
    ### ⚠️ Validaciones Automáticas:
    
    - Verifica que no se exceda la capacidad del camión
    - Valida que todas las direcciones sean geocodificables
    - Alerta si el tiempo total excede la jornada laboral
    - Prioriza entregas urgentes al inicio de la ruta
    
    ### 🗺️ Integración con Mapas:
    
    La geometría retornada es compatible con:
    - Leaflet.js
    - Mapbox GL JS
    - Google Maps
    - OpenLayers
```javascript
    // Ejemplo de uso en el frontend
    const resultado = await fetch('/api/v1/optimize/pedidos', {
        method: 'POST',
        body: JSON.stringify(data)
    }).then(r => r.json());
    
    // Dibujar en mapa
    L.geoJSON(resultado.geometria).addTo(map);
```
    """,
    response_description="Ruta optimizada con secuencia de entregas, resumen de métricas y geometría",
    responses={
        200: {
            "description": "✅ Ruta optimizada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "secuencia_entregas": [
                            {
                                "orden": 1,
                                "id_pedido": "ORD-001",
                                "cliente": "Hospital San José",
                                "direccion": "Calle 45 #12-34, Bogotá",
                                "direccion_formateada": "Cl 45 12 34, 110111 Bogotá, Colombia",
                                "lat": 4.637582,
                                "lon": -74.148166,
                                "hora_estimada": "08:15",
                                "cajas": 12,
                                "urgencia": "alta",
                                "zona": "norte",
                                "distancia_desde_anterior_km": 5.2,
                                "tiempo_desde_anterior_min": 12.5
                            },
                            {
                                "orden": 2,
                                "id_pedido": "ORD-002",
                                "cliente": "Clínica del Norte",
                                "direccion": "Carrera 15 #78-90, Bogotá",
                                "direccion_formateada": "Cra 15 78 90, 110221 Bogotá, Colombia",
                                "lat": 4.668062,
                                "lon": -74.056889,
                                "hora_estimada": "08:42",
                                "cajas": 8,
                                "urgencia": "media",
                                "zona": "norte",
                                "distancia_desde_anterior_km": 3.8,
                                "tiempo_desde_anterior_min": 9.2
                            }
                        ],
                        "resumen": {
                            "total_entregas": 8,
                            "distancia_total_km": 42.5,
                            "tiempo_total_min": 200,
                            "tiempo_conduccion_min": 140,
                            "tiempo_entregas_min": 60,
                            "total_cajas": 68,
                            "costo_estimado": 85000,
                            "hora_inicio": "07:30 AM",
                            "hora_fin_estimada": "11:50",
                            "capacidad_peso_usada_pct": 25.0,
                            "capacidad_volumen_usada_pct": 17.5
                        },
                        "geometria": {
                            "type": "LineString",
                            "coordinates": [
                                [-74.0851, 4.7110],
                                [-74.148166, 4.637582],
                                [-74.056889, 4.668062]
                            ]
                        },
                        "alertas": []
                    }
                }
            }
        },
        400: {
            "description": "❌ Error en los parámetros de entrada",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error de validación: campo 'urgencia' debe ser 'alta', 'media' o 'baja'"
                    }
                }
            }
        },
        404: {
            "description": "❌ No se encontraron resultados",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "No se pudo geocodificar ninguna dirección"
                    }
                }
            }
        },
        500: {
            "description": "❌ Error interno del servidor",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error al optimizar pedidos: OSRM no responde"
                    }
                }
            }
        }
    }
)
async def optimizar_pedidos(request: OptimizarPedidosRequest):
    """
    Endpoint completo para optimizar pedidos desde el frontend
    
    Recibe:
    - Configuración de ruta (bodega, camión, horarios)
    - Lista de pedidos (con direcciones)
    
    Devuelve:
    - Secuencia optimizada con horarios
    - Resumen completo (distancia, tiempo, costo)
    - Geometría para el mapa
    - Alertas si hay problemas
    """
    try:
        resultado = pedidos_service.optimizar_pedidos_completo(
            configuracion=request.configuracion.dict(),
            pedidos=[p.dict() for p in request.pedidos],
            costo_km=request.costo_km,
            costo_hora=request.costo_hora
        )
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))