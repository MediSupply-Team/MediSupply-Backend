"""
Rutas API para cliente-service siguiendo patrón catalogo-service
Endpoints REST para HU07: Consultar Cliente + CRUD completo
"""
import time
import logging
import random
import string
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, List

from app.db import get_session
from app.services.client_service import ClienteService
from app.schemas import (
    ClienteBasicoResponse, HistoricoCompletoResponse,
    ClienteCreate, ClienteUpdate,
    ErrorResponse
)
from app.config import get_settings

# Router para endpoints de cliente
router = APIRouter(prefix="/cliente", tags=["cliente"])
settings = get_settings()
logger = logging.getLogger(__name__)


async def generar_codigo_unico(session: AsyncSession, max_intentos: int = 10) -> str:
    """
    Genera un código único con formato: 3 letras mayúsculas + 3 números (ejemplo: ABC123)
    Verifica que el código sea único en la base de datos.
    
    Args:
        session: Sesión de base de datos
        max_intentos: Número máximo de intentos para generar un código único
        
    Returns:
        str: Código único generado
        
    Raises:
        HTTPException: Si no se puede generar un código único después de max_intentos
    """
    from app.models.client_model import Cliente
    
    for intento in range(max_intentos):
        # Generar 3 letras mayúsculas aleatorias
        letras = ''.join(random.choices(string.ascii_uppercase, k=3))
        # Generar 3 números aleatorios
        numeros = ''.join(random.choices(string.digits, k=3))
        # Combinar en el formato XXX999
        codigo = f"{letras}{numeros}"
        
        # Verificar si el código ya existe
        existing = (await session.execute(
            select(Cliente).where(Cliente.codigo_unico == codigo)
        )).scalar_one_or_none()
        
        if not existing:
            logger.info(f"✨ Código único generado: {codigo} (intento {intento + 1})")
            return codigo
    
    # Si llegamos aquí, no se pudo generar un código único
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "error": "CODIGO_GENERATION_FAILED",
            "message": f"No se pudo generar un código único después de {max_intentos} intentos",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
    )


@router.get("/sin-vendedor", response_model=List[ClienteBasicoResponse])
async def listar_clientes_sin_vendedor(
    request: Request,
    limite: int = Query(
        default=50,
        ge=1,
        le=500,
        description="Número máximo de clientes a retornar"
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Número de registros a saltar (para paginación)"
    ),
    activos_solo: bool = Query(
        default=True,
        description="Si mostrar solo clientes activos (true) o todos (false)"
    ),
    session: AsyncSession = Depends(get_session)
):
    """
    Listar todos los clientes que NO tienen vendedor asociado
    
    **Útil para:**
    - Identificar clientes sin asignar
    - Asignar vendedores a clientes nuevos
    - Reportes de cobertura de vendedores
    
    **Retorna:**
    - Lista de clientes sin vendedor_id
    """
    from app.models.client_model import Cliente
    
    started = time.perf_counter_ns()
    logger.info(f"📋 Listando clientes sin vendedor (activos_solo={activos_solo})")
    
    try:
        # Construir query para clientes sin vendedor
        query = select(Cliente).where(Cliente.vendedor_id.is_(None))
        
        if activos_solo:
            query = query.where(Cliente.activo == True)
        
        # Ordenar por nombre
        query = query.order_by(Cliente.nombre)
        
        # Aplicar paginación
        query = query.offset(offset).limit(limite)
        
        # Ejecutar query
        result = await session.execute(query)
        clientes_sin_vendedor = result.scalars().all()
        
        # Medir performance
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        logger.info(f"📋 Encontrados {len(clientes_sin_vendedor)} clientes sin vendedor en {took_ms}ms")
        
        # Formatear respuesta
        return [
            {
                "id": str(c.id),
                "nit": c.nit,
                "nombre": c.nombre,
                "codigo_unico": c.codigo_unico,
                "email": c.email,
                "telefono": c.telefono,
                "direccion": c.direccion,
                "ciudad": c.ciudad,
                "pais": c.pais,
                "activo": c.activo,
                "vendedor_id": None,
                "rol": c.rol if hasattr(c, 'rol') else None,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None
            }
            for c in clientes_sin_vendedor
        ]
        
    except Exception as e:
        logger.error(f"❌ Error listando clientes sin vendedor: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Error interno al listar clientes sin vendedor",
                "details": {"error_id": f"ERR_{int(time.time())}"},
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        )


