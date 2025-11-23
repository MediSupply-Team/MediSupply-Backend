"""
Cliente para validar productos contra la base de datos de Catálogo
"""
import os
from typing import List, Dict, Any, Optional
import asyncpg
import logging

log = logging.getLogger("orders.catalog_client")


class CatalogClient:
    """Cliente para consultar productos en la base de datos de Catálogo"""
    
    def __init__(self):
        self.catalog_database_url = os.getenv("CATALOG_DB_URL")
        if not self.catalog_database_url:
            log.warning("CATALOG_DB_URL no configurada, validación de SKUs deshabilitada")
            self.enabled = False
            return
        
        # asyncpg solo acepta 'postgresql://' o 'postgres://', no 'postgresql+asyncpg://'
        if self.catalog_database_url.startswith("postgresql+asyncpg://"):
            self.catalog_database_url = self.catalog_database_url.replace("postgresql+asyncpg://", "postgresql://")
        
        self.pool: Optional[asyncpg.Pool] = None
        self.enabled = True
    
    async def connect(self):
        """Establece el pool de conexiones a la base de datos de catálogo"""
        if not self.enabled:
            return
            
        if not self.pool:
            try:
                log.info(f"Conectando a catálogo: {self.catalog_database_url[:50]}...")
                self.pool = await asyncpg.create_pool(
                    self.catalog_database_url,
                    min_size=1,
                    max_size=5,
                    command_timeout=10,  # Aumentado de 5 a 10 segundos para consultas complejas
                    timeout=15  # Timeout para obtener conexión del pool
                )
                log.info("Conexión a base de datos de catálogo establecida exitosamente")
            except Exception as e:
                log.error(f"Error conectando a catálogo: {e}")
                self.enabled = False
    
    async def disconnect(self):
        """Cierra el pool de conexiones"""
        if self.pool:
            await self.pool.close()
            self.pool = None
    
    async def validate_skus(self, skus: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Valida que los SKUs existan en el catálogo y retorna su información
        
        Args:
            skus: Lista de códigos de productos (SKUs)
            
        Returns:
            Diccionario con código como clave y datos del producto como valor.
            Si un SKU no existe, no aparecerá en el diccionario.
        """
        if not self.enabled or not self.pool:
            log.warning("Validación de SKUs deshabilitada - no hay conexión al catálogo")
            return {}
        
        if not skus:
            return {}
        
        log.info(f"Iniciando validación de {len(skus)} SKUs: {skus}")
        
        try:
            # Crear placeholders para la consulta
            placeholders = ', '.join(f'${i+1}' for i in range(len(skus)))
            
            query = f"""
                SELECT 
                    codigo,
                    nombre,
                    precio_unitario,
                    activo
                FROM producto
                WHERE codigo IN ({placeholders}) AND activo = true
            """
            
            log.info(f"Adquiriendo conexión del pool de catálogo...")
            async with self.pool.acquire() as conn:
                log.info(f"Ejecutando query de validación...")
                rows = await conn.fetch(query, *skus)
                log.info(f"Query ejecutada, {len(rows)} productos encontrados")
                
                products = {}
                for row in rows:
                    product = dict(row)
                    # Convertir decimal a float para precio_unitario
                    if product.get('precio_unitario'):
                        product['precio_unitario'] = float(product['precio_unitario'])
                    
                    products[product['codigo']] = product
                
                log.info(f"Validados {len(products)} de {len(skus)} SKUs exitosamente")
                return products
                
        except Exception as e:
            log.error(f"Error validando SKUs: {e}")
            # En caso de error, permitir la creación (fail open)
            return {}


# Instancia global del cliente
catalog_client = CatalogClient()
