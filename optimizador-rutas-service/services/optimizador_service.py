from typing import List, Dict
from services.geocoder_service import geocoder_service
from services.osrm_service import osrm_service

class OptimizadorService:
    
    def optimizar_entregas(self, bodega: dict, paradas: List[dict], retorna_bodega: bool = True) -> dict:
        '''Optimizar ruta de entregas considerando prioridades'''
        try:
            # 1. Geocodificar si es necesario
            paradas_geocoded = []
            for parada in paradas:
                if not parada.get("lat") or not parada.get("lon"):
                    resultado = geocoder_service.geocodificar(parada["direccion"])
                    parada["lat"] = resultado["lat"]
                    parada["lon"] = resultado["lon"]
                paradas_geocoded.append(parada)
            
            if not bodega.get("lat") or not bodega.get("lon"):
                resultado = geocoder_service.geocodificar(bodega["direccion"])
                bodega["lat"] = resultado["lat"]
                bodega["lon"] = resultado["lon"]
            
            # 2. Separar por prioridad
            urgentes = [p for p in paradas_geocoded if p.get("prioridad") == "alta"]
            normales = [p for p in paradas_geocoded if p.get("prioridad") in ["media", "baja"]]
            
            # 3. Optimizar
            origen = {"lat": bodega["lat"], "lon": bodega["lon"]}
            destino = origen if retorna_bodega else None
            
            todas_paradas = urgentes + normales
            puntos = [{"lat": p["lat"], "lon": p["lon"]} for p in todas_paradas]
            
            # 4. Llamar a OSRM
            ruta_optimizada = osrm_service.optimizar_ruta(origen, puntos, destino)
            
            # 5. Mapear waypoints con paradas originales
            secuencia_paradas = []
            for waypoint in ruta_optimizada["secuencia_waypoints"]:
                waypoint_index = waypoint["waypoint_index"]
                if waypoint_index > 0 and (not retorna_bodega or waypoint_index < len(puntos) + 1):
                    parada_original = todas_paradas[waypoint_index - 1]
                    secuencia_paradas.append({
                        "orden": len(secuencia_paradas) + 1,
                        "id": parada_original.get("id"),
                        "direccion": parada_original.get("direccion"),
                        "lat": parada_original["lat"],
                        "lon": parada_original["lon"],
                        "prioridad": parada_original.get("prioridad"),
                        "tiempo_estimado": parada_original.get("tiempo_estimado_entrega", 10)
                    })
            
            # 6. Métricas
            tiempo_total_entregas = sum(p.get("tiempo_estimado_entrega", 10) for p in todas_paradas)
            
            metricas = {
                "distancia_total_km": float(ruta_optimizada["distancia_total_km"]),
                "duracion_conduccion_min": float(ruta_optimizada["duracion_total_minutos"]),
                "duracion_entregas_min": tiempo_total_entregas,
                "duracion_total_min": float(ruta_optimizada["duracion_total_minutos"]) + tiempo_total_entregas,
                "numero_paradas": len(secuencia_paradas),
                "paradas_urgentes": len(urgentes),
                "paradas_normales": len(normales)
            }
            
            return {
                "distancia_total_km": float(ruta_optimizada["distancia_total_km"]),
                "duracion_total_minutos": float(ruta_optimizada["duracion_total_minutos"]) + tiempo_total_entregas,
                "secuencia_paradas": secuencia_paradas,
                "geometria": ruta_optimizada["geometria"],
                "metricas": metricas
            }
            
        except Exception as e:
            raise Exception(f"Error al optimizar entregas: {str(e)}")

optimizador_service = OptimizadorService()