# tests/integration/test_health_coverage.py
"""Tests adicionales para mejorar cobertura del endpoint /health"""
import pytest


def test_health_ok(client):
    """
    Test: /health retorna OK cuando DB está bien
    """
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["db"] == "ok"


def test_health_endpoint_structure(client):
    """
    Test: Verificar estructura completa de respuesta de health
    """
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    
    # Verificar que tiene los campos requeridos
    assert "status" in data
    assert "db" in data
    
    # Tipos correctos
    assert isinstance(data["status"], str)
    assert isinstance(data["db"], str)


def test_health_multiple_calls(client):
    """
    Test: Health check puede ser llamado múltiples veces
    """
    for _ in range(5):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
