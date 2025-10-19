"""
Cliente HTTP para consumir el cliente-service desde el BFF-Cliente
"""
import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ClienteServiceClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.is_mock_mode = "placeholder" in base_url or "example.com" in base_url
        logger.info(f"ClienteServiceClient initialized - URL: {base_url}, Mock mode: {self.is_mock_mode}")
        
    async def _make_request(self, method: str, endpoint: str, 
                          params: Optional[Dict] = None, 
                          json_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Realiza una petición HTTP al cliente-service o retorna datos mock"""
        
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
                        logger.error(f"Error en cliente-service: {response.status} - {error_text}")
                        return {"error": f"Service error: {response.status}", "details": error_text}
                    
                    return await response.json()
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout llamando a {url}")
            return {"error": "Service timeout"}
        except aiohttp.ClientConnectorError as e:
            logger.error(f"No se puede conectar a cliente-service: {e}")
            # En caso de error de conectividad, fallback a mock
            return await self._get_mock_response(endpoint, method, params, json_data)
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            return {"error": "Internal error", "details": str(e)}

    async def _get_mock_response(self, endpoint: str, method: str, params: Dict = None, json_data: Dict = None) -> Dict[str, Any]:
        """Devuelve datos mock simulando el cliente-service"""
        
        if endpoint == "/api/cliente/":
            if method == "GET":
                return [
                    {
                        "cliente_id": "CLI001",
                        "nombre": "Farmacia San Pedro S.A.S.",
                        "nit": "900123456-7",
                        "codigo_unico": "FSP001",
                        "direccion": "Calle 85 # 15-32, Bogotá",
                        "telefono": "+57 1 234-5678",
                        "email": "gerencia@farmaciasanpedro.com",
                        "vendedor_asignado": "VEND001",
                        "estado": "ACTIVO",
                        "fecha_registro": "2024-01-15T10:30:00Z",
                        "limite_credito": 50000000.0,
                        "credito_disponible": 35000000.0
                    },
                    {
                        "cliente_id": "CLI002",
                        "nombre": "Droguería El Descuento Ltda.",
                        "nit": "800987654-3",
                        "codigo_unico": "DED002",
                        "direccion": "Carrera 7 # 45-18, Medellín",
                        "telefono": "+57 4 987-6543",
                        "email": "compras@drogueriaeldescuento.com",
                        "vendedor_asignado": "VEND002",
                        "estado": "ACTIVO",
                        "fecha_registro": "2024-02-20T14:15:00Z",
                        "limite_credito": 25000000.0,
                        "credito_disponible": 18500000.0
                    },
                    {
                        "cliente_id": "CLI003",
                        "nombre": "Farmacia Central Cali",
                        "nit": "900555777-1",
                        "codigo_unico": "FCC003",
                        "direccion": "Avenida 6N # 23-50, Cali",
                        "telefono": "+57 2 555-7777",
                        "email": "admin@farmaciacentralcali.co",
                        "vendedor_asignado": "VEND001",
                        "estado": "ACTIVO",
                        "fecha_registro": "2024-03-10T09:45:00Z",
                        "limite_credito": 30000000.0,
                        "credito_disponible": 22000000.0
                    }
                ]
        
        elif endpoint == "/api/cliente/search":
            if method == "GET":
                # Simulamos búsqueda basada en el parámetro q
                search_query = params.get("q", "").lower() if params else ""
                
                if "900123456" in search_query or "san pedro" in search_query:
                    return {
                        "cliente_id": "CLI001",
                        "nombre": "Farmacia San Pedro S.A.S.",
                        "nit": "900123456-7",
                        "codigo_unico": "FSP001",
                        "direccion": "Calle 85 # 15-32, Bogotá",
                        "telefono": "+57 1 234-5678",
                        "email": "gerencia@farmaciasanpedro.com",
                        "vendedor_asignado": "VEND001",
                        "estado": "ACTIVO",
                        "fecha_registro": "2024-01-15T10:30:00Z",
                        "limite_credito": 50000000.0,
                        "credito_disponible": 35000000.0
                    }
                else:
                    return {
                        "cliente_id": "CLI002",
                        "nombre": "Droguería El Descuento Ltda.",
                        "nit": "800987654-3",
                        "codigo_unico": "DED002",
                        "direccion": "Carrera 7 # 45-18, Medellín",
                        "telefono": "+57 4 987-6543",
                        "email": "compras@drogueriaeldescuento.com",
                        "vendedor_asignado": "VEND002",
                        "estado": "ACTIVO",
                        "fecha_registro": "2024-02-20T14:15:00Z",
                        "limite_credito": 25000000.0,
                        "credito_disponible": 18500000.0
                    }
        
        elif "/historico" in endpoint:
            if method == "GET":
                cliente_id = endpoint.split("/")[3]  # Extraer cliente_id de /api/cliente/{cliente_id}/historico
                return {
                    "cliente_id": cliente_id,
                    "nombre_cliente": "Farmacia San Pedro S.A.S.",
                    "periodo_consultado": {
                        "desde": "2023-10-01T00:00:00Z",
                        "hasta": "2024-10-19T23:59:59Z",
                        "meses": 12
                    },
                    "historico_compras": [
                        {
                            "pedido_id": "PED001",
                            "fecha": "2024-10-15T10:30:00Z",
                            "productos": [
                                {"producto_id": "PROD001", "nombre": "Amoxicilina 500mg", "cantidad": 100, "valor_unitario": 1250.0},
                                {"producto_id": "PROD006", "nombre": "Ibuprofeno 400mg", "cantidad": 200, "valor_unitario": 320.0}
                            ],
                            "total": 189000.0,
                            "estado": "ENTREGADO"
                        },
                        {
                            "pedido_id": "PED002",
                            "fecha": "2024-09-28T14:20:00Z",
                            "productos": [
                                {"producto_id": "PROD007", "nombre": "Acetaminofén 500mg", "cantidad": 300, "valor_unitario": 180.0}
                            ],
                            "total": 54000.0,
                            "estado": "ENTREGADO"
                        }
                    ],
                    "productos_preferidos": [
                        {
                            "producto_id": "PROD001",
                            "nombre": "Amoxicilina 500mg",
                            "frecuencia_pedidos": 8,
                            "cantidad_total": 800,
                            "valor_total": 1000000.0,
                            "promedio_mensual": 67
                        },
                        {
                            "producto_id": "PROD006",
                            "nombre": "Ibuprofeno 400mg",
                            "frecuencia_pedidos": 6,
                            "cantidad_total": 1200,
                            "valor_total": 384000.0,
                            "promedio_mensual": 100
                        }
                    ],
                    "devoluciones": [
                        {
                            "devolucion_id": "DEV001",
                            "fecha": "2024-09-30T16:45:00Z",
                            "pedido_original": "PED001",
                            "productos": [
                                {"producto_id": "PROD001", "nombre": "Amoxicilina 500mg", "cantidad": 10}
                            ],
                            "motivo": "DEFECTO_CALIDAD",
                            "estado": "APROBADA",
                            "valor_devolucion": 12500.0
                        }
                    ],
                    "estadisticas": {
                        "total_pedidos": 15,
                        "total_comprado": 2500000.0,
                        "promedio_pedido": 166666.67,
                        "productos_diferentes": 25,
                        "total_devoluciones": 1,
                        "porcentaje_devolucion": 0.5
                    }
                }
        
        elif endpoint == "/api/cliente/health":
            if method == "GET":
                return {
                    "status": "healthy",
                    "service": "cliente-service",
                    "version": "1.0.0",
                    "timestamp": "2024-10-19T15:30:00Z",
                    "sla_max_response_ms": 2000,
                    "database": "connected"
                }
        
        elif endpoint == "/api/cliente/metrics":
            if method == "GET":
                return {
                    "total_clientes": 156,
                    "clientes_activos": 142,
                    "clientes_inactivos": 14,
                    "pedidos_ultimo_mes": 89,
                    "valor_total_ultimo_mes": 12500000.0,
                    "promedio_credito_utilizado": 68.5,
                    "top_vendedores": [
                        {"vendedor_id": "VEND001", "clientes": 45, "ventas": 5600000.0},
                        {"vendedor_id": "VEND002", "clientes": 38, "ventas": 4200000.0}
                    ]
                }
        
        # Respuesta por defecto para endpoints no reconocidos
        return {"error": "Mock endpoint not found", "endpoint": endpoint}

    # Métodos de conveniencia para cada endpoint
    async def listar_clientes(self, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Lista todos los clientes con filtros opcionales"""
        return await self._make_request("GET", "/api/cliente/", params=params)
    
    async def buscar_cliente(self, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Busca un cliente por NIT, nombre o código único"""
        return await self._make_request("GET", "/api/cliente/search", params=params)
    
    async def obtener_historico_cliente(self, cliente_id: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Obtiene el histórico completo de un cliente"""
        return await self._make_request("GET", f"/api/cliente/{cliente_id}/historico", params=params)
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check del cliente-service"""
        return await self._make_request("GET", "/api/cliente/health")
    
    async def obtener_metricas(self) -> Dict[str, Any]:
        """Obtiene las métricas del cliente-service"""
        return await self._make_request("GET", "/api/cliente/metrics")