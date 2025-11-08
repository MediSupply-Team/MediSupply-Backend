# services/report_service.py
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
from dateutil.relativedelta import relativedelta
from collections import defaultdict

from services.orders_client import orders_client
from schemas.report import (
    ReportResponse, FiltersApplied, Period, Summary, Charts,
    TrendPoint, TopProduct, Table, TableRow
)
import logging

logger = logging.getLogger(__name__)

def _as_date(dt) -> date:
    return dt.date() if isinstance(dt, datetime) else dt

def _parse_order_date(order: Dict[str, Any]) -> datetime:
    """Extrae la fecha de una orden (created_at o updated_at)"""
    created_at = order.get("created_at")
    if isinstance(created_at, str):
        return datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    return datetime.now()

def _calculate_order_revenue(order: Dict[str, Any]) -> float:
    """Calcula el revenue total de una orden basado en items"""
    items = order.get("items", [])
    total = 0.0
    for item in items:
        quantity = item.get("quantity", 0)
        price = item.get("price", 0.0)
        total += quantity * price
    return total

async def get_sales_performance(
    period_from: date,
    period_to: date,
    vendor_id: Optional[int] = None,
    product_id: Optional[int] = None,
    max_trend_points: int = 90,
    top_n_products: int = 5,
) -> ReportResponse:

    # -------- Filtros base
    stmt_base = select(Venta).where(
        Venta.fecha >= datetime.combine(period_from, datetime.min.time()),
        Venta.fecha <= datetime.combine(period_to, datetime.max.time()),
    )
    if vendor_id:
        stmt_base = stmt_base.where(Venta.vendedor_id == vendor_id)
    if product_id:
        stmt_base = stmt_base.where(Venta.producto_id == product_id)

    # -------- Summary.total_sales
    total_sales = session.exec(
        select(func.coalesce(func.sum(Venta.monto_total), 0.0))
        .where(
            Venta.fecha >= datetime.combine(period_from, datetime.min.time()),
            Venta.fecha <= datetime.combine(period_to, datetime.max.time()),
            *( [Venta.vendedor_id == vendor_id] if vendor_id else [] ),
            *( [Venta.producto_id == product_id] if product_id else [] ),
        )
    ).first()


    # -------- pending_orders
    pending_orders = session.exec(
        select(func.count(Venta.id))
        .where(
            Venta.estado == "pendiente",
            Venta.fecha >= datetime.combine(period_from, datetime.min.time()),
            Venta.fecha <= datetime.combine(period_to, datetime.max.time()),
        )
    ).first()



    # -------- products_in_stock (sum simple)
    products_in_stock = session.exec(
        select(func.coalesce(func.sum(Producto.stock), 0))
    ).first()


    # -------- sales_change_pct_vs_prev_period
    delta_days = (period_to - period_from).days + 1
    prev_from = period_from - timedelta(days=delta_days)
    prev_to = period_from - timedelta(days=1)

    prev_total = session.exec(
        select(func.coalesce(func.sum(Venta.monto_total), 0.0))
        .where(
            Venta.fecha >= datetime.combine(prev_from, datetime.min.time()),
            Venta.fecha <= datetime.combine(prev_to, datetime.max.time()),
            *( [Venta.vendedor_id == vendor_id] if vendor_id else [] ),
            *( [Venta.producto_id == product_id] if product_id else [] ),
        )
    ).first()

    change_pct = 0.0 if prev_total == 0 else (total_sales - prev_total) / prev_total



    # -------- charts.trend (agregado por día; si el rango es grande, compactá a semana/mes)
    days_span = (period_to - period_from).days + 1
    if days_span <= max_trend_points:
        # por día
        rows = session.exec(
            select(func.date(Venta.fecha), func.coalesce(func.sum(Venta.monto_total), 0.0))
            .where(
                Venta.fecha >= datetime.combine(period_from, datetime.min.time()),
                Venta.fecha <= datetime.combine(period_to, datetime.max.time()),
                *( [Venta.vendedor_id == vendor_id] if vendor_id else [] ),
                *( [Venta.producto_id == product_id] if product_id else [] ),
            )
            .group_by(func.date(Venta.fecha))
            .order_by(func.date(Venta.fecha))
        ).all()
    else:
        # por mes (también podés hacer por semana si preferís)
        rows = session.exec(
            select(func.date_trunc("month", Venta.fecha), func.coalesce(func.sum(Venta.monto_total), 0.0))
            .where(
                Venta.fecha >= datetime.combine(period_from, datetime.min.time()),
                Venta.fecha <= datetime.combine(period_to, datetime.max.time()),
                *( [Venta.vendedor_id == vendor_id] if vendor_id else [] ),
                *( [Venta.producto_id == product_id] if product_id else [] ),
            )
            .group_by(func.date_trunc("month", Venta.fecha))
            .order_by(func.date_trunc("month", Venta.fecha))
        ).all()

    trend = [TrendPoint(date=_as_date(r[0]), total=float(r[1])) for r in rows]

    # -------- charts.top_products (top N)
    top_rows = session.exec(
        select(Producto.nombre, func.coalesce(func.sum(Venta.monto_total), 0.0))
        .join(Producto, Producto.id == Venta.producto_id)
        .where(
            Venta.fecha >= datetime.combine(period_from, datetime.min.time()),
            Venta.fecha <= datetime.combine(period_to, datetime.max.time()),
            *( [Venta.vendedor_id == vendor_id] if vendor_id else [] ),
            *( [Venta.producto_id == product_id] if product_id else [] ),
        )
        .group_by(Producto.id, Producto.nombre)
        .order_by(func.sum(Venta.monto_total).desc())
        .limit(top_n_products)
    ).all()
    top_products = [TopProduct(product_name=r[0], amount=float(r[1])) for r in top_rows]
    top_sum = sum(tp.amount for tp in top_products)
    others_amount = max(0.0, float(total_sales) - float(top_sum))

    # -------- table.rows (ventas individuales sin agrupar)
    table_rows_db = session.exec(
        select(Vendedor.nombre, Producto.nombre, Venta.cantidad, Venta.monto_total, Venta.estado)
        .join(Vendedor, Vendedor.id == Venta.vendedor_id)
        .join(Producto, Producto.id == Venta.producto_id)
        .where(
            Venta.fecha >= datetime.combine(period_from, datetime.min.time()),
            Venta.fecha <= datetime.combine(period_to, datetime.max.time()),
            *( [Venta.vendedor_id == vendor_id] if vendor_id else [] ),
            *( [Venta.producto_id == product_id] if product_id else [] ),
        )
        .order_by(Venta.fecha.desc())
    ).all()

    table = Table(
        rows=[
            TableRow(
                vendor_name=r[0],
                product_name=r[1],
                quantity=int(r[2] or 0),
                revenue=float(r[3] or 0.0),
                status=(r[4] or "completado"),
            )
            for r in table_rows_db
        ]
    )

    return ReportResponse(
        filters_applied=FiltersApplied(
            period=Period(from_=period_from, to=period_to),
            vendor_id=vendor_id,
            product_id=product_id,
        ),
        summary=Summary(
            total_sales=float(total_sales),
            pending_orders=int(pending_orders),
            products_in_stock=int(products_in_stock),
            sales_change_pct_vs_prev_period=float(change_pct),
        ),
        charts=Charts(
            trend=trend,
            top_products=top_products,
            others_amount=float(others_amount),
        ),
        table=table,
        currency="USD",
    )
