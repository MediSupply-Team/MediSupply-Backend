"""
Router para gestión de bodegas (warehouses).

Endpoints:
- GET /api/v1/bodegas - Listar todas las bodegas
- POST /api/v1/bodegas - Crear una nueva bodega
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db import get_session
from app.models.catalogo_model import Bodega
from app.schemas import BodegaCreate, BodegaResponse, BodegaListResponse, Meta
from typing import Optional
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Bodegas"])


@router.post("", response_model=BodegaResponse, status_code=status.HTTP_201_CREATED)
async def crear_bodega(
    bodega: BodegaCreate,
    usuario_id: str = Query("SYSTEM", description="ID del usuario que crea la bodega"),
    session: AsyncSession = Depends(get_session)
):
    """
    **Crear una nueva bodega**
    
    Crea una nueva bodega en el sistema para gestionar inventario.
    
    ### Validaciones:
    - El código debe ser único
    - El código se almacena en mayúsculas
    - El país debe ser un código ISO de 2 letras en mayúsculas
    
    ### Campos Requeridos:
    - `codigo`: Código único (ej: BOG_CENTRAL, MED_NORTE)
    - `nombre`: Nombre descriptivo
    - `pais`: Código del país (CO, MX, PE, CL, etc.)
    
    ### Campos Opcionales:
    - `direccion`, `ciudad`, `responsable`, `telefono`, `email`
    - `tipo`: PRINCIPAL, SECUNDARIA, TRANSITO
    - `capacidad_m3`: Capacidad en metros cúbicos
    - `notas`: Información adicional
    
    ### Respuesta:
    - **201**: Bodega creada exitosamente
    - **409**: Ya existe una bodega con ese código
    - **400**: Datos inválidos
    """
    logger.info(f"📦 Creando bodega: {bodega.codigo}")
    
    try:
        # Normalizar código y país a mayúsculas
        codigo_normalizado = bodega.codigo.upper().strip()
        pais_normalizado = bodega.pais.upper().strip()
        
        # Verificar si ya existe
        existing = (await session.execute(
            select(Bodega).where(Bodega.codigo == codigo_normalizado)
        )).scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "BODEGA_ALREADY_EXISTS",
                    "message": f"Ya existe una bodega con código '{codigo_normalizado}'",
                    "codigo": codigo_normalizado
                }
            )
        
        # Generar UUID para la bodega
        import uuid
        bodega_id = str(uuid.uuid4())
        
        # Crear nueva bodega
        nueva_bodega = Bodega(
            id=bodega_id,
            codigo=codigo_normalizado,
            nombre=bodega.nombre,
            pais=pais_normalizado,
            direccion=bodega.direccion,
            ciudad=bodega.ciudad,
            responsable=bodega.responsable,
            telefono=bodega.telefono,
            email=bodega.email,
            capacidad_m3=bodega.capacidad_m3,
            tipo=bodega.tipo,
            notas=bodega.notas,
            activo=True,
            created_by_user_id=usuario_id
        )
        
        session.add(nueva_bodega)
        await session.commit()
        await session.refresh(nueva_bodega)
        
        logger.info(f"✅ Bodega creada: {codigo_normalizado} - {bodega.nombre}")
        
        return BodegaResponse.model_validate(nueva_bodega)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creando bodega: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "Error al crear bodega",
                "details": str(e)
            }
        )


@router.get("", response_model=BodegaListResponse)
async def listar_bodegas(
    pais: Optional[str] = Query(None, description="Filtrar por país (código ISO 2 letras)"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo (PRINCIPAL, SECUNDARIA, TRANSITO)"),
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(50, ge=1, le=100, description="Tamaño de página"),
    session: AsyncSession = Depends(get_session)
):
    """
    **Listar todas las bodegas**
    
    Obtiene la lista de bodegas registradas en el sistema con información detallada.
    
    ### Filtros Disponibles:
    - `pais`: Filtrar por país (ej: CO, MX, PE)
    - `activo`: true para activas, false para inactivas
    - `tipo`: PRINCIPAL, SECUNDARIA, TRANSITO
    - `page`: Número de página (default: 1)
    - `size`: Resultados por página (default: 50, max: 100)
    
    ### Información Retornada:
    - Datos completos de cada bodega
    - Información de contacto y ubicación
    - Estado activo/inactivo
    - Paginación con metadata
    
    ### Respuesta:
    - **200**: Lista de bodegas con paginación
    """
    start_time = time.time()
    logger.info(f"📦 Listando bodegas (página {page}, tamaño {size})")
    
    try:
        # Construir query base
        query = select(Bodega)
        count_query = select(func.count()).select_from(Bodega)
        
        # Aplicar filtros
        if pais:
            pais_upper = pais.upper()
            query = query.where(Bodega.pais == pais_upper)
            count_query = count_query.where(Bodega.pais == pais_upper)
        
        if activo is not None:
            query = query.where(Bodega.activo == activo)
            count_query = count_query.where(Bodega.activo == activo)
        
        if tipo:
            tipo_upper = tipo.upper()
            query = query.where(Bodega.tipo == tipo_upper)
            count_query = count_query.where(Bodega.tipo == tipo_upper)
        
        # Obtener total
        total = (await session.execute(count_query)).scalar_one()
        
        # Aplicar paginación y ordenamiento
        query = query.order_by(Bodega.pais, Bodega.codigo)
        query = query.offset((page - 1) * size).limit(size)
        
        # Ejecutar query
        result = await session.execute(query)
        bodegas = result.scalars().all()
        
        # Calcular tiempo de ejecución
        took_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"✅ Se encontraron {len(bodegas)} bodega(s) de {total} totales")
        
        return BodegaListResponse(
            items=[BodegaResponse.model_validate(b) for b in bodegas],
            meta=Meta(
                page=page,
                size=size,
                total=total,
                tookMs=took_ms
            )
        )
    
    except Exception as e:
        logger.error(f"❌ Error listando bodegas: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "Error al listar bodegas",
                "details": str(e)
            }
        )
