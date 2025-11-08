from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine as sa_create_engine, text
from sqlalchemy.exc import OperationalError

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./visitas.db")

def ensure_database_exists():
    """Crea la base de datos si no existe (solo para PostgreSQL)"""
    if not DATABASE_URL.startswith("postgresql"):
        return  # Solo funciona con PostgreSQL
    
    # Extraer información de la URL
    try:
        # Conectar a la base de datos 'postgres' por defecto
        parts = DATABASE_URL.rsplit("/", 1)
        if len(parts) != 2:
            return
        
        base_url = parts[0]
        db_name = parts[1].split("?")[0]  # Remover parámetros de query si existen
        
        # Conectar a la base de datos postgres para crear la nueva DB
        postgres_url = f"{base_url}/postgres"
        
        # Usar isolation_level="AUTOCOMMIT" para poder crear base de datos
        temp_engine = sa_create_engine(postgres_url, isolation_level="AUTOCOMMIT")
        
        with temp_engine.connect() as conn:
            # Verificar si la base de datos existe
            result = conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
            )
            exists = result.fetchone() is not None
            
            if not exists:
                print(f"Creando base de datos '{db_name}'...")
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                print(f"Base de datos '{db_name}' creada exitosamente")
            else:
                print(f"Base de datos '{db_name}' ya existe")
        
        temp_engine.dispose()
    except Exception as e:
        print(f"Error al verificar/crear base de datos: {e}")
        # Continuar de todas formas, puede que la DB ya exista

# Asegurar que la base de datos existe antes de crear el engine
ensure_database_exists()

engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    """Crea todas las tablas en la base de datos"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependency para obtener una sesión de base de datos"""
    with Session(engine) as session:
        yield session
