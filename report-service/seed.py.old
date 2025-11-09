# seed.py  — datos de ejemplo para reportes de ventas
from sqlmodel import Session, delete, select
from database import engine, init_db
from models import Vendedor, Producto, Venta
from datetime import datetime

init_db()

def venta(fecha_ymd: str, vendedor_id: int, producto_id: int, cantidad: int, precio_unit: float, estado: str = "completado"):
    monto = round(cantidad * precio_unit, 2)
    return Venta(
        fecha=datetime.fromisoformat(fecha_ymd + "T10:00:00"),
        vendedor_id=vendedor_id,
        producto_id=producto_id,
        cantidad=cantidad,
        monto_total=monto,
        estado=estado
    )

with Session(engine) as session:
    # 1) Limpiar en orden por FKs (primero hijos)
    session.exec(delete(Venta))
    session.exec(delete(Producto))
    session.exec(delete(Vendedor))
    session.commit()

    # 2) Vendedores
    vendedores = [
        Vendedor(nombre="Juan Pérez"),
        Vendedor(nombre="María García"),
        Vendedor(nombre="Pedro Rodríguez"),
        Vendedor(nombre="Ana López"),
        Vendedor(nombre="Carlos Martínez"),
    ]
    session.add_all(vendedores)
    session.commit()  # asegura IDs autoincrementales

    vend_map = {v.nombre: v.id for v in session.exec(select(Vendedor)).all()}

    # 3) Productos (stock simple para summary)
    productos = [
        Producto(nombre="Jeringas Desechables", stock=500),
        Producto(nombre="Guantes de Látex", stock=600),
        Producto(nombre="Mascarillas N95", stock=400),
        Producto(nombre="Batas Quirúrgicas", stock=300),
        Producto(nombre="Alcohol en Gel", stock=700),
    ]
    session.add_all(productos)
    session.commit()

    prod_map = {p.nombre: p.id for p in session.exec(select(Producto)).all()}

    # 4) Ventas de ejemplo (septiembre 2025)
    #    Mantenemos números coherentes con el mockup (varios completados y algunos pendientes)
    ventas = [
        # 2025-09-01
        venta("2025-09-01", vend_map["Juan Pérez"],     prod_map["Jeringas Desechables"], 50,  200.0, "completado"),  # 10,000
        venta("2025-09-01", vend_map["María García"],   prod_map["Guantes de Látex"],     30,  250.0, "pendiente"),   # 7,500
        venta("2025-09-01", vend_map["Pedro Rodríguez"],prod_map["Mascarillas N95"],       40,  200.0, "completado"),  # 8,000
        venta("2025-09-01", vend_map["Ana López"],      prod_map["Batas Quirúrgicas"],     25,  200.0, "pendiente"),   # 5,000
        venta("2025-09-01", vend_map["Carlos Martínez"],prod_map["Alcohol en Gel"],        35,  185.7,"completado"),   # ~6,500

        # 2025-09-02
        venta("2025-09-02", vend_map["Juan Pérez"],     prod_map["Jeringas Desechables"], 35,  200.0, "completado"),
        venta("2025-09-02", vend_map["María García"],   prod_map["Guantes de Látex"],     20,  250.0, "completado"),
        venta("2025-09-02", vend_map["Pedro Rodríguez"],prod_map["Mascarillas N95"],       30,  200.0, "completado"),
        venta("2025-09-02", vend_map["Ana López"],      prod_map["Batas Quirúrgicas"],     10,  200.0, "pendiente"),
        venta("2025-09-02", vend_map["Carlos Martínez"],prod_map["Alcohol en Gel"],        20,  185.7,"completado"),

        # 2025-09-03
        venta("2025-09-03", vend_map["Juan Pérez"],     prod_map["Jeringas Desechables"], 45,  200.0, "completado"),
        venta("2025-09-03", vend_map["María García"],   prod_map["Guantes de Látex"],     25,  250.0, "completado"),
        venta("2025-09-03", vend_map["Pedro Rodríguez"],prod_map["Mascarillas N95"],       35,  200.0, "completado"),
        venta("2025-09-03", vend_map["Ana López"],      prod_map["Batas Quirúrgicas"],     15,  200.0, "pendiente"),
        venta("2025-09-03", vend_map["Carlos Martínez"],prod_map["Alcohol en Gel"],        18,  185.7,"completado"),
    ]

    session.add_all(ventas)
    session.commit()
    print("✅ Datos iniciales de reportes cargados.")