"""
Cliente HTTP para consumir el catalogo-service desde el BFF-Venta
"""
import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class CatalogoServiceClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.is_mock_mode = "placeholder" in base_url or "example.com" in base_url
        logger.info(f"CatalogoServiceClient initialized - URL: {base_url}, Mock mode: {self.is_mock_mode}")
        
    async def _make_request(self, method: str, endpoint: str, 
                          params: Optional[Dict] = None, 
                          json_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Realiza una petición HTTP al catalogo-service o retorna datos mock"""
        
        # Si estamos en modo mock, devolvemos datos simulados
        if self.is_mock_mode:
            return await self._get_mock_response(endpoint, method, params, json_data)
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data
                ) as response:
                    
                    if response.status == 404:
                        return {"error": "Not found", "status": 404}
                    
                    if response.status >= 400:
                        error_text = await response.text()
                        logger.error(f"Error en catalogo-service: {response.status} - {error_text}")
                        return {"error": f"Service error: {response.status}", "details": error_text}
                    
                    return await response.json()
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout llamando a {url}")
            return {"error": "Service timeout"}
        except aiohttp.ClientConnectorError as e:
            logger.error(f"No se puede conectar a catalogo-service: {e}")
            # En caso de error de conectividad, fallback a mock
            return await self._get_mock_response(endpoint, method, params, json_data)
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            return {"error": "Internal error", "details": str(e)}

    async def _get_mock_response(self, endpoint: str, method: str, params: Dict = None, json_data: Dict = None) -> Dict[str, Any]:
        """Devuelve datos mock simulando el catalogo-service"""
        
        if endpoint == "/api/catalog/items":
            if method == "GET":
                return {
                    "items": [
                        {
                            "id": "PROD001",
                            "nombre": "Amoxicilina 500mg",
                            "codigo": "AMX500",
                            "categoria": "ANTIBIOTICS",
                            "presentacion": "Cápsula",
                            "precioUnitario": 1250.00,
                            "requisitosAlmacenamiento": "Temperatura ambiente, lugar seco",
                            "inventarioResumen": {
                                "cantidadTotal": 1000,
                                "paises": ["CO", "MX", "PE"]
                            }
                        },
                        {
                            "id": "PROD006",
                            "nombre": "Ibuprofeno 400mg",
                            "codigo": "IBU400",
                            "categoria": "ANALGESICS",
                            "presentacion": "Tableta",
                            "precioUnitario": 320.00,
                            "requisitosAlmacenamiento": "Temperatura ambiente",
                            "inventarioResumen": {
                                "cantidadTotal": 4500,
                                "paises": ["CO", "MX", "PE", "CL"]
                            }
                        },
                        {
                            "id": "PROD007",
                            "nombre": "Acetaminofén 500mg",
                            "codigo": "ACE500",
                            "categoria": "ANALGESICS",
                            "presentacion": "Tableta",
                            "precioUnitario": 180.00,
                            "requisitosAlmacenamiento": "Lugar seco",
                            "inventarioResumen": {
                                "cantidadTotal": 4300,
                                "paises": ["CO", "MX", "PE"]
                            }
                        }
                    ],
                    "meta": {
                        "page": params.get("page", 1) if params else 1,
                        "size": params.get("size", 20) if params else 20,
                        "total": 25,
                        "tookMs": 45
                    }
                }
            elif method == "POST":
                return {
                    "id": "PROD_NEW",
                    "message": "Item created successfully (MOCK)",
                    "data": json_data
                }
        
        # Mock para item específico
        if "/api/catalog/items/" in endpoint and method == "GET":
            item_id = endpoint.split("/")[-1]
            if item_id == "inventario":
                item_id = endpoint.split("/")[-2]
                # Mock inventario
                return {
                    "items": [
                        {
                            "pais": "CO",
                            "bodegaId": "BOG_CENTRAL",
                            "lote": f"{item_id}_001_2024",
                            "cantidad": 500,
                            "vence": "2025-12-31",
                            "condiciones": "Almacén principal"
                        },
                        {
                            "pais": "MX",
                            "bodegaId": "CDMX_NORTE",
                            "lote": f"{item_id}_002_2024",
                            "cantidad": 750,
                            "vence": "2026-01-15",
                            "condiciones": "Centro de distribución"
                        }
                    ],
                    "meta": {
                        "page": 1,
                        "size": 50,
                        "total": 2,
                        "tookMs": 23
                    }
                }
            else:
                # Mock item específico
                return {
                    "id": item_id,
                    "nombre": f"Producto {item_id}",
                    "codigo": f"COD{item_id}",
                    "categoria": "MOCK_CATEGORY",
                    "presentacion": "Tableta",
                    "precioUnitario": 999.99,
                    "requisitosAlmacenamiento": "Mock storage requirements"
                }
        
        # Mock para operaciones de modificación
        if method in ["PUT", "DELETE"]:
            return {
                "message": f"Operation {method} completed successfully (MOCK)",
                "endpoint": endpoint
            }
        
        return {
            "error": "Mock endpoint not implemented",
            "endpoint": endpoint,
            "method": method
        }

    async def get_items(self, q: Optional[str] = None, 
                       categoria_id: Optional[str] = None,
                       codigo: Optional[str] = None,
                       pais: Optional[str] = None,
                       bodega_id: Optional[str] = None,
                       page: int = 1,
                       size: int = 20,
                       sort: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene la lista de items del catálogo"""
        params = {"page": page, "size": size}
        
        if q:
            params["q"] = q
        if categoria_id:
            params["categoriaId"] = categoria_id  
        if codigo:
            params["codigo"] = codigo
        if pais:
            params["pais"] = pais
        if bodega_id:
            params["bodegaId"] = bodega_id
        if sort:
            params["sort"] = sort
            
        return await self._make_request("GET", "/api/catalog/items", params=params)

    async def get_item(self, item_id: str) -> Dict[str, Any]:
        """Obtiene un item específico por ID"""
        return await self._make_request("GET", f"/api/catalog/items/{item_id}")

    async def get_item_inventory(self, item_id: str, page: int = 1, size: int = 50) -> Dict[str, Any]:
        """Obtiene el inventario de un item específico"""
        params = {"page": page, "size": size}
        return await self._make_request("GET", f"/api/catalog/items/{item_id}/inventario", params=params)

    async def create_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un nuevo item en el catálogo"""
        return await self._make_request("POST", "/api/catalog/items", json_data=item_data)

    async def update_item(self, item_id: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza un item existente"""
        return await self._make_request("PUT", f"/api/catalog/items/{item_id}", json_data=item_data)

    async def delete_item(self, item_id: str) -> Dict[str, Any]:
        """Elimina un item del catálogo"""
        return await self._make_request("DELETE", f"/api/catalog/items/{item_id}")

    async def health_check(self) -> Dict[str, Any]:
        """Verifica la salud del catalogo-service"""
        return await self._make_request("GET", "/health")