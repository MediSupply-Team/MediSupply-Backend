"""
Rutas API para catálogos de soporte en cliente-service
Endpoints CRUD para TipoRolVendedor, Territorio, TipoPlan, Region, Zona
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db import get_session
from app.models.catalogo_model import (
    TipoRolVendedor, Territorio, TipoPlan, Region, Zona
)
from app.schemas import (
    TipoRolVendedorCreate, TipoRolVendedorResponse, TipoRolVendedorListResponse,
    TerritorioCreate, TerritorioResponse, TerritorioListResponse,
    TipoPlanCreate, TipoPlanResponse, TipoPlanListResponse,
    RegionCreate, RegionResponse, RegionListResponse,
    ZonaCreate, ZonaResponse, ZonaListResponse
)
from typing import Optional
from uuid import UUID
import time
import logging

router = APIRouter(tags=["catalogos"])
logger = logging.getLogger(__name__)


# ============================================================================
# TIPO ROL VENDEDOR
# ============================================================================

@router.post("/tipos-rol", response_model=TipoRolVendedorResponse, status_code=status.HTTP_201_CREATED)
async def crear_tipo_rol(tipo_rol: TipoRolVendedorCreate, session: AsyncSession = Depends(get_session)):
    """
    Crea un nuevo tipo de rol de vendedor
    """
    started = time.perf_counter_ns()
    
    try:
        # Verificar si el código ya existe
        stmt = select(TipoRolVendedor).where(TipoRolVendedor.codigo == tipo_rol.codigo)
        existing = await session.execute(stmt)
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "CODIGO_DUPLICADO", "message": f"Ya existe un tipo de rol con código '{tipo_rol.codigo}'"}
            )
        
        # Crear nuevo tipo de rol
        nuevo_tipo_rol = TipoRolVendedor(**tipo_rol.model_dump())
        session.add(nuevo_tipo_rol)
        await session.commit()
        await session.refresh(nuevo_tipo_rol)
        
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        logger.info(f"✅ Tipo de rol creado: {nuevo_tipo_rol.id} ({nuevo_tipo_rol.codigo}) - {took_ms}ms")
        
        return nuevo_tipo_rol
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"❌ Error creando tipo de rol: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "ERROR_INTERNO", "message": "Error al crear tipo de rol"}
        )


@router.get("/tipos-rol", response_model=TipoRolVendedorListResponse)
async def listar_tipos_rol(
    activo: Optional[bool] = Query(True, description="Filtrar por estado activo"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """
    Lista todos los tipos de rol de vendedor con paginación
    """
    started = time.perf_counter_ns()
    
    try:
        # Query base
        stmt = select(TipoRolVendedor).order_by(TipoRolVendedor.nivel_jerarquia.asc(), TipoRolVendedor.nombre.asc())
        count_stmt = select(func.count()).select_from(TipoRolVendedor)
        
        # Filtro por activo
        if activo is not None:
            stmt = stmt.where(TipoRolVendedor.activo == activo)
            count_stmt = count_stmt.where(TipoRolVendedor.activo == activo)
        
        # Ejecutar queries
        total = (await session.execute(count_stmt)).scalar_one()
        result = await session.execute(stmt.offset((page - 1) * size).limit(size))
        tipos_rol = result.scalars().all()
        
        total_pages = (total + size - 1) // size
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        
        logger.info(f"📋 Listado tipos de rol: {len(tipos_rol)}/{total} - página {page}/{total_pages} - {took_ms}ms")
        
        return TipoRolVendedorListResponse(
            tipos_rol=tipos_rol,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"❌ Error listando tipos de rol: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "ERROR_INTERNO", "message": "Error al listar tipos de rol"}
        )


@router.get("/tipos-rol/{tipo_rol_id}", response_model=TipoRolVendedorResponse)
async def obtener_tipo_rol(tipo_rol_id: str, session: AsyncSession = Depends(get_session)):
    """
    Obtiene un tipo de rol de vendedor por ID
    """
    try:
        uuid_id = UUID(tipo_rol_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_UUID", "message": f"ID '{tipo_rol_id}' no es un UUID válido"}
        )
    
    tipo_rol = await session.get(TipoRolVendedor, uuid_id)
    if not tipo_rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NO_ENCONTRADO", "message": f"Tipo de rol con ID '{tipo_rol_id}' no encontrado"}
        )
    
    return tipo_rol


# ============================================================================
# TERRITORIO
# ============================================================================

@router.post("/territorios", response_model=TerritorioResponse, status_code=status.HTTP_201_CREATED)
async def crear_territorio(territorio: TerritorioCreate, session: AsyncSession = Depends(get_session)):
    """
    Crea un nuevo territorio
    """
    started = time.perf_counter_ns()
    
    try:
        # Verificar si el código ya existe
        stmt = select(Territorio).where(Territorio.codigo == territorio.codigo)
        existing = await session.execute(stmt)
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "CODIGO_DUPLICADO", "message": f"Ya existe un territorio con código '{territorio.codigo}'"}
            )
        
        # Crear nuevo territorio
        nuevo_territorio = Territorio(**territorio.model_dump())
        session.add(nuevo_territorio)
        await session.commit()
        await session.refresh(nuevo_territorio)
        
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        logger.info(f"✅ Territorio creado: {nuevo_territorio.id} ({nuevo_territorio.codigo}) - {took_ms}ms")
        
        return nuevo_territorio
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"❌ Error creando territorio: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "ERROR_INTERNO", "message": "Error al crear territorio"}
        )


@router.get("/territorios", response_model=TerritorioListResponse)
async def listar_territorios(
    pais: Optional[str] = Query(None, min_length=2, max_length=2, description="Filtrar por código de país"),
    activo: Optional[bool] = Query(True, description="Filtrar por estado activo"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """
    Lista todos los territorios con paginación
    """
    started = time.perf_counter_ns()
    
    try:
        # Query base
        stmt = select(Territorio).order_by(Territorio.pais.asc(), Territorio.nombre.asc())
        count_stmt = select(func.count()).select_from(Territorio)
        
        # Filtros
        if pais:
            stmt = stmt.where(Territorio.pais == pais.upper())
            count_stmt = count_stmt.where(Territorio.pais == pais.upper())
        if activo is not None:
            stmt = stmt.where(Territorio.activo == activo)
            count_stmt = count_stmt.where(Territorio.activo == activo)
        
        # Ejecutar queries
        total = (await session.execute(count_stmt)).scalar_one()
        result = await session.execute(stmt.offset((page - 1) * size).limit(size))
        territorios = result.scalars().all()
        
        total_pages = (total + size - 1) // size
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        
        logger.info(f"📋 Listado territorios: {len(territorios)}/{total} - página {page}/{total_pages} - {took_ms}ms")
        
        return TerritorioListResponse(
            territorios=territorios,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"❌ Error listando territorios: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "ERROR_INTERNO", "message": "Error al listar territorios"}
        )


@router.get("/territorios/{territorio_id}", response_model=TerritorioResponse)
async def obtener_territorio(territorio_id: str, session: AsyncSession = Depends(get_session)):
    """
    Obtiene un territorio por ID
    """
    try:
        uuid_id = UUID(territorio_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_UUID", "message": f"ID '{territorio_id}' no es un UUID válido"}
        )
    
    territorio = await session.get(Territorio, uuid_id)
    if not territorio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NO_ENCONTRADO", "message": f"Territorio con ID '{territorio_id}' no encontrado"}
        )
    
    return territorio


# ============================================================================
# TIPO PLAN
# ============================================================================

@router.post("/tipos-plan", response_model=TipoPlanResponse, status_code=status.HTTP_201_CREATED)
async def crear_tipo_plan(tipo_plan: TipoPlanCreate, session: AsyncSession = Depends(get_session)):
    """
    Crea un nuevo tipo de plan de venta
    """
    started = time.perf_counter_ns()
    
    try:
        # Verificar si el código ya existe
        stmt = select(TipoPlan).where(TipoPlan.codigo == tipo_plan.codigo)
        existing = await session.execute(stmt)
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "CODIGO_DUPLICADO", "message": f"Ya existe un tipo de plan con código '{tipo_plan.codigo}'"}
            )
        
        # Crear nuevo tipo de plan
        nuevo_tipo_plan = TipoPlan(**tipo_plan.model_dump())
        session.add(nuevo_tipo_plan)
        await session.commit()
        await session.refresh(nuevo_tipo_plan)
        
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        logger.info(f"✅ Tipo de plan creado: {nuevo_tipo_plan.id} ({nuevo_tipo_plan.codigo}) - {took_ms}ms")
        
        return nuevo_tipo_plan
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"❌ Error creando tipo de plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "ERROR_INTERNO", "message": "Error al crear tipo de plan"}
        )


@router.get("/tipos-plan", response_model=TipoPlanListResponse)
async def listar_tipos_plan(
    activo: Optional[bool] = Query(True, description="Filtrar por estado activo"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """
    Lista todos los tipos de plan con paginación
    """
    started = time.perf_counter_ns()
    
    try:
        # Query base
        stmt = select(TipoPlan).order_by(TipoPlan.comision_base_defecto.desc(), TipoPlan.nombre.asc())
        count_stmt = select(func.count()).select_from(TipoPlan)
        
        # Filtro por activo
        if activo is not None:
            stmt = stmt.where(TipoPlan.activo == activo)
            count_stmt = count_stmt.where(TipoPlan.activo == activo)
        
        # Ejecutar queries
        total = (await session.execute(count_stmt)).scalar_one()
        result = await session.execute(stmt.offset((page - 1) * size).limit(size))
        tipos_plan = result.scalars().all()
        
        total_pages = (total + size - 1) // size
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        
        logger.info(f"📋 Listado tipos de plan: {len(tipos_plan)}/{total} - página {page}/{total_pages} - {took_ms}ms")
        
        return TipoPlanListResponse(
            tipos_plan=tipos_plan,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"❌ Error listando tipos de plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "ERROR_INTERNO", "message": "Error al listar tipos de plan"}
        )


@router.get("/tipos-plan/{tipo_plan_id}", response_model=TipoPlanResponse)
async def obtener_tipo_plan(tipo_plan_id: str, session: AsyncSession = Depends(get_session)):
    """
    Obtiene un tipo de plan por ID
    """
    try:
        uuid_id = UUID(tipo_plan_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_UUID", "message": f"ID '{tipo_plan_id}' no es un UUID válido"}
        )
    
    tipo_plan = await session.get(TipoPlan, uuid_id)
    if not tipo_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NO_ENCONTRADO", "message": f"Tipo de plan con ID '{tipo_plan_id}' no encontrado"}
        )
    
    return tipo_plan


# ============================================================================
# REGION
# ============================================================================

@router.post("/regiones", response_model=RegionResponse, status_code=status.HTTP_201_CREATED)
async def crear_region(region: RegionCreate, session: AsyncSession = Depends(get_session)):
    """
    Crea una nueva región
    """
    started = time.perf_counter_ns()
    
    try:
        # Verificar si el código ya existe
        stmt = select(Region).where(Region.codigo == region.codigo)
        existing = await session.execute(stmt)
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "CODIGO_DUPLICADO", "message": f"Ya existe una región con código '{region.codigo}'"}
            )
        
        # Crear nueva región
        nueva_region = Region(**region.model_dump())
        session.add(nueva_region)
        await session.commit()
        await session.refresh(nueva_region)
        
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        logger.info(f"✅ Región creada: {nueva_region.id} ({nueva_region.codigo}) - {took_ms}ms")
        
        return nueva_region
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"❌ Error creando región: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "ERROR_INTERNO", "message": "Error al crear región"}
        )


@router.get("/regiones", response_model=RegionListResponse)
async def listar_regiones(
    pais: Optional[str] = Query(None, min_length=2, max_length=2, description="Filtrar por código de país"),
    activo: Optional[bool] = Query(True, description="Filtrar por estado activo"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """
    Lista todas las regiones con paginación
    """
    started = time.perf_counter_ns()
    
    try:
        # Query base
        stmt = select(Region).order_by(Region.pais.asc(), Region.nombre.asc())
        count_stmt = select(func.count()).select_from(Region)
        
        # Filtros
        if pais:
            stmt = stmt.where(Region.pais == pais.upper())
            count_stmt = count_stmt.where(Region.pais == pais.upper())
        if activo is not None:
            stmt = stmt.where(Region.activo == activo)
            count_stmt = count_stmt.where(Region.activo == activo)
        
        # Ejecutar queries
        total = (await session.execute(count_stmt)).scalar_one()
        result = await session.execute(stmt.offset((page - 1) * size).limit(size))
        regiones = result.scalars().all()
        
        total_pages = (total + size - 1) // size
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        
        logger.info(f"📋 Listado regiones: {len(regiones)}/{total} - página {page}/{total_pages} - {took_ms}ms")
        
        return RegionListResponse(
            regiones=regiones,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"❌ Error listando regiones: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "ERROR_INTERNO", "message": "Error al listar regiones"}
        )


@router.get("/regiones/{region_id}", response_model=RegionResponse)
async def obtener_region(region_id: str, session: AsyncSession = Depends(get_session)):
    """
    Obtiene una región por ID
    """
    try:
        uuid_id = UUID(region_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_UUID", "message": f"ID '{region_id}' no es un UUID válido"}
        )
    
    region = await session.get(Region, uuid_id)
    if not region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NO_ENCONTRADO", "message": f"Región con ID '{region_id}' no encontrada"}
        )
    
    return region


# ============================================================================
# ZONA
# ============================================================================

@router.post("/zonas", response_model=ZonaResponse, status_code=status.HTTP_201_CREATED)
async def crear_zona(zona: ZonaCreate, session: AsyncSession = Depends(get_session)):
    """
    Crea una nueva zona
    """
    started = time.perf_counter_ns()
    
    try:
        # Verificar si el código ya existe
        stmt = select(Zona).where(Zona.codigo == zona.codigo)
        existing = await session.execute(stmt)
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "CODIGO_DUPLICADO", "message": f"Ya existe una zona con código '{zona.codigo}'"}
            )
        
        # Crear nueva zona
        nueva_zona = Zona(**zona.model_dump())
        session.add(nueva_zona)
        await session.commit()
        await session.refresh(nueva_zona)
        
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        logger.info(f"✅ Zona creada: {nueva_zona.id} ({nueva_zona.codigo}) - {took_ms}ms")
        
        return nueva_zona
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"❌ Error creando zona: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "ERROR_INTERNO", "message": "Error al crear zona"}
        )


@router.get("/zonas", response_model=ZonaListResponse)
async def listar_zonas(
    tipo: Optional[str] = Query(None, description="Filtrar por tipo de zona"),
    activo: Optional[bool] = Query(True, description="Filtrar por estado activo"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """
    Lista todas las zonas con paginación
    """
    started = time.perf_counter_ns()
    
    try:
        # Query base
        stmt = select(Zona).order_by(Zona.tipo.asc(), Zona.nombre.asc())
        count_stmt = select(func.count()).select_from(Zona)
        
        # Filtros
        if tipo:
            stmt = stmt.where(Zona.tipo == tipo.lower())
            count_stmt = count_stmt.where(Zona.tipo == tipo.lower())
        if activo is not None:
            stmt = stmt.where(Zona.activo == activo)
            count_stmt = count_stmt.where(Zona.activo == activo)
        
        # Ejecutar queries
        total = (await session.execute(count_stmt)).scalar_one()
        result = await session.execute(stmt.offset((page - 1) * size).limit(size))
        zonas = result.scalars().all()
        
        total_pages = (total + size - 1) // size
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        
        logger.info(f"📋 Listado zonas: {len(zonas)}/{total} - página {page}/{total_pages} - {took_ms}ms")
        
        return ZonaListResponse(
            zonas=zonas,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"❌ Error listando zonas: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "ERROR_INTERNO", "message": "Error al listar zonas"}
        )


@router.get("/zonas/{zona_id}", response_model=ZonaResponse)
async def obtener_zona(zona_id: str, session: AsyncSession = Depends(get_session)):
    """
    Obtiene una zona por ID
    """
    try:
        uuid_id = UUID(zona_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_UUID", "message": f"ID '{zona_id}' no es un UUID válido"}
        )
    
    zona = await session.get(Zona, uuid_id)
    if not zona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NO_ENCONTRADO", "message": f"Zona con ID '{zona_id}' no encontrada"}
        )
    
    return zona

