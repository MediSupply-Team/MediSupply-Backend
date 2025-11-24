# tests/integration/test_catalog_validation.py
"""Tests específicos para validación de catálogo - Mejora cobertura líneas 56-57"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock


@pytest.fixture
def client_with_partial_catalog(monkeypatch, test_engine):
    """
    Cliente con mock de catalog que retorna algunos SKUs como inválidos
    """
    import app.main as main_mod
    import app.db as db_mod
    
    # Parchar engine
    monkeypatch.setattr(main_mod, "engine", test_engine, raising=True)
    monkeypatch.setattr(db_mod, "engine", test_engine, raising=True)
    
    # Mock que solo retorna algunos SKUs como válidos
    async def mock_validate_with_invalid(skus):
        """Solo el primer SKU es válido"""
        valid_skus = skus[:1]  # Solo el primero
        return {
            sku: {
                "precio_unitario": 100.0,
                "nombre": f"Producto {sku}",
                "activo": True
            }
            for sku in valid_skus
        }
    
    # Parchar el catalog_client
    monkeypatch.setattr(
        main_mod.catalog_client,
        'validate_skus',
        mock_validate_with_invalid
    )
    
    with TestClient(main_mod.app) as c:
        yield c


def test_create_order_with_invalid_skus(client_with_partial_catalog):
    """
    Test: Crear orden con SKUs que no existen en catálogo
    Cubre líneas 56-57 en main.py (logging y raise HTTPException)
    """
    order = {
        "customer_id": "Test-Customer",
        "seller_id": "test-seller",
        "items": [
            {"sku": "VALID-SKU", "qty": 1},      # Este es válido
            {"sku": "INVALID-SKU-1", "qty": 2},  # Este NO
            {"sku": "INVALID-SKU-2", "qty": 3}   # Este NO
        ],
        "created_by_role": "seller",
        "source": "test"
    }
    
    r = client_with_partial_catalog.post(
        "/orders",
        headers={"Idempotency-Key": "test-invalid-skus"},
        json=order
    )
    
    # Debe rechazar con 400
    assert r.status_code == 400
    data = r.json()
    assert "detail" in data
    assert "no existen" in data["detail"].lower() or "activos" in data["detail"].lower()
    # Verificar que menciona los SKUs inválidos
    assert "INVALID-SKU" in data["detail"]


def test_create_order_all_skus_invalid(client_with_partial_catalog):
    """
    Test: Todos los SKUs son inválidos
    """
    order = {
        "customer_id": "Test-Customer",
        "items": [
            {"sku": "FAKE-1", "qty": 1},
            {"sku": "FAKE-2", "qty": 2}
        ],
        "created_by_role": "admin",
        "source": "test"
    }
    
    r = client_with_partial_catalog.post(
        "/orders",
        headers={"Idempotency-Key": "test-all-invalid"},
        json=order
    )
    
    assert r.status_code == 400
    assert "FAKE-1" in r.json()["detail"] or "FAKE-2" in r.json()["detail"]


def test_create_order_empty_catalog_response(monkeypatch, test_engine):
    """
    Test: Catálogo retorna respuesta vacía
    """
    import app.main as main_mod
    import app.db as db_mod
    
    monkeypatch.setattr(main_mod, "engine", test_engine, raising=True)
    monkeypatch.setattr(db_mod, "engine", test_engine, raising=True)
    
    # Mock que retorna diccionario vacío
    async def mock_validate_empty(skus):
        return {}  # Ningún SKU válido
    
    monkeypatch.setattr(
        main_mod.catalog_client,
        'validate_skus',
        mock_validate_empty
    )
    
    with TestClient(main_mod.app) as client:
        order = {
            "customer_id": "Test",
            "items": [{"sku": "ANY-SKU", "qty": 1}],
            "created_by_role": "seller",
            "source": "test"
        }
        
        r = client.post(
            "/orders",
            headers={"Idempotency-Key": "test-empty-catalog"},
            json=order
        )
        
        assert r.status_code == 400
        assert "ANY-SKU" in r.json()["detail"]
