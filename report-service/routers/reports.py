# routers/reports.py
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session
from database import get_session
from schemas.report import ReportResponse, ExportResponse
from services.report_service import get_sales_performance
from services.export_service import generate_csv, generate_pdf
from services.s3_service import s3_service
import logging

logger = logging.getLogger(__name__)

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

@router.get("/sales-performance/export", response_model=ExportResponse)
def export_sales_performance(
    period_from: date = Query(..., alias="from"),
    period_to: date = Query(..., alias="to"),
    vendor_id: int | None = Query(None),
    product_id: int | None = Query(None),
    format: str = Query("csv", pattern="^(csv|pdf)$"),
    session: Session = Depends(get_session),
):
    """
    Exporta el reporte de desempeño de ventas y retorna una URL de S3
    
    Args:
        period_from: Fecha de inicio del período
        period_to: Fecha de fin del período
        vendor_id: ID del vendedor (opcional)
        product_id: ID del producto (opcional)
        format: Formato de exportación (csv o pdf)
        session: Sesión de base de datos
    
    Returns:
        ExportResponse con la URL del archivo en S3
    """
    try:
        # Obtener los datos del reporte
        report = get_sales_performance(
            session=session, 
            period_from=period_from, 
            period_to=period_to, 
            vendor_id=vendor_id, 
            product_id=product_id
        )
        
        # Generar el archivo según el formato solicitado
        if format == "csv":
            file_content = generate_csv(report)
            file_name = f"sales_performance_{period_from}_{period_to}.csv"
            content_type = "text/csv"
        elif format == "pdf":
            file_content = generate_pdf(report)
            file_name = f"sales_performance_{period_from}_{period_to}.pdf"
            content_type = "application/pdf"
        else:
            raise HTTPException(status_code=400, detail=f"Formato no soportado: {format}")
        
        # Subir el archivo a S3
        s3_url = s3_service.upload_file(
            file_content=file_content,
            file_name=file_name,
            content_type=content_type
        )
        
        logger.info(f"Archivo exportado exitosamente: {file_name} - URL: {s3_url}")
        
        return ExportResponse(
            url=s3_url,
            format=format,
            expires_in_seconds=604800,  # 7 días
            message=f"Reporte generado exitosamente en formato {format.upper()}"
        )
        
    except Exception as e:
        logger.error(f"Error al exportar reporte: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error al generar y subir el reporte: {str(e)}"
        )
