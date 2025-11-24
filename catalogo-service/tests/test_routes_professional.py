"""
Tests profesionales para rutas críticas - Enfoque en coverage real
Autor: Senior Developer
Target: Cubrir rutas con 11-26% actual hasta 70%+
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from uuid import uuid4
from datetime import datetime, date
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import select


class TestProveedorRoutesComplete:
    """Suite completa de tests para rutas de proveedores (11% -> 70%)"""
    
    @pytest.mark.asyncio
    async def test_listar_proveedores_con_filtros(self, mock_session):
        """Test listar proveedores con múltiples filtros"""
        from app.routes.proveedor import listar_proveedores
        
        # Setup mocks
        mock_count = MagicMock()
        mock_count.scalar.return_value = 5
        
        mock_query = MagicMock()
        mock_prov = MagicMock()
        mock_prov.id = str(uuid4())
        mock_prov.nombre = "Proveedor Test"
        mock_prov.nit = "900123456"
        mock_prov.activo = True
        mock_query.scalars.return_value.all.return_value = [mock_prov]
        
        mock_session.execute = AsyncMock(side_effect=[mock_count, mock_query])
        
        result = await listar_proveedores(
            session=mock_session,
            page=1,
            size=10,
            activo=True,
            search="Test"
        )
        
        assert result["meta"]["total"] == 5
        assert len(result["items"]) == 1
        assert mock_session.execute.call_count == 2
    
    @pytest.mark.asyncio
    async def test_obtener_proveedor_existente(self, mock_session):
        """Test obtener proveedor por ID - caso exitoso"""
        from app.routes.proveedor import obtener_proveedor
        
        proveedor_id = str(uuid4())
        mock_result = MagicMock()
        mock_prov = MagicMock()
        mock_prov.id = proveedor_id
        mock_prov.nombre = "Farmaceutica XYZ"
        mock_result.scalar_one_or_none.return_value = mock_prov
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await obtener_proveedor(proveedor_id=proveedor_id, session=mock_session)
        
        assert result.id == proveedor_id
        assert result.nombre == "Farmaceutica XYZ"
    
    @pytest.mark.asyncio
    async def test_obtener_proveedor_no_existe(self, mock_session):
        """Test obtener proveedor que no existe - debe lanzar 404"""
        from app.routes.proveedor import obtener_proveedor
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        with pytest.raises(HTTPException) as exc:
            await obtener_proveedor(proveedor_id=str(uuid4()), session=mock_session)
        
        assert exc.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_actualizar_proveedor_existente(self, mock_session):
        """Test actualizar proveedor - caso exitoso"""
        from app.routes.proveedor import actualizar_proveedor
        from app.schemas import ProveedorUpdate
        
        proveedor_id = str(uuid4())
        update_data = ProveedorUpdate(
            nombre="Nuevo Nombre",
            activo=False
        )
        
        mock_result = MagicMock()
        mock_prov = MagicMock()
        mock_prov.id = proveedor_id
        mock_prov.nombre = "Viejo Nombre"
        mock_prov.activo = True
        mock_result.scalar_one_or_none.return_value = mock_prov
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        result = await actualizar_proveedor(
            proveedor_id=proveedor_id,
            proveedor=update_data,
            session=mock_session
        )
        
        assert mock_prov.nombre == "Nuevo Nombre"
        assert mock_prov.activo == False
        assert mock_session.commit.called
    
    @pytest.mark.asyncio
    async def test_eliminar_proveedor_soft_delete(self, mock_session):
        """Test eliminación lógica (soft delete) de proveedor"""
        from app.routes.proveedor import eliminar_proveedor
        
        proveedor_id = str(uuid4())
        mock_result = MagicMock()
        mock_prov = MagicMock()
        mock_prov.id = proveedor_id
        mock_prov.activo = True
        mock_result.scalar_one_or_none.return_value = mock_prov
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        result = await eliminar_proveedor(proveedor_id=proveedor_id, session=mock_session)
        
        assert mock_prov.activo == False
        assert mock_session.commit.called
        assert "message" in result


class TestCatalogRoutesComplete:
    """Suite completa para rutas de catálogo (16% -> 70%)"""
    
    @pytest.mark.asyncio
    async def test_listar_productos_con_paginacion(self, mock_session):
        """Test listar productos con paginación"""
        from app.routes.catalog import listar_productos
        
        with patch('app.routes.catalog.buscar_productos') as mock_buscar:
            mock_producto = MagicMock()
            mock_producto.id = str(uuid4())
            mock_producto.nombre = "Producto Test"
            mock_buscar.return_value = ([mock_producto], 1)
            
            result = await listar_productos(
                session=mock_session,
                page=1,
                size=10
            )
            
            assert len(result["items"]) == 1
            assert result["meta"]["total"] == 1
    
    @pytest.mark.asyncio
    async def test_obtener_producto_con_inventario(self, mock_session):
        """Test obtener producto individual con su inventario"""
        from app.routes.catalog import obtener_producto
        
        producto_id = str(uuid4())
        
        # Mock producto
        mock_prod_result = MagicMock()
        mock_prod = MagicMock()
        mock_prod.id = producto_id
        mock_prod.nombre = "Paracetamol"
        mock_prod_result.scalar_one_or_none.return_value = mock_prod
        
        # Mock inventario
        mock_inv_result = MagicMock()
        mock_inv = MagicMock()
        mock_inv.cantidad = 100
        mock_inv_result.scalars.return_value.all.return_value = [mock_inv]
        
        mock_session.execute = AsyncMock(side_effect=[mock_prod_result, mock_inv_result])
        
        result = await obtener_producto(producto_id=producto_id, session=mock_session)
        
        assert result.id == producto_id
        assert result.nombre == "Paracetamol"
    
    @pytest.mark.asyncio
    async def test_actualizar_producto(self, mock_session):
        """Test actualizar producto existente"""
        from app.routes.catalog import actualizar_producto
        from app.schemas import ProductUpdate
        
        producto_id = str(uuid4())
        update_data = ProductUpdate(
            nombre="Nombre Actualizado",
            precio_unitario=Decimal("2000.00")
        )
        
        mock_result = MagicMock()
        mock_prod = MagicMock()
        mock_prod.id = producto_id
        mock_result.scalar_one_or_none.return_value = mock_prod
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        result = await actualizar_producto(
            producto_id=producto_id,
            producto=update_data,
            session=mock_session
        )
        
        assert mock_prod.nombre == "Nombre Actualizado"
        assert mock_session.commit.called
    
    @pytest.mark.asyncio
    async def test_eliminar_producto_soft_delete(self, mock_session):
        """Test eliminación lógica de producto"""
        from app.routes.catalog import eliminar_producto
        
        producto_id = str(uuid4())
        mock_result = MagicMock()
        mock_prod = MagicMock()
        mock_prod.activo = True
        mock_result.scalar_one_or_none.return_value = mock_prod
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        
        result = await eliminar_producto(producto_id=producto_id, session=mock_session)
        
        assert mock_prod.activo == False
        assert mock_session.commit.called


class TestInventarioRoutesComplete:
    """Suite completa para rutas de inventario (15% -> 70%)"""
    
    @pytest.mark.asyncio
    async def test_listar_movimientos_con_filtros(self, mock_session):
        """Test listar movimientos con filtros múltiples"""
        from app.routes.inventario import listar_movimientos
        
        # Mock count
        mock_count = MagicMock()
        mock_count.scalar.return_value = 10
        
        # Mock query
        mock_query = MagicMock()
        mock_mov = MagicMock()
        mock_mov.id = 1
        mock_mov.tipo_movimiento = "INGRESO"
        mock_query.scalars.return_value.all.return_value = [mock_mov]
        
        mock_session.execute = AsyncMock(side_effect=[mock_count, mock_query])
        
        result = await listar_movimientos(
            session=mock_session,
            tipo_movimiento="INGRESO",
            pais="CO",
            page=1,
            size=10
        )
        
        assert result["meta"]["total"] == 10
        assert len(result["items"]) == 1
    
    @pytest.mark.asyncio
    async def test_obtener_movimiento_por_id(self, mock_session):
        """Test obtener movimiento específico"""
        from app.routes.inventario import obtener_movimiento
        
        movimiento_id = 123
        mock_result = MagicMock()
        mock_mov = MagicMock()
        mock_mov.id = movimiento_id
        mock_mov.tipo_movimiento = "SALIDA"
        mock_result.scalar_one_or_none.return_value = mock_mov
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await obtener_movimiento(movimiento_id=movimiento_id, session=mock_session)
        
        assert result.id == movimiento_id
        assert result.tipo_movimiento == "SALIDA"
    
    @pytest.mark.asyncio
    async def test_marcar_alerta_como_leida(self, mock_session):
        """Test marcar alerta de inventario como leída"""
        from app.routes.inventario import marcar_alerta_leida
        
        alerta_id = 456
        usuario_id = "USR001"
        
        mock_result = MagicMock()
        mock_alerta = MagicMock()
        mock_alerta.id = alerta_id
        mock_alerta.leida = False
        mock_result.scalar_one_or_none.return_value = mock_alerta
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        result = await marcar_alerta_leida(
            alerta_id=alerta_id,
            usuario_id=usuario_id,
            session=mock_session
        )
        
        assert mock_alerta.leida == True
        assert mock_alerta.leida_por == usuario_id
        assert mock_session.commit.called


class TestBodegaRoutesComplete:
    """Suite completa para rutas de bodegas (26% -> 70%)"""
    
    @pytest.mark.asyncio
    async def test_listar_bodegas_filtro_pais(self, mock_session):
        """Test listar bodegas filtradas por país"""
        from app.routes.bodega import listar_bodegas
        
        mock_count = MagicMock()
        mock_count.scalar.return_value = 3
        
        mock_query = MagicMock()
        mock_bodega = MagicMock()
        mock_bodega.codigo = "BOG01"
        mock_bodega.pais = "CO"
        mock_query.scalars.return_value.all.return_value = [mock_bodega]
        
        mock_session.execute = AsyncMock(side_effect=[mock_count, mock_query])
        
        result = await listar_bodegas(
            session=mock_session,
            pais="CO",
            page=1,
            size=10
        )
        
        assert result["meta"]["total"] == 3
        assert result["items"][0].pais == "CO"
    
    @pytest.mark.asyncio
    async def test_obtener_bodega_por_codigo(self, mock_session):
        """Test obtener bodega por código"""
        from app.routes.bodega import obtener_bodega
        
        bodega_id = str(uuid4())
        mock_result = MagicMock()
        mock_bodega = MagicMock()
        mock_bodega.id = bodega_id
        mock_bodega.codigo = "BOG01"
        mock_result.scalar_one_or_none.return_value = mock_bodega
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await obtener_bodega(bodega_id=bodega_id, session=mock_session)
        
        assert result.codigo == "BOG01"
    
    @pytest.mark.asyncio
    async def test_actualizar_bodega(self, mock_session):
        """Test actualizar información de bodega"""
        from app.routes.bodega import actualizar_bodega
        from app.schemas import BodegaUpdate
        
        bodega_id = str(uuid4())
        update_data = BodegaUpdate(
            nombre="Bodega Actualizada",
            responsable="Nuevo Responsable"
        )
        
        mock_result = MagicMock()
        mock_bodega = MagicMock()
        mock_bodega.id = bodega_id
        mock_result.scalar_one_or_none.return_value = mock_bodega
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        result = await actualizar_bodega(
            bodega_id=bodega_id,
            bodega=update_data,
            session=mock_session
        )
        
        assert mock_bodega.nombre == "Bodega Actualizada"
        assert mock_session.commit.called


class TestInventarioServiceComplete:
    """Suite completa para servicio de inventario (16% -> 70%)"""
    
    @pytest.mark.asyncio
    async def test_validar_stock_suficiente_ok(self, mock_session):
        """Test validar stock suficiente - caso exitoso"""
        from app.services.inventario_service import validar_stock_suficiente
        
        mock_result = MagicMock()
        mock_inv = MagicMock()
        mock_inv.cantidad = 100
        mock_result.scalar_one_or_none.return_value = mock_inv
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # No debe lanzar excepción
        await validar_stock_suficiente(
            session=mock_session,
            producto_id=str(uuid4()),
            bodega_id=str(uuid4()),
            pais="CO",
            cantidad_requerida=50,
            lote=""
        )
        
        assert mock_session.execute.called
    
    @pytest.mark.asyncio
    async def test_validar_stock_insuficiente(self, mock_session):
        """Test validar stock - stock insuficiente"""
        from app.services.inventario_service import validar_stock_suficiente
        
        mock_result = MagicMock()
        mock_inv = MagicMock()
        mock_inv.cantidad = 10
        mock_result.scalar_one_or_none.return_value = mock_inv
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        with pytest.raises(HTTPException) as exc:
            await validar_stock_suficiente(
                session=mock_session,
                producto_id=str(uuid4()),
                bodega_id=str(uuid4()),
                pais="CO",
                cantidad_requerida=50,
                lote=""
            )
        
        assert exc.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_actualizar_inventario_ingreso(self, mock_session):
        """Test actualizar inventario - movimiento INGRESO"""
        from app.services.inventario_service import actualizar_inventario
        
        # Mock para inventario existente
        mock_result = MagicMock()
        mock_inv = MagicMock()
        mock_inv.cantidad = 100
        mock_result.scalar_one_or_none.return_value = mock_inv
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        
        await actualizar_inventario(
            session=mock_session,
            producto_id=str(uuid4()),
            bodega_id=str(uuid4()),
            pais="CO",
            lote="",
            cantidad=50,
            tipo_movimiento="INGRESO",
            fecha_vencimiento=None
        )
        
        assert mock_inv.cantidad == 150
        assert mock_session.commit.called
    
    @pytest.mark.asyncio
    async def test_actualizar_inventario_salida(self, mock_session):
        """Test actualizar inventario - movimiento SALIDA"""
        from app.services.inventario_service import actualizar_inventario
        
        mock_result = MagicMock()
        mock_inv = MagicMock()
        mock_inv.cantidad = 100
        mock_result.scalar_one_or_none.return_value = mock_inv
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        
        await actualizar_inventario(
            session=mock_session,
            producto_id=str(uuid4()),
            bodega_id=str(uuid4()),
            pais="CO",
            lote="",
            cantidad=30,
            tipo_movimiento="SALIDA",
            fecha_vencimiento=None
        )
        
        assert mock_inv.cantidad == 70
        assert mock_session.commit.called


class TestRepositoriesComplete:
    """Suite completa para repositorios (13% -> 70%)"""
    
    @pytest.mark.asyncio
    async def test_buscar_productos_con_query(self, mock_session):
        """Test buscar productos con texto de búsqueda"""
        from app.repositories.catalog_repo import buscar_productos
        
        # Mock count
        mock_count = MagicMock()
        mock_count.scalar.return_value = 5
        
        # Mock query
        mock_query = MagicMock()
        mock_query.all.return_value = []
        
        mock_session.execute = AsyncMock(side_effect=[mock_count, mock_query])
        
        productos, total = await buscar_productos(
            session=mock_session,
            query="Paracetamol",
            limit=10,
            offset=0
        )
        
        assert total == 5
        assert isinstance(productos, list)
    
    @pytest.mark.asyncio
    async def test_buscar_productos_con_categoria(self, mock_session):
        """Test buscar productos filtrados por categoría"""
        from app.repositories.catalog_repo import buscar_productos
        
        mock_count = MagicMock()
        mock_count.scalar.return_value = 3
        
        mock_query = MagicMock()
        mock_query.all.return_value = []
        
        mock_session.execute = AsyncMock(side_effect=[mock_count, mock_query])
        
        productos, total = await buscar_productos(
            session=mock_session,
            categoria_id="CAT001",
            limit=10,
            offset=0
        )
        
        assert total == 3

