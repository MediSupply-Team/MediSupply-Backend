# services/export_service.py
import csv
from io import StringIO, BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, ListFlowable, ListItem
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from schemas.report import ReportResponse
from services.analytics_service import generate_insights


def generate_csv(report: ReportResponse, insights: dict = None) -> bytes:
    """
    Genera un archivo CSV con los datos del reporte y análisis ejecutivo
    
    Args:
        report: Datos del reporte
        insights: Insights y análisis generados (opcional)
    """
    buffer = StringIO()
    writer = csv.writer(buffer)
    
    # === INFORME ANALÍTICO ===
    writer.writerow(["=" * 80])
    writer.writerow(["INFORME ANALÍTICO DE VENTAS"])
    writer.writerow(["=" * 80])
    writer.writerow([])
    
    # Período del reporte
    writer.writerow(["Período analizado:", f"{report.filters_applied.period.from_} a {report.filters_applied.period.to}"])
    writer.writerow([])
    
    # === RESUMEN EJECUTIVO ===
    if insights and 'executive_summary' in insights:
        writer.writerow(["=" * 80])
        writer.writerow(["RESUMEN EJECUTIVO Y CONCLUSIONES"])
        writer.writerow(["=" * 80])
        for conclusion in insights['executive_summary']:
            writer.writerow([conclusion])
        writer.writerow([])
    
    # === MÉTRICAS CLAVE ===
    writer.writerow(["=" * 80])
    writer.writerow(["MÉTRICAS CLAVE"])
    writer.writerow(["=" * 80])
    writer.writerow(["Total de Ventas", f"${report.summary.total_sales:,.2f} {report.currency}"])
    writer.writerow(["Órdenes Pendientes", report.summary.pending_orders])
    writer.writerow(["Productos en Stock", report.summary.products_in_stock])
    writer.writerow(["Cambio vs Período Anterior", f"{report.summary.sales_change_pct_vs_prev_period * 100:.2f}%"])
    writer.writerow([])
    
    # === ANÁLISIS DE VENDEDORES ===
    if insights and 'vendor_insights' in insights:
        vendor_insights = insights['vendor_insights']
        
        writer.writerow(["=" * 80])
        writer.writerow(["ANÁLISIS DE VENDEDORES"])
        writer.writerow(["=" * 80])
        writer.writerow([])
        
        # Mejor vendedor
        if vendor_insights.get('top_vendor'):
            top = vendor_insights['top_vendor']
            writer.writerow(["🏆 MEJOR VENDEDOR"])
            writer.writerow(["Nombre", top['name']])
            writer.writerow(["Ventas Totales", f"${top['total_sales']:,.2f}"])
            writer.writerow(["Número de Órdenes", top['order_count']])
            writer.writerow(["Promedio por Orden", f"${top['avg_order_value']:,.2f}"])
            writer.writerow(["Variedad de Productos", top['product_variety']])
            writer.writerow(["Unidades Vendidas", top['total_units']])
            writer.writerow([])
        
        # Vendedores destacados
        if vendor_insights.get('outstanding_vendors'):
            writer.writerow(["⭐ VENDEDORES DESTACADOS (Top performers)"])
            writer.writerow(["Vendedor", "Ventas", "Órdenes", "Promedio/Orden", "Variedad Productos"])
            for vendor in vendor_insights['outstanding_vendors']:
                writer.writerow([
                    vendor['name'],
                    f"${vendor['total_sales']:,.2f}",
                    vendor['order_count'],
                    f"${vendor['avg_order_value']:,.2f}",
                    vendor['product_variety']
                ])
            writer.writerow([])
        
        # Ranking completo
        writer.writerow(["📊 RANKING DE VENDEDORES"])
        writer.writerow(["Posición", "Vendedor", "Ventas", "Órdenes", "Promedio/Orden"])
        for i, vendor in enumerate(vendor_insights.get('all_vendors', []), 1):
            writer.writerow([
                i,
                vendor['name'],
                f"${vendor['total_sales']:,.2f}",
                vendor['order_count'],
                f"${vendor['avg_order_value']:,.2f}"
            ])
        writer.writerow([])
        writer.writerow(["Promedio de ventas por vendedor:", f"${vendor_insights.get('average_sales_per_vendor', 0):,.2f}"])
        writer.writerow([])
    
    # === ANÁLISIS DE PRODUCTOS ===
    if insights and 'product_insights' in insights:
        product_insights = insights['product_insights']
        
        writer.writerow(["=" * 80])
        writer.writerow(["ANÁLISIS DE PRODUCTOS Y CATEGORÍAS"])
        writer.writerow(["=" * 80])
        writer.writerow([])
        
        # Top productos
        writer.writerow(["📦 PRODUCTOS CON MAYOR MOVIMIENTO"])
        writer.writerow(["Producto", "Código", "Categoría", "Unidades", "Revenue", "Órdenes", "Vendedores"])
        for product in product_insights.get('top_products', []):
            writer.writerow([
                product['name'],
                product['code'],
                product['category'],
                product['total_units'],
                f"${product['total_revenue']:,.2f}",
                product['order_count'],
                product['unique_vendors']
            ])
        writer.writerow([])
        
        # Top categorías
        writer.writerow(["📊 CATEGORÍAS MÁS VENDIDAS"])
        writer.writerow(["Categoría", "Revenue", "Unidades"])
        for category in product_insights.get('top_categories', []):
            writer.writerow([
                category['category'],
                f"${category['revenue']:,.2f}",
                category['units']
            ])
        writer.writerow([])
    
    # === ANÁLISIS GEOGRÁFICO ===
    if insights and 'geographic_insights' in insights:
        geo_insights = insights['geographic_insights']
        
        writer.writerow(["=" * 80])
        writer.writerow(["ANÁLISIS GEOGRÁFICO"])
        writer.writerow(["=" * 80])
        writer.writerow([])
        
        writer.writerow(["🌍 ZONAS CON MAYOR MOVIMIENTO"])
        writer.writerow(["Ubicación", "Número de Órdenes"])
        for location in geo_insights.get('top_locations', []):
            if location['location'] != 'Ubicación desconocida':
                writer.writerow([location['location'], location['order_count']])
        writer.writerow([])
    
    # === TENDENCIAS ===
    writer.writerow(["=" * 80])
    writer.writerow(["TENDENCIA DE VENTAS"])
    writer.writerow(["=" * 80])
    writer.writerow(["Fecha", "Total"])
    for point in report.charts.trend:
        writer.writerow([point.date.isoformat(), f"${point.total:,.2f}"])
    writer.writerow([])
    
    # === DETALLE DE TRANSACCIONES ===
    writer.writerow(["=" * 80])
    writer.writerow(["DETALLE DE TRANSACCIONES"])
    writer.writerow(["=" * 80])
    writer.writerow(["Vendedor", "Producto", "Cantidad", "Ingresos", "Estado"])
    for row in report.table.rows:
        writer.writerow([
            row.vendor_name,
            row.product_name,
            row.quantity,
            f"${row.revenue:,.2f}",
            row.status
        ])
    
    # Convertir a bytes
    csv_content = buffer.getvalue()
    return csv_content.encode('utf-8')


