# tests/unit/test_password_service.py
import pytest
from app.services.password_service import password_service

def test_hash_password():
    plain = "my_secure_password"
    hashed = password_service.hash_password(plain)
    
    assert isinstance(hashed, str)
    assert len(hashed) > 0
    assert hashed != plain

def test_hash_password_different_each_time():
    plain = "same_password"
    hash1 = password_service.hash_password(plain)
    hash2 = password_service.hash_password(plain)
    
    assert hash1 != hash2

def test_verify_password_correct():
    plain = "correct_password"
    hashed = password_service.hash_password(plain)
    
    assert password_service.verify_password(plain, hashed) is True

def test_verify_password_incorrect():
    plain = "correct_password"
    hashed = password_service.hash_password(plain)
    
    assert password_service.verify_password("wrong_password", hashed) is False

def test_verify_password_empty():
    plain = ""
    hashed = password_service.hash_password(plain)
    
    assert password_service.verify_password("", hashed) is True
    assert password_service.verify_password("nonempty", hashed) is False
