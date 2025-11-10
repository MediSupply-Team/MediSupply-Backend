# services/report_service.py
"""
Servicio de generación de reportes basado en datos reales de la base de datos de Orders
"""
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict
import logging

from services.database_client import db_client
from schemas.report import (
    ReportResponse, FiltersApplied, Period, Summary, Charts,
    TrendPoint, TopProduct, Table, TableRow
)

logger = logging.getLogger(__name__)

def _as_date(dt) -> date:
    """Convierte datetime a date"""
    return dt.date() if isinstance(dt, datetime) else dt

def _parse_order_date(order: Dict[str, Any]) -> datetime:
    """Extrae la fecha de una orden"""
    created_at = order.get("created_at")
    if isinstance(created_at, str):
        # Maneja formato ISO con Z o timezone
        return datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    elif isinstance(created_at, datetime):
        return created_at
    return datetime.now()

def _calculate_order_revenue(order: Dict[str, Any], products: Dict[str, Dict[str, Any]]) -> float:
    """Calcula el revenue total de una orden basado en items usando precios del catálogo"""
    items = order.get("items", [])
    total = 0.0
    for item in items:
        # El campo puede ser 'sku' o 'codigo' dependiendo de la fuente
        codigo = item.get("sku") or item.get("codigo")
        quantity = item.get("qty", 0)
        
        # Obtener precio del catálogo si existe, sino usar el precio del item
        price = 0.0
        if codigo and codigo in products:
            price = products[codigo].get("precio_unitario", 0.0)
        else:
            # Fallback al precio en el item
            price = item.get("price", 0.0)
        
        total += quantity * price
    return round(total, 2)

def _filter_orders_by_date(
    orders: List[Dict[str, Any]],
    from_date: date,
    to_date: date
) -> List[Dict[str, Any]]:
    """Filtra órdenes por rango de fechas"""
    filtered = []
    for order in orders:
        order_date = _parse_order_date(order)
        if from_date <= order_date.date() <= to_date:
            filtered.append(order)
    return filtered

