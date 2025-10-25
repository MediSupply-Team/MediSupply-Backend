# routers/reports.py
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from database import get_session
from schemas.report import ReportResponse
from services.report_service import get_sales_performance

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/sales-performance", response_model=ReportResponse)
def sales_performance(
    period_from: date = Query(..., alias="from"),
    period_to: date = Query(..., alias="to"),
    vendor_id: int | None = Query(None),
    product_id: int | None = Query(None),
    session: Session = Depends(get_session),
):
    return get_sales_performance(
        session=session,
        period_from=period_from,
        period_to=period_to,
        vendor_id=vendor_id,
        product_id=product_id,
    )

# Export CSV simple (el PDF podés dejarlo para después)
from fastapi.responses import StreamingResponse
import csv
from io import StringIO

@router.get("/sales-performance/export")
def export_sales_performance(
    period_from: date = Query(..., alias="from"),
    period_to: date = Query(..., alias="to"),
    vendor_id: int | None = Query(None),
    product_id: int | None = Query(None),
    format: str = Query("csv", pattern="^(csv|pdf)$"),
    session: Session = Depends(get_session),
):
    report = get_sales_performance(session, period_from, period_to, vendor_id, product_id)

    if format == "csv":
        buffer = StringIO()
        writer = csv.writer(buffer)
        # Encabezados
        writer.writerow(["date","trend_total"])
        for p in report.charts.trend:
            writer.writerow([p.date.isoformat(), f"{p.total:.2f}"])
        writer.writerow([])
        writer.writerow(["product_name","amount"])
        for tp in report.charts.top_products:
            writer.writerow([tp.product_name, f"{tp.amount:.2f}"])
        writer.writerow(["others_amount", f"{report.charts.others_amount:.2f}"])
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="text/csv",
                                 headers={"Content-Disposition": "attachment; filename=report.csv"})
    else:
        # placeholder simple para PDF (devuelve 501 hasta que lo implementes)
        from fastapi import HTTPException
        raise HTTPException(status_code=501, detail="PDF export not implemented yet")