def generate_pdf(report: ReportResponse, insights: dict = None) -> bytes:
    """
    Genera un PDF analítico con insights, análisis y conclusiones
    
    Args:
        report: Datos del reporte
        insights: Insights y análisis generados (opcional)
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    
    # === ESTILOS ===
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=26,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#666666'),
        spaceAfter=30,
        alignment=TA_CENTER,
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold',
        borderWidth=1,
        borderColor=colors.HexColor('#2c3e50'),
        borderPadding=5,
        backColor=colors.HexColor('#ecf0f1')
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubheading',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=8,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    conclusion_style = ParagraphStyle(
        'ConclusionStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=8,
        leftIndent=20,
        alignment=TA_JUSTIFY
    )
    
    # === PORTADA ===
    elements.append(Spacer(1, 1*inch))
    elements.append(Paragraph("📊 INFORME ANALÍTICO DE VENTAS", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    period_text = f"Período: {report.filters_applied.period.from_} a {report.filters_applied.period.to}"
    elements.append(Paragraph(period_text, subtitle_style))
    elements.append(Spacer(1, 0.5*inch))
    
    # === RESUMEN EJECUTIVO Y CONCLUSIONES ===
    if insights and 'executive_summary' in insights:
        elements.append(Paragraph("📋 RESUMEN EJECUTIVO", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        for conclusion in insights['executive_summary']:
            elements.append(Paragraph(conclusion, conclusion_style))
        
        elements.append(Spacer(1, 0.3*inch))
    
    # === MÉTRICAS CLAVE ===
    elements.append(Paragraph("📈 MÉTRICAS CLAVE", heading_style))
    elements.append(Spacer(1, 0.1*inch))
    
    summary_data = [
        ["Métrica", "Valor"],
        ["Total de Ventas", f"${report.summary.total_sales:,.2f} {report.currency}"],
        ["Órdenes Pendientes", str(report.summary.pending_orders)],
        ["Productos en Stock", str(report.summary.products_in_stock)],
        ["Cambio vs Período Anterior", f"{report.summary.sales_change_pct_vs_prev_period * 100:+.2f}%"]
    ]
    
    summary_table = Table(summary_data, colWidths=[3.5*inch, 2.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7'))
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # === ANÁLISIS DE VENDEDORES ===
    if insights and 'vendor_insights' in insights:
        vendor_insights = insights['vendor_insights']
        
        elements.append(Paragraph("👥 ANÁLISIS DE VENDEDORES", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # Mejor vendedor
        if vendor_insights.get('top_vendor'):
            top = vendor_insights['top_vendor']
            elements.append(Paragraph("🏆 MEJOR VENDEDOR", subheading_style))
            
            top_vendor_data = [
                ["Nombre", top['name']],
                ["Ventas Totales", f"${top['total_sales']:,.2f}"],
                ["Número de Órdenes", str(top['order_count'])],
                ["Promedio por Orden", f"${top['avg_order_value']:,.2f}"],
                ["Variedad de Productos", str(top['product_variety'])],
                ["Unidades Vendidas", str(top['total_units'])]
            ]
            
            top_vendor_table = Table(top_vendor_data, colWidths=[2*inch, 4*inch])
            top_vendor_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#27ae60')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#d5f4e6')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#27ae60')),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(top_vendor_table)
            elements.append(Spacer(1, 0.2*inch))
        
        # Vendedores destacados
        if vendor_insights.get('outstanding_vendors') and len(vendor_insights['outstanding_vendors']) > 1:
            elements.append(Paragraph("⭐ VENDEDORES DESTACADOS", subheading_style))
            
            outstanding_data = [["Vendedor", "Ventas", "Órdenes", "Prom/Orden", "Variedad"]]
            for vendor in vendor_insights['outstanding_vendors'][:5]:
                outstanding_data.append([
                    vendor['name'][:25],
                    f"${vendor['total_sales']:,.0f}",
                    str(vendor['order_count']),
                    f"${vendor['avg_order_value']:,.0f}",
                    str(vendor['product_variety'])
                ])
            
            outstanding_table = Table(outstanding_data, colWidths=[1.8*inch, 1.2*inch, 0.8*inch, 1*inch, 0.8*inch])
            outstanding_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f39c12')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fef5e7')),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#f39c12'))
            ]))
            elements.append(outstanding_table)
            elements.append(Spacer(1, 0.2*inch))
        
        # Ranking de vendedores
        elements.append(Paragraph("📊 RANKING DE VENDEDORES", subheading_style))
        
        ranking_data = [["Pos", "Vendedor", "Ventas", "Órdenes"]]
        for i, vendor in enumerate(vendor_insights.get('all_vendors', [])[:10], 1):
            ranking_data.append([
                str(i),
                vendor['name'][:30],
                f"${vendor['total_sales']:,.2f}",
                str(vendor['order_count'])
            ])
        
        ranking_table = Table(ranking_data, colWidths=[0.5*inch, 2.5*inch, 1.8*inch, 1*inch])
        ranking_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        elements.append(ranking_table)
        elements.append(Spacer(1, 0.2*inch))
    
    # === NUEVA PÁGINA ===
    elements.append(PageBreak())
    
    # === ANÁLISIS DE PRODUCTOS ===
    if insights and 'product_insights' in insights:
        product_insights = insights['product_insights']
        
        elements.append(Paragraph("📦 ANÁLISIS DE PRODUCTOS", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # Top productos
        elements.append(Paragraph("Productos con Mayor Movimiento", subheading_style))
        
        product_data = [["Producto", "Código", "Categoría", "Unidades", "Revenue"]]
        for product in product_insights.get('top_products', [])[:10]:
            product_data.append([
                product['name'][:25],
                product['code'],
                product['category'][:15],
                str(product['total_units']),
                f"${product['total_revenue']:,.0f}"
            ])
        
        product_table = Table(product_data, colWidths=[2*inch, 0.8*inch, 1.2*inch, 0.8*inch, 1*inch])
        product_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ebf5fb')),
            ('ALIGN', (3, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#3498db'))
        ]))
        elements.append(product_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Top categorías
        elements.append(Paragraph("Categorías Más Vendidas", subheading_style))
        
        category_data = [["Categoría", "Revenue", "Unidades"]]
        for category in product_insights.get('top_categories', [])[:8]:
            category_data.append([
                category['category'],
                f"${category['revenue']:,.2f}",
                str(category['units'])
            ])
        
        category_table = Table(category_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
        category_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f4ecf7')),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#9b59b6'))
        ]))
        elements.append(category_table)
        elements.append(Spacer(1, 0.2*inch))
    
    # === ANÁLISIS GEOGRÁFICO ===
    if insights and 'geographic_insights' in insights:
        geo_insights = insights['geographic_insights']
        
        if geo_insights.get('top_locations') and geo_insights['top_locations'][0]['location'] != 'Ubicación desconocida':
            elements.append(Paragraph("🌍 ANÁLISIS GEOGRÁFICO", heading_style))
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph("Zonas con Mayor Movimiento", subheading_style))
            
            location_data = [["Ubicación", "Órdenes"]]
            for location in geo_insights['top_locations'][:10]:
                if location['location'] != 'Ubicación desconocida':
                    location_data.append([
                        location['location'],
                        str(location['order_count'])
                    ])
            
            if len(location_data) > 1:
                location_table = Table(location_data, colWidths=[4*inch, 2*inch])
                location_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a085')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#d1f2eb')),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#16a085'))
                ]))
                elements.append(location_table)
                elements.append(Spacer(1, 0.2*inch))
    
    # === CONSTRUIR PDF ===
    doc.build(elements)
    
    pdf_content = buffer.getvalue()
    buffer.close()
    return pdf_content
