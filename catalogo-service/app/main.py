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
# El ALB rutea /catalog/* al servicio, por lo que el prefix completo debe ser /catalog/api/*
app.include_router(catalog_router, prefix="/catalog/api/catalog")
app.include_router(inventario_router, prefix="/catalog/api/inventory")

# Logs de configuración de rutas para debugging
logger.info("📦 Catalog API iniciada con gestión de inventario")
logger.info("🔗 Rutas registradas:")
logger.info("   ├─ Catalog router: prefix='/catalog/api/catalog'")
logger.info("   │  └─ Endpoints: /items, /items/{id}, /items/{id}/inventario, /items/bulk-upload")
logger.info("   └─ Inventory router: prefix='/catalog/api/inventory'")
logger.info("      └─ Endpoints: /movements, /transfers, /alerts, /reports/saldos")
logger.info(f"⚙️  Configuración:")
logger.info(f"   ├─ Puerto: 3000")
logger.info(f"   ├─ Health check: /health")
logger.info(f"   └─ API Prefix (interno): {settings.api_prefix}")

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
