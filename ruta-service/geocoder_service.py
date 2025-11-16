"""
Servicio de geocodificación usando Mapbox API
Convierte direcciones en coordenadas GPS (latitud, longitud)
"""
import httpx
from typing import Dict, List, Optional
from urllib.parse import quote
from config import settings


class GeocoderService:
    """Cliente para la API de geocodificación de Mapbox"""
    
    def __init__(self):
        self.base_url = "https://api.mapbox.com/geocoding/v5/mapbox.places"
        self.access_token = settings.mapbox_access_token
    
    def geocodificar(self, direccion: str, ciudad: str = "Bogotá") -> Dict[str, float]:
        """
        Convertir dirección a coordenadas GPS
        
        Args:
            direccion: Dirección a geocodificar
            ciudad: Ciudad de la dirección (default: Bogotá)
            
        Returns:
            Dict con lat, lon, direccion_formateada y confianza
            
        Raises:
            Exception: Si no se pueden obtener las coordenadas
        """
        try:
            # Construir query completo
            query = f"{direccion}, {ciudad}, Colombia"
            query_encoded = quote(query)
            url = f"{self.base_url}/{query_encoded}.json"
            
            # Parámetros de la petición
            params = {
                "access_token": self.access_token,
                "country": "CO",
                "limit": 1,
                "language": "es"
            }
            
            # Realizar petición a Mapbox
            response = httpx.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            # Verificar que se encontraron resultados
            if not data.get("features"):
                raise ValueError(f"No se encontraron coordenadas para: {direccion}")
            
            # Extraer coordenadas del primer resultado
            feature = data["features"][0]
            lon, lat = feature["center"]
            
            return {
                "lat": lat,
                "lon": lon,
                "direccion_formateada": feature["place_name"],
                "confianza": feature["relevance"]
            }
            
        except httpx.HTTPError as e:
            raise Exception(f"Error HTTP al geocodificar dirección: {str(e)}")
        except Exception as e:
            raise Exception(f"Error al geocodificar dirección '{direccion}': {str(e)}")
    
    def geocodificar_multiple(self, direcciones: List[str], ciudad: str = "Bogotá") -> List[Optional[Dict]]:
        """
        Geocodificar múltiples direcciones
        
        Args:
            direcciones: Lista de direcciones a geocodificar
            ciudad: Ciudad de las direcciones
            
        Returns:
            Lista de resultados (None si falla alguna geocodificación)
        """
        resultados = []
        for direccion in direcciones:
            try:
                resultado = self.geocodificar(direccion, ciudad)
                resultados.append(resultado)
            except Exception as e:
                print(f"⚠️  Error geocodificando {direccion}: {str(e)}")
                resultados.append(None)
        
        return resultados


# Instancia global del servicio
geocoder_service = GeocoderService()
