from fastapi import FastAPI
from app.routes.catalog import router as catalog_router
from app.routes.inventario import router as inventario_router
from app.config import settings
from app.db import engine, Base
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MediSupply Catalog API",
    description="API para gestión de catálogo de productos y movimientos de inventario",
    version="2.0.0"
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "catalogo-service",
        "version": "2.0.0",
        "features": ["catalog", "inventory-movements", "alerts"]
    }

# Registrar routers
app.include_router(catalog_router, prefix=f"{settings.api_prefix}/catalog")
app.include_router(inventario_router, prefix=f"{settings.api_prefix}/inventario")

logger.info("📦 Catalog API iniciada con gestión de inventario")

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
