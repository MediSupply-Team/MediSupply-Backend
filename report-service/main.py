from fastapi import FastAPI, Request
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


# Middleware personalizado para manejar CORS sin duplicados
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    response = await call_next(request)
    
    # Limpiar headers CORS existentes
    headers_to_remove = [
        "access-control-allow-origin",
        "access-control-allow-credentials",
        "access-control-allow-methods",
        "access-control-allow-headers"
    ]
    
    for header in headers_to_remove:
        if header in response.headers:
            del response.headers[header]
    
    # Agregar headers CORS limpios
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"
    
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response


@app.get("/health")
def health(): 
    return {"ok": True, "service": "reports"}


# Monta el router de reportes 
app.include_router(reports_router)