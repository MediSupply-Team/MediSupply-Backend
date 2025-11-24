"""
Configuración de fixtures para tests de cliente-service
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from fastapi.testclient import TestClient
from uuid import uuid4

# Test database URL using SQLite for fast tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///test_cliente.db"

@pytest.fixture
def mock_session():
    """Mock de sesión de base de datos para tests unitarios"""
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.rollback = AsyncMock()
    return session

@pytest.fixture
def mock_cliente():
    """Mock de un cliente para tests"""
    cliente = MagicMock()
    cliente.id = uuid4()
    cliente.nit = "123456789"
    cliente.nombre = "Cliente Test"
    cliente.email = "cliente@test.com"
    cliente.telefono = "+57 1 1234567"
    cliente.codigo_unico = "ABC123"
    cliente.activo = True
    cliente.vendedor_id = None
    return cliente

@pytest.fixture
def mock_vendedor():
    """Mock de un vendedor para tests"""
    vendedor = MagicMock()
    vendedor.id = uuid4()
    vendedor.identificacion = "987654321"
    vendedor.nombre = "Vendedor"
    vendedor.apellido = "Test"
    vendedor.email = "vendedor@test.com"
    vendedor.username = "vendedortest"
    vendedor.telefono = "+57 1 7654321"
    vendedor.activo = True
    return vendedor

@pytest.fixture
def sample_cliente_data():
    """Datos de ejemplo para crear un cliente"""
    return {
        "nit": "123456789",
        "nombre": "Cliente de Prueba",
        "email": "cliente@test.com",
        "telefono": "+57 1 1234567",
        "direccion": "Calle 123 #45-67",
        "ciudad": "Bogotá",
        "pais": "CO",
        "activo": True
    }

@pytest.fixture
def sample_vendedor_data():
    """Datos de ejemplo para crear un vendedor"""
    return {
        "identificacion": "987654321",
        "nombre": "Vendedor",
        "apellido": "De Prueba",
        "email": "vendedor@test.com",
        "telefono": "+57 1 7654321",
        "pais": "CO",
        "username": "vendedortest",
        "password_hash": "$2b$12$testhashedpassword",
        "activo": True
    }

# Marker for async tests
pytest_plugins = ('pytest_asyncio',)

