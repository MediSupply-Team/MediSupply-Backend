# tests/integration/test_auth_login.py
import pytest
from sqlalchemy import select
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.services.password_service import password_service

@pytest.mark.anyio
async def test_login_success(client, test_session, override_db):
    """Test: Login exitoso retorna token y datos de usuario"""
    # Crear rol
    role = Role(name="USER_LOGIN_SUCCESS", description="Regular user")
    test_session.add(role)
    await test_session.flush()
    
    # Crear usuario
    hashed = password_service.hash_password("password123")
    user = User(
        email="user@example.com",
        password_hash=hashed,
        name="Test User",
        role_id=role.id,
        is_active=True
    )
    test_session.add(user)
    await test_session.commit()
    
    # Login
    r = client.post("/login", json={
        "email": "user@example.com",
        "password": "password123"
    })
    
    assert r.status_code == 200
    data = r.json()
    assert "token" in data
    assert "refresh_token" in data
    assert "user" in data
    assert data["user"]["email"] == "user@example.com"
    assert data["user"]["name"] == "Test User"
    assert data["user"]["role"] == "USER_LOGIN_SUCCESS"

@pytest.mark.anyio
async def test_login_invalid_email(client, test_session, override_db):
    """Test: Login con email inexistente retorna 401"""
    r = client.post("/login", json={
        "email": "notfound@example.com",
        "password": "password123"
    })
    
    assert r.status_code == 401
    assert "detail" in r.json()

@pytest.mark.anyio
async def test_login_invalid_password(client, test_session, override_db):
    """Test: Login con contraseña incorrecta retorna 401"""
    # Crear rol y usuario
    role = Role(name="USER_INVALID_PASS", description="Regular user")
    test_session.add(role)
    await test_session.flush()
    
    hashed = password_service.hash_password("correct_password")
    user = User(
        email="user@example.com",
        password_hash=hashed,
        name="Test User",
        role_id=role.id,
        is_active=True
    )
    test_session.add(user)
    await test_session.commit()
    
    # Login con contraseña incorrecta
    r = client.post("/login", json={
        "email": "user@example.com",
        "password": "wrong_password"
    })
    
    assert r.status_code == 401
    assert "detail" in r.json()

@pytest.mark.anyio
async def test_login_inactive_user(client, test_session, override_db):
    """Test: Login con usuario inactivo retorna 401"""
    role = Role(name="USER_INACTIVE", description="Regular user")
    test_session.add(role)
    await test_session.flush()
    
    hashed = password_service.hash_password("password123")
    user = User(
        email="inactive@example.com",
        password_hash=hashed,
        name="Inactive User",
        role_id=role.id,
        is_active=False
    )
    test_session.add(user)
    await test_session.commit()
    
    r = client.post("/login", json={
        "email": "inactive@example.com",
        "password": "password123"
    })
    
    assert r.status_code == 401
    assert "detail" in r.json()

@pytest.mark.anyio
async def test_login_with_permissions(client, test_session, override_db):
    """Test: Login retorna permisos del rol"""
    # Crear permisos
    perm1 = Permission(name="orders:create", resource="orders", action="create")
    perm2 = Permission(name="orders:read", resource="orders", action="read")
    test_session.add_all([perm1, perm2])
    await test_session.flush()
    
    # Crear rol con permisos
    role = Role(name="SELLER", description="Sales role")
    role.permissions.extend([perm1, perm2])
    test_session.add(role)
    await test_session.flush()
    
    # Crear usuario
    hashed = password_service.hash_password("password123")
    user = User(
        email="seller@example.com",
        password_hash=hashed,
        name="Seller User",
        role_id=role.id,
        is_active=True
    )
    test_session.add(user)
    await test_session.commit()
    
    # Login
    r = client.post("/login", json={
        "email": "seller@example.com",
        "password": "password123"
    })
    
    assert r.status_code == 200
    data = r.json()
    assert "user" in data
    assert "permissions" in data["user"]
    permissions = data["user"]["permissions"]
    assert "orders:create" in permissions
    assert "orders:read" in permissions
    assert len(permissions) == 2
