"""
Tests profesionales para rutas críticas de cliente-service
Autor: Senior Developer
Target: Cubrir rutas críticas hasta 70%+
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from uuid import uuid4, UUID
from datetime import datetime, date
from fastapi import HTTPException
from sqlalchemy import select


class TestClientRoutesComplete:
    """Suite completa de tests para rutas de clientes"""
    
    @pytest.mark.asyncio
    async def test_listar_clientes_con_filtro_vendedor(self, mock_session):
        """Test listar clientes filtrados por vendedor_id"""
        from app.routes.client import listar_clientes
        
        vendedor_id = str(uuid4())
        
        # Mock count
        mock_count = MagicMock()
        mock_count.scalar.return_value = 5
        
        # Mock query
        mock_query = MagicMock()
        mock_cliente = MagicMock()
        mock_cliente.id = uuid4()
        mock_cliente.nombre = "Cliente Test"
        mock_cliente.vendedor_id = UUID(vendedor_id)
        mock_query.scalars.return_value.all.return_value = [mock_cliente]
        
        mock_session.execute = AsyncMock(side_effect=[mock_count, mock_query])
        
        result = await listar_clientes(
            session=mock_session,
            vendedor_id=vendedor_id,
            page=1,
            size=10
        )
        
        assert result["meta"]["total"] == 5
        assert len(result["items"]) == 1
    
    @pytest.mark.asyncio
    async def test_listar_clientes_activos(self, mock_session):
        """Test listar solo clientes activos"""
        from app.routes.client import listar_clientes
        
        mock_count = MagicMock()
        mock_count.scalar.return_value = 3
        
        mock_query = MagicMock()
        mock_cliente = MagicMock()
        mock_cliente.activo = True
        mock_query.scalars.return_value.all.return_value = [mock_cliente]
        
        mock_session.execute = AsyncMock(side_effect=[mock_count, mock_query])
        
        result = await listar_clientes(
            session=mock_session,
            activo=True,
            page=1,
            size=10
        )
        
        assert result["meta"]["total"] == 3
    
    @pytest.mark.asyncio
    async def test_obtener_cliente_existente(self, mock_session):
        """Test obtener cliente por ID - caso exitoso"""
        from app.routes.client import obtener_cliente
        
        cliente_id = uuid4()
        mock_result = MagicMock()
        mock_cliente = MagicMock()
        mock_cliente.id = cliente_id
        mock_cliente.nombre = "Farmacia Central"
        mock_cliente.nit = "900123456"
        mock_result.scalar_one_or_none.return_value = mock_cliente
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await obtener_cliente(cliente_id=cliente_id, session=mock_session)
        
        assert result.id == cliente_id
        assert result.nombre == "Farmacia Central"
    
    @pytest.mark.asyncio
    async def test_obtener_cliente_no_existe(self, mock_session):
        """Test obtener cliente que no existe - debe lanzar 404"""
        from app.routes.client import obtener_cliente
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        with pytest.raises(HTTPException) as exc:
            await obtener_cliente(cliente_id=uuid4(), session=mock_session)
        
        assert exc.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_actualizar_cliente_datos_basicos(self, mock_session):
        """Test actualizar datos básicos de cliente"""
        from app.routes.client import actualizar_cliente
        from app.schemas import ClienteUpdate
        
        cliente_id = uuid4()
        update_data = ClienteUpdate(
            nombre="Nuevo Nombre",
            email="nuevo@email.com",
            telefono="+57 300 9876543"
        )
        
        mock_result = MagicMock()
        mock_cliente = MagicMock()
        mock_cliente.id = cliente_id
        mock_result.scalar_one_or_none.return_value = mock_cliente
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        result = await actualizar_cliente(
            cliente_id=cliente_id,
            cliente=update_data,
            session=mock_session
        )
        
        assert mock_cliente.nombre == "Nuevo Nombre"
        assert mock_cliente.email == "nuevo@email.com"
        assert mock_session.commit.called
    
    @pytest.mark.asyncio
    async def test_actualizar_cliente_cambiar_vendedor(self, mock_session):
        """Test cambiar vendedor asignado a cliente"""
        from app.routes.client import actualizar_cliente
        from app.schemas import ClienteUpdate
        
        cliente_id = uuid4()
        nuevo_vendedor_id = str(uuid4())
        
        update_data = ClienteUpdate(vendedor_id=nuevo_vendedor_id)
        
        # Mock cliente
        mock_cliente_result = MagicMock()
        mock_cliente = MagicMock()
        mock_cliente.id = cliente_id
        mock_cliente.vendedor_id = None
        mock_cliente_result.scalar_one_or_none.return_value = mock_cliente
        
        # Mock vendedor
        mock_vendedor_result = MagicMock()
        mock_vendedor = MagicMock()
        mock_vendedor.activo = True
        mock_vendedor_result.scalar_one_or_none.return_value = mock_vendedor
        
        mock_session.execute = AsyncMock(side_effect=[mock_cliente_result, mock_vendedor_result])
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        result = await actualizar_cliente(
            cliente_id=cliente_id,
            cliente=update_data,
            session=mock_session
        )
        
        assert mock_cliente.vendedor_id == UUID(nuevo_vendedor_id)
        assert mock_session.commit.called
    
    @pytest.mark.asyncio
    async def test_eliminar_cliente_soft_delete(self, mock_session):
        """Test eliminación lógica (soft delete) de cliente"""
        from app.routes.client import eliminar_cliente
        
        cliente_id = uuid4()
        mock_result = MagicMock()
        mock_cliente = MagicMock()
        mock_cliente.id = cliente_id
        mock_cliente.activo = True
        mock_result.scalar_one_or_none.return_value = mock_cliente
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        
        result = await eliminar_cliente(cliente_id=cliente_id, session=mock_session)
        
        assert mock_cliente.activo == False
        assert mock_session.commit.called
        assert "message" in result
    
    @pytest.mark.asyncio
    async def test_listar_clientes_sin_vendedor_vacio(self, mock_session):
        """Test listar clientes sin vendedor cuando no hay ninguno"""
        from app.routes.client import listar_clientes_sin_vendedor
        
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        
        mock_query = MagicMock()
        mock_query.scalars.return_value.all.return_value = []
        
        mock_session.execute = AsyncMock(side_effect=[mock_count, mock_query])
        
        result = await listar_clientes_sin_vendedor(
            session=mock_session,
            page=1,
            size=10
        )
        
        assert result["meta"]["total"] == 0
        assert len(result["items"]) == 0
    
    @pytest.mark.asyncio
    async def test_listar_clientes_sin_vendedor_con_resultados(self, mock_session):
        """Test listar clientes sin vendedor con resultados"""
        from app.routes.client import listar_clientes_sin_vendedor
        
        mock_count = MagicMock()
        mock_count.scalar.return_value = 2
        
        mock_query = MagicMock()
        mock_cliente1 = MagicMock()
        mock_cliente1.vendedor_id = None
        mock_cliente2 = MagicMock()
        mock_cliente2.vendedor_id = None
        mock_query.scalars.return_value.all.return_value = [mock_cliente1, mock_cliente2]
        
        mock_session.execute = AsyncMock(side_effect=[mock_count, mock_query])
        
        result = await listar_clientes_sin_vendedor(
            session=mock_session,
            page=1,
            size=10
        )
        
        assert result["meta"]["total"] == 2
        assert len(result["items"]) == 2


class TestVendedorRoutesComplete:
    """Suite completa de tests para rutas de vendedores"""
    
    @pytest.mark.asyncio
    async def test_listar_vendedores_con_paginacion(self, mock_session):
        """Test listar vendedores con paginación"""
        from app.routes.vendedor import listar_vendedores
        
        mock_count = MagicMock()
        mock_count.scalar.return_value = 15
        
        mock_query = MagicMock()
        mock_vendedor = MagicMock()
        mock_vendedor.id = uuid4()
        mock_vendedor.nombre = "Juan"
        mock_query.scalars.return_value.all.return_value = [mock_vendedor]
        
        mock_session.execute = AsyncMock(side_effect=[mock_count, mock_query])
        
        result = await listar_vendedores(
            session=mock_session,
            page=2,
            size=5
        )
        
        assert result["meta"]["total"] == 15
        assert result["meta"]["page"] == 2
        assert result["meta"]["pages"] == 3
    
    @pytest.mark.asyncio
    async def test_listar_vendedores_filtro_activos(self, mock_session):
        """Test listar solo vendedores activos"""
        from app.routes.vendedor import listar_vendedores
        
        mock_count = MagicMock()
        mock_count.scalar.return_value = 8
        
        mock_query = MagicMock()
        mock_vendedor = MagicMock()
        mock_vendedor.activo = True
        mock_query.scalars.return_value.all.return_value = [mock_vendedor]
        
        mock_session.execute = AsyncMock(side_effect=[mock_count, mock_query])
        
        result = await listar_vendedores(
            session=mock_session,
            activo=True,
            page=1,
            size=10
        )
        
        assert result["meta"]["total"] == 8
    
    @pytest.mark.asyncio
    async def test_obtener_vendedor_existente(self, mock_session):
        """Test obtener vendedor por ID"""
        from app.routes.vendedor import obtener_vendedor
        
        vendedor_id = uuid4()
        mock_result = MagicMock()
        mock_vendedor = MagicMock()
        mock_vendedor.id = vendedor_id
        mock_vendedor.nombre = "María"
        mock_vendedor.apellido = "García"
        mock_result.scalar_one_or_none.return_value = mock_vendedor
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await obtener_vendedor(vendedor_id=vendedor_id, session=mock_session)
        
        assert result.id == vendedor_id
        assert result.nombre == "María"
    
    @pytest.mark.asyncio
    async def test_actualizar_vendedor(self, mock_session):
        """Test actualizar información de vendedor"""
        from app.routes.vendedor import actualizar_vendedor
        from app.schemas import VendedorUpdate
        
        vendedor_id = uuid4()
        update_data = VendedorUpdate(
            email="nuevo@email.com",
            telefono="+57 300 1111111"
        )
        
        mock_result = MagicMock()
        mock_vendedor = MagicMock()
        mock_vendedor.id = vendedor_id
        mock_result.scalar_one_or_none.return_value = mock_vendedor
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        result = await actualizar_vendedor(
            vendedor_id=vendedor_id,
            vendedor=update_data,
            session=mock_session
        )
        
        assert mock_vendedor.email == "nuevo@email.com"
        assert mock_session.commit.called
    
    @pytest.mark.asyncio
    async def test_asociar_clientes_a_vendedor_exitoso(self, mock_session):
        """Test asociar múltiples clientes a un vendedor"""
        from app.routes.vendedor import asociar_clientes_vendedor
        from app.schemas import AsociarClientesRequest
        
        vendedor_id = uuid4()
        cliente_id1 = uuid4()
        cliente_id2 = uuid4()
        
        request_data = AsociarClientesRequest(
            cliente_ids=[str(cliente_id1), str(cliente_id2)]
        )
        
        # Mock vendedor
        mock_vendedor_result = MagicMock()
        mock_vendedor = MagicMock()
        mock_vendedor.id = vendedor_id
        mock_vendedor.activo = True
        mock_vendedor_result.scalar_one_or_none.return_value = mock_vendedor
        
        # Mock clientes
        mock_clientes_result = MagicMock()
        mock_cliente1 = MagicMock()
        mock_cliente1.id = cliente_id1
        mock_cliente1.vendedor_id = None
        mock_cliente1.activo = True
        mock_cliente2 = MagicMock()
        mock_cliente2.id = cliente_id2
        mock_cliente2.vendedor_id = None
        mock_cliente2.activo = True
        mock_clientes_result.scalars.return_value.all.return_value = [mock_cliente1, mock_cliente2]
        
        mock_session.execute = AsyncMock(side_effect=[mock_vendedor_result, mock_clientes_result])
        mock_session.commit = AsyncMock()
        
        result = await asociar_clientes_vendedor(
            vendedor_id=vendedor_id,
            request=request_data,
            session=mock_session
        )
        
        assert result["vendedor_id"] == str(vendedor_id)
        assert result["clientes_asociados"] == 2
        assert mock_cliente1.vendedor_id == vendedor_id
        assert mock_cliente2.vendedor_id == vendedor_id
    
    @pytest.mark.asyncio
    async def test_asociar_clientes_vendedor_no_existe(self, mock_session):
        """Test asociar clientes a vendedor inexistente - debe fallar"""
        from app.routes.vendedor import asociar_clientes_vendedor
        from app.schemas import AsociarClientesRequest
        
        request_data = AsociarClientesRequest(
            cliente_ids=[str(uuid4())]
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        with pytest.raises(HTTPException) as exc:
            await asociar_clientes_vendedor(
                vendedor_id=uuid4(),
                request=request_data,
                session=mock_session
            )
        
        assert exc.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_asociar_clientes_vendedor_inactivo(self, mock_session):
        """Test asociar clientes a vendedor inactivo - debe fallar"""
        from app.routes.vendedor import asociar_clientes_vendedor
        from app.schemas import AsociarClientesRequest
        
        request_data = AsociarClientesRequest(
            cliente_ids=[str(uuid4())]
        )
        
        mock_result = MagicMock()
        mock_vendedor = MagicMock()
        mock_vendedor.activo = False
        mock_result.scalar_one_or_none.return_value = mock_vendedor
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        with pytest.raises(HTTPException) as exc:
            await asociar_clientes_vendedor(
                vendedor_id=uuid4(),
                request=request_data,
                session=mock_session
            )
        
        assert exc.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_asociar_clientes_ya_tienen_vendedor(self, mock_session):
        """Test asociar clientes que ya tienen vendedor asignado"""
        from app.routes.vendedor import asociar_clientes_vendedor
        from app.schemas import AsociarClientesRequest
        
        vendedor_id = uuid4()
        otro_vendedor_id = uuid4()
        
        request_data = AsociarClientesRequest(
            cliente_ids=[str(uuid4())]
        )
        
        # Mock vendedor
        mock_vendedor_result = MagicMock()
        mock_vendedor = MagicMock()
        mock_vendedor.activo = True
        mock_vendedor_result.scalar_one_or_none.return_value = mock_vendedor
        
        # Mock cliente con vendedor ya asignado
        mock_clientes_result = MagicMock()
        mock_cliente = MagicMock()
        mock_cliente.vendedor_id = otro_vendedor_id  # Ya tiene vendedor
        mock_cliente.activo = True
        mock_clientes_result.scalars.return_value.all.return_value = [mock_cliente]
        
        mock_session.execute = AsyncMock(side_effect=[mock_vendedor_result, mock_clientes_result])
        mock_session.commit = AsyncMock()
        
        result = await asociar_clientes_vendedor(
            vendedor_id=vendedor_id,
            request=request_data,
            session=mock_session
        )
        
        # No debería asociar clientes que ya tienen vendedor
        assert result["clientes_asociados"] == 0
        assert len(result["clientes_con_vendedor"]) == 1


class TestUtilitiesFunctions:
    """Tests para funciones utilitarias"""
    
    @pytest.mark.asyncio
    async def test_generar_codigo_unico_formato(self, mock_session):
        """Test que generar_codigo_unico devuelve formato correcto"""
        from app.routes.client import generar_codigo_unico
        
        # Mock para verificar unicidad
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        codigo = await generar_codigo_unico(mock_session)
        
        assert len(codigo) == 6
        assert codigo[:3].isalpha()
        assert codigo[:3].isupper()
        assert codigo[3:].isdigit()
    
    @pytest.mark.asyncio
    async def test_generar_codigo_unico_es_unico(self, mock_session):
        """Test que generar_codigo_unico valida unicidad"""
        from app.routes.client import generar_codigo_unico
        
        # Primera llamada: código ya existe
        mock_result_exists = MagicMock()
        mock_result_exists.scalar_one_or_none.return_value = MagicMock()  # Ya existe
        
        # Segunda llamada: código disponible
        mock_result_available = MagicMock()
        mock_result_available.scalar_one_or_none.return_value = None
        
        mock_session.execute = AsyncMock(side_effect=[mock_result_exists, mock_result_available])
        
        codigo = await generar_codigo_unico(mock_session)
        
        # Debería haber intentado 2 veces
        assert mock_session.execute.call_count == 2
        assert len(codigo) == 6


class TestBusinessValidations:
    """Tests para validaciones de negocio críticas"""
    
    @pytest.mark.asyncio
    async def test_crear_cliente_nit_duplicado(self, mock_session):
        """Test crear cliente con NIT duplicado - debe fallar"""
        from app.routes.client import crear_cliente
        from app.schemas import ClienteCreate
        
        cliente_data = ClienteCreate(
            nit="900123456",
            nombre="Cliente Test",
            email="test@test.com",
            telefono="+57 1 1234567",
            direccion="Calle 123",
            ciudad="Bogotá",
            pais="CO",
            activo=True
        )
        
        # Mock: NIT ya existe
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()  # Ya existe
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        with pytest.raises(HTTPException) as exc:
            await crear_cliente(cliente=cliente_data, session=mock_session)
        
        assert exc.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_crear_vendedor_username_duplicado(self, mock_session):
        """Test crear vendedor con username duplicado - debe fallar"""
        from app.routes.vendedor import crear_vendedor
        from app.schemas import VendedorCreate
        
        vendedor_data = VendedorCreate(
            identificacion="123456789",
            nombre="Juan",
            apellido="Pérez",
            email="juan@test.com",
            telefono="+57 300 1234567",
            pais="CO",
            username="juanperez",
            password_hash="$2b$12$test",
            activo=True
        )
        
        # Mock: username ya existe
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()  # Ya existe
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        with pytest.raises(HTTPException) as exc:
            await crear_vendedor(vendedor=vendedor_data, session=mock_session)
        
        assert exc.value.status_code == 400

