import requests
from config.settings import settings
from typing import List

class RutaServiceClient:
    """Cliente para comunicarse con ruta-service"""
    
    def __init__(self):
        self.base_url = settings.ruta_service_url
    
    def obtener_visitas(self, fecha: str, vendedor_id: int) -> List[dict]:
        """Obtener visitas desde ruta-service"""
        try:
            url = self.base_url + "/api/ruta"
            params = {
                "fecha": fecha,
                "vendedor_id": vendedor_id
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return data.get("visitas", [])
            
        except Exception as e:
            raise Exception("Error al obtener visitas: " + str(e))

ruta_service_client = RutaServiceClient()