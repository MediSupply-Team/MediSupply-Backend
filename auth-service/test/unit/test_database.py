# test/unit/test_database.py
from app.database import get_async_url

def test_get_async_url_postgresql():
    """Test: Conversión de URL PostgreSQL a asyncpg"""
    url = "postgresql://user:pass@localhost/db"
    result = get_async_url(url)
    assert result == "postgresql+asyncpg://user:pass@localhost/db"

def test_get_async_url_already_async():
    """Test: URL ya async no se modifica"""
    url = "postgresql+asyncpg://user:pass@localhost/db"
    result = get_async_url(url)
    assert result == url

def test_get_async_url_other_driver():
    """Test: Otros drivers no se modifican"""
    url = "sqlite:///./test.db"
    result = get_async_url(url)
    assert result == "sqlite:///./test.db"