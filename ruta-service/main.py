from fastapi import FastAPI, Depends, Query
from sqlmodel import Session, select
from database import get_session, init_db
from models import Visita
from datetime import date
from contextlib import asynccontextmanager
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Rutas Service",
    description="Servicio para gestionar visitas y rutas optimizadas",
    version="1.0.0",
    lifespan=lifespan
)

# ========================================
# Health check
# ========================================
@app.get("/health")
def health(): 
    return {"status": "healthy", "service": "rutas-service"}


# ========================================
# Endpoints de Visitas (EXISTENTES - NO MODIFICADOS)
# ========================================
@app.get("/api/ruta")
def obtener_ruta(
    fecha: date = Query(...),
    vendedor_id: int = Query(...),
    session: Session = Depends(get_session)
):
    """
    Endpoint original para obtener visitas de un vendedor en una fecha
    """
    query = select(Visita).where(Visita.fecha == fecha, Visita.vendedor_id == vendedor_id)
    visitas = session.exec(query).all()

    visitas_ordenadas = sorted(visitas, key=lambda v: v.hora)
    result = []
    for i, v in enumerate(visitas_ordenadas):
        data = v.dict()
        data["tiempo_desde_anterior"] = None if i == 0 else "15 min"  # Simulado
        result.append(data)

    return {"fecha": fecha, "visitas": result}


# ========================================
# NUEVO: Incluir router de Rutas Optimizadas
# ========================================
from router_rutas import router as rutas_router
app.include_router(rutas_router)


# Root endpoint con información del servicio
@app.get("/")
def root():
    return {
        "service": "Rutas Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "visitas": "/api/ruta",
            "rutas": "/rutas"
        }
    }