@router.get("/",response_model=List[ClienteBasicoResponse],)
async def listar_clientes(
    request: Request,
    limite: int = Query(
        default=50,
        ge=1,
        le=500,
        description="Número máximo de clientes a retornar"
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Número de registros a saltar (para paginación)"
    ),
    activos_solo: bool = Query(
        default=True,
        description="Si mostrar solo clientes activos (true) o todos (false)"
    ),
    ordenar_por: str = Query(
        default="nombre",
        pattern="^(nombre|nit|codigo_unico|created_at)$",
        description="Campo por el cual ordenar los resultados"
    ),
    vendedor_id: Optional[str] = Query(
        None,
        min_length=1,
        max_length=64,
        description="ID del vendedor para filtrar clientes (opcional)"
    ),
    session: AsyncSession = Depends(get_session)
):
    """
    Listar todos los clientes disponibles con paginación y filtros
    
    Si se proporciona vendedor_id, filtra solo los clientes de ese vendedor
    """
    started = time.perf_counter_ns()
    
    # Validación de vendedor_id fuera del try principal para manejar correctamente el error
    if vendedor_id:
        from uuid import UUID
        try:
            vendedor_uuid = UUID(vendedor_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "INVALID_VENDEDOR_UUID",
                    "message": f"vendedor_id '{vendedor_id}' no es un UUID válido. Debe ser un UUID en formato: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                }
            )
    
    try:
        # Si se proporciona vendedor_id, filtrar por ese vendedor
        if vendedor_id:
            from app.models.client_model import Cliente
            
            # Construir query con filtro de vendedor
            query = select(Cliente).where(Cliente.vendedor_id == vendedor_uuid)
            
            if activos_solo:
                query = query.where(Cliente.activo == True)
            
            # Ordenar
            if ordenar_por == "nombre":
                query = query.order_by(Cliente.nombre)
            elif ordenar_por == "nit":
                query = query.order_by(Cliente.nit)
            elif ordenar_por == "codigo_unico":
                query = query.order_by(Cliente.codigo_unico)
            elif ordenar_por == "created_at":
                query = query.order_by(Cliente.created_at.desc())
            
            # Aplicar paginación
            query = query.offset(offset).limit(limite)
            
            # Ejecutar query
            result = await session.execute(query)
            clientes_filtrados = result.scalars().all()
            
            # Medir performance
            took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
            logger.info(f"📋 Listados {len(clientes_filtrados)} clientes del vendedor {vendedor_id} en {took_ms}ms")
            
            # Formatear respuesta (mismo formato que el listado sin filtro)
            return [
                {
                    "id": str(c.id),
                    "nit": c.nit,
                    "nombre": c.nombre,
                    "codigo_unico": c.codigo_unico,
                    "email": c.email,
                    "telefono": c.telefono,
                    "direccion": c.direccion,
                    "ciudad": c.ciudad,
                    "pais": c.pais,
                    "activo": c.activo,
                    "vendedor_id": str(c.vendedor_id) if c.vendedor_id else None,
                    "rol": c.rol if hasattr(c, 'rol') else None,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "updated_at": c.updated_at.isoformat() if c.updated_at else None
                }
                for c in clientes_filtrados
            ]
        
        # Si no hay vendedor_id, usar el servicio normal
        service = ClienteService(session, settings)
        clientes = await service.listar_clientes(
            limite=limite,
            offset=offset,
            activos_solo=activos_solo,
            ordenar_por=ordenar_por
        )
        
        # Medir performance
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        
        print(f"🔍 DEBUG: Listando {len(clientes)} clientes en {took_ms}ms")
        
        # Usar return directo - FastAPI maneja la serialización automáticamente
        return clientes
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Error interno al listar clientes",
                "details": {"error_id": f"ERR_{int(time.time())}"},
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        )


