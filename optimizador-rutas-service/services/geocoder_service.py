import requests
from config.settings import settings
from typing import List
from urllib.parse import quote

class GeocoderService:
    def __init__(self):
        self.base_url = "https://api.mapbox.com/geocoding/v5/mapbox.places"
        self.access_token = settings.mapbox_access_token
    
    def geocodificar(self, direccion: str, ciudad: str = "Bogota") -> dict:
        """Convertir direccion a coordenadas"""
        try:
            query = direccion + ", " + ciudad + ", Colombia"
            query_encoded = quote(query)
            url = self.base_url + "/" + query_encoded + ".json"
            params = {
                "access_token": self.access_token,
                "country": "CO",
                "limit": 1,
                "language": "es"
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("features"):
                raise ValueError("No se encontraron coordenadas para: " + direccion)
            
            feature = data["features"][0]
            lon, lat = feature["center"]
            
            return {
                "lat": lat,
                "lon": lon,
                "direccion_formateada": feature["place_name"],
                "confianza": feature["relevance"]
            }
        except Exception as e:
            raise Exception("Error al geocodificar direccion: " + str(e))
    
    def geocodificar_multiple(self, direcciones: List[str]) -> List[dict]:
        """Geocodificar multiples direcciones"""
        resultados = []
        for direccion in direcciones:
            try:
                resultado = self.geocodificar(direccion)
                resultados.append(resultado)
            except Exception as e:
                print("Error geocodificando " + direccion + ": " + str(e))
                resultados.append(None)
        return resultados

geocoder_service = GeocoderService()