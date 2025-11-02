from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./visitas.db")
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    """Crea todas las tablas en la base de datos"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependency para obtener una sesión de base de datos"""
    with Session(engine) as session:
        yield session
