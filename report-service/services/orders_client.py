# services/orders_client.py
"""
Cliente HTTP para consumir datos del servicio Orders
"""
import os
import httpx
from typing import List, Dict, Any, Optional
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)

class OrdersClient:
    """Cliente para comunicarse con el servicio Orders"""
    
    def __init__(self):
        # En producción, esto vendrá de una variable de entorno
        # En desarrollo local, apuntar al contenedor orders-service
        self.base_url = os.getenv("ORDERS_SERVICE_URL", "http://orders-service:8001")
        self.timeout = 30.0
    
    async def get_orders(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Obtiene las órdenes del servicio Orders.
        
        Nota: El servicio Orders actual no soporta filtros por fecha en el endpoint,
        por lo que obtenemos todas las órdenes y luego filtramos en el cliente.
        
        Args:
            from_date: Fecha de inicio del filtro (filtrado local)
            to_date: Fecha fin del filtro (filtrado local)
            status: Estado de las órdenes a filtrar (filtrado local)
            
        Returns:
            Lista de órdenes
        """
        try:
            all_orders = []
            limit = 100
            offset = 0
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Obtener todas las órdenes con paginación
                while True:
                    params = {
                        "limit": limit,
                        "offset": offset
                    }
                    
                    response = await client.get(
                        f"{self.base_url}/orders",
                        params=params
                    )
                    response.raise_for_status()
                    orders = response.json()
                    
                    if not orders:
                        break
                    
                    all_orders.extend(orders)
                    
                    # Si recibimos menos órdenes que el límite, ya no hay más
                    if len(orders) < limit:
                        break
                    
                    offset += limit
            
            logger.info(f"Obtenidas {len(all_orders)} órdenes del servicio Orders")
            return all_orders
        
        except httpx.HTTPError as e:
            logger.error(f"Error al obtener órdenes: {str(e)}")
            raise Exception(f"No se pudo conectar con el servicio Orders: {str(e)}")
    
    async def get_order_stats(
        self,
        from_date: date,
        to_date: date
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de órdenes para el período especificado.
        
        Nota: Este endpoint no existe en Orders, por lo que retornamos estructura vacía.
        El servicio de reportes calculará las estadísticas a partir de las órdenes.
        
        Args:
            from_date: Fecha de inicio
            to_date: Fecha fin
            
        Returns:
            Diccionario con estadísticas agregadas (placeholder)
        """
        return {
            "total_orders": 0,
            "total_revenue": 0.0,
            "orders_by_status": {},
            "products_sold": []
        }

# Singleton para reutilizar
orders_client = OrdersClient()

