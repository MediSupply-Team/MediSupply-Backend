# app/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    name: str
    hospital_id: Optional[str] = None
    cliente_id: Optional[str] = None
    venta_id: Optional[str] = None

class UserCreate(UserBase):
    password: str
    role_id: int

class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    cliente_id: Optional[str] = None
    venta_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True