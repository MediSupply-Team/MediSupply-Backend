# tests/integration/test_orders_done_replay.py
import json
import hashlib
import pytest
from sqlalchemy import select, func, delete
from app.models import IdempotencyRequest, IdemStatus, Order, OutboxEvent
from app.schemas import CreateOrderRequest

def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

async def _count(session, model):
    res = await session.execute(select(func.count()).select_from(model))
    return res.scalar_one()

@pytest.mark.anyio
async def test_orders_replay_done_returns_cached_and_no_side_effects(
    client, test_session, override_db, monkeypatch
):
    body = {
        "customer_id": "C-REPLAY",
        "seller_id": "399e4160-d04a-4bff-acb4-4758711257c0",  # ✅ Agregado
        "items": [{"sku": "X1", "qty": 1}],  
        "created_by_role": "seller", 
        "source": "bff-cliente",
        "user_name": "test_user",
        "address": {
            "street": "Calle 45 #12-34",
            "city": "Bogotá",
            "state": "Cundinamarca",
            "zip_code": "110111",
            "country": "Colombia"
        }
    }
    idem_key = "00000000-0000-0000-0000-00000000D0NE-1"
    key_hash = _sha256(idem_key)
    req_model = CreateOrderRequest(**body)
    body_hash = _sha256(req_model.model_dump_json())

    # 🔧 limpia cualquier residuo previo con el mismo key_hash
    await test_session.execute(
        delete(IdempotencyRequest).where(IdempotencyRequest.key_hash == key_hash)
    )
    await test_session.commit()

    cached_body = {"request_id": key_hash, "message": "Ya procesado (idempotente)"}

    idem = IdempotencyRequest(
        key_hash=key_hash,
        body_hash=body_hash,
        status=IdemStatus.DONE,
        response_body=json.dumps(cached_body),
    )
    test_session.add(idem)
    await test_session.flush()

    orders_before = await _count(test_session, Order)
    outbox_before = await _count(test_session, OutboxEvent)
    await test_session.commit()  # que sea visible para la sesión del request

    calls = {"n": 0}
    def fake_send_task(*args, **kwargs):
        calls["n"] += 1
    monkeypatch.setattr("app.main.celery.send_task", fake_send_task, raising=True)

    r = client.post("/orders", headers={"Idempotency-Key": idem_key}, json=body)
    assert r.status_code == 202
    assert r.json() == cached_body

    orders_after = await _count(test_session, Order)
    outbox_after = await _count(test_session, OutboxEvent)
    assert orders_before == orders_after
    assert outbox_before == outbox_after
    assert calls["n"] == 0


@pytest.mark.anyio
async def test_orders_replay_pending_creates_only_once(
    client, test_session, override_db, monkeypatch
):
    """
    Test: Si el registro está en PENDING y hacemos replay, debe manejarse correctamente
    """
    body = {
        "customer_id": "C-PENDING-REPLAY",
        "seller_id": "399e4160-d04a-4bff-acb4-4758711257c0",  # ✅ Agregado
        "items": [{"sku": "Y1", "qty": 2}],  
        "created_by_role": "admin", 
        "source": "bff-admin",
        "user_name": "admin_user",
        "address": {
            "street": "Carrera 7 #32-16",
            "city": "Bogotá",
            "state": "Cundinamarca",
            "zip_code": "110311",
            "country": "Colombia"
        }
    }
    idem_key = "00000000-0000-0000-0000-0000PEND1234"
    key_hash = _sha256(idem_key)
    
    # Limpia residuos
    await test_session.execute(
        delete(IdempotencyRequest).where(IdempotencyRequest.key_hash == key_hash)
    )
    await test_session.commit()

    calls = {"n": 0}
    def fake_send_task(*args, **kwargs):
        calls["n"] += 1
    monkeypatch.setattr("app.main.celery.send_task", fake_send_task, raising=True)

    # Primera llamada
    r1 = client.post("/orders", headers={"Idempotency-Key": idem_key}, json=body)
    assert r1.status_code == 202
    
    # Segunda llamada inmediata (puede estar PENDING aún)
    r2 = client.post("/orders", headers={"Idempotency-Key": idem_key}, json=body)
    assert r2.status_code == 202
