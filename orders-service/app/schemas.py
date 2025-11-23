from pydantic import BaseModel, Field
from typing import List, Optional

class OrderItem(BaseModel):
    sku: str
    qty: int

class Address(BaseModel):
    street: str
    city: str
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: str

class CreateOrderRequest(BaseModel):
    customer_id: Optional[str] = None
    seller_id: Optional[str] = None
    items: List[OrderItem]
    created_by_role: str
    source: str
    user_name: Optional[str] = None
    address: Optional[Address] = None

class AcceptedResponse(BaseModel):
    request_id: str = Field(..., description="Idempotency key hash")
    message: str = "Enqueued"

class CreatedOrderResponse(BaseModel):
    order_id: str
    status: str = "CREATED"

class OrderResponse(BaseModel):
    id: str
    customer_id: Optional[str] = None
    seller_id: Optional[str] = None
    items: List[dict]
    status: str
    created_by_role: str
    source: str
    user_name: Optional[str] = None
    address: Optional[dict] = None
    created_at: str
    
    class Config:
        from_attributes = True