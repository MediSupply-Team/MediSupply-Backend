# tests/conftest.py
import sys
from unittest.mock import MagicMock

# ========================================
# CRITICAL: Este mock DEBE estar ANTES de cualquier import de app.main
# ========================================

class MockCatalogClient:
    """Mock del CatalogClient que siempre retorna SKUs válidos"""
    
    def __init__(self):
        self.pool = None
        self.connected = False
    
    async def connect(self):
        """Simula conexión exitosa"""
        self.connected = True
        print("🟢 MockCatalogClient.connect() llamado")
    
    async def disconnect(self):
        """Simula desconexión sin errores"""
        self.connected = False
        print("🔴 MockCatalogClient.disconnect() llamado")
    
    async def validate_skus(self, skus: list) -> dict:
        """
        Mock que retorna TODOS los SKUs como válidos.
        Retorna formato: {sku: {"precio_unitario": float, "nombre": str}}
        """
        print(f"🔍 MockCatalogClient.validate_skus llamado con: {skus}")
        result = {
            sku: {
                "precio_unitario": 100.0,
                "nombre": f"Producto {sku}",
                "activo": True
            }
            for sku in skus
        }
        print(f"✅ MockCatalogClient.validate_skus retornando: {list(result.keys())}")
        return result

# Crear instancia del mock
mock_catalog_client_instance = MockCatalogClient()

# Crear módulo mock ANTES de que se importe app.catalog_client
mock_catalog_module = MagicMock()
mock_catalog_module.catalog_client = mock_catalog_client_instance
mock_catalog_module.CatalogClient = MockCatalogClient

# Insertar en sys.modules ANTES de cualquier import
sys.modules['app.catalog_client'] = mock_catalog_module

print("✅ Mock de catalog_client inyectado en sys.modules")

# ========================================
# AHORA SÍ podemos importar el resto
# ========================================

import importlib
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app as fastapi_app
from app.db import get_session
from app.models import Base

# -----------------------------
# TestClient con lifespan real
# -----------------------------
@pytest.fixture()
def client(test_engine, monkeypatch):
    """
    TestClient con lifespan + engine parcheado a SQLite en memoria.
    """
    import app.main as main_mod
    import app.db as db_mod

    # Parchar engine
    monkeypatch.setattr(main_mod, "engine", test_engine, raising=True)
    monkeypatch.setattr(db_mod, "engine", test_engine, raising=True)
    
    # Verificar que catalog_client es el mock
    print(f"🔍 catalog_client en main.py es: {type(main_mod.catalog_client)}")
    assert isinstance(main_mod.catalog_client, MockCatalogClient), \
        f"catalog_client NO es el mock! Es: {type(main_mod.catalog_client)}"

    with TestClient(fastapi_app) as c:
        yield c

# -----------------------------
# Engine SQLite en memoria
# -----------------------------
@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()

# -----------------------------
# Sesión para PRE-SEMBRAR datos
# -----------------------------
@pytest.fixture
async def test_session(test_engine):
    Session = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)
    async with Session() as s:
        try:
            yield s
        finally:
            await s.rollback()

# -----------------------------
# OVERRIDE por REQUEST
# -----------------------------
@pytest.fixture(autouse=True)
def override_db(test_engine, monkeypatch):
    Session = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)

    async def _override():
        async with Session() as s:
            yield s

    fastapi_app.dependency_overrides[get_session] = _override
    dbmod = importlib.import_module("app.db")
    monkeypatch.setattr(dbmod, "get_session", _override)

    yield
    fastapi_app.dependency_overrides.clear()

# -----------------------------
# Redis falso
# -----------------------------
@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    import fakeredis, redis
    r = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(redis, "Redis", lambda *a, **k: r)
    return r

# -----------------------------
# Celery dummy
# -----------------------------
@pytest.fixture(autouse=True)
def _replace_celery_object(monkeypatch):
    main = importlib.import_module("app.main")

    class _DummyCelery:
        def __init__(self):
            self.calls = []
        def send_task(self, name, args=None, kwargs=None, **kw):
            self.calls.append((name, args, kwargs))
            return None

    monkeypatch.setattr(main, "celery", _DummyCelery())
