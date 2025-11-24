# tests/unit/test_models.py
import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission

@pytest.mark.anyio
async def test_user_model_creation(test_session):
    """Test: Crear usuario con campos obligatorios"""
    role = Role(name="USER", description="Regular user")
    test_session.add(role)
    await test_session.flush()
    
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        name="Test User",
        role_id=role.id,
        is_active=True
    )
    test_session.add(user)
    await test_session.commit()
    
    result = await test_session.execute(
        select(User).where(User.email == "test@example.com")
    )
    saved_user = result.scalar_one()
    
    assert saved_user.email == "test@example.com"
    assert saved_user.name == "Test User"
    assert saved_user.is_active is True
    assert saved_user.created_at is not None

@pytest.mark.anyio
async def test_user_with_optional_fields(test_session):
    """Test: Crear usuario con campos opcionales"""
    role = Role(name="SELLER", description="Seller role")
    test_session.add(role)
    await test_session.flush()
    
    user = User(
        email="seller@example.com",
        password_hash="hashed",
        name="Seller User",
        role_id=role.id,
        hospital_id="HOSP-001",
        cliente_id="CLI-001",
        venta_id="VTA-001",
        is_active=True
    )
    test_session.add(user)
    await test_session.commit()
    
    result = await test_session.execute(
        select(User).where(User.email == "seller@example.com")
    )
    saved_user = result.scalar_one()
    
    assert saved_user.hospital_id == "HOSP-001"
    assert saved_user.cliente_id == "CLI-001"
    assert saved_user.venta_id == "VTA-001"

@pytest.mark.anyio
async def test_role_model_creation(test_session):
    """Test: Crear rol"""
    role = Role(name="ADMIN", description="Administrator")
    test_session.add(role)
    await test_session.commit()
    
    result = await test_session.execute(
        select(Role).where(Role.name == "ADMIN")
    )
    saved_role = result.scalar_one()
    
    assert saved_role.name == "ADMIN"
    assert saved_role.description == "Administrator"
    assert saved_role.created_at is not None

@pytest.mark.anyio
async def test_permission_model_creation(test_session):
    """Test: Crear permiso"""
    perm = Permission(
        name="orders:create",
        resource="orders",
        action="create"
    )
    test_session.add(perm)
    await test_session.commit()
    
    result = await test_session.execute(
        select(Permission).where(Permission.name == "orders:create")
    )
    saved_perm = result.scalar_one()
    
    assert saved_perm.name == "orders:create"
    assert saved_perm.resource == "orders"
    assert saved_perm.action == "create"

@pytest.mark.anyio
async def test_user_role_relationship(test_session):
    """Test: Relación User -> Role"""
    role = Role(name="USER", description="Regular user")
    test_session.add(role)
    await test_session.flush()
    
    user = User(
        email="test@example.com",
        password_hash="hashed",
        name="Test User",
        role_id=role.id,
        is_active=True
    )
    test_session.add(user)
    await test_session.commit()
    
    # Cargar con relación
    result = await test_session.execute(
        select(User)
        .options(selectinload(User.role))
        .where(User.email == "test@example.com")
    )
    loaded_user = result.scalar_one()
    
    assert loaded_user.role is not None
    assert loaded_user.role.name == "USER"

@pytest.mark.anyio
async def test_role_permissions_relationship(test_session):
    """Test: Relación Role -> Permissions (many-to-many)"""
    # Crear permisos
    perm1 = Permission(name="orders:create", resource="orders", action="create")
    perm2 = Permission(name="orders:read", resource="orders", action="read")
    test_session.add_all([perm1, perm2])
    await test_session.flush()
    
    # Crear rol con permisos
    role = Role(name="SELLER", description="Seller role")
    role.permissions.extend([perm1, perm2])
    test_session.add(role)
    await test_session.commit()
    
    # Cargar con relación
    result = await test_session.execute(
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.name == "SELLER")
    )
    loaded_role = result.scalar_one()
    
    assert len(loaded_role.permissions) == 2
    perm_names = [p.name for p in loaded_role.permissions]
    assert "orders:create" in perm_names
    assert "orders:read" in perm_names

@pytest.mark.anyio
async def test_role_users_relationship(test_session):
    """Test: Relación Role -> Users"""
    role = Role(name="USER", description="Regular user")
    test_session.add(role)
    await test_session.flush()
    
    user1 = User(
        email="user1@example.com",
        password_hash="hash1",
        name="User 1",
        role_id=role.id,
        is_active=True
    )
    user2 = User(
        email="user2@example.com",
        password_hash="hash2",
        name="User 2",
        role_id=role.id,
        is_active=True
    )
    test_session.add_all([user1, user2])
    await test_session.commit()
    
    # Cargar con relación
    result = await test_session.execute(
        select(Role)
        .options(selectinload(Role.users))
        .where(Role.name == "USER")
    )
    loaded_role = result.scalar_one()
    
    assert len(loaded_role.users) == 2
    emails = [u.email for u in loaded_role.users]
    assert "user1@example.com" in emails
    assert "user2@example.com" in emails

@pytest.mark.anyio
async def test_user_unique_email_constraint(test_session):
    """Test: Constraint de email único"""
    role = Role(name="USER", description="Regular user")
    test_session.add(role)
    await test_session.flush()
    
    user1 = User(
        email="duplicate@example.com",
        password_hash="hash1",
        name="User 1",
        role_id=role.id,
        is_active=True
    )
    test_session.add(user1)
    await test_session.commit()
    
    user2 = User(
        email="duplicate@example.com",
        password_hash="hash2",
        name="User 2",
        role_id=role.id,
        is_active=True
    )
    test_session.add(user2)
    
    with pytest.raises(Exception):
        await test_session.commit()
