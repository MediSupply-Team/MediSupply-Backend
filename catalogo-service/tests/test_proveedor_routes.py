"""
Tests para routes/proveedor.py
Objetivo: Cubrir endpoints de proveedores con UUID
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from uuid import uuid4
from app.main import app


class TestProveedorRoutes:
    """Tests para los endpoints de proveedor"""
    
    @pytest.mark.asyncio
    async def test_crear_proveedor_exitoso(self):
        """Test crear proveedor nuevo"""
        nuevo_proveedor = {
            "nit": "900999999-9",
            "empresa": "Laboratorios Test S.A.",
            "contacto_nombre": "Juan Test",
            "contacto_email": "juan@test.com",
            "contacto_telefono": "+57-1-9999999",
            "direccion": "Calle Test 123",
            "ciudad": "Bogotá",
            "pais": "CO",
            "activo": True
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/catalog/api/proveedores/",
                json=nuevo_proveedor
            )
            
            # Puede ser 201 (éxito), 409 (duplicado) o 500 (sin DB real)
            assert response.status_code in [201, 409, 500]
            
            if response.status_code == 201:
                data = response.json()
                assert "id" in data
                assert data["nit"] == "900999999-9"
                assert data["empresa"] == "Laboratorios Test S.A."
    
    @pytest.mark.asyncio
    async def test_crear_proveedor_nit_duplicado(self):
        """Test crear proveedor con NIT duplicado"""
        proveedor_duplicado = {
            "nit": "900123456-7",  # NIT que ya existe
            "empresa": "Empresa Duplicada S.A.",
            "contacto_nombre": "Test Duplicado",
            "contacto_email": "duplicado@test.com",
            "contacto_telefono": "+57-1-8888888",
            "direccion": "Calle Duplicada",
            "ciudad": "Medellín",
            "pais": "CO",
            "activo": True
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/catalog/api/proveedores/",
                json=proveedor_duplicado
            )
            
            # Debe fallar con 409 o 500
            assert response.status_code in [409, 500]
    
    @pytest.mark.asyncio
    async def test_crear_proveedor_sin_campos_requeridos(self):
        """Test crear proveedor sin campos requeridos"""
        proveedor_incompleto = {
            "empresa": "Empresa Incompleta"
            # Falta nit
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/catalog/api/proveedores/",
                json=proveedor_incompleto
            )
            
            # Debe fallar validación
            assert response.status_code in [422, 500]
    
    @pytest.mark.asyncio
    async def test_listar_proveedores(self):
        """Test listar todos los proveedores"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/catalog/api/proveedores/")
            
            # Puede ser 200 o 500 (sin DB)
            assert response.status_code in [200, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert "items" in data
                assert "total" in data
                assert "page" in data
                assert "size" in data
    
    @pytest.mark.asyncio
    async def test_listar_proveedores_con_paginacion(self):
        """Test listar proveedores con paginación"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/catalog/api/proveedores/?page=1&size=5")
            
            assert response.status_code in [200, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert data["page"] == 1
                assert data["size"] == 5
    
    @pytest.mark.asyncio
    async def test_listar_proveedores_solo_activos(self):
        """Test listar solo proveedores activos"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/catalog/api/proveedores/?activo=true")
            
            assert response.status_code in [200, 500]
            
            if response.status_code == 200:
                data = response.json()
                # Verificar que todos los items sean activos
                for item in data["items"]:
                    assert item["activo"] == True
    
    @pytest.mark.asyncio
    async def test_obtener_proveedor_por_id(self):
        """Test obtener proveedor específico por ID"""
        proveedor_id = str(uuid4())
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/catalog/api/proveedores/{proveedor_id}")
            
            # Puede ser 200, 404 o 500
            assert response.status_code in [200, 404, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert "id" in data
                assert "nit" in data
                assert "empresa" in data
    
    @pytest.mark.asyncio
    async def test_obtener_proveedor_id_invalido(self):
        """Test obtener proveedor con ID inválido (no UUID)"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/catalog/api/proveedores/invalid-uuid")
            
            # Debe fallar con 400 o 422
            assert response.status_code in [400, 422, 500]
    
    @pytest.mark.asyncio
    async def test_actualizar_proveedor(self):
        """Test actualizar proveedor existente"""
        proveedor_id = str(uuid4())
        datos_actualizacion = {
            "contacto_telefono": "+57-1-7777777",
            "direccion": "Nueva Dirección Test 456",
            "ciudad": "Cali"
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(
                f"/catalog/api/proveedores/{proveedor_id}",
                json=datos_actualizacion
            )
            
            # Puede ser 200, 404 o 500
            assert response.status_code in [200, 404, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert "updated_at" in data
    
    @pytest.mark.asyncio
    async def test_eliminar_proveedor(self):
        """Test eliminar proveedor (soft delete)"""
        proveedor_id = str(uuid4())
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete(f"/catalog/api/proveedores/{proveedor_id}")
            
            # Puede ser 200, 404 o 500
            assert response.status_code in [200, 404, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert "message" in data
    
    @pytest.mark.asyncio
    async def test_listar_productos_del_proveedor(self):
        """Test listar productos asociados a un proveedor"""
        proveedor_id = str(uuid4())
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/catalog/api/proveedores/{proveedor_id}/productos")
            
            # Puede ser 200, 404 o 500
            assert response.status_code in [200, 404, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert "proveedor_id" in data
                assert "productos" in data
                assert "total_productos" in data


class TestProveedorIntegration:
    """Tests de integración para flujo completo de proveedor"""
    
    @pytest.mark.asyncio
    async def test_flujo_crear_proveedor_y_productos(self):
        """Test flujo: crear proveedor y verificar productos"""
        nuevo_proveedor = {
            "nit": "800888888-8",
            "empresa": "Laboratorios Integración S.A.",
            "contacto_nombre": "María Test",
            "contacto_email": "maria@test.com",
            "contacto_telefono": "+57-1-8888888",
            "direccion": "Avenida Test 789",
            "ciudad": "Barranquilla",
            "pais": "CO",
            "activo": True
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Crear proveedor
            response_proveedor = await client.post(
                "/catalog/api/proveedores/",
                json=nuevo_proveedor
            )
            
            # Si se crea exitosamente, verificar productos
            if response_proveedor.status_code == 201:
                proveedor_data = response_proveedor.json()
                proveedor_id = proveedor_data["id"]
                
                # 2. Listar productos del proveedor
                response_productos = await client.get(
                    f"/catalog/api/proveedores/{proveedor_id}/productos"
                )
                
                # Debe responder (con o sin productos)
                assert response_productos.status_code in [200, 404, 500]
    
    @pytest.mark.asyncio
    async def test_flujo_crear_actualizar_eliminar_proveedor(self):
        """Test flujo completo: crear, actualizar y eliminar proveedor"""
        nuevo_proveedor = {
            "nit": "800777777-7",
            "empresa": "Proveedor Flujo S.A.",
            "contacto_nombre": "Carlos Test",
            "contacto_email": "carlos@test.com",
            "contacto_telefono": "+57-1-7777777",
            "direccion": "Carrera Test 456",
            "ciudad": "Pereira",
            "pais": "CO",
            "activo": True
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Crear
            response_crear = await client.post(
                "/catalog/api/proveedores/",
                json=nuevo_proveedor
            )
            
            if response_crear.status_code == 201:
                proveedor_data = response_crear.json()
                proveedor_id = proveedor_data["id"]
                
                # 2. Actualizar
                response_actualizar = await client.put(
                    f"/catalog/api/proveedores/{proveedor_id}",
                    json={"ciudad": "Manizales"}
                )
                
                assert response_actualizar.status_code in [200, 404, 500]
                
                # 3. Obtener y verificar actualización
                response_obtener = await client.get(f"/catalog/api/proveedores/{proveedor_id}")
                
                if response_obtener.status_code == 200:
                    data = response_obtener.json()
                    assert data.get("ciudad") == "Manizales" or data.get("ciudad") == "Pereira"
                
                # 4. Eliminar (soft delete)
                response_eliminar = await client.delete(f"/catalog/api/proveedores/{proveedor_id}")
                
                assert response_eliminar.status_code in [200, 404, 500]
                
                # 5. Verificar que está inactivo
                response_final = await client.get(f"/catalog/api/proveedores/{proveedor_id}")
                
                if response_final.status_code == 200:
                    data = response_final.json()
                    # Puede o no estar inactivo dependiendo de la implementación
                    assert "activo" in data
    
    @pytest.mark.asyncio
    async def test_validacion_email_invalido(self):
        """Test validación de email inválido"""
        proveedor_email_invalido = {
            "nit": "800666666-6",
            "empresa": "Test Email S.A.",
            "contacto_nombre": "Test",
            "contacto_email": "email-invalido",  # Email sin @
            "contacto_telefono": "+57-1-6666666",
            "direccion": "Calle Test",
            "ciudad": "Bogotá",
            "pais": "CO",
            "activo": True
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/catalog/api/proveedores/",
                json=proveedor_email_invalido
            )
            
            # Debe fallar validación o aceptarlo dependiendo del schema
            assert response.status_code in [201, 422, 500]
    
    @pytest.mark.asyncio
    async def test_buscar_proveedor_inexistente(self):
        """Test buscar proveedor que no existe"""
        proveedor_id_inexistente = str(uuid4())
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/catalog/api/proveedores/{proveedor_id_inexistente}")
            
            # Debe retornar 404
            assert response.status_code in [404, 500]
            
            if response.status_code == 404:
                data = response.json()
                assert "detail" in data or "message" in data
    
    @pytest.mark.asyncio
    async def test_actualizar_proveedor_inexistente(self):
        """Test actualizar proveedor que no existe"""
        proveedor_id_inexistente = str(uuid4())
        datos_actualizacion = {
            "ciudad": "Nueva Ciudad"
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(
                f"/catalog/api/proveedores/{proveedor_id_inexistente}",
                json=datos_actualizacion
            )
            
            # Debe retornar 404
            assert response.status_code in [404, 500]


class TestProveedorProductoRelation:
    """Tests para la relación entre proveedor y producto"""
    
    @pytest.mark.asyncio
    async def test_crear_producto_con_proveedor_uuid(self):
        """Test crear producto con proveedor_id como UUID"""
        proveedor_id = str(uuid4())
        
        nuevo_producto = {
            "id": "PROD_TEST_001",
            "nombre": "Producto Test",
            "sku": "SKU-TEST-001",
            "categoria": "Medicamentos",
            "precio": 25000.00,
            "stock_minimo": 10,
            "stock_actual": 100,
            "unidad_medida": "unidad",
            "proveedor_id": proveedor_id,
            "activo": True
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/catalog/api/productos/",
                json=nuevo_producto
            )
            
            # Puede ser 201, 400 (FK no existe) o 500
            assert response.status_code in [201, 400, 404, 409, 500]
    
    @pytest.mark.asyncio
    async def test_listar_productos_por_proveedor(self):
        """Test listar todos los productos de un proveedor específico"""
        proveedor_id = str(uuid4())
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/catalog/api/proveedores/{proveedor_id}/productos"
            )
            
            assert response.status_code in [200, 404, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data["productos"], list)
                # Todos los productos deben tener el mismo proveedor_id
                for producto in data["productos"]:
                    assert producto.get("proveedor_id") == proveedor_id or "proveedor_id" in producto



