from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.routes.client import router as cliente_router
from app.routes.vendedor import router as vendedor_router
from app.config import settings
from app.db import engine, Base

app = FastAPI(title="MediSupply Cliente API", description="API para gestión de clientes y vendedores", version="2.0.0")
app.include_router(cliente_router, prefix=settings.api_prefix)
app.include_router(vendedor_router, prefix=f"{settings.api_prefix}/vendedores")

@app.get("/health")
async def health_check():
    """Health check endpoint en raíz para ALB"""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "cliente-service"}
    )

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)