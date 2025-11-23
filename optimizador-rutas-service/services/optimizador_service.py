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
            
            # 2. Separar por prioridad (AHORA EN 3 GRUPOS)
            urgentes = [p for p in paradas_geocoded if p.get("prioridad") == "alta"]
            medias = [p for p in paradas_geocoded if p.get("prioridad") == "media"]
            bajas = [p for p in paradas_geocoded if p.get("prioridad") == "baja"]
            
            print(f"📊 Pedidos por urgencia: Alta={len(urgentes)}, Media={len(medias)}, Baja={len(bajas)}")
            
            # 3. Variables para acumular resultados
            origen = {"lat": bodega["lat"], "lon": bodega["lon"]}
            secuencia_final = []
            geometria_completa = {"type": "LineString", "coordinates": []}
            distancia_total = 0
            duracion_total = 0
            ultimo_punto = origen
            
            # 4. Función helper para optimizar un grupo
            def optimizar_grupo(grupo: List[dict], punto_inicio: dict, es_ultimo_grupo: bool):
                nonlocal distancia_total, duracion_total, geometria_completa, ultimo_punto
                
                if not grupo:
                    return []
                
                # Determinar destino
                destino = origen if (retorna_bodega and es_ultimo_grupo) else None
                
                # Puntos del grupo
                puntos = [{"lat": p["lat"], "lon": p["lon"]} for p in grupo]
                
                # Optimizar grupo con OSRM
                ruta_grupo = osrm_service.optimizar_ruta(punto_inicio, puntos, destino)
                
                distancia_total += ruta_grupo["distancia_total_km"]
                duracion_total += ruta_grupo["duracion_total_minutos"]
                
                # Agregar geometría
                if ruta_grupo["geometria"]["coordinates"]:
                    geometria_completa["coordinates"].extend(
                        ruta_grupo["geometria"]["coordinates"]
                    )
                
                # Mapear waypoints
                secuencia_grupo = []
                for waypoint in ruta_grupo["secuencia_waypoints"]:
                    waypoint_index = waypoint["waypoint_index"]
                    # Saltar origen y destino
                    if waypoint_index > 0 and (not destino or waypoint_index < len(puntos) + 1):
                        parada_original = grupo[waypoint_index - 1]
                        secuencia_grupo.append(parada_original)
                        ultimo_punto = {
                            "lat": parada_original["lat"],
                            "lon": parada_original["lon"]
                        }
                
                return secuencia_grupo
            
            # 5. Optimizar grupos en orden de prioridad
            print("🔴 Optimizando grupo ALTA...")
            secuencia_urgentes = optimizar_grupo(urgentes, ultimo_punto, False)
            secuencia_final.extend(secuencia_urgentes)
            
            print("🟡 Optimizando grupo MEDIA...")
            secuencia_medias = optimizar_grupo(medias, ultimo_punto, False)
            secuencia_final.extend(secuencia_medias)
            
            print("🔵 Optimizando grupo BAJA...")
            secuencia_bajas = optimizar_grupo(bajas, ultimo_punto, True)
            secuencia_final.extend(secuencia_bajas)
            
            # 6. Construir respuesta final con orden correcto
            paradas_ordenadas = []
            for idx, parada in enumerate(secuencia_final):
                paradas_ordenadas.append({
                    "orden": idx + 1,
                    "id": parada.get("id"),
                    "direccion": parada.get("direccion"),
                    "lat": parada["lat"],
                    "lon": parada["lon"],
                    "prioridad": parada.get("prioridad"),
                    "tiempo_estimado": parada.get("tiempo_estimado_entrega", 10)
                })
            
            # 7. Métricas
            tiempo_total_entregas = sum(p.get("tiempo_estimado_entrega", 10) for p in paradas_geocoded)
            
            metricas = {
                "distancia_total_km": float(distancia_total),
                "duracion_conduccion_min": float(duracion_total),
                "duracion_entregas_min": tiempo_total_entregas,
                "duracion_total_min": float(duracion_total) + tiempo_total_entregas,
                "numero_paradas": len(paradas_ordenadas),
                "paradas_urgentes": len(urgentes),
                "paradas_medias": len(medias),
                "paradas_bajas": len(bajas)
            }
            
            print(f"✅ Ruta optimizada: {len(paradas_ordenadas)} paradas, {distancia_total:.2f} km")
            
            return {
                "distancia_total_km": float(distancia_total),
                "duracion_total_minutos": float(duracion_total) + tiempo_total_entregas,
                "secuencia_paradas": paradas_ordenadas,
                "geometria": geometria_completa,
                "metricas": metricas
            }
            
        except Exception as e:
            raise Exception(f"Error al optimizar entregas: {str(e)}")
optimizador_service = OptimizadorService()