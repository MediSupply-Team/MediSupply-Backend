from datetime import date
from unittest.mock import MagicMock, patch
import pytest

from routers.reports import sales_performance, export_sales_performance

@patch('services.report_service.get_sales_performance')
def test_sales_performance_endpoint(mock_get_sales):
    session = MagicMock()
    mock_get_sales.return_value = MagicMock(currency="USD")
    result = sales_performance(
        period_from=date(2023, 1, 1),
        period_to=date(2023, 1, 31),
        vendor_id=None,
        product_id=None,
        session=session
    )
    assert result.currency == "USD"

@patch('services.report_service.get_sales_performance')
@patch('services.export_service.generate_csv')
@patch('services.s3_service.s3_service.upload_file', return_value="https://s3-url")
def test_export_sales_performance_csv(mock_upload, mock_csv, mock_get_sales):
    session = MagicMock()
    mock_get_sales.return_value = MagicMock()
    mock_csv.return_value = b"csvdata"
    result = export_sales_performance(
        period_from=date(2023, 1, 1),
        period_to=date(2023, 1, 31),
        vendor_id=None,
        product_id=None,
        format="csv",
        session=session
    )
    assert result.url == "https://s3-url"
    assert result.format == "csv"
    assert "Reporte generado exitosamente" in result.message

@patch('services.report_service.get_sales_performance')
@patch('services.export_service.generate_pdf')
@patch('services.s3_service.s3_service.upload_file', return_value="https://s3-url")
def test_export_sales_performance_pdf(mock_upload, mock_pdf, mock_get_sales):
    session = MagicMock()
    mock_get_sales.return_value = MagicMock()
    mock_pdf.return_value = b"pdfdata"
    result = export_sales_performance(
        period_from=date(2023, 1, 1),
        period_to=date(2023, 1, 31),
        vendor_id=None,
        product_id=None,
        format="pdf",
        session=session
    )
    assert result.url == "https://s3-url"
    assert result.format == "pdf"
    assert "Reporte generado exitosamente" in result.message

@patch('services.report_service.get_sales_performance')
def test_export_sales_performance_invalid_format(mock_get_sales):
    session = MagicMock()
    mock_get_sales.return_value = MagicMock()
    with pytest.raises(Exception) as exc:
        export_sales_performance(
            period_from=date(2023, 1, 1),
            period_to=date(2023, 1, 31),
            vendor_id=None,
            product_id=None,
            format="xlsx",
            session=session
        )
    assert "Formato no soportado" in str(exc.value)

@patch('services.report_service.get_sales_performance', side_effect=Exception("fail"))
def test_export_sales_performance_error(mock_get_sales):
    session = MagicMock()
    with pytest.raises(Exception) as exc:
        export_sales_performance(
            period_from=date(2023, 1, 1),
            period_to=date(2023, 1, 31),
            vendor_id=None,
            product_id=None,
            format="csv",
            session=session
        )
    assert "Error al generar y subir el reporte" in str(exc.value)
