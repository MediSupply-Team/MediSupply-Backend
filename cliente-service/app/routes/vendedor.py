"""
Rutas para gestión de Vendedores
HU: Registrar Vendedor - CRUD completo de vendedores
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.db import get_session
from app.models.client_model import Vendedor, Cliente
from app.schemas import (
    VendedorCreate,
    VendedorUpdate,
    VendedorResponse,
    VendedorListResponse
)
from typing import Optional
from uuid import UUID
import time
import logging

router = APIRouter(tags=["vendedores"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=VendedorResponse, status_code=status.HTTP_201_CREATED)
async def crear_vendedor(
    vendedor: VendedorCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Crear un nuevo vendedor (ID se genera automáticamente)
    
    **Criterios de aceptación:**
    - Identificación debe ser única
    - Email debe ser único
    - Registro en ≤ 1 segundo
    - Trazabilidad completa
    
    **Retorna:**
    - 201: Vendedor creado exitosamente
    - 409: Identificación o email ya existe
    - 500: Error interno
    """
    logger.info(f"📝 Creando vendedor: {vendedor.nombre_completo}")
    started = time.perf_counter_ns()
    
    try:
        # Verificar si la identificación ya existe
        existing_by_id = (await session.execute(
            select(Vendedor).where(Vendedor.identificacion == vendedor.identificacion)
        )).scalar_one_or_none()
        
        if existing_by_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "IDENTIFICACION_ALREADY_EXISTS",
                    "message": f"Vendedor con identificación {vendedor.identificacion} ya existe",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                }
            )
        
        # Verificar si el email ya existe
        existing_by_email = (await session.execute(
            select(Vendedor).where(Vendedor.email == vendedor.email)
        )).scalar_one_or_none()
        
        if existing_by_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "EMAIL_ALREADY_EXISTS",
                    "message": f"Vendedor con email {vendedor.email} ya existe",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                }
            )
        
        # Crear nuevo vendedor (ID se genera automáticamente)
        new_vendedor = Vendedor(
            identificacion=vendedor.identificacion,
            nombre_completo=vendedor.nombre_completo,
            email=vendedor.email,
            telefono=vendedor.telefono,
            pais=vendedor.pais,
            plan_de_ventas=vendedor.plan_de_ventas,
            rol=vendedor.rol,
            activo=vendedor.activo,
            password_hash=vendedor.password_hash,
            created_by_user_id=vendedor.created_by_user_id
        )
        
        session.add(new_vendedor)
        await session.commit()
        await session.refresh(new_vendedor)
        
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        logger.info(f"✅ Vendedor creado: {new_vendedor.id} en {took_ms}ms")
        
        return VendedorResponse.model_validate(new_vendedor)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creando vendedor: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Error interno al crear vendedor",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        )


