"""
Tests comprehensivos para cliente-service - Objetivo: 80%+ de cobertura
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, date
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


pytestmark = pytest.mark.asyncio


class TestClientRoutes:
    """Tests para app/routes/client.py"""
    
    @patch('app.routes.client.ClienteService')
    async def test_listar_clientes_exitoso(self, mock_service_class):
        """Test listar clientes exitoso"""
        from app.routes.client import listar_clientes
        from app.schemas import ClienteBasicoResponse
        
        # Mock service
        mock_service = Mock()
        mock_cliente = ClienteBasicoResponse(
            codigo_unico="CLI001",
            nit="900123456-1",
            nombre="Cliente Test",
            direccion="Calle 123",
            telefono="3001234567",
            activo=True,
            created_at=datetime.now()
        )
        mock_service.listar_clientes = AsyncMock(return_value=[mock_cliente])
        mock_service_class.return_value = mock_service
        
        mock_request = Mock()
        mock_session = AsyncMock()
        
        result = await listar_clientes(
            request=mock_request,
            limite=50,
            offset=0,
            activos_solo=True,
            ordenar_por="nombre",
            vendedor_id=None,
            session=mock_session
        )
        
        assert len(result) == 1
        assert result[0].codigo_unico == "CLI001"
    
    @patch('app.routes.client.ClienteService')
    async def test_listar_clientes_con_filtros(self, mock_service_class):
        """Test listar clientes con filtros"""
        from app.routes.client import listar_clientes
        
        mock_service = Mock()
        mock_service.listar_clientes = AsyncMock(return_value=[])
        mock_service_class.return_value = mock_service
        
        mock_request = Mock()
        mock_session = AsyncMock()
        
        result = await listar_clientes(
            request=mock_request,
            limite=10,
            offset=5,
            activos_solo=False,
            ordenar_por="nit",
            vendedor_id="VEND001",
            session=mock_session
        )
        
        assert isinstance(result, list)
        mock_service.listar_clientes.assert_called_once()
    
    @patch('app.routes.client.ClienteService')
    async def test_listar_clientes_error(self, mock_service_class):
        """Test listar clientes con error"""
        from app.routes.client import listar_clientes
        
        mock_service = Mock()
        mock_service.listar_clientes = AsyncMock(side_effect=Exception("DB Error"))
        mock_service_class.return_value = mock_service
        
        mock_request = Mock()
        mock_session = AsyncMock()
        
        with pytest.raises(HTTPException) as exc_info:
            await listar_clientes(
                request=mock_request,
                limite=50,
                offset=0,
                activos_solo=True,
                ordenar_por="nombre",
                vendedor_id=None,
                session=mock_session
            )
        
        assert exc_info.value.status_code == 500
    
    @patch('app.routes.client.ClienteService')
    async def test_buscar_cliente_exitoso(self, mock_service_class):
        """Test buscar cliente exitoso"""
        from app.routes.client import buscar_cliente
        from app.schemas import ClienteBasicoResponse
        
        mock_service = Mock()
        mock_cliente = ClienteBasicoResponse(
            codigo_unico="CLI002",
            nit="900123457-2",
            nombre="Cliente Búsqueda",
            direccion="Calle 456",
            telefono="3001234568",
            activo=True,
            created_at=datetime.now()
        )
        mock_service.buscar_cliente = AsyncMock(return_value=mock_cliente)
        mock_service_class.return_value = mock_service
        
        mock_request = Mock()
        mock_session = AsyncMock()
        
        result = await buscar_cliente(
            termino_busqueda="900123457-2",
            vendedor_id="VEND001",
            request=mock_request,
            session=mock_session
        )
        
        assert result.codigo_unico == "CLI002"
        assert result.nit == "900123457-2"
    
    @patch('app.routes.client.ClienteService')
    async def test_buscar_cliente_no_encontrado(self, mock_service_class):
        """Test buscar cliente no encontrado"""
        from app.routes.client import buscar_cliente
        
        mock_service = Mock()
        mock_service.buscar_cliente = AsyncMock(
            side_effect=HTTPException(status_code=404, detail="Not found")
        )
        mock_service_class.return_value = mock_service
        
        mock_request = Mock()
        mock_session = AsyncMock()
        
        with pytest.raises(HTTPException) as exc_info:
            await buscar_cliente(
                termino_busqueda="NOEXISTE",
                vendedor_id="VEND001",
                request=mock_request,
                session=mock_session
            )
        
        assert exc_info.value.status_code == 404
    
    @patch('app.routes.client.ClienteService')
    async def test_historico_cliente_exitoso(self, mock_service_class):
        """Test obtener histórico de cliente"""
        from app.routes.client import obtener_historico_cliente
        from app.schemas import HistoricoCompletoResponse, HistoricoItem
        
        mock_service = Mock()
        mock_historico = HistoricoCompletoResponse(
            codigo_unico="CLI003",
            nombre="Cliente Histórico",
            total_consultas=10,
            primera_consulta=datetime.now(),
            ultima_consulta=datetime.now(),
            historico_consultas=[
                HistoricoItem(
                    fecha=datetime.now(),
                    vendedor_id="VEND001",
                    tipo_busqueda="nit",
                    tiempo_respuesta_ms=100
                )
            ]
        )
        mock_service.obtener_historico_completo = AsyncMock(return_value=mock_historico)
        mock_service_class.return_value = mock_service
        
        mock_request = Mock()
        mock_session = AsyncMock()
        
        result = await obtener_historico_cliente(
            codigo_unico="CLI003",
            vendedor_id="VEND001",
            request=mock_request,
            session=mock_session
        )
        
        assert result.codigo_unico == "CLI003"
        assert result.total_consultas == 10
    
    @patch('app.routes.client.ClienteService')
    async def test_obtener_metricas_exitoso(self, mock_service_class):
        """Test obtener métricas"""
        from app.routes.client import obtener_metricas
        
        mock_service = Mock()
        mock_service.obtener_metricas = AsyncMock(return_value={
            "total_clientes": 100,
            "clientes_activos": 90,
            "clientes_inactivos": 10
        })
        mock_service_class.return_value = mock_service
        
        mock_request = Mock()
        mock_session = AsyncMock()
        
        result = await obtener_metricas(
            request=mock_request,
            session=mock_session
        )
        
        assert result["total_clientes"] == 100
        assert result["clientes_activos"] == 90
    
    @patch('app.routes.client.ClienteService')
    async def test_validar_cliente_exitoso(self, mock_service_class):
        """Test validar cliente"""
        from app.routes.client import validar_cliente
        from app.schemas import ValidacionResponse
        
        mock_service = Mock()
        mock_validacion = ValidacionResponse(
            valido=True,
            mensaje="Cliente válido",
            detalles={}
        )
        mock_service.validar_cliente = AsyncMock(return_value=mock_validacion)
        mock_service_class.return_value = mock_service
        
        mock_request = Mock()
        mock_session = AsyncMock()
        
        result = await validar_cliente(
            nit="900123456-1",
            request=mock_request,
            session=mock_session
        )
        
        assert result.valido is True
    
    @patch('app.routes.client.ClienteService')
    async def test_crear_cliente_exitoso(self, mock_service_class):
        """Test crear cliente"""
        from app.routes.client import crear_cliente
        from app.schemas import ClienteCreate, ClienteBasicoResponse
        
        cliente_data = ClienteCreate(
            nit="900123458-3",
            nombre="Nuevo Cliente",
            direccion="Calle 789",
            telefono="3001234569",
            email="nuevo@test.com",
            ciudad="Bogotá",
            activo=True
        )
        
        mock_service = Mock()
        mock_cliente = ClienteBasicoResponse(
            codigo_unico="CLI004",
            nit="900123458-3",
            nombre="Nuevo Cliente",
            direccion="Calle 789",
            telefono="3001234569",
            activo=True,
            created_at=datetime.now()
        )
        mock_service.crear_cliente = AsyncMock(return_value=mock_cliente)
        mock_service_class.return_value = mock_service
        
        mock_request = Mock()
        mock_session = AsyncMock()
        
        result = await crear_cliente(
            cliente=cliente_data,
            request=mock_request,
            session=mock_session
        )
        
        assert result.codigo_unico == "CLI004"
        assert result.nit == "900123458-3"
    
    @patch('app.routes.client.ClienteService')
    async def test_actualizar_cliente_exitoso(self, mock_service_class):
        """Test actualizar cliente"""
        from app.routes.client import actualizar_cliente
        from app.schemas import ClienteUpdate, ClienteBasicoResponse
        
        update_data = ClienteUpdate(
            nombre="Cliente Actualizado",
            telefono="3009999999"
        )
        
        mock_service = Mock()
        mock_cliente = ClienteBasicoResponse(
            codigo_unico="CLI005",
            nit="900123459-4",
            nombre="Cliente Actualizado",
            direccion="Calle 123",
            telefono="3009999999",
            activo=True,
            created_at=datetime.now()
        )
        mock_service.actualizar_cliente = AsyncMock(return_value=mock_cliente)
        mock_service_class.return_value = mock_service
        
        mock_request = Mock()
        mock_session = AsyncMock()
        
        result = await actualizar_cliente(
            codigo_unico="CLI005",
            cliente=update_data,
            request=mock_request,
            session=mock_session
        )
        
        assert result.nombre == "Cliente Actualizado"
        assert result.telefono == "3009999999"
    
    @patch('app.routes.client.ClienteService')
    async def test_eliminar_cliente_exitoso(self, mock_service_class):
        """Test eliminar cliente"""
        from app.routes.client import eliminar_cliente
        
        mock_service = Mock()
        mock_service.eliminar_cliente = AsyncMock(return_value=True)
        mock_service_class.return_value = mock_service
        
        mock_request = Mock()
        mock_session = AsyncMock()
        
        result = await eliminar_cliente(
            codigo_unico="CLI006",
            request=mock_request,
            session=mock_session
        )
        
        assert "message" in result or "detail" in result or result == {"status": "success"}


class TestClientService:
    """Tests para app/services/client_service.py"""
    
    async def test_buscar_cliente_exitoso(self):
        """Test buscar_cliente"""
        from app.services.client_service import ClienteService
        
        mock_session = AsyncMock()
        mock_settings = Mock()
        
        service = ClienteService(mock_session, mock_settings)
        
        # Mock repository
        mock_cliente = Mock()
        mock_cliente.codigo_unico = "CLI007"
        mock_cliente.nit = "900123460-5"
        mock_cliente.nombre = "Cliente Service Test"
        mock_cliente.direccion = "Calle 123"
        mock_cliente.telefono = "3001234570"
        mock_cliente.email = "test@test.com"
        mock_cliente.ciudad = "Bogotá"
        mock_cliente.activo = True
        mock_cliente.created_at = datetime.now()
        
        service.repository.buscar_cliente_por_termino = AsyncMock(return_value=mock_cliente)
        service.repository.registrar_consulta = AsyncMock()
        
        result = await service.buscar_cliente("900123460-5", "VEND001")
        
        assert result.codigo_unico == "CLI007"
        service.repository.registrar_consulta.assert_called_once()
    
    async def test_buscar_cliente_no_encontrado(self):
        """Test buscar cliente no encontrado"""
        from app.services.client_service import ClienteService
        
        mock_session = AsyncMock()
        service = ClienteService(mock_session)
        
        service.repository.buscar_cliente_por_termino = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.buscar_cliente("NOEXISTE", "VEND001")
        
        assert exc_info.value.status_code == 404
    
    async def test_listar_clientes(self):
        """Test listar clientes"""
        from app.services.client_service import ClienteService
        
        mock_session = AsyncMock()
        service = ClienteService(mock_session)
        
        mock_clientes = [
            Mock(codigo_unico="CLI008", nit="900123461-6", nombre="Cliente 1",
                 direccion="Calle 1", telefono="3001111111", activo=True, created_at=datetime.now()),
            Mock(codigo_unico="CLI009", nit="900123462-7", nombre="Cliente 2",
                 direccion="Calle 2", telefono="3002222222", activo=True, created_at=datetime.now())
        ]
        
        service.repository.listar_clientes = AsyncMock(return_value=mock_clientes)
        
        result = await service.listar_clientes(limite=50, offset=0, activos_solo=True, ordenar_por="nombre")
        
        assert len(result) == 2
        assert result[0].codigo_unico == "CLI008"
    
    async def test_obtener_historico_completo(self):
        """Test obtener histórico completo"""
        from app.services.client_service import ClienteService
        
        mock_session = AsyncMock()
        service = ClienteService(mock_session)
        
        mock_cliente = Mock()
        mock_cliente.codigo_unico = "CLI010"
        mock_cliente.nombre = "Cliente Histórico"
        
        mock_historico = [
            Mock(fecha=datetime.now(), vendedor_id="VEND001", tipo_busqueda="nit", tiempo_respuesta_ms=100)
        ]
        
        service.repository.buscar_cliente_por_codigo = AsyncMock(return_value=mock_cliente)
        service.repository.obtener_historico = AsyncMock(return_value=mock_historico)
        service.repository.registrar_consulta = AsyncMock()
        
        result = await service.obtener_historico_completo("CLI010", "VEND001")
        
        assert result.codigo_unico == "CLI010"
        assert result.total_consultas == 1
    
    async def test_obtener_metricas(self):
        """Test obtener métricas"""
        from app.services.client_service import ClienteService
        
        mock_session = AsyncMock()
        service = ClienteService(mock_session)
        
        service.repository.contar_clientes = AsyncMock(return_value=150)
        
        result = await service.obtener_metricas()
        
        assert result["total_clientes"] == 150
    
    async def test_validar_cliente(self):
        """Test validar cliente"""
        from app.services.client_service import ClienteService
        
        mock_session = AsyncMock()
        service = ClienteService(mock_session)
        
        mock_cliente = Mock()
        mock_cliente.codigo_unico = "CLI011"
        mock_cliente.activo = True
        
        service.repository.buscar_cliente_por_nit = AsyncMock(return_value=mock_cliente)
        
        result = await service.validar_cliente("900123463-8")
        
        assert result.valido is True
    
    async def test_crear_cliente(self):
        """Test crear cliente"""
        from app.services.client_service import ClienteService
        from app.schemas import ClienteCreate
        
        cliente_data = ClienteCreate(
            nit="900123464-9",
            nombre="Cliente Nuevo Service",
            direccion="Calle Nueva",
            telefono="3003333333",
            email="nuevo@service.com",
            ciudad="Medellín",
            activo=True
        )
        
        mock_session = AsyncMock()
        service = ClienteService(mock_session)
        
        mock_cliente = Mock()
        mock_cliente.codigo_unico = "CLI012"
        mock_cliente.nit = "900123464-9"
        mock_cliente.nombre = "Cliente Nuevo Service"
        mock_cliente.direccion = "Calle Nueva"
        mock_cliente.telefono = "3003333333"
        mock_cliente.activo = True
        mock_cliente.created_at = datetime.now()
        
        service.repository.crear_cliente = AsyncMock(return_value=mock_cliente)
        
        result = await service.crear_cliente(cliente_data)
        
        assert result.codigo_unico == "CLI012"
    
    async def test_actualizar_cliente(self):
        """Test actualizar cliente"""
        from app.services.client_service import ClienteService
        from app.schemas import ClienteUpdate
        
        update_data = ClienteUpdate(nombre="Actualizado Service")
        
        mock_session = AsyncMock()
        service = ClienteService(mock_session)
        
        mock_cliente = Mock()
        mock_cliente.codigo_unico = "CLI013"
        mock_cliente.nombre = "Actualizado Service"
        mock_cliente.nit = "900123465-0"
        mock_cliente.direccion = "Calle 123"
        mock_cliente.telefono = "3001234571"
        mock_cliente.activo = True
        mock_cliente.created_at = datetime.now()
        
        service.repository.actualizar_cliente = AsyncMock(return_value=mock_cliente)
        
        result = await service.actualizar_cliente("CLI013", update_data)
        
        assert result.nombre == "Actualizado Service"
    
    async def test_eliminar_cliente(self):
        """Test eliminar cliente"""
        from app.services.client_service import ClienteService
        
        mock_session = AsyncMock()
        service = ClienteService(mock_session)
        
        service.repository.eliminar_cliente = AsyncMock(return_value=True)
        
        result = await service.eliminar_cliente("CLI014")
        
        assert result is True


class TestClientRepository:
    """Tests para app/repositories/client_repo.py"""
    
    async def test_buscar_cliente_por_termino(self):
        """Test buscar cliente por término"""
        from app.repositories.client_repo import ClienteRepository
        
        mock_session = AsyncMock()
        repo = ClienteRepository(mock_session)
        
        mock_cliente = Mock()
        mock_cliente.codigo_unico = "CLI015"
        
        mock_result = Mock()
        mock_result.first = Mock(return_value=mock_cliente)
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await repo.buscar_cliente_por_termino("900123466-1")
        
        assert result == mock_cliente
    
    async def test_listar_clientes(self):
        """Test listar clientes repository"""
        from app.repositories.client_repo import ClienteRepository
        
        mock_session = AsyncMock()
        repo = ClienteRepository(mock_session)
        
        mock_clientes = [Mock(), Mock()]
        
        mock_result = Mock()
        mock_result.scalars = Mock()
        mock_result.scalars.return_value.all = Mock(return_value=mock_clientes)
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await repo.listar_clientes(limite=50, offset=0, activos_solo=True, ordenar_por="nombre")
        
        assert len(result) == 2
    
    async def test_registrar_consulta(self):
        """Test registrar consulta"""
        from app.repositories.client_repo import ClienteRepository
        
        mock_session = AsyncMock()
        repo = ClienteRepository(mock_session)
        
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        result = await repo.registrar_consulta(
            codigo_unico="CLI016",
            vendedor_id="VEND001",
            tipo_busqueda="nit",
            tiempo_respuesta_ms=100
        )
        
        mock_session.commit.assert_called_once()
    
    async def test_contar_clientes(self):
        """Test contar clientes"""
        from app.repositories.client_repo import ClienteRepository
        
        mock_session = AsyncMock()
        repo = ClienteRepository(mock_session)
        
        mock_result = Mock()
        mock_result.scalar = Mock(return_value=200)
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await repo.contar_clientes(activos_solo=True)
        
        assert result == 200

