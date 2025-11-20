"""
Rutas para gestión de Vendedores - Fase 3 Completo
HU: Registrar Vendedor - CRUD completo con Plan de Venta en cascada
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from app.db import get_session
from app.models.client_model import Vendedor, Cliente
from app.models.catalogo_model import TipoRolVendedor, Territorio, TipoPlan, Region, Zona
from app.models.plan_venta_model import PlanVenta, PlanProducto, PlanRegion, PlanZona
from app.schemas import (
    VendedorCreate,
    VendedorUpdate,
    VendedorResponse,
    VendedorDetalleResponse,
    VendedorListResponse,
    ClienteBasicoResponse,
    AsociarClientesRequest,
    AsociarClientesResponse
)
from typing import Optional, List
from uuid import UUID
import time
import logging
import secrets
import string
from passlib.context import CryptContext

router = APIRouter(tags=["vendedores"])
logger = logging.getLogger(__name__)

# Configurar bcrypt para hashear contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_random_password(length: int = 12) -> str:
    """Genera una contraseña aleatoria segura (max 12 chars para bcrypt)"""
    # Usar solo caracteres ASCII simples para evitar problemas de codificación
    # Caracteres especiales de 1 byte
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    # Limitar a 12 caracteres para evitar el límite de 72 bytes de bcrypt
    safe_length = min(length, 12)
    password = ''.join(secrets.choice(alphabet) for _ in range(safe_length))
    return password


def truncate_to_bytes(text: str, max_bytes: int = 72) -> str:
    """Trunca un string para que no exceda max_bytes cuando se codifica a UTF-8"""
    encoded = text.encode('utf-8')
    if len(encoded) <= max_bytes:
        return text
    # Truncar byte por byte hasta que quepa
    return encoded[:max_bytes].decode('utf-8', errors='ignore')


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
        # 🔹 GENERAR CONTRASEÑA AUTOMÁTICAMENTE SI NO SE PROPORCIONA
        generated_password = None
        if not vendedor.username:
            # Generar username automático basado en email
            vendedor.username = vendedor.email.split('@')[0].lower()
        
        # Si no tiene password_hash, generar contraseña automática
        if not vendedor.password_hash:
            generated_password = generate_random_password()
            logger.info(f"🔐 Generando contraseña automática para {vendedor.email}")
            logger.info(f"🔐 Contraseña generada: longitud={len(generated_password)} bytes={len(generated_password.encode('utf-8'))}")
            # Truncar a 72 bytes si es necesario (límite de bcrypt)
            generated_password = truncate_to_bytes(generated_password, 72)
            vendedor.password_hash = pwd_context.hash(generated_password)
            logger.info(f"🔐 Contraseña hasheada exitosamente")
        else:
            logger.info(f"🔐 password_hash recibido: longitud={len(vendedor.password_hash)}")
            # Si viene password_hash, verificar que no sea demasiado largo (probablemente ya está hasheado)
            # Si es muy largo (>100 chars), asumir que ya está hasheado
            # Si es corto, hashear
            if len(vendedor.password_hash) < 100:
                logger.info(f"🔐 Hasheando password recibido (longitud < 100)")
                # Es una contraseña en texto plano, truncar a 72 bytes y hashear
                password_truncated = truncate_to_bytes(vendedor.password_hash, 72)
                vendedor.password_hash = pwd_context.hash(password_truncated)
                logger.info(f"🔐 Contraseña hasheada para {vendedor.username}")
            else:
                logger.info(f"🔐 password_hash ya está hasheado (longitud >= 100)")
        
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
        
        # Verificar si el username ya existe (si se proporciona)
        if vendedor.username:
            existing_by_username = (await session.execute(
                select(Vendedor).where(Vendedor.username == vendedor.username)
            )).scalar_one_or_none()
            
            if existing_by_username:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": "USERNAME_ALREADY_EXISTS",
                        "message": f"Username '{vendedor.username}' ya está en uso",
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                    }
                )
        
        # Validar FK: rol_vendedor_id (si se proporciona)
        if vendedor.rol_vendedor_id:
            tipo_rol = await session.get(TipoRolVendedor, vendedor.rol_vendedor_id)
            if not tipo_rol or not tipo_rol.activo:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": "TIPO_ROL_NOT_FOUND",
                        "message": f"Tipo de rol con ID '{vendedor.rol_vendedor_id}' no encontrado o inactivo"
                    }
                )
        
        # Validar FK: territorio_id (si se proporciona)
        if vendedor.territorio_id:
            territorio = await session.get(Territorio, vendedor.territorio_id)
            if not territorio or not territorio.activo:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": "TERRITORIO_NOT_FOUND",
                        "message": f"Territorio con ID '{vendedor.territorio_id}' no encontrado o inactivo"
                    }
                )
        
        # Validar FK: supervisor_id (si se proporciona)
        supervisor_uuid = None
        if vendedor.supervisor_id:
            try:
                supervisor_uuid = UUID(vendedor.supervisor_id)
                supervisor = await session.get(Vendedor, supervisor_uuid)
                if not supervisor or not supervisor.activo:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail={
                            "error": "SUPERVISOR_NOT_FOUND",
                            "message": f"Supervisor con ID '{vendedor.supervisor_id}' no encontrado o inactivo"
                        }
                    )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": "INVALID_UUID", "message": f"supervisor_id '{vendedor.supervisor_id}' no es un UUID válido"}
                )
        
        # Crear nuevo vendedor (ID se genera automáticamente)
        new_vendedor = Vendedor(
            identificacion=vendedor.identificacion,
            nombre_completo=vendedor.nombre_completo,
            email=vendedor.email,
            telefono=vendedor.telefono,
            pais=vendedor.pais,
            username=vendedor.username,
            password_hash=vendedor.password_hash,
            rol=vendedor.rol,
            rol_vendedor_id=vendedor.rol_vendedor_id,
            territorio_id=vendedor.territorio_id,
            supervisor_id=supervisor_uuid,
            fecha_ingreso=vendedor.fecha_ingreso,
            observaciones=vendedor.observaciones,
            activo=vendedor.activo,
            created_by_user_id=vendedor.created_by_user_id
        )
        
        session.add(new_vendedor)
        await session.flush()  # Flush para obtener el ID del vendedor sin hacer commit
        
        # 🔹 CREAR PLAN DE VENTA EN CASCADA (si se envió)
        if vendedor.plan_venta:
            logger.info(f"📦 Creando Plan de Venta para vendedor {new_vendedor.id}")
            plan_data = vendedor.plan_venta
            
            # Validar tipo_plan_id (si se proporciona)
            if plan_data.tipo_plan_id:
                tipo_plan = await session.get(TipoPlan, plan_data.tipo_plan_id)
                if not tipo_plan or not tipo_plan.activo:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail={
                            "error": "TIPO_PLAN_NOT_FOUND",
                            "message": f"Tipo de plan con ID '{plan_data.tipo_plan_id}' no encontrado o inactivo"
                        }
                    )
            
            # Crear el Plan de Venta
            new_plan = PlanVenta(
                vendedor_id=new_vendedor.id,  # ← ID del vendedor recién creado
                tipo_plan_id=plan_data.tipo_plan_id,
                nombre_plan=plan_data.nombre_plan,
                fecha_inicio=plan_data.fecha_inicio,
                fecha_fin=plan_data.fecha_fin,
                meta_ventas=plan_data.meta_ventas,
                comision_base=plan_data.comision_base,
                estructura_bonificaciones=plan_data.estructura_bonificaciones,
                observaciones=plan_data.observaciones,
                activo=plan_data.activo,
                created_by_user_id=plan_data.created_by_user_id
            )
            session.add(new_plan)
            await session.flush()  # Flush para obtener el ID del plan
            
            # Crear productos asignados
            if plan_data.productos:
                for producto_item in plan_data.productos:
                    plan_producto = PlanProducto(
                        plan_venta_id=new_plan.id,
                        producto_id=producto_item.producto_id,  # Solo ID, frontend consulta catalogo-service
                        meta_cantidad=producto_item.meta_cantidad,
                        precio_unitario=producto_item.precio_unitario
                    )
                    session.add(plan_producto)
                logger.info(f"   ✅ {len(plan_data.productos)} productos asignados")
            
            # Crear regiones asignadas
            if plan_data.region_ids:
                for region_id in plan_data.region_ids:
                    # Validar que la región exista y esté activa
                    region = await session.get(Region, region_id)
                    if not region or not region.activo:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail={
                                "error": "REGION_NOT_FOUND",
                                "message": f"Región con ID '{region_id}' no encontrada o inactiva"
                            }
                        )
                    
                    plan_region = PlanRegion(
                        plan_venta_id=new_plan.id,
                        region_id=region_id
                    )
                    session.add(plan_region)
                logger.info(f"   ✅ {len(plan_data.region_ids)} regiones asignadas")
            
            # Crear zonas asignadas
            if plan_data.zona_ids:
                for zona_id in plan_data.zona_ids:
                    # Validar que la zona exista y esté activa
                    zona = await session.get(Zona, zona_id)
                    if not zona or not zona.activo:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail={
                                "error": "ZONA_NOT_FOUND",
                                "message": f"Zona con ID '{zona_id}' no encontrada o inactiva"
                            }
                        )
                    
                    plan_zona = PlanZona(
                        plan_venta_id=new_plan.id,
                        zona_id=zona_id
                    )
                    session.add(plan_zona)
                logger.info(f"   ✅ {len(plan_data.zona_ids)} zonas asignadas")
        
        # Commit de toda la transacción (vendedor + plan + productos + regiones + zonas)
        await session.commit()
        await session.refresh(new_vendedor)
        
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        logger.info(f"✅ Vendedor creado: {new_vendedor.id} en {took_ms}ms")
        
        # Obtener plan_venta_id si se creó
        plan_venta_id = new_plan.id if vendedor.plan_venta else None
        
        # Construir response con plan_venta_id
        vendedor_dict = {
            "id": new_vendedor.id,
            "identificacion": new_vendedor.identificacion,
            "nombre_completo": new_vendedor.nombre_completo,
            "email": new_vendedor.email,
            "telefono": new_vendedor.telefono,
            "pais": new_vendedor.pais,
            "username": new_vendedor.username,
            "rol": new_vendedor.rol,
            "rol_vendedor_id": new_vendedor.rol_vendedor_id,
            "territorio_id": new_vendedor.territorio_id,
            "supervisor_id": new_vendedor.supervisor_id,
            "fecha_ingreso": new_vendedor.fecha_ingreso,
            "observaciones": new_vendedor.observaciones,
            "activo": new_vendedor.activo,
            "created_at": new_vendedor.created_at,
            "updated_at": new_vendedor.updated_at,
            "created_by_user_id": new_vendedor.created_by_user_id,
            "plan_venta_id": plan_venta_id  # Solo el ID del plan
        }
        
        response = VendedorResponse(**vendedor_dict)
        
        # 🔐 Si se generó contraseña, agregarla a la respuesta (solo esta vez)
        if generated_password:
            response_dict = response.model_dump()
            response_dict["temporary_password"] = generated_password
            logger.info(f"✅ Vendedor creado con contraseña temporal")
            return response_dict
        
        return response
        
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
    
    # Obtener plan_venta_id si existe
    plan_venta = (await session.execute(
        select(PlanVenta.id).where(PlanVenta.vendedor_id == uuid_id)
    )).scalar_one_or_none()
    
    # Construir response con plan_venta_id
    vendedor_dict = {
        "id": vendedor.id,
        "identificacion": vendedor.identificacion,
        "nombre_completo": vendedor.nombre_completo,
        "email": vendedor.email,
        "telefono": vendedor.telefono,
        "pais": vendedor.pais,
        "username": vendedor.username,
        "rol": vendedor.rol,
        "rol_vendedor_id": vendedor.rol_vendedor_id,
        "territorio_id": vendedor.territorio_id,
        "supervisor_id": vendedor.supervisor_id,
        "fecha_ingreso": vendedor.fecha_ingreso,
        "observaciones": vendedor.observaciones,
        "activo": vendedor.activo,
        "created_at": vendedor.created_at,
        "updated_at": vendedor.updated_at,
        "created_by_user_id": vendedor.created_by_user_id,
        "plan_venta_id": plan_venta  # Solo el ID del plan
    }
    
    return VendedorResponse(**vendedor_dict)


@router.get("/{vendedor_id}/detalle", response_model=VendedorDetalleResponse)
async def obtener_vendedor_detalle(
    vendedor_id: str,  # Recibe como string desde URL
    session: AsyncSession = Depends(get_session)
):
    """
    Obtener DETALLE COMPLETO de un vendedor con TODO su plan de venta
    
    Incluye:
    - Información del vendedor
    - Plan de venta completo con:
        - Tipo de plan (objeto completo)
        - Productos asignados (solo IDs, frontend consulta catalogo-service)
        - Regiones asignadas (objetos completos)
        - Zonas asignadas (objetos completos)
        - Estructura de bonificaciones
    
    **Retorna:**
    - 200: Vendedor con plan completo encontrado
    - 400: ID inválido
    - 404: Vendedor no encontrado
    """
    logger.info(f"🔍 Obteniendo DETALLE COMPLETO de vendedor: {vendedor_id}")
    started = time.perf_counter_ns()
    
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
    
    # Cargar vendedor CON todas las relaciones del plan (eager loading)
    vendedor = (await session.execute(
        select(Vendedor)
        .options(
            selectinload(Vendedor.plan_venta)
            .selectinload(PlanVenta.tipo_plan)
        )
        .options(
            selectinload(Vendedor.plan_venta)
            .selectinload(PlanVenta.productos_asignados)
        )
        .options(
            selectinload(Vendedor.plan_venta)
            .selectinload(PlanVenta.regiones_asignadas)
            .selectinload(PlanRegion.region)
        )
        .options(
            selectinload(Vendedor.plan_venta)
            .selectinload(PlanVenta.zonas_asignadas)
            .selectinload(PlanZona.zona)
        )
        .where(Vendedor.id == uuid_id)
    )).scalar_one_or_none()
    
    if not vendedor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "VENDEDOR_NOT_FOUND",
                "message": f"Vendedor {vendedor_id} no encontrado"
            }
        )
    
    # Construir respuesta transformando las relaciones M2M
    vendedor_dict = {
        "id": vendedor.id,
        "identificacion": vendedor.identificacion,
        "nombre_completo": vendedor.nombre_completo,
        "email": vendedor.email,
        "telefono": vendedor.telefono,
        "pais": vendedor.pais,
        "username": vendedor.username,
        "rol": vendedor.rol,
        "rol_vendedor_id": vendedor.rol_vendedor_id,
        "territorio_id": vendedor.territorio_id,
        "supervisor_id": vendedor.supervisor_id,
        "fecha_ingreso": vendedor.fecha_ingreso,
        "observaciones": vendedor.observaciones,
        "activo": vendedor.activo,
        "created_at": vendedor.created_at,
        "updated_at": vendedor.updated_at,
        "created_by_user_id": vendedor.created_by_user_id,
        "plan_venta": None
    }
    
    # Si tiene plan de venta, construir el objeto completo
    if vendedor.plan_venta:
        plan = vendedor.plan_venta
        vendedor_dict["plan_venta"] = {
            "id": plan.id,
            "vendedor_id": plan.vendedor_id,
            "tipo_plan_id": plan.tipo_plan_id,
            "nombre_plan": plan.nombre_plan,
            "fecha_inicio": plan.fecha_inicio,
            "fecha_fin": plan.fecha_fin,
            "meta_ventas": plan.meta_ventas,
            "comision_base": plan.comision_base,
            "estructura_bonificaciones": plan.estructura_bonificaciones,
            "observaciones": plan.observaciones,
            "activo": plan.activo,
            "created_at": plan.created_at,
            "updated_at": plan.updated_at,
            "created_by_user_id": plan.created_by_user_id,
            "tipo_plan": plan.tipo_plan,  # Ya es un objeto TipoPlan
            "productos_asignados": plan.productos_asignados,  # Ya es List[PlanProducto]
            "regiones_asignadas": [pr.region for pr in plan.regiones_asignadas],  # Extraer Region de PlanRegion
            "zonas_asignadas": [pz.zona for pz in plan.zonas_asignadas]  # Extraer Zona de PlanZona
        }
    
    took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
    logger.info(f"✅ Detalle de vendedor cargado en {took_ms}ms (plan completo incluido)")
    
    return VendedorDetalleResponse.model_validate(vendedor_dict)


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
        
        # Validar username único (si se actualiza)
        if vendedor_data.username and vendedor_data.username != vendedor.username:
            existing_username = (await session.execute(
                select(Vendedor).where(Vendedor.username == vendedor_data.username)
            )).scalar_one_or_none()
            if existing_username:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"error": "USERNAME_ALREADY_EXISTS", "message": f"Username '{vendedor_data.username}' ya está en uso"}
                )
        
        # Actualizar campos y validar FK
        update_data = vendedor_data.model_dump(exclude_unset=True)
        
        # Validar y convertir FK antes de asignar
        if "rol_vendedor_id" in update_data and update_data["rol_vendedor_id"]:
            tipo_rol = await session.get(TipoRolVendedor, update_data["rol_vendedor_id"])
            if not tipo_rol or not tipo_rol.activo:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": "TIPO_ROL_NOT_FOUND", "message": f"Tipo de rol no encontrado o inactivo"}
                )
        
        if "territorio_id" in update_data and update_data["territorio_id"]:
            territorio = await session.get(Territorio, update_data["territorio_id"])
            if not territorio or not territorio.activo:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": "TERRITORIO_NOT_FOUND", "message": f"Territorio no encontrado o inactivo"}
                )
        
        if "supervisor_id" in update_data and update_data["supervisor_id"]:
            try:
                supervisor_uuid = UUID(update_data["supervisor_id"])
                # Evitar ciclo: el vendedor no puede ser su propio supervisor
                if supervisor_uuid == uuid_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={"error": "SELF_SUPERVISION_NOT_ALLOWED", "message": "Un vendedor no puede ser su propio supervisor"}
                    )
                supervisor = await session.get(Vendedor, supervisor_uuid)
                if not supervisor or not supervisor.activo:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail={"error": "SUPERVISOR_NOT_FOUND", "message": f"Supervisor no encontrado o inactivo"}
                    )
                update_data["supervisor_id"] = supervisor_uuid
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": "INVALID_UUID", "message": "supervisor_id no es un UUID válido"}
                )
        
        # Aplicar cambios
        for key, value in update_data.items():
            setattr(vendedor, key, value)
        
        await session.commit()
        await session.refresh(vendedor)
        
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        logger.info(f"✅ Vendedor actualizado: {vendedor_id} en {took_ms}ms")
        
        # Obtener plan_venta_id si existe
        plan_venta_id_result = (await session.execute(
            select(PlanVenta.id).where(PlanVenta.vendedor_id == uuid_id)
        )).scalar_one_or_none()
        
        # Construir response con plan_venta_id
        vendedor_dict = {
            "id": vendedor.id,
            "identificacion": vendedor.identificacion,
            "nombre_completo": vendedor.nombre_completo,
            "email": vendedor.email,
            "telefono": vendedor.telefono,
            "pais": vendedor.pais,
            "username": vendedor.username,
            "rol": vendedor.rol,
            "rol_vendedor_id": vendedor.rol_vendedor_id,
            "territorio_id": vendedor.territorio_id,
            "supervisor_id": vendedor.supervisor_id,
            "fecha_ingreso": vendedor.fecha_ingreso,
            "observaciones": vendedor.observaciones,
            "activo": vendedor.activo,
            "created_at": vendedor.created_at,
            "updated_at": vendedor.updated_at,
            "created_by_user_id": vendedor.created_by_user_id,
            "plan_venta_id": plan_venta_id_result  # Solo el ID del plan
        }
        
        return VendedorResponse(**vendedor_dict)
        
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


@router.post("/{vendedor_id}/clientes/asociar", response_model=AsociarClientesResponse, status_code=status.HTTP_200_OK)
async def asociar_clientes_a_vendedor(
    vendedor_id: str,
    payload: AsociarClientesRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Asociar múltiples clientes a un vendedor
    
    **Validaciones:**
    - El vendedor debe existir y estar activo
    - Los clientes deben existir
    - Solo se asocian clientes activos
    - Se reportan clientes no encontrados o inactivos
    
    **Retorna:**
    - 200: Clientes asociados exitosamente (con detalles de éxitos y fallos)
    - 400: ID de vendedor inválido
    - 404: Vendedor no encontrado o inactivo
    """
    logger.info(f"🔗 Asociando {len(payload.clientes_ids)} clientes al vendedor: {vendedor_id}")
    started = time.perf_counter_ns()
    
    # Validar UUID del vendedor
    try:
        vendedor_uuid = UUID(vendedor_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_VENDEDOR_UUID",
                "message": f"ID de vendedor '{vendedor_id}' no es un UUID válido"
            }
        )
    
    # Verificar que el vendedor existe y está activo
    vendedor = (await session.execute(
        select(Vendedor).where(Vendedor.id == vendedor_uuid)
    )).scalar_one_or_none()
    
    if not vendedor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "VENDEDOR_NOT_FOUND",
                "message": f"Vendedor {vendedor_id} no encontrado"
            }
        )
    
    if not vendedor.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "VENDEDOR_INACTIVE",
                "message": f"Vendedor {vendedor.nombre_completo} está inactivo y no puede tener clientes asociados"
            }
        )
    
    # Procesar cada cliente
    clientes_asociados = 0
    clientes_no_encontrados = []
    clientes_inactivos = []
    clientes_con_vendedor = []
    
    for cliente_id_str in payload.clientes_ids:
        try:
            # Validar UUID del cliente
            try:
                cliente_uuid = UUID(cliente_id_str)
            except ValueError:
                logger.warning(f"⚠️  Cliente ID inválido: {cliente_id_str}")
                clientes_no_encontrados.append(cliente_id_str)
                continue
            
            # Buscar el cliente
            cliente = (await session.execute(
                select(Cliente).where(Cliente.id == cliente_uuid)
            )).scalar_one_or_none()
            
            if not cliente:
                logger.warning(f"⚠️  Cliente no encontrado: {cliente_id_str}")
                clientes_no_encontrados.append(cliente_id_str)
                continue
            
            if not cliente.activo:
                logger.warning(f"⚠️  Cliente inactivo: {cliente.nombre}")
                clientes_inactivos.append(cliente_id_str)
                continue
            
            # Verificar que el cliente NO tenga ya un vendedor asociado
            if cliente.vendedor_id is not None:
                logger.warning(f"⚠️  Cliente {cliente.nombre} ya tiene un vendedor asociado: {cliente.vendedor_id}")
                clientes_con_vendedor.append(cliente_id_str)
                continue
            
            # Asociar el cliente al vendedor
            cliente.vendedor_id = vendedor_uuid
            clientes_asociados += 1
            logger.info(f"  ✅ Cliente '{cliente.nombre}' asociado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error procesando cliente {cliente_id_str}: {e}")
            clientes_no_encontrados.append(cliente_id_str)
    
    # Guardar cambios
    await session.commit()
    
    took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
    
    # Construir mensaje de resultado
    mensaje_partes = []
    if clientes_asociados > 0:
        mensaje_partes.append(f"{clientes_asociados} cliente(s) asociado(s) exitosamente")
    if clientes_no_encontrados:
        mensaje_partes.append(f"{len(clientes_no_encontrados)} cliente(s) no encontrado(s)")
    if clientes_inactivos:
        mensaje_partes.append(f"{len(clientes_inactivos)} cliente(s) inactivo(s)")
    if clientes_con_vendedor:
        mensaje_partes.append(f"{len(clientes_con_vendedor)} cliente(s) ya tenían vendedor asociado")
    
    mensaje = ". ".join(mensaje_partes) if mensaje_partes else "No se realizaron cambios"
    
    logger.info(f"✅ Asociación completada en {took_ms}ms: {mensaje}")
    
    return AsociarClientesResponse(
        vendedor_id=vendedor_uuid,
        vendedor_nombre=vendedor.nombre_completo,
        clientes_asociados=clientes_asociados,
        clientes_no_encontrados=clientes_no_encontrados,
        clientes_inactivos=clientes_inactivos,
        clientes_con_vendedor=clientes_con_vendedor,
        mensaje=mensaje
    )

