"""
Tests para routes/catalog.py (endpoints de proveedores) en BFF-Venta
Objetivo: Verificar que los proxies de proveedores funcionan correctamente
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


class TestProveedorBFFRoutes:
    """Tests para los endpoints proxy de proveedor en BFF-Venta"""
    
    def test_listar_proveedores_exitoso(self, client):
        """Test proxy listar proveedores"""
        with patch('app.routes.catalog.requests.get') as mock_get:
            # Mock de respuesta exitosa del catalogo-service
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "nit": "900123456-7",
                        "empresa": "Laboratorios Test S.A.",
                        "activo": True
                    }
                ],
                "total": 1,
                "page": 1,
                "size": 50
            }
            mock_get.return_value = mock_response
            
            # Hacer request al BFF
            response = client.get('/api/v1/catalog/proveedores')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert "items" in data
            assert data["total"] == 1
    
    def test_listar_proveedores_servicio_no_disponible(self, client):
        """Test cuando catalogo-service no está disponible"""
        with patch('app.routes.catalog.get_catalogo_service_url') as mock_url:
            # Simular que no hay URL configurada
            mock_url.return_value = None
            
            response = client.get('/api/v1/catalog/proveedores')
            
            assert response.status_code == 503
            data = json.loads(response.data)
            assert "error" in data
    
    def test_crear_proveedor_exitoso(self, client):
        """Test proxy crear proveedor"""
        with patch('app.routes.catalog.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "nit": "900999999-9",
                "empresa": "Nuevo Proveedor S.A.",
                "activo": True
            }
            mock_post.return_value = mock_response
            
            nuevo_proveedor = {
                "nit": "900999999-9",
                "empresa": "Nuevo Proveedor S.A.",
                "contacto_nombre": "Juan Test",
                "contacto_email": "juan@test.com",
                "contacto_telefono": "+57-1-9999999",
                "direccion": "Calle Test",
                "ciudad": "Bogotá",
                "pais": "CO",
                "activo": True
            }
            
            response = client.post(
                '/api/v1/catalog/proveedores',
                data=json.dumps(nuevo_proveedor),
                content_type='application/json'
            )
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data["nit"] == "900999999-9"
    
    def test_obtener_proveedor_por_id(self, client):
        """Test proxy obtener proveedor por ID"""
        proveedor_id = "123e4567-e89b-12d3-a456-426614174000"
        
        with patch('app.routes.catalog.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": proveedor_id,
                "nit": "900123456-7",
                "empresa": "Test Proveedor S.A.",
                "activo": True
            }
            mock_get.return_value = mock_response
            
            response = client.get(f'/api/v1/catalog/proveedores/{proveedor_id}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["id"] == proveedor_id
    
    def test_obtener_proveedor_no_encontrado(self, client):
        """Test proxy obtener proveedor que no existe"""
        proveedor_id = "123e4567-e89b-12d3-a456-426614174000"
        
        with patch('app.routes.catalog.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.json.return_value = {
                "detail": "Proveedor no encontrado"
            }
            mock_get.return_value = mock_response
            
            response = client.get(f'/api/v1/catalog/proveedores/{proveedor_id}')
            
            assert response.status_code == 404
    
    def test_actualizar_proveedor(self, client):
        """Test proxy actualizar proveedor"""
        proveedor_id = "123e4567-e89b-12d3-a456-426614174000"
        
        with patch('app.routes.catalog.requests.put') as mock_put:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": proveedor_id,
                "contacto_telefono": "+57-1-8888888",
                "updated_at": "2024-11-13T00:00:00"
            }
            mock_put.return_value = mock_response
            
            datos_actualizacion = {
                "contacto_telefono": "+57-1-8888888"
            }
            
            response = client.put(
                f'/api/v1/catalog/proveedores/{proveedor_id}',
                data=json.dumps(datos_actualizacion),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["contacto_telefono"] == "+57-1-8888888"
    
    def test_eliminar_proveedor(self, client):
        """Test proxy eliminar proveedor"""
        proveedor_id = "123e4567-e89b-12d3-a456-426614174000"
        
        with patch('app.routes.catalog.requests.delete') as mock_delete:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "message": "Proveedor eliminado"
            }
            mock_delete.return_value = mock_response
            
            response = client.delete(f'/api/v1/catalog/proveedores/{proveedor_id}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert "message" in data
    
    def test_listar_productos_proveedor(self, client):
        """Test proxy listar productos de un proveedor"""
        proveedor_id = "123e4567-e89b-12d3-a456-426614174000"
        
        with patch('app.routes.catalog.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "proveedor_id": proveedor_id,
                "proveedor_nombre": "Test Proveedor",
                "total_productos": 5,
                "productos": [
                    {
                        "id": "PROD001",
                        "nombre": "Producto Test",
                        "precio": 25000.00
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            response = client.get(f'/api/v1/catalog/proveedores/{proveedor_id}/productos')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["proveedor_id"] == proveedor_id
            assert "productos" in data
    
    def test_timeout_error(self, client):
        """Test manejo de timeout en llamada al servicio"""
        with patch('app.routes.catalog.requests.get') as mock_get:
            from requests.exceptions import Timeout
            mock_get.side_effect = Timeout()
            
            response = client.get('/api/v1/catalog/proveedores')
            
            assert response.status_code == 504
            data = json.loads(response.data)
            assert "error" in data
    
    def test_connection_error(self, client):
        """Test manejo de error de conexión"""
        with patch('app.routes.catalog.requests.get') as mock_get:
            from requests.exceptions import RequestException
            mock_get.side_effect = RequestException("Connection error")
            
            response = client.get('/api/v1/catalog/proveedores')
            
            assert response.status_code == 503
            data = json.loads(response.data)
            assert "error" in data


class TestProveedorBFFIntegration:
    """Tests de integración para flujo completo a través del BFF"""
    
    def test_flujo_completo_crear_proveedor_y_listar(self, client):
        """Test flujo: crear proveedor y luego listarlo"""
        proveedor_id = "123e4567-e89b-12d3-a456-426614174000"
        
        with patch('app.routes.catalog.requests.post') as mock_post, \
             patch('app.routes.catalog.requests.get') as mock_get:
            
            # Mock para crear
            mock_response_post = MagicMock()
            mock_response_post.status_code = 201
            mock_response_post.json.return_value = {
                "id": proveedor_id,
                "nit": "800888888-8",
                "empresa": "Test Integración S.A."
            }
            mock_post.return_value = mock_response_post
            
            # Mock para listar
            mock_response_get = MagicMock()
            mock_response_get.status_code = 200
            mock_response_get.json.return_value = {
                "items": [
                    {
                        "id": proveedor_id,
                        "nit": "800888888-8",
                        "empresa": "Test Integración S.A."
                    }
                ],
                "total": 1
            }
            mock_get.return_value = mock_response_get
            
            # 1. Crear proveedor
            nuevo_proveedor = {
                "nit": "800888888-8",
                "empresa": "Test Integración S.A.",
                "contacto_nombre": "Test",
                "contacto_email": "test@test.com",
                "contacto_telefono": "+57-1-8888888",
                "direccion": "Test",
                "ciudad": "Bogotá",
                "pais": "CO"
            }
            
            response_crear = client.post(
                '/api/v1/catalog/proveedores',
                data=json.dumps(nuevo_proveedor),
                content_type='application/json'
            )
            
            assert response_crear.status_code == 201
            
            # 2. Listar proveedores
            response_listar = client.get('/api/v1/catalog/proveedores')
            
            assert response_listar.status_code == 200
            data = json.loads(response_listar.data)
            assert len(data["items"]) > 0


class TestProveedorBFFPaginacion:
    """Tests para verificar paginación en proxies"""
    
    def test_listar_proveedores_con_paginacion(self, client):
        """Test proxy con parámetros de paginación"""
        with patch('app.routes.catalog.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "items": [],
                "total": 0,
                "page": 2,
                "size": 10
            }
            mock_get.return_value = mock_response
            
            response = client.get('/api/v1/catalog/proveedores?page=2&size=10')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["page"] == 2
            assert data["size"] == 10
    
    def test_listar_proveedores_filtro_activo(self, client):
        """Test proxy con filtro de activos"""
        with patch('app.routes.catalog.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "items": [],
                "total": 0
            }
            mock_get.return_value = mock_response
            
            response = client.get('/api/v1/catalog/proveedores?activo=true')
            
            assert response.status_code == 200


class TestProveedorBFFValidaciones:
    """Tests para validaciones y errores en BFF"""
    
    def test_crear_proveedor_datos_invalidos(self, client):
        """Test crear proveedor con datos inválidos"""
        with patch('app.routes.catalog.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 422
            mock_response.json.return_value = {
                "detail": "Datos inválidos"
            }
            mock_post.return_value = mock_response
            
            proveedor_invalido = {
                "empresa": "Sin NIT"
                # Falta nit
            }
            
            response = client.post(
                '/api/v1/catalog/proveedores',
                data=json.dumps(proveedor_invalido),
                content_type='application/json'
            )
            
            assert response.status_code == 422
    
    def test_actualizar_proveedor_no_encontrado(self, client):
        """Test actualizar proveedor que no existe"""
        proveedor_id = "123e4567-e89b-12d3-a456-426614174000"
        
        with patch('app.routes.catalog.requests.put') as mock_put:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.json.return_value = {
                "detail": "Proveedor no encontrado"
            }
            mock_put.return_value = mock_response
            
            response = client.put(
                f'/api/v1/catalog/proveedores/{proveedor_id}',
                data=json.dumps({"ciudad": "Cali"}),
                content_type='application/json'
            )
            
            assert response.status_code == 404



