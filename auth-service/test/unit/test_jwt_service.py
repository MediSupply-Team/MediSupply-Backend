# tests/unit/test_jwt_service.py
import pytest
from datetime import datetime, timedelta
from jose import jwt, JWTError
from app.services.jwt_service import jwt_service, JWTService

def test_create_access_token():
    data = {"user_id": 1, "email": "test@example.com", "role": "USER"}
    token = jwt_service.create_access_token(data)
    
    assert isinstance(token, str)
    assert len(token) > 0
    
    payload = jwt.decode(token, JWTService.SECRET_KEY, algorithms=[JWTService.ALGORITHM])
    assert payload["user_id"] == 1
    assert payload["email"] == "test@example.com"
    assert payload["role"] == "USER"
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload

def test_create_refresh_token():
    user_id = 42
    token = jwt_service.create_refresh_token(user_id)
    
    assert isinstance(token, str)
    assert len(token) > 0
    
    payload = jwt.decode(token, JWTService.SECRET_KEY, algorithms=[JWTService.ALGORITHM])
    assert payload["user_id"] == user_id
    assert payload["type"] == "refresh"
    assert "exp" in payload
    assert "iat" in payload

def test_verify_token_valid():
    data = {"user_id": 1, "email": "test@example.com", "role": "ADMIN"}
    token = jwt_service.create_access_token(data)
    
    payload = jwt_service.verify_token(token)
    assert payload is not None
    assert payload["user_id"] == 1
    assert payload["email"] == "test@example.com"
    assert payload["role"] == "ADMIN"

def test_verify_token_invalid():
    invalid_token = "invalid.token.here"
    payload = jwt_service.verify_token(invalid_token)
    assert payload is None

def test_verify_token_expired():
    data = {"user_id": 1, "email": "test@example.com"}
    
    # Crear token expirado
    expire = datetime.utcnow() - timedelta(minutes=10)
    to_encode = data.copy()
    to_encode.update({"exp": expire, "type": "access"})
    expired_token = jwt.encode(to_encode, JWTService.SECRET_KEY, algorithm=JWTService.ALGORITHM)
    
    payload = jwt_service.verify_token(expired_token)
    assert payload is None

def test_access_token_expiration_time():
    token = jwt_service.create_access_token({"user_id": 1})
    payload = jwt.decode(token, JWTService.SECRET_KEY, algorithms=[JWTService.ALGORITHM])
    
    exp_time = datetime.fromtimestamp(payload["exp"])
    iat_time = datetime.fromtimestamp(payload["iat"])
    diff = (exp_time - iat_time).total_seconds() / 60
    
    assert abs(diff - JWTService.ACCESS_TOKEN_EXPIRE_MINUTES) < 1

def test_refresh_token_expiration_time():
    token = jwt_service.create_refresh_token(1)
    payload = jwt.decode(token, JWTService.SECRET_KEY, algorithms=[JWTService.ALGORITHM])
    
    exp_time = datetime.fromtimestamp(payload["exp"])
    iat_time = datetime.fromtimestamp(payload["iat"])
    diff = (exp_time - iat_time).total_seconds() / 86400
    
    assert abs(diff - JWTService.REFRESH_TOKEN_EXPIRE_DAYS) < 1
