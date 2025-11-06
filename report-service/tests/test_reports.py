
from datetime import date
from unittest.mock import MagicMock

def test_sales_performance_endpoint_unit():
    from routers.reports import sales_performance
    import services.report_service
    session = MagicMock()
    result = MagicMock()
    result.currency = "USD"
    services.report_service.get_sales_performance = MagicMock(return_value=result)
    response = sales_performance(
        period_from=date(2023, 1, 1),
        period_to=date(2023, 1, 31),
        vendor_id=None,
        product_id=None,
        session=session
    )
    assert response.currency == "USD"
