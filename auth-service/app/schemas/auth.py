# app/schemas/auth.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List

class TokenData(BaseModel):
    user_id: int
    email: str
    name: Optional[str] = None
    role: str
    hospital_id: Optional[str] = None
    permissions: List[dict] = []

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    token: str
    refresh_token: str
    user: dict

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    role_id: int
    hospital_id: Optional[str] = None
    cliente_id: Optional[str] = None
    venta_id: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str