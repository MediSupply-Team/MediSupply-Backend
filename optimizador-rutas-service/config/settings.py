from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    port: int = 8001
    environment: str = "development"
    log_level: str = "INFO"
    osrm_url: str
    mapbox_access_token: str
    ruta_service_url: str = "http://localhost:8000"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()