@router.post("/", response_model=ClienteBasicoResponse, status_code=status.HTTP_201_CREATED)
async def crear_cliente(
    cliente: ClienteCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Crea un nuevo cliente en el sistema
    
    **Requiere:**
    - ID único del cliente
    - NIT (debe ser único)
    - Nombre del cliente
    - Código único (debe ser único)
    - Vendedor ID (opcional - para trazabilidad y asignación)
    
    **Retorna:**
    - 201: Cliente creado exitosamente
    - 409: Cliente ya existe (NIT o código único duplicado)
    - 500: Error interno
    """
    vendedor_info = f"por vendedor {cliente.vendedor_id}" if cliente.vendedor_id else "sin vendedor asignado"
    codigo_info = f"con código {cliente.codigo_unico}" if cliente.codigo_unico else "con código auto-generado"
    logger.info(f"📝 Creando cliente: {cliente.nombre} (NIT: {cliente.nit}) {codigo_info} {vendedor_info}")
    started = time.perf_counter_ns()
    
    # Validar vendedor_id SOLO si se proporciona
    from uuid import UUID
    vendedor_uuid = None
    if cliente.vendedor_id:
        try:
            vendedor_uuid = UUID(cliente.vendedor_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "INVALID_VENDEDOR_UUID",
                    "message": f"vendedor_id '{cliente.vendedor_id}' no es un UUID válido. Debe ser un UUID en formato: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                }
            )
    
    try:
        from app.models.client_model import Cliente
        
        # Verificar si el NIT ya existe
        existing_by_nit = (await session.execute(
            select(Cliente).where(Cliente.nit == cliente.nit)
        )).scalar_one_or_none()
        
        if existing_by_nit:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "NIT_ALREADY_EXISTS",
                    "message": f"Cliente con NIT {cliente.nit} ya existe",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                }
            )
        
        # Generar código único automáticamente si no se proporciona
        codigo_unico_final = cliente.codigo_unico
        if not codigo_unico_final:
            codigo_unico_final = await generar_codigo_unico(session)
            logger.info(f"✨ Código único auto-generado: {codigo_unico_final}")
        else:
            # Si se proporciona, verificar que no exista
            existing_by_codigo = (await session.execute(
                select(Cliente).where(Cliente.codigo_unico == codigo_unico_final)
            )).scalar_one_or_none()
            
            if existing_by_codigo:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": "CODIGO_ALREADY_EXISTS",
                        "message": f"Cliente con código único {codigo_unico_final} ya existe",
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                    }
                )
        
        # Crear nuevo cliente (id se genera automáticamente con UUID)
        new_cliente = Cliente(
            nit=cliente.nit,
            nombre=cliente.nombre,
            codigo_unico=codigo_unico_final,
            email=cliente.email,
            telefono=cliente.telefono,
            direccion=cliente.direccion,
            ciudad=cliente.ciudad,
            pais=cliente.pais,
            activo=cliente.activo,
            vendedor_id=vendedor_uuid
        )
        
        session.add(new_cliente)
        await session.commit()
        await session.refresh(new_cliente)
        
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        logger.info(f"✅ Cliente creado: {new_cliente.id} ({cliente.nombre}) en {took_ms}ms")
        
        # Retornar el cliente creado
        return ClienteBasicoResponse.model_validate(new_cliente)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creando cliente: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Error interno al crear cliente",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        )


@router.put("/{cliente_id}", response_model=ClienteBasicoResponse)
async def actualizar_cliente(
    cliente_id: str = Path(..., min_length=1, max_length=64, description="ID del cliente"),
    cliente_data: ClienteUpdate = None,
    session: AsyncSession = Depends(get_session)
):
    """
    Actualiza un cliente existente
    
    **Requiere:**
    - ID del cliente (en la URL)
    - Campos a actualizar (todos opcionales, incluyendo vendedor_id)
    
    **Retorna:**
    - 200: Cliente actualizado exitosamente
    - 404: Cliente no encontrado
    - 500: Error interno
    """
    logger.info(f"🔄 Actualizando cliente: {cliente_id}")
    started = time.perf_counter_ns()
    
    # Validar vendedor_id SOLO si se proporciona
    from uuid import UUID
    vendedor_uuid = None
    if cliente_data and cliente_data.vendedor_id:
        try:
            vendedor_uuid = UUID(cliente_data.vendedor_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "INVALID_VENDEDOR_UUID",
                    "message": f"vendedor_id '{cliente_data.vendedor_id}' no es un UUID válido. Debe ser un UUID en formato: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                }
            )
    
    try:
        from app.models.client_model import Cliente
        
        # Verificar que el cliente existe
        existing = (await session.execute(
            select(Cliente).where(Cliente.id == cliente_id)
        )).scalar_one_or_none()
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "CLIENT_NOT_FOUND",
                    "message": f"Cliente con id {cliente_id} no encontrado",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                }
            )
        
        # Actualizar solo los campos proporcionados (ahora incluye vendedor_id)
        update_data = cliente_data.model_dump(exclude_unset=True, exclude={'vendedor_id'})
        
        if update_data:
            for field, value in update_data.items():
                setattr(existing, field, value)
        
        # Actualizar vendedor_id si se proporcionó
        if cliente_data.vendedor_id is not None:
            existing.vendedor_id = vendedor_uuid
            logger.info(f"  ↳ Actualizando vendedor_id a: {vendedor_uuid}")
        
        if update_data or cliente_data.vendedor_id is not None:
            existing.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(existing)
        
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        logger.info(f"✅ Cliente actualizado: {cliente_id} en {took_ms}ms")
        
        return ClienteBasicoResponse.model_validate(existing)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error actualizando cliente: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Error interno al actualizar cliente",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        )


@router.get(
    "/search",
    response_model=ClienteBasicoResponse,
    summary="Buscar cliente por NIT, nombre o código único",
    description="""
    Busca un cliente por NIT, nombre o código único.
    
    **Criterios de aceptación implementados:**
    - El vendedor puede buscar un cliente por NIT, nombre o código único
    - La consulta debe responder en ≤ 2 segundos  
    - La información consultada queda registrada para trazabilidad
    
    **Ejemplos de búsqueda:**
    - Por NIT: `900123456-7`
    - Por nombre: `Farmacia San José` 
    - Por código: `FSJ001`
    """
)
async def buscar_cliente(
    request: Request,
    q: str = Query(
        ...,
        min_length=2,
        max_length=255,
        description="NIT, nombre o código único del cliente a buscar"
    ),
    vendedor_id: str = Query(
        ...,
        min_length=1,
        max_length=64,
        description="ID del vendedor que realiza la consulta (para trazabilidad)"
    ),
    session: AsyncSession = Depends(get_session)
):
    """Buscar cliente por NIT, nombre o código único"""
    print(f"🔍 DEBUG: Iniciando buscar_cliente con q='{q}', vendedor_id='{vendedor_id}'")
    started = time.perf_counter_ns()
    
    try:
        print(f"🔍 DEBUG: Creando ClienteService...")
        service = ClienteService(session, settings)
        print(f"🔍 DEBUG: ClienteService creado, llamando buscar_cliente...")
        cliente = await service.buscar_cliente(
            termino_busqueda=q,
            vendedor_id=vendedor_id
        )
        print(f"🔍 DEBUG: Cliente encontrado: {cliente}")
        
        # Medir performance
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        
        # Headers informativos (usando Response para agregar headers)
        print(f"🔍 DEBUG: Añadiendo headers informativos - Response time: {took_ms}ms")
        
        # Usar response directo - FastAPI maneja la serialización automáticamente
        return cliente
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ DEBUG ERROR en buscar_cliente: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"❌ DEBUG TRACEBACK: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Error interno al buscar cliente",
                "details": {"error_id": f"ERR_{int(time.time())}"},
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        )


@router.get(
    "/{cliente_id}/historico",
    response_model=HistoricoCompletoResponse,
    summary="Obtener histórico completo del cliente",
    description="""
    Obtiene el histórico completo de un cliente incluyendo:
    
    **Criterios de aceptación implementados:**
    - Histórico de compras del cliente (productos, cantidades, fechas)
    - Productos preferidos y frecuencia de compra  
    - Devoluciones realizadas con sus motivos
    - La consulta debe responder en ≤ 2 segundos
    - La información consultada queda registrada para trazabilidad
    
    **Datos incluidos:**
    - 📋 Histórico de compras (últimos N meses)
    - ⭐ Productos preferidos con estadísticas
    - 🔄 Devoluciones con motivos
    - 📊 Estadísticas resumidas del cliente
    """
)
async def obtener_historico_cliente(
    request: Request,
    cliente_id: str = Path(
        ...,
        min_length=1,
        max_length=64,
        description="ID único del cliente"
    ),
    vendedor_id: str = Query(
        ...,
        min_length=1,
        max_length=64,
        description="ID del vendedor que realiza la consulta"
    ),
    limite_meses: int = Query(
        default=12,
        ge=1,
        le=60,
        description="Número de meses hacia atrás para el histórico (máximo 60)"
    ),
    incluir_devoluciones: bool = Query(
        default=True,
        description="Si incluir o no las devoluciones en el histórico"
    ),
    session: AsyncSession = Depends(get_session)
):
    """Obtener histórico completo del cliente"""
    started = time.perf_counter_ns()
    
    try:
        service = ClienteService(session, settings)
        historico = await service.obtener_historico_completo(
            cliente_id=cliente_id,
            vendedor_id=vendedor_id,
            limite_meses=limite_meses,
            incluir_devoluciones=incluir_devoluciones
        )
        
        # Medir performance
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        print(f"🔍 DEBUG: Histórico completo obtenido en {took_ms}ms")
        
        # Usar return directo - FastAPI maneja la serialización automáticamente
        return historico
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Error interno al obtener histórico del cliente",
                "details": {
                    "cliente_id": cliente_id,
                    "error_id": f"ERR_{int(time.time())}"
                },
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        )


@router.get(
    "/health",
    summary="Health check del servicio",
    description="Endpoint de health check para verificar el estado del servicio"
)
async def health_check(request: Request):
    """Health check del servicio"""
    return {
        "status": "healthy",
        "service": "cliente-service",
        "version": "1.0.0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sla_max_response_ms": settings.sla_max_response_ms,
        "database": "connected"
    }


@router.get(
    "/metrics",
    summary="Métricas del servicio",
    description="Obtener métricas básicas del servicio cliente"
)
async def get_metrics(
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """Obtener métricas del servicio"""
    try:
        service = ClienteService(session, settings)
        metrics = await service.obtener_metricas()
        
        print(f"🔍 DEBUG: Métricas obtenidas: {metrics}")
        return metrics
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "METRICS_ERROR",
                "message": "Error al obtener métricas",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        )