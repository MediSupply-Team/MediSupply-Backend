# routers/reports.py
from datetime import date, datetime
from fastapi import APIRouter, Query, HTTPException
from schemas.report import ReportResponse, ExportResponse
from services.report_service import get_sales_performance
from services.export_service import generate_csv, generate_pdf
from services.analytics_service import generate_insights
from services.database_client import db_client
from services.s3_service import s3_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/sales-performance", response_model=ReportResponse)
async def sales_performance(
    period_from: date = Query(..., alias="from"),
    period_to: date = Query(..., alias="to"),
    vendor_id: int | None = Query(None),
    product_id: int | None = Query(None),
):
    """
    Obtiene el reporte de desempeño de ventas basado en datos reales de Orders
    """
    return await get_sales_performance(
        period_from=period_from,
        period_to=period_to,
        vendor_id=vendor_id,
        product_id=product_id,
    )

@router.get("/sales-performance/export", response_model=ExportResponse)
async def export_sales_performance(
    period_from: date = Query(..., alias="from"),
    period_to: date = Query(..., alias="to"),
    vendor_id: int | None = Query(None),
    product_id: int | None = Query(None),
    format: str = Query("csv", pattern="^(csv|pdf)$"),
):
    """
    Exporta el reporte de desempeño de ventas con análisis completo y retorna una URL de S3
    
    Args:
        period_from: Fecha de inicio del período
        period_to: Fecha de fin del período
        vendor_id: ID del vendedor (opcional)
        product_id: ID del producto (opcional)
        format: Formato de exportación (csv o pdf)
    
    Returns:
        ExportResponse con la URL del archivo en S3
    """
    try:
        # Obtener los datos del reporte
        report = await get_sales_performance(
            period_from=period_from, 
            period_to=period_to, 
            vendor_id=vendor_id, 
            product_id=product_id
        )
        
        # Obtener datos adicionales para análisis
        start_datetime = datetime.combine(period_from, datetime.min.time())
        end_datetime = datetime.combine(period_to, datetime.max.time())
        
        all_orders = await db_client.get_orders(
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        # Filtrar solo órdenes de vendedores (seller)
        orders = [
            order for order in all_orders 
            if order.get("created_by_role", "").lower() == "seller"
        ]
        
        # Obtener productos del catálogo
        all_skus = set()
        for order in orders:
            items = order.get("items", [])
            for item in items:
                codigo = item.get("sku") or item.get("codigo")
                if codigo:
                    all_skus.add(codigo)
        
        products = await db_client.get_products_by_skus(list(all_skus))
        
        # Generar insights
        logger.info("Generando insights analíticos...")
        insights = generate_insights({
            'orders': orders,
            'products': products,
            'summary': {
                'total_sales': report.summary.total_sales,
                'pending_orders': report.summary.pending_orders,
                'products_in_stock': report.summary.products_in_stock,
                'sales_change_pct_vs_prev_period': report.summary.sales_change_pct_vs_prev_period
            }
        })
        
        # Generar el archivo según el formato solicitado
        if format == "csv":
            file_content = generate_csv(report, insights)
            file_name = f"sales_analytics_{period_from}_{period_to}.csv"
            content_type = "text/csv"
        elif format == "pdf":
            file_content = generate_pdf(report, insights)
            file_name = f"sales_analytics_{period_from}_{period_to}.pdf"
            content_type = "application/pdf"
        else:
            raise HTTPException(status_code=400, detail=f"Formato no soportado: {format}")
        
        # Subir el archivo a S3
        s3_url = s3_service.upload_file(
            file_content=file_content,
            file_name=file_name,
            content_type=content_type
        )
        
        logger.info(f"Archivo analítico exportado exitosamente: {file_name} - URL: {s3_url}")
        
        return ExportResponse(
            url=s3_url,
            format=format,
            expires_in_seconds=604800,  # 7 días
            message=f"Informe analítico generado exitosamente en formato {format.upper()}"
        )
        
    except Exception as e:
        logger.error(f"Error al exportar reporte analítico: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error al generar y subir el informe: {str(e)}"
        )
