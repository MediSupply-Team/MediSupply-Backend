import os
import sys
import importlib
import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True)
def clear_env():
    os.environ.pop("DATABASE_URL", None)

@patch("psycopg.connect")
def test_no_database_url(mock_connect):
    # Simula que no hay DATABASE_URL
    if "create_rutas_db" in sys.modules:
        del sys.modules["create_rutas_db"]
    with patch("builtins.print") as mock_print, pytest.raises(SystemExit):
        importlib.import_module("create_rutas_db")
        mock_print.assert_any_call("⚠️ DATABASE_URL no configurada")
        mock_connect.assert_not_called()

@patch("psycopg.connect")
def test_database_exists(mock_connect):
    os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/existentdb"
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (1,)
    if "create_rutas_db" in sys.modules:
        del sys.modules["create_rutas_db"]
    with patch("builtins.print") as mock_print, pytest.raises(SystemExit):
        importlib.import_module("create_rutas_db")
        mock_print.assert_any_call("ℹ️ Base de datos 'existentdb' ya existe")
        mock_cursor.execute.assert_any_call("SELECT 1 FROM pg_database WHERE datname = %s", ("existentdb",))

@patch("psycopg.connect")
def test_database_not_exists(mock_connect):
    os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/newdb"
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    if "create_rutas_db" in sys.modules:
        del sys.modules["create_rutas_db"]
    with patch("builtins.print") as mock_print, pytest.raises(SystemExit):
        importlib.import_module("create_rutas_db")
        mock_print.assert_any_call("📦 Creando 'newdb'...")
        mock_cursor.execute.assert_any_call('CREATE DATABASE "newdb"')
        mock_print.assert_any_call("✅ Base de datos 'newdb' creada")

@patch("psycopg.connect", side_effect=Exception("fail"))
def test_psycopg_error(mock_connect):
    os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/errordb"
    if "create_rutas_db" in sys.modules:
        del sys.modules["create_rutas_db"]
    with patch("builtins.print") as mock_print, pytest.raises(SystemExit):
        importlib.import_module("create_rutas_db")
        mock_print.assert_any_call("⚠️ Error: fail")
