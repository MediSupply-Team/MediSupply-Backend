"""
Script de inicialización de visitas
Genera visitas dinámicas para 3 días antes, hoy, y 3 días después
Conecta con la BD de cliente-service para obtener clientes reales
Usa Mapbox para geocodificar direcciones reales
"""
from sqlmodel import Session, delete, create_engine, select
from sqlalchemy import text
from database import engine, init_db
from models import Visita
from datetime import date, timedelta
import os
import random
from geocoder_service import geocoder_service

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
        
        # Usar UUID de vendedor por defecto (compatible con nuevo schema)
        vendedor_id = "3c479f61-8eba-48b8-9c42-88dea377215b"
        print(f"👤 Usando vendedor_id: {vendedor_id}")
        
        # Obtener clientes asociados al vendedor desde cliente-service
        with Session(cliente_engine) as cliente_session:
            # Query para obtener clientes del vendedor específico (relación directa en tabla cliente)
            from sqlalchemy import text
            result = cliente_session.execute(text("""
                SELECT id::text, nombre, direccion, ciudad
                FROM cliente
                WHERE vendedor_id = :vendedor_id
                  AND activo = true 
                ORDER BY nombre
            """), {"vendedor_id": vendedor_id})
            clientes = result.fetchall()
            
            if not clientes:
                print(f"⚠️  ADVERTENCIA: No se encontraron clientes asociados al vendedor {vendedor_id}")
                print("   El servicio iniciará sin datos de visitas")
                return
            
            print(f"✅ Encontrados {len(clientes)} clientes para el vendedor")
        
    except Exception as e:
        print(f"⚠️  ADVERTENCIA: Error conectando a cliente-service: {e}")
        print("   El servicio iniciará sin datos de visitas")
        return
    
    # Generar visitas distribuyendo clientes desde hoy en adelante (máximo 2 por día)
    hoy = date.today()
    visitas = []
    clientes_por_dia = 2  # Máximo 2 clientes por día
    
    # Distribuir clientes desde hoy en adelante
    total_clientes = len(clientes)
    dias_necesarios = (total_clientes + clientes_por_dia - 1) // clientes_por_dia  # Redondeo hacia arriba
    
    print(f"📅 Distribuyendo {total_clientes} clientes en {dias_necesarios} días (max 2 por día)")
    
    for dia_offset in range(dias_necesarios):
        fecha_visita = hoy + timedelta(days=dia_offset)
        
        # Seleccionar clientes para este día (máximo 2)
        inicio = dia_offset * clientes_por_dia
        fin = min(inicio + clientes_por_dia, total_clientes)
        clientes_del_dia = clientes[inicio:fin]
        
        for idx, cliente in enumerate(clientes_del_dia):
            # Geocodificar dirección real del cliente usando Mapbox
            direccion = cliente[2] if cliente[2] else "Dirección no disponible"
            ciudad = cliente[3] if cliente[3] else "Bogotá"
            
            # Intentar geocodificar la dirección real
            try:
                geocode_result = geocoder_service.geocodificar(direccion, ciudad)
                lat = geocode_result["lat"]
                lng = geocode_result["lon"]
                print(f"✅ Geocodificado: {cliente[1]} - {direccion} -> ({lat}, {lng})")
            except Exception as e:
                # Si falla, usar coordenadas de respaldo de Bogotá
                print(f"⚠️  Error geocodificando {direccion}: {e}. Usando coordenadas de respaldo.")
                lat = BOGOTA_COORDS[idx % len(BOGOTA_COORDS)][0]
                lng = BOGOTA_COORDS[idx % len(BOGOTA_COORDS)][1]
            
            # Asignar horario
            horario = HORARIOS[idx % len(HORARIOS)]
            
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
                estado="pendiente",
                observaciones=f"Visita programada"
            )
            visitas.append(visita)
    
    # Guardar en la base de datos de rutas
    with Session(engine) as session:
        # Migración: Alterar tipo de columna vendedor_id si es necesario
        try:
            print("🔄 Verificando tipo de columna vendedor_id...")
            session.exec(text("""
                DO $$ 
                BEGIN
                    IF EXISTS (
                        SELECT 1 
                        FROM information_schema.columns 
                        WHERE table_name = 'visita' 
                        AND column_name = 'vendedor_id' 
                        AND data_type = 'integer'
                    ) THEN
                        ALTER TABLE visita ALTER COLUMN vendedor_id TYPE VARCHAR USING vendedor_id::text;
                        RAISE NOTICE 'Columna vendedor_id migrada a VARCHAR';
                    END IF;
                END $$;
            """))
            session.commit()
            print("✅ Tipo de columna verificado/actualizado")
        except Exception as e:
            print(f"⚠️  Error en migración de columna: {e}")
            session.rollback()
        
        # Limpiar visitas anteriores
        session.exec(delete(Visita))
        session.commit()
        
        # Insertar nuevas visitas
        session.add_all(visitas)
        session.commit()
        
        print(f"✅ Generadas {len(visitas)} visitas desde cliente-service:")
        print(f"   - Total clientes: {total_clientes}")
        print(f"   - Días necesarios: {dias_necesarios}")
        print(f"   - Fecha inicio: {hoy}")
        print(f"   - Fecha fin: {hoy + timedelta(days=dias_necesarios - 1)}")
        
        # Desglose por día
        for dia in range(dias_necesarios):
            fecha = hoy + timedelta(days=dia)
            visitas_dia = [v for v in visitas if v.fecha == fecha]
            print(f"   - {fecha}: {len(visitas_dia)} visitas")


if __name__ == "__main__":
    generar_visitas_desde_cliente_service()