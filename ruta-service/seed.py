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
        print("⚠️  ADVERTENCIA: CLIENTE_DB_URL no configurada")
        print("   El servicio iniciará sin datos de visitas")
        print("   Las visitas se pueden crear más tarde mediante la API")
        return
    
    print(f"📡 Conectando a cliente-service...")
    
    try:
        # Convertir asyncpg URL a psycopg2 para uso síncrono
        cliente_db_url_sync = cliente_db_url.replace("postgresql+asyncpg://", "postgresql://")
        cliente_engine = create_engine(cliente_db_url_sync)
        
        # Obtener clientes activos de cliente-service
        with Session(cliente_engine) as cliente_session:
            # Query para obtener clientes (ajustado a la estructura real)
            from sqlalchemy import text
            result = cliente_session.execute(text("""
                SELECT id::text, nombre, direccion, ciudad
                FROM cliente 
                WHERE activo = true 
                ORDER BY nombre
                LIMIT 50
            """))
            clientes = result.fetchall()
            
            if not clientes:
                print("⚠️  ADVERTENCIA: No se encontraron clientes activos en cliente-service")
                print("   El servicio iniciará sin datos de visitas")
                return
            
            print(f"✅ Encontrados {len(clientes)} clientes activos")
        
        # Usar vendedor_id = 1 por defecto (compatible con endpoint actual)
        vendedor_id = 1
        print(f"👤 Usando vendedor_id: {vendedor_id}")
        
    except Exception as e:
        print(f"⚠️  ADVERTENCIA: Error conectando a cliente-service: {e}")
        print("   El servicio iniciará sin datos de visitas")
        return
    
    # Generar visitas para 7 días (3 antes, hoy, 3 después)
    hoy = date.today()
    visitas = []
    
    # Distribuir clientes en los 7 días
    clientes_por_dia = max(3, len(clientes) // 7)
    
    for dia_offset in range(-3, 4):  # -3 a +3
        fecha_visita = hoy + timedelta(days=dia_offset)
        
        # Seleccionar clientes para este día
        inicio = (dia_offset + 3) * clientes_por_dia
        fin = inicio + clientes_por_dia
        clientes_del_dia = clientes[inicio:fin] if inicio < len(clientes) else clientes[:clientes_por_dia]
        
        for idx, cliente in enumerate(clientes_del_dia):
            # Usar coordenadas de Bogotá
            lat = BOGOTA_COORDS[idx % len(BOGOTA_COORDS)][0]
            lng = BOGOTA_COORDS[idx % len(BOGOTA_COORDS)][1]
            
            # Asignar horario
            horario = HORARIOS[idx % len(HORARIOS)]
            
            # Crear visita con datos reales del cliente
            direccion = cliente[2] if cliente[2] else "Dirección no disponible"
            ciudad = cliente[3] if cliente[3] else "Bogotá"
            
            visita = Visita(
                vendedor_id=vendedor_id,
                cliente=cliente[1],  # nombre del cliente
                direccion=direccion,
                fecha=fecha_visita,
                hora=horario,
                lat=lat,
                lng=lng,
                cliente_id=cliente[0],  # UUID del cliente
                ciudad=ciudad,
                estado="pendiente" if dia_offset >= 0 else random.choice(["completada", "pendiente"]),
                observaciones=f"Visita programada"
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
        
        print(f"✅ Generadas {len(visitas)} visitas desde cliente-service:")
        print(f"   - 3 días antes: {len([v for v in visitas if v.fecha < hoy])} visitas")
        print(f"   - Hoy:          {len([v for v in visitas if v.fecha == hoy])} visitas")
        print(f"   - 3 días después: {len([v for v in visitas if v.fecha > hoy])} visitas")
        print(f"   - Fecha actual:  {hoy}")
        print(f"   - Rango:         {hoy - timedelta(days=3)} a {hoy + timedelta(days=3)}")


if __name__ == "__main__":
    generar_visitas_desde_cliente_service()