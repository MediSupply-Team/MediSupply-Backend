# tests/integration/test_auth_refresh.py
import pytest
from app.services.jwt_service import jwt_service
from datetime import datetime, timedelta
from jose import jwt

@pytest.mark.anyio
async def test_refresh_token_success(client):
    """Test: Refresh token válido retorna nuevo access token"""
    # Crear refresh token válido
    refresh_token = jwt_service.create_refresh_token(user_id=1)
    
    r = client.post("/refresh", json={
        "refresh_token": refresh_token
    })
    
    assert r.status_code == 200
    data = r.json()
    assert "token" in data
    assert isinstance(data["token"], str)
    assert len(data["token"]) > 0

@pytest.mark.anyio
async def test_refresh_token_invalid(client):
    """Test: Refresh token inválido retorna 401"""
    r = client.post("/refresh", json={
        "refresh_token": "invalid.token.here"
    })
    
    assert r.status_code == 401
    assert "detail" in r.json()

@pytest.mark.anyio
async def test_refresh_token_expired(client):
    """Test: Refresh token expirado retorna 401"""
    # Crear token expirado
    expire = datetime.utcnow() - timedelta(days=1)
    to_encode = {
        "user_id": 1,
        "exp": expire,
        "type": "refresh"
    }
    expired_token = jwt.encode(
        to_encode, 
        jwt_service.SECRET_KEY, 
        algorithm=jwt_service.ALGORITHM
    )
    
    r = client.post("/refresh", json={
        "refresh_token": expired_token
    })
    
    assert r.status_code == 401

@pytest.mark.anyio
async def test_refresh_with_access_token_fails(client):
    """Test: Usar access token en lugar de refresh token falla"""
    # Crear access token (tipo incorrecto)
    access_token = jwt_service.create_access_token({
        "user_id": 1,
        "email": "test@example.com",
        "role": "USER"
    })
    
    r = client.post("/refresh", json={
        "refresh_token": access_token
    })
    
    assert r.status_code == 401
    assert "detail" in r.json()