async def get_sales_performance(
    period_from: date,
    period_to: date,
    vendor_id: Optional[int] = None,
    product_id: Optional[int] = None,
    max_trend_points: int = 90,
    top_n_products: int = 5,
) -> ReportResponse:
    """
    Genera reporte de desempeño de ventas basado en datos reales de Orders
    
    Args:
        period_from: Fecha de inicio del período
        period_to: Fecha fin del período
        vendor_id: ID del vendedor (opcional, no implementado aún)
        product_id: ID del producto (opcional)
        max_trend_points: Máximo número de puntos en el gráfico de tendencia
        top_n_products: Número de productos top a mostrar
        
    Returns:
        ReportResponse con todas las métricas y datos
    """
    try:
        # Obtener órdenes directamente de la base de datos
        logger.info(f"Obteniendo órdenes desde {period_from} hasta {period_to}")
        
        # Convertir dates a datetime para la query
        start_datetime = datetime.combine(period_from, datetime.min.time())
        end_datetime = datetime.combine(period_to, datetime.max.time())
        
        all_orders = await db_client.get_orders(
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        # Filtrar por fechas (validación adicional)
        orders = _filter_orders_by_date(all_orders, period_from, period_to)
        
        # Obtener todos los SKUs únicos de las órdenes
        all_skus = set()
        for order in orders:
            items = order.get("items", [])
            for item in items:
                # El campo puede ser 'sku' o 'codigo' 
                codigo = item.get("sku") or item.get("codigo")
                if codigo:
                    all_skus.add(codigo)
        
        # Obtener productos del catálogo
        logger.info(f"Obteniendo productos del catálogo para {len(all_skus)} SKUs")
        products = await db_client.get_products_by_skus(list(all_skus))
        logger.info(f"Obtenidos {len(products)} productos del catálogo")
        
        # Filtrar por product_id si se especifica
        if product_id:
            filtered_orders = []
            for order in orders:
                items = order.get("items", [])
                for item in items:
                    if str(item.get("sku")) == str(product_id):
                        filtered_orders.append(order)
                        break
            orders = filtered_orders
        
        logger.info(f"Total de órdenes obtenidas: {len(orders)}")
        
        # -------- SUMMARY: Total Sales --------
        total_sales = sum(_calculate_order_revenue(order, products) for order in orders)
        
        # -------- SUMMARY: Pending Orders --------
        pending_orders = sum(
            1 for order in orders 
            if order.get("status", "").upper() in ["NEW", "VALIDATED", "CONFIRMED", "PROCESSING", "ON_HOLD"]
        )
        
        # -------- SUMMARY: Products in Stock --------
        # TODO: Esto debería venir del servicio de Catálogo/Inventario
        # Por ahora, usamos un valor placeholder
        products_in_stock = 0  # Placeholder
        
        # -------- SUMMARY: Sales Change vs Previous Period --------
        delta_days = (period_to - period_from).days + 1
        prev_from = period_from - timedelta(days=delta_days)
        prev_to = period_from - timedelta(days=1)
        
        # Convertir dates a datetime para la query del período anterior
        prev_start_datetime = datetime.combine(prev_from, datetime.min.time())
        prev_end_datetime = datetime.combine(prev_to, datetime.max.time())
        
        prev_orders = await db_client.get_orders(
            start_date=prev_start_datetime,
            end_date=prev_end_datetime
        )
        prev_orders = _filter_orders_by_date(prev_orders, prev_from, prev_to)
        prev_total = sum(_calculate_order_revenue(order, products) for order in prev_orders)
        
        sales_change_pct = 0.0
        if prev_total > 0:
            sales_change_pct = round((total_sales - prev_total) / prev_total, 4)
        
        # -------- CHARTS: Trend (agregado por día o mes) --------
        days_span = (period_to - period_from).days + 1
        
        # Agrupar ventas por fecha
        sales_by_date: Dict[date, float] = defaultdict(float)
        for order in orders:
            order_date = _parse_order_date(order).date()
            revenue = _calculate_order_revenue(order, products)
            sales_by_date[order_date] += revenue
        
        # Crear puntos de tendencia
        trend: List[TrendPoint] = []
        if days_span <= max_trend_points:
            # Agregación diaria
            for d in sorted(sales_by_date.keys()):
                trend.append(TrendPoint(date=d, total=sales_by_date[d]))
        else:
            # Agregación mensual
            sales_by_month: Dict[str, float] = defaultdict(float)
            for d, total in sales_by_date.items():
                month_key = d.strftime("%Y-%m")
                sales_by_month[month_key] += total
            
            for month_str in sorted(sales_by_month.keys()):
                # Usar el primer día del mes como fecha representativa
                year, month = map(int, month_str.split("-"))
                trend.append(TrendPoint(
                    date=date(year, month, 1),
                    total=sales_by_month[month_str]
                ))
        
        # -------- CHARTS: Top Products --------
        product_sales: Dict[str, float] = defaultdict(float)
        product_names: Dict[str, str] = {}
        
        for order in orders:
            items = order.get("items", [])
            for item in items:
                # El campo puede ser 'sku' o 'codigo'
                codigo = item.get("sku") or item.get("codigo")
                if not codigo:
                    continue
                    
                quantity = item.get("qty", 0)
                
                # Obtener precio y nombre del catálogo
                price = 0.0
                if codigo in products:
                    price = products[codigo].get("precio_unitario", 0.0)
                    product_names[codigo] = products[codigo].get("nombre", f"Producto {codigo}")
                else:
                    # Fallback al precio en el item
                    price = item.get("price", 0.0)
                    product_names[codigo] = item.get("product_name", f"Producto {codigo}")
                
                revenue = quantity * price
                product_sales[codigo] += revenue
        
        # Ordenar y tomar top N
        sorted_products = sorted(
            product_sales.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        top_products: List[TopProduct] = []
        top_sum = 0.0
        for i, (prod_id, amount) in enumerate(sorted_products[:top_n_products]):
            top_products.append(TopProduct(
                product_name=product_names.get(prod_id, f"Producto {prod_id}"),
                amount=round(amount, 2)
            ))
            top_sum += amount
        
        others_amount = max(0.0, total_sales - top_sum)
        
        # -------- TABLE: Rows (órdenes individuales) --------
        table_rows: List[TableRow] = []
        for order in orders:
            vendor_name = order.get("user_name", "N/A")
            items = order.get("items", [])
            status = order.get("status", "COMPLETED")
            
            # Crear una fila por cada item en la orden
            for item in items:
                # El campo puede ser 'sku' o 'codigo'
                codigo = item.get("sku") or item.get("codigo")
                quantity = item.get("qty", 0)
                
                # Obtener nombre y precio del catálogo
                if codigo and codigo in products:
                    product_name = products[codigo].get("nombre", "Producto desconocido")
                    price = products[codigo].get("precio_unitario", 0.0)
                else:
                    product_name = item.get("product_name", "Producto desconocido")
                    price = item.get("price", 0.0)
                
                revenue = round(quantity * price, 2)
                
                table_rows.append(TableRow(
                    vendor_name=vendor_name,
                    product_name=product_name,
                    quantity=quantity,
                    revenue=revenue,
                    status=status.lower()
                ))
        
        # Ordenar por revenue descendente
        table_rows.sort(key=lambda x: x.revenue, reverse=True)
        
        # -------- Construir respuesta --------
        return ReportResponse(
            filters_applied=FiltersApplied(
                period=Period(from_=period_from, to=period_to),
                vendor_id=vendor_id,
                product_id=product_id,
            ),
            summary=Summary(
                total_sales=round(total_sales, 2),
                pending_orders=pending_orders,
                products_in_stock=products_in_stock,
                sales_change_pct_vs_prev_period=sales_change_pct,
            ),
            charts=Charts(
                trend=trend,
                top_products=top_products,
                others_amount=round(others_amount, 2),
            ),
            table=Table(rows=table_rows),
            currency="USD",
        )
    
    except Exception as e:
        logger.error(f"Error generando reporte: {str(e)}", exc_info=True)
        # Devolver respuesta vacía en caso de error
        return ReportResponse(
            filters_applied=FiltersApplied(
                period=Period(from_=period_from, to=period_to),
                vendor_id=vendor_id,
                product_id=product_id,
            ),
            summary=Summary(
                total_sales=0.0,
                pending_orders=0,
                products_in_stock=0,
                sales_change_pct_vs_prev_period=0.0,
            ),
            charts=Charts(
                trend=[],
                top_products=[],
                others_amount=0.0,
            ),
            table=Table(rows=[]),
            currency="USD",
        )
