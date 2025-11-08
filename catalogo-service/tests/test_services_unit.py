"""
Tests unitarios directos para services
Evitamos la complejidad de los endpoints HTTP
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestInventarioServiceUnit:
    """Tests unitarios para InventarioService"""
    
    @pytest.mark.asyncio
    async def test_inventario_service_initialization(self):
        """Test inicialización del servicio"""
        from app.services.inventario_service import InventarioService
        
        mock_session = AsyncMock()
        service = InventarioService(mock_session)
        
        assert service.session == mock_session
    
    @pytest.mark.asyncio
    async def test_calcular_saldo_actual_basico(self):
        """Test calcular saldo actual"""
        from app.services.inventario_service import InventarioService
        from app.models.movimiento_model import MovimientoInventario
        
        mock_session = AsyncMock()
        service = InventarioService(mock_session)
        
        # Mock de movimientos
        movimientos = [
            MagicMock(tipo_movimiento="INGRESO", cantidad=100, anulado=False),
            MagicMock(tipo_movimiento="SALIDA", cantidad=30, anulado=False),
            MagicMock(tipo_movimiento="INGRESO", cantidad=50, anulado=False),
        ]
        
        # Mock de la query
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = movimientos
        mock_session.execute.return_value = mock_result
        
        saldo = await service.calcular_saldo_actual("PROD001", "BOD001", "LOTE123")
        
        # 100 - 30 + 50 = 120
        assert saldo == 120
    
    @pytest.mark.asyncio
    async def test_verificar_stock_suficiente(self):
        """Test verificar stock suficiente"""
        from app.services.inventario_service import InventarioService
        from app.models.movimiento_model import MovimientoInventario
        
        mock_session = AsyncMock()
        service = InventarioService(mock_session)
        
        # Mock con stock suficiente
        movimientos = [
            MagicMock(tipo_movimiento="INGRESO", cantidad=100, anulado=False),
        ]
        
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = movimientos
        mock_session.execute.return_value = mock_result
        
        # Verificar que hay 100, solicitar 50 (debe pasar)
        resultado = await service.verificar_stock_suficiente("PROD001", "BOD001", "LOTE123", 50)
        assert resultado is True


class TestSQSPublisherUnit:
    """Tests unitarios para SQSPublisher"""
    
    def test_sqs_publisher_initialization(self):
        """Test inicialización del publisher"""
        from app.services.sqs_publisher import SQSPublisher
        
        with patch('app.services.sqs_publisher.boto3'):
            publisher = SQSPublisher()
            assert publisher is not None
    
    @pytest.mark.asyncio
    async def test_publish_message_basico(self):
        """Test publicar mensaje básico"""
        from app.services.sqs_publisher import SQSPublisher
        
        with patch('app.services.sqs_publisher.boto3') as mock_boto3:
            mock_sqs = MagicMock()
            mock_boto3.client.return_value = mock_sqs
            mock_sqs.send_message.return_value = {"MessageId": "123"}
            
            publisher = SQSPublisher()
            result = await publisher.publish_message(
                queue_name="test-queue",
                message_body={"test": "data"}
            )
            
            assert result is not None
            mock_sqs.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_publish_message_con_delay(self):
        """Test publicar mensaje con delay"""
        from app.services.sqs_publisher import SQSPublisher
        
        with patch('app.services.sqs_publisher.boto3') as mock_boto3:
            mock_sqs = MagicMock()
            mock_boto3.client.return_value = mock_sqs
            mock_sqs.send_message.return_value = {"MessageId": "456"}
            
            publisher = SQSPublisher()
            result = await publisher.publish_message(
                queue_name="test-queue",
                message_body={"test": "data"},
                delay_seconds=10
            )
            
            assert result is not None
            call_kwargs = mock_sqs.send_message.call_args[1]
            assert call_kwargs.get("DelaySeconds") == 10
    
    @pytest.mark.asyncio
    async def test_publish_batch_messages(self):
        """Test publicar mensajes en batch"""
        from app.services.sqs_publisher import SQSPublisher
        
        with patch('app.services.sqs_publisher.boto3') as mock_boto3:
            mock_sqs = MagicMock()
            mock_boto3.client.return_value = mock_sqs
            mock_sqs.send_message_batch.return_value = {
                "Successful": [{"MessageId": "1"}, {"MessageId": "2"}],
                "Failed": []
            }
            
            publisher = SQSPublisher()
            messages = [
                {"id": "1", "body": {"test": "data1"}},
                {"id": "2", "body": {"test": "data2"}}
            ]
            
            result = await publisher.publish_batch(queue_name="test-queue", messages=messages)
            
            assert result is not None
            mock_sqs.send_message_batch.assert_called_once()


class TestCatalogRoutesUnit:
    """Tests para cubrir lógica de routes/catalog.py"""
    
    def test_catalog_router_exists(self):
        """Test que el router de catálogo existe"""
        from app.routes.catalog import router
        
        assert router is not None
        routes = [route.path for route in router.routes]
        assert len(routes) > 0
    
    def test_catalog_router_has_bulk_upload_route(self):
        """Test que existe la ruta de carga masiva"""
        from app.routes.catalog import router
        
        routes = [route.path for route in router.routes]
        assert any("bulk-upload" in route for route in routes)


class TestInventarioRoutesUnit:
    """Tests para cubrir lógica de routes/inventario.py"""
    
    def test_inventario_router_exists(self):
        """Test que el router de inventario existe"""
        from app.routes.inventario import router
        
        assert router is not None
        routes = [route.path for route in router.routes]
        assert len(routes) > 0
    
    def test_inventario_router_has_movimientos_route(self):
        """Test que existe la ruta de movimientos"""
        from app.routes.inventario import router
        
        routes = [route.path for route in router.routes]
        assert any("movimientos" in route for route in routes)
    
    def test_inventario_router_has_kardex_route(self):
        """Test que existe la ruta de kardex"""
        from app.routes.inventario import router
        
        routes = [route.path for route in router.routes]
        assert any("kardex" in route for route in routes)
    
    def test_inventario_router_has_alertas_route(self):
        """Test que existe la ruta de alertas"""
        from app.routes.inventario import router
        
        routes = [route.path for route in router.routes]
        assert any("alertas" in route for route in routes)

