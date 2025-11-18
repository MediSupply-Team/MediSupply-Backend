from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from contextlib import asynccontextmanager
from routers.reports import router as reports_router
from services.database_client import db_client
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Middleware personalizado para limpiar headers CORS duplicados
class CORSCleanupMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Remover cualquier header CORS existente para evitar duplicados
        if "access-control-allow-origin" in response.headers:
            del response.headers["access-control-allow-origin"]
        if "access-control-allow-credentials" in response.headers:
            del response.headers["access-control-allow-credentials"]
        if "access-control-allow-methods" in response.headers:
            del response.headers["access-control-allow-methods"]
        if "access-control-allow-headers" in response.headers:
            del response.headers["access-control-allow-headers"]
        
        # Agregar headers CORS limpios
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        
        return response

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación"""
    # Startup: Conectar a la base de datos
    logger.info("Conectando a la base de datos de Orders...")
    try:
        await db_client.connect()
        logger.info("Conexión a la base de datos establecida")
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        raise
    
    yield
    
    # Shutdown: Desconectar de la base de datos
    logger.info("Desconectando de la base de datos...")
    await db_client.disconnect()
    logger.info("Desconexión completada")

app = FastAPI(
    title="MediSupply Reports Service",
    description="Servicio de generación de reportes basado en datos reales de la base de datos de Orders",
    version="2.0.0",
    lifespan=lifespan
)

# Aplicar middleware personalizado primero para limpiar headers
app.add_middleware(CORSCleanupMiddleware)

@app.get("/health")
def health(): 
    return {"ok": True, "service": "reports"}

# Monta el router de reportes 
app.include_router(reports_router)