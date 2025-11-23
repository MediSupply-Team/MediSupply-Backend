# tests/integration/test_orders_endpoints.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from app.main import app
from app.models import Order, IdempotencyRequest, OutboxEvent
from uuid import UUID

client = TestClient(app)


def test_get_all_orders_empty():
    """
    Test: GET /orders cuando no hay órdenes debe retornar lista vacía
    """
    # Limpiar todo primero
    client.delete("/clear-all")
    
    r = client.get("/orders")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_all_orders_after_seed():
    """
    Test: GET /orders después de seed-data debe retornar 3 órdenes
    """
    # Limpiar y cargar datos
    client.delete("/clear-all")
    r_seed = client.post("/seed-data")
    assert r_seed.status_code == 201
    
    # Obtener todas las órdenes
    r = client.get("/orders")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 3
    
    # Verificar estructura de respuesta
    for order in data:
        assert "id" in order
        assert "customer_id" in order or "seller_id" in order  # ✅ Al menos uno debe existir
        assert "items" in order
        assert "status" in order
        assert "created_by_role" in order
        assert "source" in order
        assert "address" in order
        assert "created_at" in order


def test_get_all_orders_pagination():
    """
    Test: GET /orders con paginación limit y offset
    """
    # Limpiar y cargar datos
    client.delete("/clear-all")
    client.post("/seed-data")
    
    # Primera página (2 resultados)
    r1 = client.get("/orders?limit=2&offset=0")
    assert r1.status_code == 200
    data1 = r1.json()
    assert len(data1) == 2
    
    # Segunda página (1 resultado restante)
    r2 = client.get("/orders?limit=2&offset=2")
    assert r2.status_code == 200
    data2 = r2.json()
    assert len(data2) == 1
    
    # Verificar que son órdenes diferentes
    ids1 = {order["id"] for order in data1}
    ids2 = {order["id"] for order in data2}
    assert len(ids1.intersection(ids2)) == 0


