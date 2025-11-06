from unittest.mock import patch, MagicMock
import builtins
import sys

# Para importar el script como módulo
import importlib.util
import os

def run_script():
    script_path = os.path.join(os.path.dirname(__file__), '../create_reports_db.py')
    spec = importlib.util.spec_from_file_location("create_reports_db", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

@patch('psycopg.connect')
@patch('os.getenv')
def test_create_reports_db_creates_db(mock_getenv, mock_connect):
    # Simular DATABASE_URL
    mock_getenv.return_value = 'postgresql://user:pass@localhost:5432/reports'
    # Mockear conexión y cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    # Simular que la base de datos no existe
    mock_cursor.fetchone.return_value = None
    # Capturar prints
    with patch.object(builtins, 'print') as mock_print:
        try:
            run_script()
        except SystemExit:
            pass
        # Verificar que se intentó crear la base de datos
        mock_cursor.execute.assert_any_call('CREATE DATABASE "reports"')
        mock_print.assert_any_call("📦 Creando 'reports'...")
        mock_print.assert_any_call("✅ Base de datos 'reports' creada")

@patch('psycopg.connect')
@patch('os.getenv')
def test_create_reports_db_exists(mock_getenv, mock_connect):
    mock_getenv.return_value = 'postgresql://user:pass@localhost:5432/reports'
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    # Simular que la base de datos ya existe
    mock_cursor.fetchone.return_value = (1,)
    with patch.object(builtins, 'print') as mock_print:
        try:
            run_script()
        except SystemExit:
            pass
        mock_print.assert_any_call("ℹ️ Base de datos 'reports' ya existe")
