# tests/unit/test_auth_dependencies.py
import pytest
from fastapi import HTTPException
from app.dependencies.auth import get_current_user, require_permission
from app.services.jwt_service import jwt_service
from app.models.user import User
from app.models.role import Role
from app.services.password_service import password_service
from fastapi.security import HTTPAuthorizationCredentials

@pytest.mark.anyio
async def test_get_current_user_success(test_session):
    """Test: get_current_user con token válido retorna payload"""
    # Crear rol y usuario
    role = Role(name="USER", description="Regular user")
    test_session.add(role)
    await test_session.flush()
    
    hashed = password_service.hash_password("pass123")
    user = User(
        email="test@example.com",
        password_hash=hashed,
        name="Test User",
        role_id=role.id,
        is_active=True
    )
    test_session.add(user)
    await test_session.flush()
    user_id = user.id
    await test_session.commit()
    
    # Crear token
    token = jwt_service.create_access_token({
        "user_id": user_id,
        "email": "test@example.com",
        "role": "USER"
    })
    
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    
    # Llamar get_current_user
    result = await get_current_user(credentials, test_session)
    
    assert result is not None
    assert result["user_id"] == user_id
    assert result["email"] == "test@example.com"

@pytest.mark.anyio
async def test_get_current_user_invalid_token(test_session):
    """Test: get_current_user con token inválido lanza HTTPException"""
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="invalid.token.here"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials, test_session)
    
    assert exc_info.value.status_code == 401

@pytest.mark.anyio
async def test_get_current_user_wrong_token_type(test_session):
    """Test: get_current_user con refresh token lanza HTTPException"""
    refresh_token = jwt_service.create_refresh_token(user_id=1)
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=refresh_token
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials, test_session)
    
    assert exc_info.value.status_code == 401
    assert "Invalid token type" in str(exc_info.value.detail)

@pytest.mark.anyio
async def test_get_current_user_not_found(test_session):
    """Test: get_current_user con user_id inexistente lanza HTTPException"""
    token = jwt_service.create_access_token({
        "user_id": 99999,
        "email": "notfound@example.com",
        "role": "USER"
    })
    
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials, test_session)
    
    assert exc_info.value.status_code == 401

def test_require_permission_admin_bypasses():
    """Test: require_permission con rol ADMIN siempre permite"""
    checker = require_permission("orders", "delete")
    
    current_user = {
        "user_id": 1,
        "role": "ADMIN",
        "permissions": []
    }
    
    result = checker(current_user)
    assert result == current_user

def test_require_permission_with_permission():
    """Test: require_permission con permiso correcto permite"""
    checker = require_permission("orders", "create")
    
    current_user = {
        "user_id": 1,
        "role": "USER",
        "permissions": [
            {"resource": "orders", "action": "create"},
            {"resource": "orders", "action": "read"}
        ]
    }
    
    result = checker(current_user)
    assert result == current_user

def test_require_permission_without_permission():
    """Test: require_permission sin permiso lanza HTTPException"""
    checker = require_permission("orders", "delete")
    
    current_user = {
        "user_id": 1,
        "role": "USER",
        "permissions": [
            {"resource": "orders", "action": "read"}
        ]
    }
    
    with pytest.raises(HTTPException) as exc_info:
        checker(current_user)
    
    assert exc_info.value.status_code == 403
    assert "orders:delete" in str(exc_info.value.detail)

def test_require_permission_empty_permissions():
    """Test: require_permission sin permisos lanza HTTPException"""
    checker = require_permission("orders", "read")
    
    current_user = {
        "user_id": 1,
        "role": "USER",
        "permissions": []
    }
    
    with pytest.raises(HTTPException) as exc_info:
        checker(current_user)
    
    assert exc_info.value.status_code == 403
