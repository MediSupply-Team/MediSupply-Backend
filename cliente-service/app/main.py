from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.routes.client import router as cliente_router
from app.routes.vendedor import router as vendedor_router
from app.routes.catalogos import router as catalogos_router
from app.config import settings
from app.db import engine, Base, get_session
from app.models.client_model import Cliente

app = FastAPI(title="MediSupply Cliente API", description="API para gestión de clientes y vendedores", version="2.0.0")
app.include_router(cliente_router, prefix=settings.api_prefix)
app.include_router(vendedor_router, prefix=f"{settings.api_prefix}/vendedores")
app.include_router(catalogos_router, prefix=f"{settings.api_prefix}/catalogos")

@app.get("/health")
async def health_check():
    """Health check endpoint en raíz para ALB"""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "cliente-service"}
    )

@app.post("/seed-data", status_code=201)
async def seed_initial_data(session: AsyncSession = Depends(get_session)):
    """
    Endpoint auxiliar para cargar datos de clientes de prueba iniciales
    Idempotente: Solo inserta si no existen clientes con esos NITs
    """
    from sqlalchemy import select
    
    # Datos de clientes de ejemplo
    sample_clients = [
        {
            "nit": "900123456-7",
            "nombre": "Farmacia San José",
            "codigo_unico": "FSJ001",
            "email": "contacto@farmaciasanjose.com",
            "telefono": "+57-1-2345678",
            "direccion": "Calle 45 #12-34",
            "ciudad": "Bogotá",
            "pais": "CO",
            "rol": "cliente",
            "activo": True
        },
        {
            "nit": "800987654-3",
            "nombre": "Droguería El Buen Pastor",
            "codigo_unico": "DBP002",
            "email": "ventas@elbunpastor.com",
            "telefono": "+57-2-9876543",
            "direccion": "Carrera 15 #67-89",
            "ciudad": "Medellín",
            "pais": "CO",
            "rol": "cliente",
            "activo": True
        },
        {
            "nit": "700456789-1",
            "nombre": "Farmatodo Zona Norte",
            "codigo_unico": "FZN003",
            "email": "info@farmatodo.com",
            "telefono": "+57-5-4567890",
            "direccion": "Avenida Norte #23-45",
            "ciudad": "Barranquilla",
            "pais": "CO",
            "rol": "cliente",
            "activo": True
        },
        {
            "nit": "600345678-9",
            "nombre": "Centro Médico Salud Total",
            "codigo_unico": "CST004",
            "email": "compras@saludtotal.com",
            "telefono": "+57-1-3456789",
            "direccion": "Calle 85 #34-56",
            "ciudad": "Bogotá",
            "pais": "CO",
            "rol": "cliente",
            "activo": True
        },
        {
            "nit": "500234567-5",
            "nombre": "Farmacia Popular",
            "codigo_unico": "FPO005",
            "email": "pedidos@farmapopular.com",
            "telefono": "+57-4-2345678",
            "direccion": "Carrera 70 #45-67",
            "ciudad": "Medellín",
            "pais": "CO",
            "rol": "cliente",
            "activo": True
        }
    ]
    
    created_count = 0
    skipped_count = 0
    
    for client_data in sample_clients:
        # Verificar si ya existe por NIT
        stmt = select(Cliente).where(Cliente.nit == client_data["nit"])
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if not existing:
            cliente = Cliente(**client_data)
            session.add(cliente)
            created_count += 1
        else:
            skipped_count += 1
    
    await session.commit()
    
    return {
        "message": "Datos de clientes cargados exitosamente",
        "created": created_count,
        "skipped": skipped_count,
        "total": len(sample_clients)
    }

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)