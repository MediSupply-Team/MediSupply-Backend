from fastapi import FastAPI
from app.routes.catalog import router as catalog_router
from app.routes.inventario import router as inventario_router
from app.routes.proveedor import router as proveedor_router
from app.config import settings
from app.db import engine, Base
import logging
from app.websockets.ws_catalog_router import router as ws_catalog_router
from fastapi.middleware.cors import CORSMiddleware 

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MediSupply Catalog API",
    description="API para gestión de catálogo de productos, inventario y proveedores",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
# Rutas públicas simples: /api/v1/catalog/*, /api/v1/inventory/*, /api/v1/proveedores/*
app.include_router(catalog_router, prefix="/api/v1/catalog")
app.include_router(inventario_router, prefix="/api/v1/inventory")
app.include_router(proveedor_router, prefix="/api/v1/proveedores")
app.include_router(ws_catalog_router, prefix="/api/v1/catalog") 

# Logs de configuración de rutas para debugging
logger.info("📦 Catalog API iniciada con gestión de inventario y proveedores")
logger.info("🔗 Rutas registradas:")
logger.info("   ├─ Catalog: prefix='/api/v1/catalog'")
logger.info("   │  └─ Endpoints: /api/v1/catalog/items, /api/v1/catalog/items/{id}")
logger.info("   ├─ Inventory: prefix='/api/v1/inventory'")
logger.info("   │  └─ Endpoints: /api/v1/inventory/movements, etc.")
logger.info("   ├─ Proveedores: prefix='/api/v1/proveedores'")
logger.info("   │  └─ Endpoints: /api/v1/proveedores, /api/v1/proveedores/{id}")
logger.info("   └─ WebSocket: /api/v1/catalog/items/ws")
logger.info(f"⚙️  Configuración:")
logger.info(f"   ├─ Puerto: 3000")
logger.info(f"   ├─ Health check: /health")
logger.info(f"   ├─ ALB path pattern: /api/v1/* → forward directo")
logger.info(f"   └─ BFF llama: {{ALB_URL}}/api/v1/catalog/items")

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
