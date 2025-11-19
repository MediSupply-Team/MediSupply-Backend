# tests/integration/test_auth_register.py
import pytest
from sqlalchemy import select
from app.models.user import User
from app.models.role import Role

@pytest.mark.anyio
async def test_register_success(client, test_session, override_db):
    """Test: Registro exitoso crea usuario y retorna token"""
    # Crear rol
    role = Role(name="USER", description="Regular user")
    test_session.add(role)
    await test_session.flush()
    role_id = role.id
    await test_session.commit()
    
    # Registrar
    r = client.post("/register", json={
        "email": "newuser@example.com",
        "password": "password123",
        "name": "New User",
        "role_id": role_id,
        "hospital_id": "HOSP-001"
    })
    
    assert r.status_code == 201
    data = r.json()
    assert "token" in data
    assert "refresh_token" in data
    assert "user" in data
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["name"] == "New User"
    
    # Verificar que se creó en BD
    result = await test_session.execute(
        select(User).where(User.email == "newuser@example.com")
    )
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.is_active is True
    assert user.hospital_id == "HOSP-001"

@pytest.mark.anyio
async def test_register_duplicate_email(client, test_session, override_db):
    """Test: Registro con email existente retorna 400"""
    # Crear rol y usuario existente
    role = Role(name="USER", description="Regular user")
    test_session.add(role)
    await test_session.flush()
    
    from app.services.password_service import password_service
    user = User(
        email="existing@example.com",
        password_hash=password_service.hash_password("pass123"),
        name="Existing User",
        role_id=role.id,
        is_active=True
    )
    test_session.add(user)
    await test_session.commit()
    
    # Intentar registrar con mismo email
    r = client.post("/register", json={
        "email": "existing@example.com",
        "password": "newpass",
        "name": "New User",
        "role_id": role.id
    })
    
    assert r.status_code == 400
    assert "detail" in r.json()
    assert "email ya está registrado" in r.json()["detail"].lower()

@pytest.mark.anyio
async def test_register_without_optional_fields(client, test_session, override_db):
    """Test: Registro sin campos opcionales funciona"""
    role = Role(name="USER", description="Regular user")
    test_session.add(role)
    await test_session.flush()
    role_id = role.id
    await test_session.commit()
    
    r = client.post("/register", json={
        "email": "minimal@example.com",
        "password": "password123",
        "name": "Minimal User",
        "role_id": role_id
    })
    
    assert r.status_code == 201
    data = r.json()
    assert data["user"]["email"] == "minimal@example.com"
    
    # Verificar en BD
    result = await test_session.execute(
        select(User).where(User.email == "minimal@example.com")
    )
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.hospital_id is None
    assert user.cliente_id is None
    assert user.venta_id is None

@pytest.mark.anyio
async def test_register_with_all_fields(client, test_session, override_db):
    """Test: Registro con todos los campos opcionales"""
    role = Role(name="SELLER", description="Seller role")
    test_session.add(role)
    await test_session.flush()
    role_id = role.id
    await test_session.commit()
    
    r = client.post("/register", json={
        "email": "complete@example.com",
        "password": "password123",
        "name": "Complete User",
        "role_id": role_id,
        "hospital_id": "HOSP-002",
        "cliente_id": "CLI-001",
        "venta_id": "VTA-001"
    })
    
    assert r.status_code == 201
    
    # Verificar en BD
    result = await test_session.execute(
        select(User).where(User.email == "complete@example.com")
    )
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.hospital_id == "HOSP-002"
    assert user.cliente_id == "CLI-001"
    assert user.venta_id == "VTA-001"

@pytest.mark.anyio
async def test_register_invalid_role_id(client, test_session, override_db):
    """Test: Registro con role_id inexistente falla"""
    r = client.post("/register", json={
        "email": "invalid@example.com",
        "password": "password123",
        "name": "Invalid User",
        "role_id": 9999
    })
    
    assert r.status_code in (400, 500)
