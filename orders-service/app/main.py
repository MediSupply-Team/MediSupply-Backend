from fastapi import FastAPI, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text, select, delete
from app.db import get_session, Base, engine
from app.models import IdempotencyRequest, IdemStatus, Order, OutboxEvent, OrderStatus
from app.schemas import CreateOrderRequest, AcceptedResponse, OrderResponse
from app.tasks import celery
from uuid import uuid4, UUID
from typing import List
import logging

log = logging.getLogger("orders")
app = FastAPI(title="Orders Service")

def _sha256(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def get_idempotency_key(
    idem: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        convert_underscores=False,
        description="UUID v4 para idempotencia (si lo dejas vacío, el server genera uno)",
    )
) -> str:
    return idem or str(uuid4())

@app.get("/health")
async def health():
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception as e:
        return {"status": "degraded", "db_error": str(e)}

@app.post("/orders", response_model=AcceptedResponse, status_code=202)
async def create_order(
    body: CreateOrderRequest,
    Idempotency_Key: str = Depends(get_idempotency_key),
    session: AsyncSession = Depends(get_session),
):
    key_hash = _sha256(Idempotency_Key)
    body_hash = _sha256(body.model_dump_json())

    try:
        async with session.begin():
            idem = await session.get(IdempotencyRequest, key_hash)
            if idem:
                if idem.body_hash != body_hash:
                    raise HTTPException(status_code=409, detail="Idempotency-Key ya usada con payload distinto")
                if idem.status == IdemStatus.DONE and idem.response_body:
                    return AcceptedResponse(request_id=key_hash, message="Ya procesado (idempotente)")
            else:
                idem = IdempotencyRequest(key_hash=key_hash, body_hash=body_hash, status=IdemStatus.PENDING)
                session.add(idem)

            # Convertir Address a dict si existe
            address_dict = body.address.model_dump() if body.address else None
            
            order = Order(
                customer_id=body.customer_id, 
                created_by_role=body.created_by_role, 
                source=body.source,  
                user_name=body.user_name, 
                address=address_dict,
                items=[i.model_dump() for i in body.items]
            )
            session.add(order)
            await session.flush()

            evt = OutboxEvent(
                aggregate_id=order.id,
                type="OrderCreated",
                payload={"order_id": str(order.id), "key_hash": key_hash},
            )
            session.add(evt)

    except IntegrityError:
        await session.rollback()
        idem = await session.get(IdempotencyRequest, key_hash)
        return AcceptedResponse(request_id=key_hash, message="Ya procesado por otra instancia")

    # Notificación asíncrona (no romper si no hay broker en prod)
    try:
        celery.send_task("process_outbox_event", args=[str(evt.event_id)])
    except Exception as e:
        log.warning("No se pudo publicar en Celery (continuando): %s", e)

    return AcceptedResponse(request_id=key_hash)

# ============================================
# NUEVOS ENDPOINTS
# ============================================

@app.get("/orders", response_model=List[OrderResponse])
async def get_all_orders(
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_session)
):
    """
    Obtener todas las órdenes con paginación
    """
    result = await session.execute(
        select(Order).limit(limit).offset(offset).order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    
    return [
        OrderResponse(
            id=str(order.id),
            customer_id=order.customer_id,
            items=order.items,
            status=order.status.value,
            created_by_role=order.created_by_role,
            source=order.source,
            user_name=order.user_name,
            address=order.address,
            created_at=order.created_at.isoformat()
        )
        for order in orders
    ]

@app.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order_by_id(
    order_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Obtener una orden específica por ID
    """
    try:
        order = await session.get(Order, UUID(order_id))
        if not order:
            raise HTTPException(status_code=404, detail="Orden no encontrada")
        
        return OrderResponse(
            id=str(order.id),
            customer_id=order.customer_id,
            items=order.items,
            status=order.status.value,
            created_by_role=order.created_by_role,
            source=order.source,
            user_name=order.user_name,
            address=order.address,
            created_at=order.created_at.isoformat()
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de orden inválido")

@app.post("/seed-data", status_code=201)
async def seed_initial_data(session: AsyncSession = Depends(get_session)):
    """
    Endpoint auxiliar para cargar datos de prueba iniciales
    """
    sample_orders = [
        Order(
            customer_id="Hospital San José",
            items=[{"sku": "PROD-A", "qty": 2}, {"sku": "PROD-B", "qty": 1}],
            status=OrderStatus.CREATED,
            created_by_role="seller",
            source="bff-cliente",
            user_name="juan.perez",
            address={
                "street": "Calle 45 #12-34",
                "city": "Bogotá",
                "state": "Cundinamarca",
                "zip_code": "110111",
                "country": "Colombia"
            }
        ),
        Order(
            customer_id="Clínica del Norte",
            items=[{"sku": "PROD-C", "qty": 5}],
            status=OrderStatus.NEW,
            created_by_role="admin",
            source="bff-admin",
            user_name="maria.lopez",
            address={
                "street": "Carrera 15 #78-90",
                "city": "Bogotá",
                "state": "Cundinamarca",
                "zip_code": "110221",
                "country": "Colombia"
            }
        ),
        Order(
            customer_id="Farmacia Central",
            items=[{"sku": "PROD-D", "qty": 3}, {"sku": "PROD-E", "qty": 2}],
            status=OrderStatus.CREATED,
            created_by_role="seller",
            source="bff-cliente",
            user_name="carlos.gomez",
            address={
                "street": "Avenida 68 #25-10",
                "city": "Bogotá",
                "state": "Cundinamarca",
                "zip_code": "110931",
                "country": "Colombia"
            }
        ),
    ]
    
    async with session.begin():
        for order in sample_orders:
            session.add(order)
    
    return {
        "message": "Datos de carga inicial creados exitosamente",
        "count": len(sample_orders)
    }

@app.delete("/clear-all", status_code=200)
async def clear_all_data(session: AsyncSession = Depends(get_session)):
    """
    Endpoint auxiliar para borrar TODOS los registros de la base de datos.
    CUIDADO: Esto borrará toda la información.
    """
    async with session.begin():
        # Borrar en orden para respetar foreign keys
        await session.execute(delete(OutboxEvent))
        await session.execute(delete(IdempotencyRequest))
        await session.execute(delete(Order))
    
    return {
        "message": "Todos los registros han sido eliminados",
        "tables_cleared": ["outbox_events", "idempotency_requests", "orders"]
    }

@app.on_event("startup")
async def on_startup():
    # Útil en local; en prod idealmente usar migraciones
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)