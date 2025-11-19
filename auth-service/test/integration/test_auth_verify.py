# tests/integration/test_auth_verify.py
import pytest
from sqlalchemy import select
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.services.password_service import password_service
from app.services.jwt_service import jwt_service
from datetime import datetime, timedelta
from jose import jwt

@pytest.mark.anyio
async def test_verify_token_success(client, test_session, override_db):
    """Test: Verify con token válido retorna info del usuario"""
    # Crear permisos
    perm = Permission(name="orders:read", resource="orders", action="read")
    test_session.add(perm)
    await test_session.flush()
    
    # Crear rol con permiso
    role = Role(name="USER", description="Regular user")
    role.permissions.append(perm)
    test_session.add(role)
    await test_session.flush()
    
    # Crear usuario
    hashed = password_service.hash_password("pass123")
    user = User(
        email="verify@example.com",
        password_hash=hashed,
        name="Verify User",
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
        "email": "verify@example.com",
        "role": "USER"
    })
    
    # Verificar
    r = client.post("/verify", headers={
        "Authorization": f"Bearer {token}"
    })
    
    assert r.status_code == 200
    data = r.json()
    assert data["user_id"] == user_id
    assert data["email"] == "verify@example.com"
    assert data["name"] == "Verify User"
    assert data["role"] == "USER"
    assert "permissions" in data
    assert "orders:read" in data["permissions"]

@pytest.mark.anyio
async def test_verify_token_missing_header(client):
    """Test: Verify sin Authorization header retorna 422"""
    r = client.post("/verify")
    assert r.status_code == 422

@pytest.mark.anyio
async def test_verify_token_invalid_format(client):
    """Test: Verify con formato inválido retorna 401"""
    r = client.post("/verify", headers={
        "Authorization": "InvalidFormat token"
    })
    assert r.status_code == 401

@pytest.mark.anyio
async def test_verify_token_invalid(client):
    """Test: Verify con token inválido retorna 401"""
    r = client.post("/verify", headers={
        "Authorization": "Bearer invalid.token.here"
    })
    assert r.status_code == 401

@pytest.mark.anyio
async def test_verify_token_expired(client):
    """Test: Verify con token expirado retorna 401"""
    expire = datetime.utcnow() - timedelta(minutes=10)
    to_encode = {
        "user_id": 1,
        "email": "test@example.com",
        "exp": expire,
        "type": "access"
    }
    expired_token = jwt.encode(
        to_encode,
        jwt_service.SECRET_KEY,
        algorithm=jwt_service.ALGORITHM
    )
    
    r = client.post("/verify", headers={
        "Authorization": f"Bearer {expired_token}"
    })
    assert r.status_code == 401

@pytest.mark.anyio
async def test_verify_with_refresh_token_fails(client):
    """Test: Verify con refresh token falla"""
    refresh_token = jwt_service.create_refresh_token(user_id=1)
    
    r = client.post("/verify", headers={
        "Authorization": f"Bearer {refresh_token}"
    })
    assert r.status_code == 401

@pytest.mark.anyio
async def test_verify_user_not_found(client, test_session, override_db):
    """Test: Verify con user_id inexistente retorna 401"""
    token = jwt_service.create_access_token({
        "user_id": 99999,
        "email": "notfound@example.com",
        "role": "USER"
    })
    
    r = client.post("/verify", headers={
        "Authorization": f"Bearer {token}"
    })
    assert r.status_code == 401

@pytest.mark.anyio
async def test_verify_inactive_user(client, test_session, override_db):
    """Test: Verify con usuario inactivo retorna 401"""
    role = Role(name="USER", description="Regular user")
    test_session.add(role)
    await test_session.flush()
    
    hashed = password_service.hash_password("pass123")
    user = User(
        email="inactive@example.com",
        password_hash=hashed,
        name="Inactive User",
        role_id=role.id,
        is_active=False
    )
    test_session.add(user)
    await test_session.flush()
    user_id = user.id
    await test_session.commit()
    
    token = jwt_service.create_access_token({
        "user_id": user_id,
        "email": "inactive@example.com",
        "role": "USER"
    })
    
    r = client.post("/verify", headers={
        "Authorization": f"Bearer {token}"
    })
    assert r.status_code == 401
