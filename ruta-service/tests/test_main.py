def test_obtener_ruta_una_visita(client):
    visita = MagicMock(hora="08:00", dict=lambda: {"id": 1, "hora": "08:00"})
    mock_session = MagicMock()
    mock_session.exec.return_value.all.return_value = [visita]
    def override_get_session():
        yield mock_session
    app.dependency_overrides[main_module.get_session] = override_get_session
    response = client.get("/api/ruta", params={"fecha": "2025-01-01", "vendedor_id": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data["visitas"]) == 1
    assert data["visitas"][0]["hora"] == "08:00"
    assert data["visitas"][0]["tiempo_desde_anterior"] is None
    app.dependency_overrides = {}
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../')
import pytest
from fastapi.testclient import TestClient
from main import app

from unittest.mock import MagicMock
import main as main_module

@pytest.fixture
def client():
    return TestClient(app)

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}

def test_obtener_ruta_empty(client):
    # Mockear la sesión para evitar conexión real
    mock_session = MagicMock()
    mock_session.exec.return_value.all.return_value = []
    def override_get_session():
        yield mock_session
    app.dependency_overrides[main_module.get_session] = override_get_session
    response = client.get("/api/ruta", params={"fecha": "2025-01-01", "vendedor_id": 999})
    assert response.status_code == 200
    data = response.json()
    assert data["fecha"] == "2025-01-01"
    assert isinstance(data["visitas"], list)
    assert len(data["visitas"]) == 0
    app.dependency_overrides = {}

def test_obtener_ruta_con_datos(client):
    # Simular visitas en la base de datos
    visitas = [
        MagicMock(hora="09:00", dict=lambda: {"id": 1, "hora": "09:00"}),
        MagicMock(hora="10:00", dict=lambda: {"id": 2, "hora": "10:00"}),
        MagicMock(hora="11:00", dict=lambda: {"id": 3, "hora": "11:00"}),
    ]
    mock_session = MagicMock()
    mock_session.exec.return_value.all.return_value = visitas
    def override_get_session():
        yield mock_session
    app.dependency_overrides[main_module.get_session] = override_get_session
    response = client.get("/api/ruta", params={"fecha": "2025-01-01", "vendedor_id": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["fecha"] == "2025-01-01"
    assert isinstance(data["visitas"], list)
    assert len(data["visitas"]) == 3
    # Verificar orden y campo tiempo_desde_anterior
    assert data["visitas"][0]["hora"] == "09:00"
    assert data["visitas"][0]["tiempo_desde_anterior"] is None
    assert data["visitas"][1]["hora"] == "10:00"
    assert data["visitas"][1]["tiempo_desde_anterior"] == "15 min"
    assert data["visitas"][2]["hora"] == "11:00"
    assert data["visitas"][2]["tiempo_desde_anterior"] == "15 min"
    app.dependency_overrides = {}

def test_obtener_ruta_invalid_params(client):
    response = client.get("/api/ruta", params={"fecha": "2025-01-01"})
    assert response.status_code == 422
