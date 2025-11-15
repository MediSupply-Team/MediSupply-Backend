"""
Script de inicialización de visitas
Genera visitas dinámicas para 3 días antes, hoy, y 3 días después
Conecta con la BD de cliente-service para obtener clientes reales
"""
from sqlmodel import Session, delete, create_engine, select
from database import engine, init_db
from models import Visita
from datetime import date, timedelta
import os
import random

# Coordenadas de Bogotá para clientes sin geolocalización
BOGOTA_COORDS = [
    (4.69546, -74.03281, "Norte - Usaquén"),
    (4.6680624, -74.0568885, "Chapinero"),
    (4.62842, -74.06417, "Centro"),
    (4.707713, -74.046708, "Norte Alto"),
    (4.867019, -74.041611, "Chía/Autopista Norte"),
    (4.639958, -74.065481, "Chapinero Alto"),
    (4.652655, -74.073751, "Centro Norte"),
    (4.706317, -74.070743, "Suba"),
    (4.626998, -74.117929, "Kennedy"),
    (4.7483, -74.0863, "Suba Norte"),
    (4.6432, -74.0914, "Teusaquillo"),
    (4.6663, -74.0758, "Barrios Unidos"),
]

# Horarios disponibles para visitas
HORARIOS = ["09:00", "11:00", "13:00", "15:00", "16:30"]


