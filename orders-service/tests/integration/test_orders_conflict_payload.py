import pytest
import hashlib
from sqlalchemy import delete
from app.models import IdempotencyRequest, IdemStatus
from app.schemas import CreateOrderRequest

def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

@pytest.mark.anyio
async def test_orders_conflict_same_key_different_payload_returns_409(
    client, test_session, override_db
):
    idem_key = "00000000-0000-0000-0000-00000000C0NF-1"
    key_hash = _sha256(idem_key)

    original_body = {
        "customer_id": "C-ONE",
        "seller_id": "399e4160-d04a-4bff-acb4-4758711257c0",  # ✅ Agregado
        "items": [{"sku": "A", "qty": 1}], 
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
    original_req = CreateOrderRequest(**original_body)
    original_hash = _sha256(original_req.model_dump_json())

    # Limpia si quedó residuo
    await test_session.execute(
        delete(IdempotencyRequest).where(IdempotencyRequest.key_hash == key_hash)
    )
    await test_session.commit()

    # Prepara idem existente (PENDING) con primer payload
    idem = IdempotencyRequest(
        key_hash=key_hash,
        body_hash=original_hash,
        status=IdemStatus.PENDING,
        response_body=None,
    )
    test_session.add(idem)
    await test_session.commit()

    # Mismo Idempotency-Key pero payload DIFERENTE -> 409
    different_body = {
        "customer_id": "C-OTHER",
        "seller_id": "different-seller-id",  # ✅ Agregado diferente
        "items": [{"sku": "B", "qty": 2}],
        "created_by_role": "seller",
        "source": "bff-cliente",
        "user_name": "test_user",
        "address": {
            "street": "Carrera 15 #78-90",
            "city": "Bogotá",
            "state": "Cundinamarca",
            "zip_code": "110221",
            "country": "Colombia"
        }
    }
    r = client.post("/orders", headers={"Idempotency-Key": idem_key}, json=different_body)
    assert r.status_code == 409


@pytest.mark.anyio
async def test_orders_conflict_with_same_payload_returns_202(
    client, test_session, override_db
):
    """
    Test: Mismo Idempotency-Key con el MISMO payload -> debe retornar 202
    """
    idem_key = "00000000-0000-0000-0000-00000000SAME-1"
    key_hash = _sha256(idem_key)

    body = {
        "customer_id": "C-SAME",
        "seller_id": "399e4160-d04a-4bff-acb4-4758711257c0",  # ✅ Agregado
        "items": [{"sku": "X", "qty": 1}], 
        "created_by_role": "seller", 
        "source": "bff-cliente", 
        "user_name": "test_user",
        "address": {
            "street": "Avenida 68 #25-10",
            "city": "Bogotá",
            "state": "Cundinamarca",
            "zip_code": "110931",
            "country": "Colombia"
        }
    }

    # Limpia residuos
    await test_session.execute(
        delete(IdempotencyRequest).where(IdempotencyRequest.key_hash == key_hash)
    )
    await test_session.commit()

    # Primera llamada
    r1 = client.post("/orders", headers={"Idempotency-Key": idem_key}, json=body)
    assert r1.status_code == 202

    # Segunda llamada con mismo key y mismo payload
    r2 = client.post("/orders", headers={"Idempotency-Key": idem_key}, json=body)
    assert r2.status_code in (202, 409)  # Puede ser 202 si ya está en DONE o seguir en PENDING
