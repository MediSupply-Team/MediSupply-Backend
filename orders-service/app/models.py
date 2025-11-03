import uuid
import enum
from sqlalchemy import Column, String, Enum, JSON, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, ENUM
from enum import Enum as PyEnum

from app.db import Base

# --- ENUM de OrderStatus (ciclo de vida completo) ---
class OrderStatus(PyEnum):
    """
    Estados del ciclo de vida de una orden de venta
    
    Flujo típico:
    NEW → VALIDATED → CONFIRMED → PROCESSING → RELEASED → 
    IN_TRANSIT → DELIVERED → COMPLETED
    
    Estados alternativos:
    - CANCELLED: Puede ocurrir en cualquier momento antes de DELIVERED
    - FAILED: Error en validación o procesamiento
    - ON_HOLD: Orden pausada temporalmente
    """
    # Estados iniciales
    NEW = "NEW"                           # Orden recién creada, pendiente de validación
    VALIDATED = "VALIDATED"               # Inventario y datos validados
    CONFIRMED = "CONFIRMED"               # Confirmada por cliente/sistema
    
    # Estados de procesamiento
    PROCESSING = "PROCESSING"             # En preparación (picking/packing)
    RELEASED = "RELEASED"                 # Liberada para envío/ruta
    
    # Estados de entrega
    IN_TRANSIT = "IN_TRANSIT"             # En camino al cliente
    DELIVERED = "DELIVERED"               # Entregada al cliente
    
    # Estados finales
    COMPLETED = "COMPLETED"               # Orden completada (facturada, cerrada)
    
    # Estados de excepción
    CANCELLED = "CANCELLED"               # Orden cancelada
    FAILED = "FAILED"                     # Error en validación/procesamiento
    ON_HOLD = "ON_HOLD"                   # Orden en espera (problemas de pago, stock, etc.)


# 🔹 ENUM idempotente: SQLAlchemy lo registra y usa checkfirst internamente
orderstatus_enum = ENUM(
    OrderStatus,
    name="orderstatus",
    metadata=Base.metadata,
    create_type=True,
    validate_strings=True
)


# --- ENUM de IdemStatus ---
class IdemStatus(PyEnum):
    PENDING = "PENDING"
    DONE = "DONE"


# --- MODELOS ---
class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String, nullable=False)
    items = Column(JSON, nullable=False)
    status = Column(orderstatus_enum, nullable=False, default=OrderStatus.NEW)
    created_by_role = Column(String, nullable=False)
    source = Column(String, nullable=False)
    user_name = Column(String, nullable=True)
    address = Column(JSON, nullable=True)
    
    # Campos adicionales útiles para tracking
    validated_at = Column(DateTime(timezone=True), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    released_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Auditoría
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Información adicional
    notes = Column(String, nullable=True)  # Notas internas
    cancellation_reason = Column(String, nullable=True)  # Razón de cancelación


class IdempotencyRequest(Base):
    __tablename__ = "idempotency_requests"

    key_hash = Column(String, primary_key=True)
    body_hash = Column(String, nullable=False)
    status = Column(
        Enum(IdemStatus, name="idemstatus", metadata=Base.metadata, create_type=True),
        nullable=False,
        default=IdemStatus.PENDING,
    )
    status_code = Column(Integer, nullable=True)
    response_body = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregate_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    type = Column(String, nullable=False)  # e.g., "OrderCreated", "OrderReleased", "OrderDelivered"
    payload = Column(JSON, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    retries = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# --- Transiciones de Estado Válidas ---
VALID_STATUS_TRANSITIONS = {
    OrderStatus.NEW: [OrderStatus.VALIDATED, OrderStatus.CANCELLED, OrderStatus.FAILED],
    OrderStatus.VALIDATED: [OrderStatus.CONFIRMED, OrderStatus.ON_HOLD, OrderStatus.CANCELLED],
    OrderStatus.CONFIRMED: [OrderStatus.PROCESSING, OrderStatus.ON_HOLD, OrderStatus.CANCELLED],
    OrderStatus.PROCESSING: [OrderStatus.RELEASED, OrderStatus.ON_HOLD, OrderStatus.CANCELLED, OrderStatus.FAILED],
    OrderStatus.RELEASED: [OrderStatus.IN_TRANSIT, OrderStatus.ON_HOLD, OrderStatus.CANCELLED],
    OrderStatus.IN_TRANSIT: [OrderStatus.DELIVERED, OrderStatus.FAILED],
    OrderStatus.DELIVERED: [OrderStatus.COMPLETED],
    OrderStatus.ON_HOLD: [OrderStatus.PROCESSING, OrderStatus.CANCELLED],
    # Estados finales no pueden transicionar
    OrderStatus.COMPLETED: [],
    OrderStatus.CANCELLED: [],
    OrderStatus.FAILED: [],
}


def can_transition(current_status: OrderStatus, new_status: OrderStatus) -> bool:
    """
    Verifica si una transición de estado es válida
    
    Args:
        current_status: Estado actual de la orden
        new_status: Estado al que se quiere transicionar
        
    Returns:
        True si la transición es válida, False en caso contrario
    """
    return new_status in VALID_STATUS_TRANSITIONS.get(current_status, [])


def get_next_valid_statuses(current_status: OrderStatus) -> list[OrderStatus]:
    """
    Obtiene la lista de estados válidos a los que puede transicionar
    
    Args:
        current_status: Estado actual de la orden
        
    Returns:
        Lista de estados válidos
    """
    return VALID_STATUS_TRANSITIONS.get(current_status, [])