# app/dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.services.jwt_service import jwt_service
from app.models.user import User
from app.models.role import Role

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> dict:
    token = credentials.credentials
    
    payload = jwt_service.verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # ✅ OBTENER USUARIO CON ROL Y PERMISOS ACTUALIZADOS
    result = await db.execute(
        select(User)
        .options(selectinload(User.role).selectinload(Role.permissions))
        .where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # ✅ RETORNAR INFO ACTUALIZADA DESDE LA BD
    return {
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role.name,
        "permissions": [
            {"resource": p.resource, "action": p.action}
            for p in user.role.permissions
        ]
    }

def require_permission(resource: str, action: str):
    def permission_checker(current_user: dict = Depends(get_current_user)):
        permissions = current_user.get("permissions", [])
        
        # Admin tiene todos los permisos
        if current_user.get("role") == "ADMIN":
            return current_user
        
        has_permission = any(
            p.get("resource") == resource and p.get("action") == action
            for p in permissions
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: {resource}:{action}"
            )
        
        return current_user
    
    return permission_checker