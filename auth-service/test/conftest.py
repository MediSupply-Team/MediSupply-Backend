# tests/conftest.py
import importlib
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app as fastapi_app
from app.database import get_db
from app.models import Base
from sqlalchemy import text

# TestClient con lifespan real
@pytest.fixture()
def client(test_engine, monkeypatch):
    """TestClient con lifespan + engine parcheado a SQLite en memoria."""
    import app.main as main_mod
    import app.database as db_mod

    monkeypatch.setattr(main_mod, "engine", test_engine, raising=True)
    monkeypatch.setattr(db_mod, "engine", test_engine, raising=True)

    with TestClient(fastapi_app) as c:
        yield c

# Engine SQLite en memoria
@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture(autouse=True)
async def cleanup_tables(test_engine):
    """Limpiar todas las tablas antes de cada test"""
    yield
    # Limpiar después del test
    async with test_engine.begin() as conn:
        # Eliminar en orden inverso por FKs
        await conn.execute(text("DELETE FROM users"))
        await conn.execute(text("DELETE FROM role_permissions"))
        await conn.execute(text("DELETE FROM roles"))
        await conn.execute(text("DELETE FROM permissions"))
        await conn.commit()

# Sesión para PRE-SEMBRAR datos
@pytest.fixture
async def test_session(test_engine):
    Session = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)
    async with Session() as s:
        try:
            yield s
        finally:
            await s.rollback()

# OVERRIDE por REQUEST
@pytest.fixture(autouse=True)
def override_db(test_engine, monkeypatch):
    Session = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)

    async def _override():
        async with Session() as s:
            yield s

    fastapi_app.dependency_overrides[get_db] = _override

    dbmod = importlib.import_module("app.database")
    monkeypatch.setattr(dbmod, "get_db", _override)

    yield
    fastapi_app.dependency_overrides.clear()