def generar_visitas_desde_cliente_service():
    """
    Genera visitas dinámicas consultando la BD de cliente-service
    Crea visitas para 7 días (3 antes, hoy, 3 después)
    """
    print("🔄 Inicializando base de datos de rutas...")
    init_db()
    
    # Conectar a cliente-service DB
    # En AWS, la variable CLIENTE_DB_URL vendrá de Secrets Manager
    cliente_db_url = os.getenv("CLIENTE_DB_URL")
    
    if not cliente_db_url:
        print("❌ ERROR: CLIENTE_DB_URL no configurada")
        print("   No se pueden cargar datos sin conexión a cliente-service")
        raise Exception("CLIENTE_DB_URL environment variable is required")
    
    print(f"📡 Conectando a cliente-service...")
    
    try:
        cliente_engine = create_engine(cliente_db_url)
        
        # Obtener clientes activos de cliente-service
        with Session(cliente_engine) as cliente_session:
            # Query para obtener clientes (ajustado a la estructura real)
            from sqlalchemy import text
            result = cliente_session.execute(text("""
                SELECT id::text, nombre, direccion, ciudad, latitud, longitud
                FROM cliente 
                WHERE activo = true 
                ORDER BY nombre
                LIMIT 50
            """))
            clientes = result.fetchall()
            
            if not clientes:
                print("❌ ERROR: No se encontraron clientes activos en cliente-service")
                raise Exception("No active clients found in cliente-service database")
            
            print(f"✅ Encontrados {len(clientes)} clientes activos")
        
        # Usar vendedor_id = 1 por defecto (compatible con endpoint actual)
        vendedor_id = 1
        print(f"👤 Usando vendedor_id: {vendedor_id}")
        
    except Exception as e:
        print(f"❌ ERROR conectando a cliente-service: {e}")
        raise
    
    # Generar visitas para 7 días (3 antes, hoy, 3 después)
    hoy = date.today()
    visitas = []
    
    # Distribuir clientes en los 7 días
    clientes_por_dia = max(2, len(clientes) // 7)
    
    for dia_offset in range(-3, 4):  # -3 a +3
        fecha_visita = hoy + timedelta(days=dia_offset)
        
        # Seleccionar clientes para este día
        inicio = (dia_offset + 3) * clientes_por_dia
        fin = inicio + clientes_por_dia
        clientes_del_dia = clientes[inicio:fin] if inicio < len(clientes) else clientes[:clientes_por_dia]
        
        for idx, cliente in enumerate(clientes_del_dia):
            # Asignar coordenadas de Bogotá de manera circular
            coord_idx = (inicio + idx) % len(BOGOTA_COORDS)
            lat, lng, zona = BOGOTA_COORDS[coord_idx]
            
            # Asignar horario
            horario = HORARIOS[idx % len(HORARIOS)]
            
            # Crear visita con estructura compatible
            direccion = cliente[2] if cliente[2] else f"Dirección en {zona}, Bogotá"
            ciudad = cliente[3] if cliente[3] else "Bogotá"
            
            visita = Visita(
                vendedor_id=vendedor_id,  # int para compatibilidad
                cliente=cliente[1],  # nombre del cliente
                direccion=direccion,  # dirección completa
                fecha=fecha_visita,
                hora=horario,
                lat=lat,
                lng=lng,
                cliente_id=cliente[0],  # UUID interno
                ciudad=ciudad,
                estado="pendiente" if dia_offset >= 0 else random.choice(["completada", "pendiente"]),
                observaciones=f"Visita programada - {zona}"
            )
            visitas.append(visita)
    
    # Guardar en la base de datos de rutas
    with Session(engine) as session:
        # Limpiar visitas anteriores
        session.exec(delete(Visita))
        session.commit()
        
        # Insertar nuevas visitas
        session.add_all(visitas)
        session.commit()
        
        print(f"✅ Generadas {len(visitas)} visitas dinámicas:")
        print(f"   - 3 días antes: {len([v for v in visitas if v.fecha < hoy])} visitas")
        print(f"   - Hoy:          {len([v for v in visitas if v.fecha == hoy])} visitas")
        print(f"   - 3 días después: {len([v for v in visitas if v.fecha > hoy])} visitas")
        print(f"   - Fecha actual:  {hoy}")
        print(f"   - Rango:         {hoy - timedelta(days=3)} a {hoy + timedelta(days=3)}")


def generar_visitas_ejemplo():
    """
    Genera visitas de ejemplo cuando no se puede conectar a cliente-service
    """
    hoy = date.today()
    
    clientes_ejemplo = [
        ("Fundación Santa Fe de Bogotá", "Carrera 7 #117-15, Usaquén, Bogotá", 4.69546, -74.03281),
        ("Clínica del Country", "Carrera 16 #82-32, Chapinero, Bogotá", 4.6680624, -74.0568885),
        ("Hospital San Ignacio", "Carrera 7 #40-62, Chapinero, Bogotá", 4.62842, -74.06417),
        ("Clínica Reina Sofía", "Calle 127 #20-71, Usaquén, Bogotá", 4.707713, -74.046708),
        ("Clínica Marly", "Carrera 13 #49-90, Chapinero, Bogotá", 4.639958, -74.065481),
        ("Hospital de la Policía", "Av. Caracas #66-00, Chapinero, Bogotá", 4.652655, -74.073751),
        ("Clínica Shaio", "Av. Suba #116-20, Suba, Bogotá", 4.706317, -74.070743),
        ("Clínica de Occidente", "Av. Américas #71C-29, Kennedy, Bogotá", 4.626998, -74.117929),
        ("Hospital de Suba", "Calle 145 #91-19, Suba, Bogotá", 4.7483, -74.0863),
        ("Clínica Colombia", "Carrera 23 #56-60, Teusaquillo, Bogotá", 4.6432, -74.0914),
        ("Clínica Los Nogales", "Carrera 25 #78-25, Barrios Unidos, Bogotá", 4.6663, -74.0758),
        ("Clínica Universitaria", "Av. Jiménez #5-20, Santa Fe, Bogotá", 4.5981, -74.0760),
        ("Hospital Militar", "Transversal 3 #49-00, Chapinero, Bogotá", 4.6385, -74.0678),
        ("Clínica del Norte", "Calle 138 #25-70, Usaquén, Bogotá", 4.7286, -74.0597),
    ]
    
    visitas = []
    vendedor_id = 1  # Compatible con endpoint actual
    
    for dia_offset in range(-3, 4):
        fecha_visita = hoy + timedelta(days=dia_offset)
        
        # 2-3 clientes por día
        num_visitas = 2 if dia_offset % 2 == 0 else 3
        for idx in range(num_visitas):
            cliente_idx = ((dia_offset + 3) * 3 + idx) % len(clientes_ejemplo)
            cliente = clientes_ejemplo[cliente_idx]
            
            visita = Visita(
                vendedor_id=vendedor_id,
                cliente=cliente[0],
                direccion=cliente[1],
                fecha=fecha_visita,
                hora=HORARIOS[idx % len(HORARIOS)],
                lat=cliente[2],
                lng=cliente[3],
                cliente_id=f"ejemplo-cliente-{cliente_idx}",
                ciudad="Bogotá",
                estado="pendiente" if dia_offset >= 0 else random.choice(["completada", "pendiente"]),
                observaciones="Visita de ejemplo - Datos generados automáticamente"
            )
            visitas.append(visita)
    
    with Session(engine) as session:
        session.exec(delete(Visita))
        session.commit()
        session.add_all(visitas)
        session.commit()
        
        print(f"✅ Generadas {len(visitas)} visitas de ejemplo")
        print(f"   - Fecha actual: {hoy}")
        print(f"   - Rango: {hoy - timedelta(days=3)} a {hoy + timedelta(days=3)}")


if __name__ == "__main__":
    generar_visitas_desde_cliente_service()