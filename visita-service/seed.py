"""
Script de prueba para crear datos de ejemplo
"""
from database import init_db, engine
from models import Visita, Hallazgo, EstadoVisita
from sqlmodel import Session
from datetime import datetime

def seed_data():
    """Crea datos de ejemplo en la base de datos si está vacía"""
    init_db()
    
    with Session(engine) as session:
        # Verificar si ya hay datos
        visitas_count = session.query(Visita).count()
        if visitas_count > 0:
            print(f"✅ Base de datos ya contiene {visitas_count} visitas")
            return
        
        # Crear visitas de ejemplo
        visita1 = Visita(
            vendedor_id=1,
            cliente_id=10,
            nombre_contacto="Dr. Juan Pérez",
            observaciones="Cliente interesado en equipo de ultrasonido",
            estado=EstadoVisita.PENDIENTE
        )
        
        visita2 = Visita(
            vendedor_id=1,
            cliente_id=11,
            nombre_contacto="Dra. María González",
            observaciones="Requiere mantenimiento de equipo de rayos X",
            estado=EstadoVisita.EXITOSA
        )
        
        visita3 = Visita(
            vendedor_id=2,
            cliente_id=12,
            nombre_contacto="Dr. Carlos Ramírez",
            observaciones="Visita cancelada por indisponibilidad del cliente",
            estado=EstadoVisita.CANCELADA
        )
        
        session.add(visita1)
        session.add(visita2)
        session.add(visita3)
        session.commit()
        
        # Refrescar para obtener IDs
        session.refresh(visita1)
        session.refresh(visita2)
        
        # Agregar hallazgos de ejemplo
        hallazgo1 = Hallazgo(
            visita_id=visita1.id,
            tipo="texto",
            contenido="El equipo actual tiene 10 años de antigüedad y presenta fallas frecuentes",
            descripcion="Observación técnica"
        )
        
        hallazgo2 = Hallazgo(
            visita_id=visita2.id,
            tipo="texto",
            contenido="Generador del equipo de rayos X requiere reemplazo urgente",
            descripcion="Hallazgo crítico"
        )
        
        hallazgo3 = Hallazgo(
            visita_id=visita2.id,
            tipo="texto",
            contenido="Personal capacitado y dispuesto a recibir entrenamiento adicional",
            descripcion="Observación positiva"
        )
        
        session.add(hallazgo1)
        session.add(hallazgo2)
        session.add(hallazgo3)
        session.commit()
        
        print("✅ Base de datos inicializada con datos de ejemplo")
        print(f"   - {3} visitas creadas")
        print(f"   - {3} hallazgos creados")
        print(f"\nEstados de visitas:")
        print(f"   - Pendiente: 1")
        print(f"   - Exitosa: 1")
        print(f"   - Cancelada: 1")

if __name__ == "__main__":
    seed_data()