def test_get_order_by_id_success():
    """
    Test: GET /orders/{order_id} para una orden existente
    """
    # Limpiar y cargar datos
    client.delete("/clear-all")
    client.post("/seed-data")
    
    # Obtener lista de órdenes para tener un ID válido
    r_list = client.get("/orders")
    orders = r_list.json()
    assert len(orders) > 0
    
    order_id = orders[0]["id"]
    
    # Obtener orden específica
    r = client.get(f"/orders/{order_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == order_id
    # ✅ Verificar que al menos uno de los campos existe
    assert data.get("customer_id") is not None or data.get("seller_id") is not None
    assert "items" in data
    assert "address" in data


def test_get_order_by_id_not_found():
    """
    Test: GET /orders/{order_id} para un ID que no existe debe retornar 404
    """
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    r = client.get(f"/orders/{fake_uuid}")
    assert r.status_code == 404
    assert "detail" in r.json()


def test_get_order_by_id_invalid_uuid():
    """
    Test: GET /orders/{order_id} con UUID inválido debe retornar 400
    """
    invalid_id = "not-a-valid-uuid"
    r = client.get(f"/orders/{invalid_id}")
    assert r.status_code == 400
    assert "detail" in r.json()


def test_seed_data_creates_orders():
    """
    Test: POST /seed-data crea 3 órdenes con datos predefinidos
    """
    # Limpiar primero
    client.delete("/clear-all")
    
    # Cargar datos
    r = client.post("/seed-data")
    assert r.status_code == 201
    data = r.json()
    assert "message" in data
    assert data["count"] == 3
    
    # Verificar que se crearon
    r_list = client.get("/orders")
    orders = r_list.json()
    assert len(orders) == 3
    
    # ✅ Verificar que hay 1 orden con seller_id y 2 con customer_id
    orders_with_seller = [o for o in orders if o.get("seller_id")]
    orders_with_customer = [o for o in orders if o.get("customer_id")]
    
    assert len(orders_with_seller) >= 1, "Debe haber al menos 1 orden con seller_id"
    assert len(orders_with_customer) >= 2, "Debe haber al menos 2 órdenes con customer_id"
    
    # ✅ Verificar customer_ids específicos de las órdenes que tienen customer_id
    customer_ids = [o["customer_id"] for o in orders_with_customer if o.get("customer_id")]
    assert "Clínica del Norte" in customer_ids
    # La tercera orden tiene un UUID como customer_id
    assert any("1b3e7dde" in str(cid) for cid in customer_ids if cid)
    
    # ✅ Verificar que la orden con seller_id tiene el UUID correcto
    seller_ids = [o["seller_id"] for o in orders_with_seller if o.get("seller_id")]
    assert any("399e4160" in str(sid) for sid in seller_ids if sid)
    
    # Verificar direcciones de Bogotá
    for order in orders:
        assert order["address"] is not None
        assert order["address"]["city"] == "Bogotá"
        assert order["address"]["country"] == "Colombia"


def test_seed_data_can_be_called_multiple_times():
    """
    Test: POST /seed-data puede ser llamado múltiples veces
    """
    client.delete("/clear-all")
    
    # Primera carga
    r1 = client.post("/seed-data")
    assert r1.status_code == 201
    
    # Segunda carga (no debe fallar)
    r2 = client.post("/seed-data")
    assert r2.status_code == 201
    
    # Ahora debería haber 6 órdenes
    r_list = client.get("/orders")
    orders = r_list.json()
    assert len(orders) == 6


def test_clear_all_removes_all_data():
    """
    Test: DELETE /clear-all elimina todos los registros
    """
    # Asegurar que hay datos
    client.post("/seed-data")
    r_before = client.get("/orders")
    assert len(r_before.json()) > 0
    
    # Limpiar
    r = client.delete("/clear-all")
    assert r.status_code == 200
    data = r.json()
    assert "message" in data
    assert "tables_cleared" in data
    assert len(data["tables_cleared"]) == 3
    
    # Verificar que no hay órdenes
    r_after = client.get("/orders")
    orders = r_after.json()
    assert len(orders) == 0


def test_clear_all_is_idempotent():
    """
    Test: DELETE /clear-all puede ser llamado múltiples veces sin error
    """
    # Primera limpieza
    r1 = client.delete("/clear-all")
    assert r1.status_code == 200
    
    # Segunda limpieza (no debe fallar aunque no haya datos)
    r2 = client.delete("/clear-all")
    assert r2.status_code == 200


def test_full_workflow_with_new_endpoints():
    """
    Test: Flujo completo usando todos los endpoints
    """
    # 1. Limpiar
    r_clear = client.delete("/clear-all")
    assert r_clear.status_code == 200
    
    # 2. Verificar que está vacío
    r_empty = client.get("/orders")
    assert len(r_empty.json()) == 0
    
    # 3. Cargar datos de prueba
    r_seed = client.post("/seed-data")
    assert r_seed.status_code == 201
    
    # 4. Listar órdenes
    r_list = client.get("/orders")
    assert r_list.status_code == 200
    orders = r_list.json()
    assert len(orders) == 3
    
    # 5. Obtener una orden específica
    order_id = orders[0]["id"]
    r_get = client.get(f"/orders/{order_id}")
    assert r_get.status_code == 200
    assert r_get.json()["id"] == order_id
    
    # 6. Crear una nueva orden con seller_id
    new_order_body = {
        "seller_id": "399e4160-d04a-4bff-acb4-4758711257c0",
        "customer_id": "Hospital Universitario",
        "items": [{"sku": "MED-001", "qty": 10}],
        "created_by_role": "seller",
        "source": "bff-cliente",
        "user_name": "vendedor1",
        "address": {
            "street": "Calle 100 #15-20",
            "city": "Bogotá",
            "state": "Cundinamarca",
            "zip_code": "110111",
            "country": "Colombia"
        }
    }
    r_create = client.post(
        "/orders",
        headers={"Idempotency-Key": "test-workflow-key-001"},
        json=new_order_body
    )
    assert r_create.status_code == 202
    
    # 7. Verificar que ahora hay 4 órdenes
    r_final = client.get("/orders")
    assert len(r_final.json()) == 4
    
    # 8. Limpiar todo al final
    r_cleanup = client.delete("/clear-all")
    assert r_cleanup.status_code == 200


def test_orders_list_ordered_by_created_at_desc():
    """
    Test: GET /orders retorna órdenes ordenadas por created_at descendente (más recientes primero)
    """
    client.delete("/clear-all")
    client.post("/seed-data")
    
    # Crear una orden adicional después
    new_order = {
        "customer_id": "Nueva Clínica",
        "seller_id": "399e4160-d04a-4bff-acb4-4758711257c0",
        "items": [{"sku": "NEW-001", "qty": 1}],
        "created_by_role": "seller",
        "source": "bff-cliente",
        "user_name": "vendedor_nuevo",
        "address": {
            "street": "Calle Nueva #1-1",
            "city": "Bogotá",
            "state": "Cundinamarca",
            "zip_code": "110111",
            "country": "Colombia"
        }
    }
    client.post(
        "/orders",
        headers={"Idempotency-Key": "newest-order-key"},
        json=new_order
    )
    
    # Obtener órdenes
    r = client.get("/orders")
    orders = r.json()
    
    # La orden más nueva debería estar en la posición 0
    # (asumiendo que created_at se establece al momento de creación)
    assert len(orders) == 4
    # Verificar que las fechas están en orden descendente
    created_dates = [order["created_at"] for order in orders]
    assert created_dates == sorted(created_dates, reverse=True)


def test_create_order_with_only_seller_id():
    """
    Test: Crear orden solo con seller_id (sin customer_id)
    """
    client.delete("/clear-all")
    
    order_body = {
        "seller_id": "399e4160-d04a-4bff-acb4-4758711257c0",
        "items": [{"sku": "PROD-001", "qty": 5}],
        "created_by_role": "seller",
        "source": "bff-cliente",
        "user_name": "vendedor_test",
        "address": {
            "street": "Calle Test #1-1",
            "city": "Bogotá",
            "state": "Cundinamarca",
            "zip_code": "110111",
            "country": "Colombia"
        }
    }
    
    r = client.post(
        "/orders",
        headers={"Idempotency-Key": "test-seller-only"},
        json=order_body
    )
    assert r.status_code == 202
    
    # Verificar que se creó
    r_list = client.get("/orders")
    orders = r_list.json()
    assert len(orders) == 1
    assert orders[0]["seller_id"] == "399e4160-d04a-4bff-acb4-4758711257c0"
    assert orders[0]["customer_id"] is None


def test_create_order_with_only_customer_id():
    """
    Test: Crear orden solo con customer_id (sin seller_id)
    """
    client.delete("/clear-all")
    
    order_body = {
        "customer_id": "Hospital Central",
        "items": [{"sku": "PROD-002", "qty": 3}],
        "created_by_role": "admin",
        "source": "bff-admin",
        "user_name": "admin_test",
        "address": {
            "street": "Avenida Test #2-2",
            "city": "Bogotá",
            "state": "Cundinamarca",
            "zip_code": "110222",
            "country": "Colombia"
        }
    }
    
    r = client.post(
        "/orders",
        headers={"Idempotency-Key": "test-customer-only"},
        json=order_body
    )
    assert r.status_code == 202
    
    # Verificar que se creó
    r_list = client.get("/orders")
    orders = r_list.json()
    assert len(orders) == 1
    assert orders[0]["customer_id"] == "Hospital Central"
    assert orders[0]["seller_id"] is None


def test_create_order_with_both_seller_and_customer():
    """
    Test: Crear orden con ambos seller_id y customer_id
    """
    client.delete("/clear-all")
    
    order_body = {
        "seller_id": "399e4160-d04a-4bff-acb4-4758711257c0",
        "customer_id": "Farmacia Norte",
        "items": [{"sku": "PROD-003", "qty": 10}],
        "created_by_role": "seller",
        "source": "bff-cliente",
        "user_name": "vendedor_mixto",
        "address": {
            "street": "Carrera Mixta #3-3",
            "city": "Bogotá",
            "state": "Cundinamarca",
            "zip_code": "110333",
            "country": "Colombia"
        }
    }
    
    r = client.post(
        "/orders",
        headers={"Idempotency-Key": "test-both-ids"},
        json=order_body
    )
    assert r.status_code == 202
    
    # Verificar que se creó
    r_list = client.get("/orders")
    orders = r_list.json()
    assert len(orders) == 1
    assert orders[0]["seller_id"] == "399e4160-d04a-4bff-acb4-4758711257c0"
    assert orders[0]["customer_id"] == "Farmacia Norte"
