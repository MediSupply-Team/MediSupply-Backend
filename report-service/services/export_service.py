# services/export_service.py
import csv
from io import StringIO, BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from schemas.report import ReportResponse


def generate_csv(report: ReportResponse) -> bytes:
    """
    Genera un archivo CSV con los datos del reporte
    """
    buffer = StringIO()
    writer = csv.writer(buffer)
    
    # Sección: Resumen
    writer.writerow(["RESUMEN DE VENTAS"])
    writer.writerow(["Total de Ventas", f"${report.summary.total_sales:.2f}"])
    writer.writerow(["Órdenes Pendientes", report.summary.pending_orders])
    writer.writerow(["Productos en Stock", report.summary.products_in_stock])
    writer.writerow(["Cambio vs Período Anterior", f"{report.summary.sales_change_pct_vs_prev_period * 100:.2f}%"])
    writer.writerow([])
    
    # Sección: Tendencia
    writer.writerow(["TENDENCIA DE VENTAS"])
    writer.writerow(["Fecha", "Total"])
    for point in report.charts.trend:
        writer.writerow([point.date.isoformat(), f"{point.total:.2f}"])
    writer.writerow([])
    
    # Sección: Top Productos
    writer.writerow(["TOP PRODUCTOS"])
    writer.writerow(["Producto", "Monto"])
    for product in report.charts.top_products:
        writer.writerow([product.product_name, f"{product.amount:.2f}"])
    writer.writerow(["Otros", f"{report.charts.others_amount:.2f}"])
    writer.writerow([])
    
    # Sección: Detalle por Vendedor y Producto
    writer.writerow(["DETALLE DE VENTAS"])
    writer.writerow(["Vendedor", "Producto", "Cantidad", "Ingresos", "Estado"])
    for row in report.table.rows:
        writer.writerow([
            row.vendor_name,
            row.product_name,
            row.quantity,
            f"{row.revenue:.2f}",
            row.status
        ])
    
    # Convertir a bytes
    csv_content = buffer.getvalue()
    return csv_content.encode('utf-8')


def generate_pdf(report: ReportResponse) -> bytes:
    """
    Genera un archivo PDF con los datos del reporte
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
    )
    
    # Título principal
    elements.append(Paragraph("Reporte de Desempeño de Ventas", title_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    # Período del reporte
    period_text = f"Período: {report.filters_applied.period.from_} a {report.filters_applied.period.to}"
    elements.append(Paragraph(period_text, styles['Normal']))
    elements.append(Spacer(1, 0.3 * inch))
    
    # Sección: Resumen
    elements.append(Paragraph("Resumen Ejecutivo", heading_style))
    summary_data = [
        ["Métrica", "Valor"],
        ["Total de Ventas", f"${report.summary.total_sales:,.2f} {report.currency}"],
        ["Órdenes Pendientes", str(report.summary.pending_orders)],
        ["Productos en Stock", str(report.summary.products_in_stock)],
        ["Cambio vs Período Anterior", f"{report.summary.sales_change_pct_vs_prev_period * 100:+.2f}%"]
    ]
    summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3 * inch))
    
    # Sección: Top Productos
    elements.append(Paragraph("Top Productos", heading_style))
    products_data = [["Producto", "Monto"]]
    for product in report.charts.top_products:
        products_data.append([product.product_name, f"${product.amount:,.2f}"])
    products_data.append(["Otros", f"${report.charts.others_amount:,.2f}"])
    
    products_table = Table(products_data, colWidths=[3 * inch, 2 * inch])
    products_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(products_table)
    elements.append(Spacer(1, 0.3 * inch))
    
    # Sección: Detalle de Ventas (tabla completa)
    elements.append(Paragraph("Detalle de Ventas por Vendedor", heading_style))
    detail_data = [["Vendedor", "Producto", "Cant.", "Ingresos", "Estado"]]
    for row in report.table.rows[:20]:  # Limitar a 20 filas para el PDF
        detail_data.append([
            row.vendor_name[:20],  # Truncar nombres largos
            row.product_name[:20],
            str(row.quantity),
            f"${row.revenue:,.2f}",
            row.status
        ])
    
    detail_table = Table(detail_data, colWidths=[1.5*inch, 1.5*inch, 0.7*inch, 1.2*inch, 1*inch])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(detail_table)
    
    # Construir el PDF
    doc.build(elements)
    
    # Retornar contenido como bytes
    pdf_content = buffer.getvalue()
    buffer.close()
    return pdf_content
