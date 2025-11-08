import requests
from config.settings import settings
from typing import List

class OSRMService:
    def __init__(self):
        self.base_url = settings.osrm_url
    
    def calcular_ruta(self, origen: dict, destino: dict) -> dict:
        """Calcular ruta entre dos puntos"""
        try:
            coords = str(origen['lon']) + "," + str(origen['lat']) + ";" + str(destino['lon']) + "," + str(destino['lat'])
            url = self.base_url + "/route/v1/driving/" + coords
            
            params = {
                "overview": "full",
                "geometries": "geojson",
                "steps": "true"
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != "Ok":
                raise ValueError("OSRM no pudo calcular la ruta")
            
            ruta = data["routes"][0]
            
            return {
                "distancia_metros": ruta["distance"],
                "distancia_km": round(ruta["distance"] / 1000, 2),
                "duracion_segundos": ruta["duration"],
                "duracion_minutos": round(ruta["duration"] / 60, 1),
                "geometria": ruta["geometry"],
                "pasos": ruta["legs"][0]["steps"]
            }
        except Exception as e:
            raise Exception("Error al calcular ruta: " + str(e))
    
    def calcular_matriz(self, puntos: List[dict]) -> dict:
        """Calcular matriz de distancias/tiempos"""
        try:
            coords_list = []
            for p in puntos:
                coords_list.append(str(p['lon']) + "," + str(p['lat']))
            coordenadas = ";".join(coords_list)
            
            url = self.base_url + "/table/v1/driving/" + coordenadas
            
            params = {
                "annotations": "distance,duration"
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != "Ok":
                raise ValueError("OSRM no pudo calcular la matriz")
            
            return {
                "distancias": data["distances"],
                "duraciones": data["durations"]
            }
        except Exception as e:
            raise Exception("Error al calcular matriz: " + str(e))
    
    def optimizar_ruta(self, origen: dict, paradas: List[dict], destino: dict = None) -> dict:
        """Optimizar secuencia de paradas (TSP)"""
        try:
            coordenadas = [str(origen['lon']) + "," + str(origen['lat'])]
            
            for p in paradas:
                coordenadas.append(str(p['lon']) + "," + str(p['lat']))
            
            if destino:
                coordenadas.append(str(destino['lon']) + "," + str(destino['lat']))
            
            coordenadas_str = ";".join(coordenadas)
            url = self.base_url + "/trip/v1/driving/" + coordenadas_str
            
            params = {
                "source": "first",
                "destination": "last" if destino else "any",
                "roundtrip": "false" if destino else "true",
                "overview": "full",
                "geometries": "geojson",
                "steps": "true"
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != "Ok":
                raise ValueError("OSRM no pudo optimizar la ruta")
            
            trip = data["trips"][0]
            
            return {
                "distancia_total_km": round(trip["distance"] / 1000, 2),
                "duracion_total_minutos": round(trip["duration"] / 60, 1),
                "secuencia_waypoints": data["waypoints"],
                "geometria": trip["geometry"],
                "pasos": trip["legs"]
            }
        except Exception as e:
            raise Exception("Error al optimizar ruta: " + str(e))

osrm_service = OSRMService()