@router.get("/", response_model=VendedorListResponse)
async def listar_vendedores(
    q: Optional[str] = Query(None, description="Búsqueda por nombre o identificación"),
    pais: Optional[str] = Query(None, min_length=2, max_length=2, description="Filtrar por país (código ISO)"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo"),
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(50, ge=1, le=200, description="Tamaño de página"),
    sort: str = Query("nombre_completo", pattern="^(nombre_completo|identificacion|created_at)$", description="Campo de ordenamiento"),
    session: AsyncSession = Depends(get_session)
):
    """
    Listar vendedores con filtros y paginación
    
    **Filtros disponibles:**
    - q: Búsqueda por nombre o identificación
    - pais: Código ISO del país
    - activo: true/false
    
    **Retorna:**
    - Lista de vendedores con metadata de paginación
    """
    logger.info(f"🔍 Listando vendedores: q={q}, pais={pais}, activo={activo}, page={page}")
    started = time.perf_counter_ns()
    
    try:
        # Construir query base
        stmt = select(Vendedor)
        
        # Aplicar filtros
        if q:
            stmt = stmt.where(
                or_(
                    func.lower(Vendedor.nombre_completo).like(f"%{q.lower()}%"),
                    func.lower(Vendedor.identificacion).like(f"%{q.lower()}%")
                )
            )
        
        if pais:
            stmt = stmt.where(Vendedor.pais == pais.upper())
        
        if activo is not None:
            stmt = stmt.where(Vendedor.activo == activo)
        
        # Contar total
        count_stmt = select(func.count()).select_from(Vendedor)
        if q:
            count_stmt = count_stmt.where(
                or_(
                    func.lower(Vendedor.nombre_completo).like(f"%{q.lower()}%"),
                    func.lower(Vendedor.identificacion).like(f"%{q.lower()}%")
                )
            )
        if pais:
            count_stmt = count_stmt.where(Vendedor.pais == pais.upper())
        if activo is not None:
            count_stmt = count_stmt.where(Vendedor.activo == activo)
        
        total = (await session.execute(count_stmt)).scalar_one()
        
        # Aplicar ordenamiento
        if sort == "identificacion":
            stmt = stmt.order_by(Vendedor.identificacion.asc())
        elif sort == "created_at":
            stmt = stmt.order_by(Vendedor.created_at.desc())
        else:  # nombre_completo (default)
            stmt = stmt.order_by(Vendedor.nombre_completo.asc())
        
        # Aplicar paginación
        stmt = stmt.offset((page - 1) * size).limit(size)
        
        # Ejecutar query
        result = await session.execute(stmt)
        vendedores = result.scalars().all()
        
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        logger.info(f"✅ {len(vendedores)} vendedores encontrados en {took_ms}ms")
        
        return VendedorListResponse(
            items=[VendedorResponse.model_validate(v) for v in vendedores],
            total=total,
            page=page,
            size=size,
            took_ms=took_ms
        )
        
    except Exception as e:
        logger.error(f"❌ Error listando vendedores: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al listar vendedores"
        )


@router.get("/{vendedor_id}", response_model=VendedorResponse)
async def obtener_vendedor(
    vendedor_id: str,  # Recibe como string desde URL
    session: AsyncSession = Depends(get_session)
):
    """
    Obtener un vendedor por ID
    
    **Retorna:**
    - 200: Vendedor encontrado
    - 400: ID inválido
    - 404: Vendedor no encontrado
    """
    logger.info(f"🔍 Obteniendo vendedor: {vendedor_id}")
    
    try:
        # Convertir string a UUID
        uuid_id = UUID(vendedor_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_UUID",
                "message": f"ID '{vendedor_id}' no es un UUID válido"
            }
        )
    
    vendedor = (await session.execute(
        select(Vendedor).where(Vendedor.id == uuid_id)
    )).scalar_one_or_none()
    
    if not vendedor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "VENDEDOR_NOT_FOUND",
                "message": f"Vendedor {vendedor_id} no encontrado"
            }
        )
    
    return VendedorResponse.model_validate(vendedor)


