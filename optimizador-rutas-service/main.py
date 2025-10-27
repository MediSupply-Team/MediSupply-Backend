from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers.optimizer_controller import router
from config.settings import settings
import uvicorn

# Crear app con configuración básica
app = FastAPI(
    title="MediSupply - Optimizador de Rutas",
    description="Sistema de optimización de rutas de entrega",
    version="1.0.0",
    docs_url="/docs",      
    redoc_url="/redoc"   
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "OK",
        "service": "optimizador-rutas-service",
        "version": "1.0.0"
    }

# Incluir rutas
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=True)