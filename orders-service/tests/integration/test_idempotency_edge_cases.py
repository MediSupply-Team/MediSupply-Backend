# tests/integration/test_idempotency_edge_cases.py
"""Tests adicionales de idempotencia para maximizar cobertura"""
import pytest
import hashlib
from sqlalchemy import delete
from app.models import IdempotencyRequest, IdemStatus, Order, OutboxEvent


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


@pytest.mark.anyio
async def test_idempotency_done_without_response_body(client, test_session, override_db):
    """
    Test: Registro idempotente DONE pero sin response_body
    Cubre rama alternativa en líneas 73-74
    """
    idem_key = "test-done-no-response-body"
    key_hash = _sha256(idem_key)
    
    body = {
        "customer_id": "Test-Customer",
        "seller_id": "test-seller",
        "items": [{"sku": "TEST-SKU", "qty": 1}],
        "created_by_role": "seller",
        "source": "test",
        "user_name": "tester"
    }
    
    from app.schemas import CreateOrderRequest
    req = CreateOrderRequest(**body)
    body_hash = _sha256(req.model_dump_json())
    
    # Limpiar
    await test_session.execute(
        delete(IdempotencyRequest).where(IdempotencyRequest.key_hash == key_hash)
    )
    await test_session.commit()
    
    # Crear registro DONE pero SIN response_body
    idem = IdempotencyRequest(
        key_hash=key_hash,
        body_hash=body_hash,
        status=IdemStatus.DONE,
        response_body=None  # ← Sin response_body
    )
    test_session.add(idem)
    await test_session.commit()
    
    # Intentar crear orden con mismo key
    r = client.post(
        "/orders",
        headers={"Idempotency-Key": idem_key},
        json=body
    )
    
    # Debería crear la orden ya que no hay response_body cacheado
    assert r.status_code == 202


@pytest.mark.anyio
async def test_idempotency_pending_different_session(client, test_session, override_db, monkeypatch):
    """
    Test: Registro PENDING en otra sesión - simula concurrencia
    Cubre manejo de IntegrityError
    """
    idem_key = "test-pending-race-condition"
    key_hash = _sha256(idem_key)
    
    body = {
        "customer_id": "Test-Concurrent",
        "seller_id": "seller-concurrent",
        "items": [{"sku": "CONCURRENT-SKU", "qty": 1}],
        "created_by_role": "seller",
        "source": "test"
    }
    
    from app.schemas import CreateOrderRequest
    req = CreateOrderRequest(**body)
    body_hash = _sha256(req.model_dump_json())
    
    # Limpiar
    await test_session.execute(
        delete(IdempotencyRequest).where(IdempotencyRequest.key_hash == key_hash)
    )
    await test_session.commit()
    
    # Pre-crear registro PENDING
    idem = IdempotencyRequest(
        key_hash=key_hash,
        body_hash=body_hash,
        status=IdemStatus.PENDING
    )
    test_session.add(idem)
    await test_session.commit()
    
    # Llamar endpoint - debería manejar el caso gracefully
    r = client.post(
        "/orders",
        headers={"Idempotency-Key": idem_key},
        json=body
    )
    
    # Debería retornar 202 sin error
    assert r.status_code == 202


@pytest.mark.anyio
async def test_order_creation_with_all_optional_fields(client):
    """
    Test: Crear orden con todos los campos opcionales incluidos
    Maximiza cobertura de la creación de orden
    """
    order = {
        "customer_id": "Full-Customer",
        "seller_id": "full-seller-id",
        "items": [
            {"sku": "FULL-1", "qty": 10},
            {"sku": "FULL-2", "qty": 20},
            {"sku": "FULL-3", "qty": 30}
        ],
        "created_by_role": "seller",
        "source": "bff-cliente",
        "user_name": "full_user",
        "address": {
            "street": "Calle Completa #123-45",
            "city": "Bogotá",
            "state": "Cundinamarca",
            "zip_code": "110111",
            "country": "Colombia"
        }
    }
    
    r = client.post(
        "/orders",
        headers={"Idempotency-Key": "test-full-order"},
        json=order
    )
    
    assert r.status_code == 202
    assert "request_id" in r.json()


@pytest.mark.anyio
async def test_order_with_minimal_fields(client):
    """
    Test: Orden con campos mínimos requeridos
    """
    order = {
        "items": [{"sku": "MIN-SKU", "qty": 1}],
        "created_by_role": "admin",
        "source": "test"
        # Sin customer_id, seller_id, user_name, address
    }
    
    r = client.post(
        "/orders",
        headers={"Idempotency-Key": "test-minimal-order"},
        json=order
    )
    
    assert r.status_code == 202


@pytest.mark.anyio
async def test_multiple_items_enrichment(client):
    """
    Test: Múltiples items son enriquecidos correctamente con precios
    Cubre lógica de enriched_items en línea 89 aproximadamente
    """
    client.delete("/clear-all")
    
    order = {
        "customer_id": "Multi-Items",
        "items": [
            {"sku": "ITEM-A", "qty": 5},
            {"sku": "ITEM-B", "qty": 10},
            {"sku": "ITEM-C", "qty": 15},
            {"sku": "ITEM-D", "qty": 20}
        ],
        "created_by_role": "seller",
        "source": "test"
    }
    
    r = client.post(
        "/orders",
        headers={"Idempotency-Key": "test-multi-items"},
        json=order
    )
    
    assert r.status_code == 202
    
    # Verificar que se creó y tiene items enriquecidos
    orders = client.get("/orders").json()
    assert len(orders) == 1
    
    created = orders[0]
    assert len(created["items"]) == 4
    
    # Todos los items deben tener price y product_name
    for item in created["items"]:
        assert "sku" in item
        assert "qty" in item
        assert "price" in item
        assert "product_name" in item
        assert item["price"] > 0


@pytest.mark.anyio
async def test_celery_task_failure_handled(client, monkeypatch):
    """
    Test: Fallo en envío de task a Celery no rompe creación de orden
    Cubre el except en línea ~123
    """
    import app.main as main_mod
    
    # Mock de Celery que lanza excepción
    class FailingCelery:
        def __init__(self):
            self.calls = []
        
        def send_task(self, *args, **kwargs):
            self.calls.append((args, kwargs))
            raise Exception("Celery connection failed")
    
    monkeypatch.setattr(main_mod, "celery", FailingCelery())
    
    order = {
        "customer_id": "Celery-Fail",
        "items": [{"sku": "CELERY-TEST", "qty": 1}],
        "created_by_role": "seller",
        "source": "test"
    }
    
    # Debería crear la orden exitosamente a pesar del fallo de Celery
    r = client.post(
        "/orders",
        headers={"Idempotency-Key": "test-celery-fail"},
        json=order
    )
    
    assert r.status_code == 202
    assert "request_id" in r.json()
