from sqlmodel import Session,delete
from database import engine, init_db
from models import Visita
from datetime import date
from datetime import date, timedelta

init_db()

hoy = date.today()
ayer = hoy - timedelta(days=1)
anteayer = hoy - timedelta(days=2)

visitas = [
    # Día 1 - 10 de octubre de 2025
    Visita(
        vendedor_id=1,
        cliente="Fundación Santa Fe de Bogotá",
        direccion="Carrera 7 #117-15, Usaquén, Bogotá",
        fecha=anteayer,
        hora="09:00",
        lat=4.69546,
        lng=-74.03281
    ),
    Visita(
        vendedor_id=1,
        cliente="Clínica del Country",
        direccion="Carrera 16 #82-32, Chapinero, Bogotá",
        fecha=anteayer,
        hora="11:00",
        lat=4.6680624,
        lng=-74.0568885
    ),
    Visita(
        vendedor_id=1,
        cliente="Hospital Universitario San Ignacio",
        direccion="Carrera 7 #40-62, Chapinero, Bogotá",
        fecha=anteayer,
        hora="13:00",
        lat=4.62842,
        lng=-74.06417
    ),
    Visita(
        vendedor_id=1,
        cliente="Clínica Reina Sofía",
        direccion="Calle 127 #20-71, Usaquén, Bogotá",
        fecha=anteayer,
        hora="15:30",
        lat=4.707713,
        lng=-74.046708
    ),

    # Día 2 - 11 de octubre de 2025
    Visita(
        vendedor_id=1,
        cliente="Clínica Universidad de La Sabana",
        direccion="Autopista Norte km 21, Chía (zona metropolitana de Bogotá)",
        fecha=ayer,
        hora="09:00",
        lat=4.867019,
        lng=-74.041611
    ),
    Visita(
        vendedor_id=1,
        cliente="Clínica Marly",
        direccion="Carrera 13 #49-90, Chapinero, Bogotá",
        fecha=ayer,
        hora="11:00",
        lat=4.639958,
        lng=-74.065481
    ),
    Visita(
        vendedor_id=1,
        cliente="Hospital Central de la Policía Nacional",
        direccion="Avenida Caracas #66-00, Chapinero, Bogotá",
        fecha=ayer,
        hora="13:30",
        lat=4.652655,
        lng=-74.073751
    ),
    Visita(
        vendedor_id=1,
        cliente="Clínica Shaio",
        direccion="Avenida Suba #116-20, Suba, Bogotá",
        fecha=ayer,
        hora="16:00",
        lat=4.706317,
        lng=-74.070743
    ),

    # Día 3 - 12 de octubre de 2025
    Visita(
        vendedor_id=1,
        cliente="Clínica de Occidente",
        direccion="Avenida de las Américas #71C-29, Kennedy, Bogotá",
        fecha=hoy,
        hora="09:00",
        lat=4.626998,
        lng=-74.117929
    ),
    Visita(
        vendedor_id=1,
        cliente="Hospital de Suba",
        direccion="Calle 145 #91-19, Suba, Bogotá",
        fecha=hoy,
        hora="11:00",
        lat=4.7483,
        lng=-74.0863
    ),
    Visita(
        vendedor_id=1,
        cliente="Clínica Colombia",
        direccion="Carrera 23 #56-60, Teusaquillo, Bogotá",
        fecha=hoy,
        hora="13:30",
        lat=4.6432,
        lng=-74.0914
    ),
    Visita(
        vendedor_id=1,
        cliente="Clínica Los Nogales",
        direccion="Carrera 25 #78-25, Barrios Unidos, Bogotá",
        fecha=hoy,
        hora="15:30",
        lat=4.6663,
        lng=-74.0758
    ),
]

with Session(engine) as session:
    session.exec(delete(Visita))
    session.commit()

    session.add_all(visitas)
    session.commit()
    print("✅ Datos iniciales cargados.")