# schemas/report.py
from datetime import date
from typing import List, Optional
from pydantic import BaseModel

class Period(BaseModel):
    from_: date
    to: date

class FiltersApplied(BaseModel):
    period: Period
    vendor_id: Optional[int] = None
    product_id: Optional[int] = None

class Summary(BaseModel):
    total_sales: float
    pending_orders: int
    products_in_stock: int
    sales_change_pct_vs_prev_period: float

class TrendPoint(BaseModel):
    date: date
    total: float

class TopProduct(BaseModel):
    product_name: str
    amount: float

class Charts(BaseModel):
    trend: List[TrendPoint]
    top_products: List[TopProduct]
    others_amount: float

class TableRow(BaseModel):
    vendor_name: str
    product_name: str
    quantity: int
    revenue: float
    status: str

class Table(BaseModel):
    rows: List[TableRow]

class ExportInfo(BaseModel):
    available_formats: List[str] = ["csv", "pdf"]

class ReportResponse(BaseModel):
    filters_applied: FiltersApplied
    summary: Summary
    charts: Charts
    table: Table
    currency: str = "USD"
    export: ExportInfo = ExportInfo()
