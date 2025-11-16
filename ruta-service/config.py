"""
Configuración del servicio de rutas
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración del servicio de rutas"""
    # Base de datos
    database_url: str
    
    # Mapbox
    mapbox_access_token: str
    
    # Servidor
    port: int = 8000
    environment: str = "development"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        env_file_encoding = 'utf-8'


settings = Settings()
