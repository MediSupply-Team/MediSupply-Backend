# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth
from app.database import engine, Base
from app.routes import system 

# ← IMPORTANTE: Importar todos los modelos ANTES de crear las tablas
from app.models import Role, Permission, User, role_permissions

app = FastAPI(
    title="MediSupply Auth Service",
    version="1.0.0",
    description="Servicio de autenticación y autorización para MediSupply",
    root_path="/auth"
)
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router)
app.include_router(system.router, tags=["System"])

@app.get("/")
async def root():
    return {"message": "MediSupply Auth Service", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "auth-service"}

@app.on_event("startup")
async def on_startup():
    """Crear tablas automáticamente al iniciar"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Could not create tables on startup: {e}")
        print("Service will continue, but database operations may fail")