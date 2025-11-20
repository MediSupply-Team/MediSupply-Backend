"""
Tests para routes/vendedor.py en BFF-Cliente
Objetivo: Verificar que los proxies funcionan correctamente
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from app import create_app


@pytest.fixture
def client():
    """Fixture para crear cliente de prueba"""
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestVendedorBFFRoutes:
    """Tests para los endpoints proxy de vendedor en BFF"""
    
    def test_listar_vendedores_exitoso(self, client):
        """Test proxy listar vendedores"""
        with patch('app.routes.vendedor.get_cliente_service_url') as mock_url, \
             patch('app.routes.vendedor.requests.get') as mock_get:
            # Mock URL del servicio
            mock_url.return_value = "http://cliente-service:8000"
            
            # Mock de respuesta exitosa del cliente-service
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "identificacion": "1234567890",
                        "nombre_completo": "Test Vendedor",
                        "activo": True
                    }
                ],
                "total": 1,
                "page": 1,
                "size": 50
            }
            mock_get.return_value = mock_response
            
            # Hacer request al BFF
            response = client.get('/api/v1/vendedores/')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert "items" in data
            assert data["total"] == 1
    
    def test_listar_vendedores_servicio_no_disponible(self, client):
        """Test cuando cliente-service no está disponible"""
        with patch('app.routes.vendedor.get_cliente_service_url') as mock_url:
            # Simular que no hay URL configurada
            mock_url.return_value = None
            
            response = client.get('/api/v1/vendedores/')
            
            assert response.status_code == 503
            data = json.loads(response.data)
            assert "error" in data
    
    def test_crear_vendedor_exitoso(self, client):
        """Test proxy crear vendedor"""
        with patch('app.routes.vendedor.get_cliente_service_url') as mock_url, \
             patch('app.routes.vendedor.requests.post') as mock_post:
            mock_url.return_value = "http://cliente-service:8000"
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "identificacion": "9999999999",
                "nombre_completo": "Nuevo Vendedor",
                "activo": True
            }
            mock_post.return_value = mock_response
            
            nuevo_vendedor = {
                "identificacion": "9999999999",
                "nombre_completo": "Nuevo Vendedor",
                "email": "nuevo@test.com",
                "telefono": "+57-300-9999999",
                "pais": "CO",
                "username": "nuevo",
                "rol": "seller",
                "activo": True
            }
            
            response = client.post(
                '/api/v1/vendedores/',
                data=json.dumps(nuevo_vendedor),
                content_type='application/json'
            )
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data["identificacion"] == "9999999999"
    
    def test_obtener_vendedor_por_id(self, client):
        """Test proxy obtener vendedor por ID"""
        vendedor_id = "123e4567-e89b-12d3-a456-426614174000"
        
        with patch('app.routes.vendedor.get_cliente_service_url') as mock_url, \
             patch('app.routes.vendedor.requests.get') as mock_get:
            mock_url.return_value = "http://cliente-service:8000"
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": vendedor_id,
                "identificacion": "1234567890",
                "nombre_completo": "Test Vendedor",
                "plan_venta_id": None
            }
            mock_get.return_value = mock_response
            
            response = client.get(f'/api/v1/vendedores/{vendedor_id}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["id"] == vendedor_id
    
    def test_obtener_vendedor_detalle(self, client):
        """Test proxy obtener vendedor con detalle completo"""
        vendedor_id = "123e4567-e89b-12d3-a456-426614174000"
        
        with patch('app.routes.vendedor.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": vendedor_id,
                "identificacion": "1234567890",
                "nombre_completo": "Test Vendedor",
                "plan_venta": {
                    "id": "plan-123",
                    "nombre_plan": "Plan Test",
                    "productos_asignados": [],
                    "regiones_asignadas": [],
                    "zonas_asignadas": []
                }
            }
            mock_get.return_value = mock_response
            
            response = client.get(f'/api/v1/vendedores/{vendedor_id}/detalle')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert "plan_venta" in data
    
    def test_actualizar_vendedor(self, client):
        """Test proxy actualizar vendedor"""
        vendedor_id = "123e4567-e89b-12d3-a456-426614174000"
        
        with patch('app.routes.vendedor.requests.put') as mock_put:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": vendedor_id,
                "telefono": "+57-321-9999999",
                "updated_at": "2024-11-13T00:00:00"
            }
            mock_put.return_value = mock_response
            
            datos_actualizacion = {
                "telefono": "+57-321-9999999"
            }
            
            response = client.put(
                f'/api/v1/vendedores/{vendedor_id}',
                data=json.dumps(datos_actualizacion),
                content_type='application/json'
            )
            
            assert response.status_code == 200
    
    def test_eliminar_vendedor(self, client):
        """Test proxy eliminar vendedor"""
        vendedor_id = "123e4567-e89b-12d3-a456-426614174000"
        
        with patch('app.routes.vendedor.requests.delete') as mock_delete:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "message": "Vendedor eliminado"
            }
            mock_delete.return_value = mock_response
            
            response = client.delete(f'/api/v1/vendedores/{vendedor_id}')
            
            assert response.status_code == 200
    
    def test_listar_clientes_vendedor(self, client):
        """Test proxy listar clientes de un vendedor"""
        vendedor_id = "123e4567-e89b-12d3-a456-426614174000"
        
        with patch('app.routes.vendedor.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "vendedor_id": vendedor_id,
                "vendedor_nombre": "Test Vendedor",
                "total_clientes": 2,
                "clientes": []
            }
            mock_get.return_value = mock_response
            
            response = client.get(f'/api/v1/vendedores/{vendedor_id}/clientes')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["vendedor_id"] == vendedor_id
    
    def test_timeout_error(self, client):
        """Test manejo de timeout en llamada al servicio"""
        with patch('app.routes.vendedor.requests.get') as mock_get:
            from requests.exceptions import Timeout
            mock_get.side_effect = Timeout()
            
            response = client.get('/api/v1/vendedores/')
            
            assert response.status_code == 504
            data = json.loads(response.data)
            assert "error" in data


class TestCatalogosBFFRoutes:
    """Tests para los endpoints proxy de catálogos en BFF"""
    
    def test_listar_tipos_rol(self, client):
        """Test proxy listar tipos de rol"""
        with patch('app.routes.vendedor.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "tipos_rol": [
                    {
                        "id": "123",
                        "codigo": "GERENTE",
                        "nombre": "Gerente"
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            response = client.get('/api/v1/catalogos/tipos-rol')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert "tipos_rol" in data
    
    def test_crear_tipo_rol(self, client):
        """Test proxy crear tipo de rol"""
        with patch('app.routes.vendedor.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "id": "123",
                "codigo": "NUEVO_ROL",
                "nombre": "Nuevo Rol"
            }
            mock_post.return_value = mock_response
            
            nuevo_tipo = {
                "codigo": "NUEVO_ROL",
                "nombre": "Nuevo Rol",
                "nivel_jerarquia": 5,
                "permisos": {}
            }
            
            response = client.post(
                '/api/v1/catalogos/tipos-rol',
                data=json.dumps(nuevo_tipo),
                content_type='application/json'
            )
            
            assert response.status_code == 201
    
    def test_listar_territorios(self, client):
        """Test proxy listar territorios"""
        with patch('app.routes.vendedor.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "territorios": []
            }
            mock_get.return_value = mock_response
            
            response = client.get('/api/v1/catalogos/territorios')
            
            assert response.status_code == 200
    
    def test_listar_tipos_plan(self, client):
        """Test proxy listar tipos de plan"""
        with patch('app.routes.vendedor.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "tipos_plan": []
            }
            mock_get.return_value = mock_response
            
            response = client.get('/api/v1/catalogos/tipos-plan')
            
            assert response.status_code == 200
    
    def test_listar_regiones(self, client):
        """Test proxy listar regiones"""
        with patch('app.routes.vendedor.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "regiones": []
            }
            mock_get.return_value = mock_response
            
            response = client.get('/api/v1/catalogos/regiones')
            
            assert response.status_code == 200
    
    def test_listar_zonas(self, client):
        """Test proxy listar zonas"""
        with patch('app.routes.vendedor.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "zonas": []
            }
            mock_get.return_value = mock_response
            
            response = client.get('/api/v1/catalogos/zonas')
            
            assert response.status_code == 200

