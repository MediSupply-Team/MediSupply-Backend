from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers.optimizer_controller import router
from config.settings import settings
import uvicorn

app = FastAPI(
    title="Optimizador de Rutas - MediSupply",
    description="Servicio de optimizacion de rutas con OSRM y Mapbox",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "OK",
        "service": "optimizador-rutas-service",
        "services": {
            "osrm": settings.osrm_url,
            "mapbox": "configured",
            "ruta_service": settings.ruta_service_url
        }
    }

# Routes
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True if settings.environment == "development" else False
    )