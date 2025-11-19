# tests/test_health.py
from fastapi.testclient import TestClient
from app.main import app

def test_root():
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "message" in data
    assert data["status"] == "running"

def test_health_check():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert data["service"] == "auth-service"