@router.put("/{vendedor_id}", response_model=VendedorResponse)
async def actualizar_vendedor(
    vendedor_id: str,  # Recibe como string desde URL
    vendedor_data: VendedorUpdate,
    session: AsyncSession = Depends(get_session)
):
    """
    Actualizar un vendedor existente
    
    **Retorna:**
    - 200: Vendedor actualizado
    - 400: ID inválido
    - 404: Vendedor no encontrado
    - 409: Identificación o email duplicado
    """
    logger.info(f"✏️ Actualizando vendedor: {vendedor_id}")
    started = time.perf_counter_ns()
    
    try:
        # Convertir string a UUID
        uuid_id = UUID(vendedor_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_UUID", "message": f"ID '{vendedor_id}' no es un UUID válido"}
        )
    
    try:
        # Buscar vendedor
        vendedor = (await session.execute(
            select(Vendedor).where(Vendedor.id == uuid_id)
        )).scalar_one_or_none()
        
        if not vendedor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "VENDEDOR_NOT_FOUND", "message": f"Vendedor {vendedor_id} no encontrado"}
            )
        
        # Validar identificación única (si se actualiza)
        if vendedor_data.identificacion and vendedor_data.identificacion != vendedor.identificacion:
            existing_id = (await session.execute(
                select(Vendedor).where(Vendedor.identificacion == vendedor_data.identificacion)
            )).scalar_one_or_none()
            if existing_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"error": "IDENTIFICACION_ALREADY_EXISTS", "message": f"Identificación {vendedor_data.identificacion} ya existe"}
                )
        
        # Validar email único (si se actualiza)
        if vendedor_data.email and vendedor_data.email != vendedor.email:
            existing_email = (await session.execute(
                select(Vendedor).where(Vendedor.email == vendedor_data.email)
            )).scalar_one_or_none()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"error": "EMAIL_ALREADY_EXISTS", "message": f"Email {vendedor_data.email} ya existe"}
                )
        
        # Actualizar campos
        update_data = vendedor_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(vendedor, key, value)
        
        await session.commit()
        await session.refresh(vendedor)
        
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        logger.info(f"✅ Vendedor actualizado: {vendedor_id} en {took_ms}ms")
        
        return VendedorResponse.model_validate(vendedor)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error actualizando vendedor: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar vendedor"
        )


@router.delete("/{vendedor_id}", status_code=status.HTTP_200_OK)
async def desactivar_vendedor(
    vendedor_id: str,  # Recibe como string desde URL
    session: AsyncSession = Depends(get_session)
):
    """
    Desactivar un vendedor (soft delete)
    
    No se eliminan físicamente los vendedores, solo se marcan como inactivos.
    
    **Retorna:**
    - 200: Vendedor desactivado
    - 400: ID inválido
    - 404: Vendedor no encontrado
    """
    logger.info(f"🗑️ Desactivando vendedor: {vendedor_id}")
    
    try:
        uuid_id = UUID(vendedor_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_UUID", "message": f"ID '{vendedor_id}' no es un UUID válido"}
        )
    
    vendedor = (await session.execute(
        select(Vendedor).where(Vendedor.id == uuid_id)
    )).scalar_one_or_none()
    
    if not vendedor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "VENDEDOR_NOT_FOUND", "message": f"Vendedor {vendedor_id} no encontrado"}
        )
    
    vendedor.activo = False
    await session.commit()
    
    logger.info(f"✅ Vendedor desactivado: {vendedor_id}")
    
    return {"message": f"Vendedor {vendedor_id} desactivado exitosamente"}


@router.get("/{vendedor_id}/clientes", response_model=dict)
async def obtener_clientes_vendedor(
    vendedor_id: str,  # Recibe como string desde URL
    session: AsyncSession = Depends(get_session)
):
    """
    Obtener todos los clientes de un vendedor
    
    **Retorna:**
    - Lista de clientes del vendedor
    - 400: ID inválido
    - 404: Vendedor no encontrado
    """
    logger.info(f"🔍 Obteniendo clientes del vendedor: {vendedor_id}")
    
    try:
        uuid_id = UUID(vendedor_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_UUID", "message": f"ID '{vendedor_id}' no es un UUID válido"}
        )
    
    # Verificar que el vendedor existe
    vendedor = (await session.execute(
        select(Vendedor).where(Vendedor.id == uuid_id)
    )).scalar_one_or_none()
    
    if not vendedor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "VENDEDOR_NOT_FOUND", "message": f"Vendedor {vendedor_id} no encontrado"}
        )
    
    # Obtener clientes
    clientes = (await session.execute(
        select(Cliente).where(Cliente.vendedor_id == uuid_id)
    )).scalars().all()
    
    return {
        "vendedor_id": str(vendedor_id),
        "vendedor_nombre": vendedor.nombre_completo,
        "total_clientes": len(clientes),
        "clientes": [
            {
                "id": str(c.id),
                "nit": c.nit,
                "nombre": c.nombre,
                "codigo_unico": c.codigo_unico,
                "activo": c.activo
            }
            for c in clientes
        ]
    }

