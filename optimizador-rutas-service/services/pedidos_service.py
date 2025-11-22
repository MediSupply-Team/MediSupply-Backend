from typing import List, Dict
from datetime import datetime, timedelta
from services.geocoder_service import geocoder_service
from services.osrm_service import osrm_service
from services.optimizador_service import optimizador_service

class PedidosService:
    
    def optimizar_pedidos_completo(
        self, 
        configuracion: dict, 
        pedidos: List[dict],
        costo_km: float = 2000,
        costo_hora: float = 15000
    ) -> dict:
        """Optimizar pedidos completo: geocodifica, optimiza y calcula todo"""
        
        try:
            alertas = []
            
            # 1. Geocodificar bodega
            print(f"Geocodificando bodega: {configuracion['bodega_origen']}")
            bodega_geo = geocoder_service.geocodificar(configuracion['bodega_origen'])
            
            bodega = {
                "id": "bodega",
                "direccion": configuracion['bodega_origen'],
                "lat": bodega_geo["lat"],
                "lon": bodega_geo["lon"]
            }
            
            # 2. Geocodificar todos los pedidos
            print(f"Geocodificando {len(pedidos)} pedidos...")
            paradas = []
            for pedido in pedidos:
                try:
                    geo = geocoder_service.geocodificar(pedido["direccion"])
                    paradas.append({
                        "id": pedido["id_pedido"],
                        "cliente": pedido["cliente"],
                        "direccion": pedido["direccion"],
                        "direccion_formateada": geo["direccion_formateada"],
                        "lat": geo["lat"],
                        "lon": geo["lon"],
                        "prioridad": pedido["urgencia"],
                        "tiempo_estimado_entrega": 15,  # Tiempo estimado por entrega
                        "cajas": pedido["cajas"],
                        "zona": pedido["zona"],
                        "peso_kg": pedido.get("peso_kg", 0),
                        "volumen_m3": pedido.get("volumen_m3", 0)
                    })
                except Exception as e:
                    alertas.append(f"No se pudo geocodificar: {pedido['direccion']}")
                    print(f"Error geocodificando {pedido['direccion']}: {str(e)}")
            
            if not paradas:
                raise Exception("No se pudo geocodificar ningún pedido")
            
            # 3. Optimizar ruta
            print("Optimizando ruta...")
            ruta_optimizada = optimizador_service.optimizar_entregas(
                bodega=bodega,
                paradas=paradas,
                retorna_bodega=configuracion["retornar_bodega"]
            )
            
            # 4. Calcular horarios estimados
            print("Calculando horarios...")
            hora_actual = self._parse_hora(configuracion["hora_inicio"])
            secuencia_entregas = []
            
            for i, parada in enumerate(ruta_optimizada["secuencia_paradas"]):
                # Encontrar el pedido original
                pedido_original = next(p for p in paradas if p["id"] == parada["id"])
                
                # Calcular distancia y tiempo desde parada anterior
                if i == 0:
                    # Primera parada desde bodega
                    origen = {"lat": bodega["lat"], "lon": bodega["lon"]}
                    destino = {"lat": parada["lat"], "lon": parada["lon"]}
                else:
                    parada_anterior = ruta_optimizada["secuencia_paradas"][i-1]
                    origen = {"lat": parada_anterior["lat"], "lon": parada_anterior["lon"]}
                    destino = {"lat": parada["lat"], "lon": parada["lon"]}
                
                try:
                    ruta_tramo = osrm_service.calcular_ruta(origen, destino)
                    distancia_km = ruta_tramo["distancia_km"]
                    tiempo_viaje_min = ruta_tramo["duracion_minutos"]
                except:
                    distancia_km = 0
                    tiempo_viaje_min = 0
                
                # Sumar tiempo de viaje
                hora_actual += timedelta(minutes=tiempo_viaje_min)
                
                secuencia_entregas.append({
                    "orden": i + 1,
                    "id_pedido": parada["id"],
                    "cliente": pedido_original["cliente"],
                    "direccion": pedido_original["direccion"],
                    "direccion_formateada": pedido_original["direccion_formateada"],
                    "lat": parada["lat"],
                    "lon": parada["lon"],
                    "hora_estimada": hora_actual.strftime("%H:%M"),
                    "cajas": pedido_original["cajas"],
                    "urgencia": pedido_original["prioridad"],
                    "zona": pedido_original["zona"],
                    "distancia_desde_anterior_km": round(distancia_km, 2),
                    "tiempo_desde_anterior_min": round(tiempo_viaje_min, 1)
                })
                
                # Sumar tiempo de entrega
                hora_actual += timedelta(minutes=parada["tiempo_estimado"])
            
            # 5. Calcular resumen
            total_cajas = sum(p["cajas"] for p in paradas)
            total_peso = sum(p.get("peso_kg", 0) for p in paradas)
            total_volumen = sum(p.get("volumen_m3", 0) for p in paradas)
            
            capacidad_peso_pct = (total_peso / configuracion["camion_capacidad_kg"]) * 100
            capacidad_volumen_pct = (total_volumen / configuracion["camion_capacidad_m3"]) * 100
            
            # Verificar capacidades
            if capacidad_peso_pct > 100:
                alertas.append(f"⚠️ Excede capacidad de peso: {capacidad_peso_pct:.1f}%")
            if capacidad_volumen_pct > 100:
                alertas.append(f"⚠️ Excede capacidad de volumen: {capacidad_volumen_pct:.1f}%")
            
            # ✅ FIX: Calcular distancia sumando tramos individuales
            distancia_total_real = sum(e["distancia_desde_anterior_km"] for e in secuencia_entregas)
            
            # Agregar retorno a bodega si aplica
            if configuracion["retornar_bodega"] and len(secuencia_entregas) > 0:
                ultima_entrega = secuencia_entregas[-1]
                try:
                    origen_retorno = {"lat": ultima_entrega["lat"], "lon": ultima_entrega["lon"]}
                    destino_retorno = {"lat": bodega["lat"], "lon": bodega["lon"]}
                    ruta_retorno = osrm_service.calcular_ruta(origen_retorno, destino_retorno)
                    distancia_total_real += ruta_retorno["distancia_km"]
                except:
                    pass  # Si falla, continuar sin retorno
            
            # Calcular tiempos reales
            tiempo_conduccion_real = sum(e["tiempo_desde_anterior_min"] for e in secuencia_entregas)
            tiempo_entregas_real = len(secuencia_entregas) * 15  # 15 min por entrega
            tiempo_total_real = tiempo_conduccion_real + tiempo_entregas_real
            
            # Calcular costos con valores reales
            costo_distancia = distancia_total_real * costo_km
            costo_tiempo = (tiempo_total_real / 60) * costo_hora
            costo_total = costo_distancia + costo_tiempo
            
            resumen = {
                "total_entregas": len(secuencia_entregas),
                "distancia_total_km": round(distancia_total_real, 2),  # ✅ Distancia correcta
                "tiempo_total_min": round(tiempo_total_real, 1),  # ✅ Tiempo correcto
                "tiempo_conduccion_min": round(tiempo_conduccion_real, 1),  # ✅ Conducción correcta
                "tiempo_entregas_min": tiempo_entregas_real,
                "total_cajas": total_cajas,
                "costo_estimado": round(costo_total, 0),
                "hora_inicio": configuracion["hora_inicio"],
                "hora_fin_estimada": hora_actual.strftime("%H:%M"),
                "capacidad_peso_usada_pct": round(capacidad_peso_pct, 1),
                "capacidad_volumen_usada_pct": round(capacidad_volumen_pct, 1)
            }
            
            return {
                "secuencia_entregas": secuencia_entregas,
                "resumen": resumen,
                "geometria": ruta_optimizada["geometria"],
                "alertas": alertas
            }
            
        except Exception as e:
            raise Exception(f"Error al optimizar pedidos: {str(e)}")
    
    def _parse_hora(self, hora_str: str) -> datetime:
        """Convertir hora en formato '07:30 AM' a datetime"""
        try:
            # Formato: "07:30 AM"
            hora = datetime.strptime(hora_str, "%I:%M %p")
            # Usar fecha de hoy
            ahora = datetime.now()
            return ahora.replace(hour=hora.hour, minute=hora.minute, second=0, microsecond=0)
        except:
            # Fallback: usar hora actual
            return datetime.now()

pedidos_service = PedidosService()