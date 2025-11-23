import re
import pytest
from fastapi.testclient import TestClient
from app.main import app, _sha256

client = TestClient(app)

def test_sha256():
    h = _sha256("hola")
    assert re.fullmatch(r"[0-9a-f]{64}", h)

def test_get_idempotency_key_generated_when_missing():
    # Sin header: debe generarse un UUID (string no vacío)
    r = client.post("/orders", json={
        "customer_id": "C1",
        "seller_id": "399e4160-d04a-4bff-acb4-4758711257c0",  # ✅ Agregado
        "items": [],
        "created_by_role": "seller",
        "source": "bff-cliente",
        "user_name": "test_user",
        "address": {
            "street": "Av. Reforma 123",
            "city": "Ciudad de México",
            "state": "CDMX",
            "zip_code": "01000",
            "country": "México"
        }
    })
    assert r.status_code in (200, 201, 202)
    data = r.json()
    assert "request_id" in data
    assert isinstance(data["request_id"], str)
    assert len(data["request_id"]) > 0
