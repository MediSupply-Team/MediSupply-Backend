# services/analytics_service.py
"""
Servicio de análisis avanzado para generar insights y conclusiones
"""
from typing import Dict, List, Any, Tuple
from collections import defaultdict
from datetime import date
import statistics

def generate_insights(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera insights y análisis avanzado a partir de los datos del reporte
    
    Args:
        report_data: Diccionario con los datos del reporte incluyendo:
            - orders: Lista de órdenes
            - products: Diccionario de productos
            - summary: Resumen de métricas
            
    Returns:
        Diccionario con insights organizados por categorías
    """
    orders = report_data.get('orders', [])
    products = report_data.get('products', {})
    
    # Análisis por vendedor
    vendor_analysis = _analyze_vendors(orders, products)
    
    # Análisis por producto
    product_analysis = _analyze_products(orders, products)
    
    # Análisis geográfico (si hay datos de ubicación)
    geo_analysis = _analyze_geography(orders)
    
    # Tendencias y patrones
    trend_analysis = _analyze_trends(orders, products)
    
    # Conclusiones ejecutivas
    conclusions = _generate_conclusions(
        vendor_analysis, 
        product_analysis, 
        geo_analysis,
        trend_analysis,
        report_data.get('summary', {})
    )
    
    return {
        'vendor_insights': vendor_analysis,
        'product_insights': product_analysis,
        'geographic_insights': geo_analysis,
        'trend_insights': trend_analysis,
        'executive_summary': conclusions
    }

def _analyze_vendors(orders: List[Dict[str, Any]], products: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Analiza el desempeño de los vendedores"""
    vendor_stats = defaultdict(lambda: {
        'total_sales': 0.0,
        'order_count': 0,
        'product_variety': set(),
        'avg_order_value': 0.0,
        'total_units': 0
    })
    
    for order in orders:
        vendor = order.get('user_name') or 'Vendedor desconocido'
        items = order.get('items', [])
        
        # Calcular revenue de la orden
        order_revenue = 0.0
        order_units = 0
        
        for item in items:
            codigo = item.get('sku') or item.get('codigo')
            qty = item.get('qty', 0)
            
            price = 0.0
            if codigo and codigo in products:
                price = products[codigo].get('precio_unitario', 0.0)
                vendor_stats[vendor]['product_variety'].add(codigo)
            else:
                price = item.get('price', 0.0)
            
            order_revenue += qty * price
            order_units += qty
        
        vendor_stats[vendor]['total_sales'] += order_revenue
        vendor_stats[vendor]['order_count'] += 1
        vendor_stats[vendor]['total_units'] += order_units
    
    # Calcular promedios y rankings
    vendor_list = []
    for vendor, stats in vendor_stats.items():
        stats['avg_order_value'] = stats['total_sales'] / stats['order_count'] if stats['order_count'] > 0 else 0
        stats['product_variety'] = len(stats['product_variety'])
        vendor_list.append({
            'name': vendor,
            **stats
        })
    
    # Ordenar por ventas totales
    vendor_list.sort(key=lambda x: x['total_sales'], reverse=True)
    
    # Identificar vendedores destacados
    if vendor_list:
        top_vendor = vendor_list[0]
        avg_sales = statistics.mean([v['total_sales'] for v in vendor_list]) if len(vendor_list) > 1 else 0
        
        outstanding_vendors = [
            v for v in vendor_list 
            if v['total_sales'] > avg_sales * 1.2  # 20% por encima del promedio
        ]
    else:
        top_vendor = None
        avg_sales = 0
        outstanding_vendors = []
    
    return {
        'top_vendor': top_vendor,
        'all_vendors': vendor_list,
        'outstanding_vendors': outstanding_vendors,
        'average_sales_per_vendor': avg_sales,
        'total_vendors': len(vendor_list)
    }

def _analyze_products(orders: List[Dict[str, Any]], products: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Analiza el movimiento de productos"""
    product_stats = defaultdict(lambda: {
        'total_units': 0,
        'total_revenue': 0.0,
        'order_count': 0,
        'vendors': set()
    })
    
    for order in orders:
        vendor = order.get('user_name') or 'Vendedor desconocido'
        items = order.get('items', [])
        
        for item in items:
            codigo = item.get('sku') or item.get('codigo')
            qty = item.get('qty', 0)
            
            if codigo:
                price = 0.0
                if codigo in products:
                    price = products[codigo].get('precio_unitario', 0.0)
                else:
                    price = item.get('price', 0.0)
                
                product_stats[codigo]['total_units'] += qty
                product_stats[codigo]['total_revenue'] += qty * price
                product_stats[codigo]['order_count'] += 1
                product_stats[codigo]['vendors'].add(vendor)
    
    # Construir lista de productos con estadísticas
    product_list = []
    for codigo, stats in product_stats.items():
        product_name = products.get(codigo, {}).get('nombre', codigo)
        categoria = products.get(codigo, {}).get('categoria_id', 'Sin categoría')
        
        product_list.append({
            'code': codigo,
            'name': product_name,
            'category': categoria,
            'total_units': stats['total_units'],
            'total_revenue': stats['total_revenue'],
            'order_count': stats['order_count'],
            'unique_vendors': len(stats['vendors']),
            'avg_units_per_order': stats['total_units'] / stats['order_count'] if stats['order_count'] > 0 else 0
        })
    
    # Ordenar por revenue
    product_list.sort(key=lambda x: x['total_revenue'], reverse=True)
    
    # Análisis por categoría
    category_stats = defaultdict(lambda: {'revenue': 0.0, 'units': 0})
    for product in product_list:
        category_stats[product['category']]['revenue'] += product['total_revenue']
        category_stats[product['category']]['units'] += product['total_units']
    
    top_categories = sorted(
        [{'category': k, **v} for k, v in category_stats.items()],
        key=lambda x: x['revenue'],
        reverse=True
    )
    
    return {
        'top_products': product_list[:10],
        'all_products': product_list,
        'top_categories': top_categories,
        'total_products_sold': len(product_list)
    }

def _analyze_geography(orders: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analiza la distribución geográfica de las ventas"""
    # Por ahora, extraer información de direcciones si está disponible
    location_stats = defaultdict(lambda: {
        'order_count': 0,
        'total_revenue': 0.0
    })
    
    for order in orders:
        address = order.get('address', {})
        if isinstance(address, dict):
            city = address.get('city', 'Desconocida')
            country = address.get('country', 'Desconocido')
            location = f"{city}, {country}"
        else:
            location = 'Ubicación desconocida'
        
        location_stats[location]['order_count'] += 1
    
    location_list = [
        {'location': k, **v}
        for k, v in location_stats.items()
    ]
    location_list.sort(key=lambda x: x['order_count'], reverse=True)
    
    return {
        'top_locations': location_list[:10],
        'total_locations': len(location_list)
    }

def _analyze_trends(orders: List[Dict[str, Any]], products: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Analiza tendencias y patrones"""
    if not orders:
        return {
            'growth_trend': 'neutral',
            'seasonality': 'insufficient_data'
        }
    
    # Análisis simple de tendencia
    total_orders = len(orders)
    
    # Calcular distribución por estado
    status_distribution = defaultdict(int)
    for order in orders:
        status = order.get('status', 'UNKNOWN')
        status_distribution[status] += 1
    
    # Calcular tasa de completitud
    completed = status_distribution.get('COMPLETED', 0)
    completion_rate = (completed / total_orders * 100) if total_orders > 0 else 0
    
    return {
        'total_orders': total_orders,
        'status_distribution': dict(status_distribution),
        'completion_rate': completion_rate,
        'avg_products_per_order': sum(len(o.get('items', [])) for o in orders) / total_orders if total_orders > 0 else 0
    }

def _generate_conclusions(
    vendor_analysis: Dict[str, Any],
    product_analysis: Dict[str, Any],
    geo_analysis: Dict[str, Any],
    trend_analysis: Dict[str, Any],
    summary: Dict[str, Any]
) -> List[str]:
    """Genera conclusiones ejecutivas basadas en todos los análisis"""
    conclusions = []
    
    # Análisis de vendedores
    top_vendor = vendor_analysis.get('top_vendor')
    if top_vendor:
        conclusions.append(
            f"🏆 MEJOR VENDEDOR: {top_vendor['name']} lidera con ${top_vendor['total_sales']:,.2f} "
            f"en ventas ({top_vendor['order_count']} órdenes, promedio de ${top_vendor['avg_order_value']:,.2f} por orden)."
        )
    
    outstanding = vendor_analysis.get('outstanding_vendors', [])
    if len(outstanding) > 1:
        names = ', '.join([v['name'] for v in outstanding[1:3]])
        conclusions.append(
            f"⭐ VENDEDORES DESTACADOS: {names} superan el promedio en un 20% o más."
        )
    
    # Análisis de productos
    top_products = product_analysis.get('top_products', [])
    if top_products:
        top_3 = top_products[:3]
        product_names = ', '.join([p['name'] for p in top_3])
        conclusions.append(
            f"📦 PRODUCTOS TOP: {product_names} generan el mayor volumen de ventas."
        )
    
    top_categories = product_analysis.get('top_categories', [])
    if top_categories:
        top_cat = top_categories[0]
        conclusions.append(
            f"📊 CATEGORÍA LÍDER: {top_cat['category']} domina con ${top_cat['revenue']:,.2f} "
            f"({top_cat['units']} unidades vendidas)."
        )
    
    # Análisis geográfico
    top_locations = geo_analysis.get('top_locations', [])
    if top_locations and top_locations[0]['location'] != 'Ubicación desconocida':
        top_loc = top_locations[0]
        conclusions.append(
            f"🌍 ZONA DE MAYOR MOVIMIENTO: {top_loc['location']} con {top_loc['order_count']} órdenes."
        )
    
    # Tendencias
    completion_rate = trend_analysis.get('completion_rate', 0)
    if completion_rate > 0:
        conclusions.append(
            f"📈 EFICIENCIA OPERATIVA: Tasa de completitud del {completion_rate:.1f}%."
        )
    
    # Recomendaciones
    conclusions.append("\n💡 RECOMENDACIONES:")
    
    if top_vendor and top_vendor['total_sales'] > vendor_analysis.get('average_sales_per_vendor', 0) * 2:
        conclusions.append(
            f"• Analizar las prácticas de {top_vendor['name']} para replicar su éxito con otros vendedores."
        )
    
    if top_products:
        low_stock_products = [p for p in top_products if p.get('total_units', 0) > 50]
        if low_stock_products:
            conclusions.append(
                "• Asegurar inventario suficiente de productos de alta demanda para evitar quiebres de stock."
            )
    
    if vendor_analysis.get('total_vendors', 0) > 0:
        avg_variety = statistics.mean([v['product_variety'] for v in vendor_analysis['all_vendors']]) if vendor_analysis['all_vendors'] else 0
        if avg_variety < 3:
            conclusions.append(
                "• Capacitar vendedores en portafolio completo de productos para aumentar variedad de ventas."
            )
    
    return conclusions
