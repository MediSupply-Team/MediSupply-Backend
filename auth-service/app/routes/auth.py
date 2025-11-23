# app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RefreshTokenRequest
from app.models.user import User
from app.models.role import Role
from app.services.password_service import password_service
from app.services.jwt_service import jwt_service

router = APIRouter(tags=["auth"])

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Autenticar usuario y retornar token JWT"""
    
    # Buscar usuario
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas o usuario inactivo"
        )
    
    # Verificar contraseña
    if not password_service.verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )
    
    # Obtener rol y permisos (con eager loading)
    result = await db.execute(
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.id == user.role_id)
    )
    role = result.scalar_one()
    
    # Preparar permisos
    permissions = [p.name for p in role.permissions]
    
    # Crear tokens
    access_token = jwt_service.create_access_token(
        data={
            "user_id": user.id,
            "email": user.email,
            "role": role.name
        }
    )
    
    refresh_token = jwt_service.create_refresh_token(user_id=user.id)
    
    return LoginResponse(
        token=access_token,
        refresh_token=refresh_token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": role.name,
            "permissions": permissions,
            "cliente_id": user.cliente_id,
            "venta_id": user.venta_id
        }
    )

@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Registrar nuevo usuario"""
    
    # Verificar si el email ya existe
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    role_result = await db.execute(
        select(Role).where(Role.id == request.role_id)
    )
    role_exists = role_result.scalar_one_or_none()
    
    if not role_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El rol con ID {request.role_id} no existe"
        )
    
    # Crear nuevo usuario
    hashed_password = password_service.hash_password(request.password)
    new_user = User(
        email=request.email,
        password_hash=hashed_password,
        name=request.name,
        role_id=request.role_id,
        hospital_id=request.hospital_id,
        cliente_id=request.cliente_id,
        venta_id=request.venta_id,
        is_active=True
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Obtener rol con permisos (eager loading)
    result = await db.execute(
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.id == new_user.role_id)
    )
    role = result.scalar_one()
    
    # Preparar permisos
    permissions = [p.name for p in role.permissions]
    
    # Crear tokens
    access_token = jwt_service.create_access_token(
        data={
            "user_id": new_user.id,
            "email": new_user.email,
            "role": role.name
        }
    )
    
    refresh_token = jwt_service.create_refresh_token(user_id=new_user.id)
    
    return LoginResponse(
        token=access_token,
        refresh_token=refresh_token,
        user={
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.name,
            "role": role.name,
            "permissions": permissions,
            "cliente_id": new_user.cliente_id,
            "venta_id": new_user.venta_id,
            "hospital_id": new_user.hospital_id
        }
    )

@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest):
    """Renovar access token usando refresh token"""
    
    payload = jwt_service.verify_token(request.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado"
        )
    
    # Crear nuevo access token
    new_access_token = jwt_service.create_access_token(
        data={
            "user_id": payload["user_id"],
            "email": payload.get("email", ""),
            "role": payload.get("role", "")
        }
    )
    
    return {"token": new_access_token}

# ============================================================
# ENDPOINT NUEVO: VERIFICAR TOKEN (para BFFs)
# ============================================================

@router.post("/verify")
async def verify_token(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Verificar token JWT y retornar información del usuario
    
    Este endpoint es llamado por los BFFs para validar tokens
    en cada request protegido
    """
    
    # Validar formato del header
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    # Extraer token
    token = authorization.replace("Bearer ", "")
    
    # Validar token JWT
    payload = jwt_service.verify_token(token)
    
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )
    
    # Obtener usuario de la base de datos
    user_id = payload.get("user_id")
    
    result = await db.execute(
        select(User)
        .options(selectinload(User.role).selectinload(Role.permissions))
        .where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo"
        )
    
    # Retornar información del usuario
    return {
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role.name,
        "permissions": [p.name for p in user.role.permissions]
    }