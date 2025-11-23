# tests/integration/test_lifecycle_and_edge_cases.py
"""Tests para lifecycle hooks y casos edge que mejoran cobertura"""
import pytest


def test_startup_and_shutdown_hooks(client):
    """
    Test: Verificar que startup y shutdown se ejecutan correctamente
    Mejora cobertura de líneas 168-171, 257-260
    El fixture client ya ejecuta startup/shutdown automáticamente
    """
    # Durante el uso del fixture, startup ya se ejecutó
    r = client.get("/health")
    assert r.status_code == 200
    # Al terminar el test, shutdown se ejecutará automáticamente


def test_get_all_orders_with_custom_limit(client):
    """
    Test: GET /orders con diferentes valores de limit y offset
    Mejora cobertura de líneas 112-114, 119-120
    """
    # Limpiar y cargar datos
    client.delete("/clear-all")
    client.post("/seed-data")
    
    # Test con limit=1
    r = client.get("/orders?limit=1&offset=0")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    
    # Test con limit=10
    r = client.get("/orders?limit=10&offset=0")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 3  # Solo hay 3 en seed
    
    # Test con offset mayor que total
    r = client.get("/orders?limit=10&offset=100")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 0


def test_get_order_by_id_not_found_coverage(client):
    """
    Test: GET /orders/{id} cuando la orden no existe
    Mejora cobertura de línea 140
    """
    fake_uuid = "00000000-0000-0000-0000-000000000999"
    r = client.get(f"/orders/{fake_uuid}")
    
    assert r.status_code == 404
    assert "detail" in r.json()
    assert "no encontrada" in r.json()["detail"].lower()


def test_seed_data_multiple_times(client):
    """
    Test: Llamar seed-data múltiples veces
    Mejora cobertura de línea 243
    """
    client.delete("/clear-all")
    
    # Primera vez
    r1 = client.post("/seed-data")
    assert r1.status_code == 201
    assert r1.json()["count"] == 3
    
    # Segunda vez
    r2 = client.post("/seed-data")
    assert r2.status_code == 201
    assert r2.json()["count"] == 3
    
    # Verificar que hay 6 órdenes
    r_list = client.get("/orders")
    assert len(r_list.json()) == 6


def test_create_order_without_address(client):
    """
    Test: Crear orden sin dirección (campo opcional)
    """
    order = {
        "customer_id": "Test-Customer",
        "seller_id": "test-seller-id",
        "items": [{"sku": "TEST-001", "qty": 1}],
        "created_by_role": "admin",
        "source": "test",
        "user_name": "tester"
        # Sin address
    }
    
    r = client.post(
        "/orders",
        headers={"Idempotency-Key": "test-no-address"},
        json=order
    )
    
    assert r.status_code == 202
    assert "request_id" in r.json()


def test_create_order_without_user_name(client):
    """
    Test: Crear orden sin user_name (campo opcional)
    """
    order = {
        "customer_id": "Test-Customer",
        "items": [{"sku": "TEST-002", "qty": 1}],
        "created_by_role": "admin",
        "source": "test"
        # Sin user_name
    }
    
    r = client.post(
        "/orders",
        headers={"Idempotency-Key": "test-no-username"},
        json=order
    )
    
    assert r.status_code == 202


def test_create_order_items_enrichment(client):
    """
    Test: Verificar que los items se enriquecen con precio del catálogo
    El mock de catalog_client debería agregar precio
    """
    client.delete("/clear-all")
    
    order = {
        "customer_id": "Test-Customer",
        "items": [
            {"sku": "PROD-RICH-001", "qty": 5},
            {"sku": "PROD-RICH-002", "qty": 3}
        ],
        "created_by_role": "seller",
        "source": "test"
    }
    
    r = client.post(
        "/orders",
        headers={"Idempotency-Key": "test-enrichment"},
        json=order
    )
    
    assert r.status_code == 202
    
    # Obtener la orden y verificar enriquecimiento
    orders = client.get("/orders").json()
    assert len(orders) > 0
    
    created_order = orders[0]
    # Los items deberían tener 'price' y 'product_name' del mock
    for item in created_order["items"]:
        assert "price" in item
        assert "product_name" in item
        assert item["price"] == 100.0  # Valor del mock


def test_get_all_orders_default_pagination(client):
    """
    Test: GET /orders sin parámetros usa valores por defecto
    """
    client.delete("/clear-all")
    client.post("/seed-data")
    
    # Sin parámetros - debería usar limit=100, offset=0
    r = client.get("/orders")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 3  # Total en seed


def test_orders_empty_list_format(client):
    """
    Test: Verificar formato de lista vacía
    """
    client.delete("/clear-all")
    
    r = client.get("/orders")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 0
