"""
Rutas para gestión de Proveedores
HU: Registrar Proveedor - CRUD completo de proveedores
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.db import get_session
from app.models.catalogo_model import Proveedor
from app.schemas import (
    ProveedorCreate, 
    ProveedorUpdate, 
    ProveedorResponse, 
    ProveedorListResponse,
    Meta
)
from typing import Optional
from uuid import UUID
import time
import logging

router = APIRouter(tags=["proveedores"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=ProveedorResponse, status_code=status.HTTP_201_CREATED)
async def crear_proveedor(
    proveedor: ProveedorCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Crear un nuevo proveedor (ID se genera automáticamente)
    
    **Criterios de aceptación:**
    - NIT debe ser único ✅
    - Email debe ser único ✅
    - Registro en ≤ 1 segundo ✅
    - Trazabilidad completa ✅
    
    **Datos básicos requeridos:**
    - Empresa/Nombre del proveedor
    - NIT (único)
    - Contacto (email)
    - País
    
    **Retorna:**
    - 201: Proveedor creado exitosamente
    - 409: NIT o email ya existe
    - 500: Error interno
    """
    logger.info(f"📝 Creando proveedor: {proveedor.empresa}")
    started = time.perf_counter_ns()
    
    try:
        # Verificar si el NIT ya existe
        existing_by_nit = (await session.execute(
            select(Proveedor).where(Proveedor.nit == proveedor.nit)
        )).scalar_one_or_none()
        
        if existing_by_nit:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "NIT_ALREADY_EXISTS",
                    "message": f"Proveedor con NIT {proveedor.nit} ya existe",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                }
            )
        
        # Verificar si el email ya existe
        existing_by_email = (await session.execute(
            select(Proveedor).where(Proveedor.contacto_email == proveedor.contacto_email)
        )).scalar_one_or_none()
        
        if existing_by_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "EMAIL_ALREADY_EXISTS",
                    "message": f"Proveedor con email {proveedor.contacto_email} ya existe",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                }
            )
        
        # Crear nuevo proveedor (ID se genera automáticamente)
        new_proveedor = Proveedor(
            nit=proveedor.nit,
            empresa=proveedor.empresa,
            contacto_nombre=proveedor.contacto_nombre,
            contacto_email=proveedor.contacto_email,
            contacto_telefono=proveedor.contacto_telefono,
            contacto_cargo=proveedor.contacto_cargo,
            direccion=proveedor.direccion,
            pais=proveedor.pais,
            activo=proveedor.activo,
            notas=proveedor.notas,
            created_by_user_id=proveedor.created_by_user_id
        )
        
        session.add(new_proveedor)
        await session.commit()
        await session.refresh(new_proveedor)
        
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        logger.info(f"✅ Proveedor creado: {new_proveedor.id} en {took_ms}ms")
        
        return ProveedorResponse.model_validate(new_proveedor)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creando proveedor: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Error interno al crear proveedor",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        )


@router.get("/", response_model=ProveedorListResponse)
async def listar_proveedores(
    q: Optional[str] = Query(None, description="Búsqueda por empresa o NIT"),
    pais: Optional[str] = Query(None, min_length=2, max_length=2, description="Filtrar por país (código ISO)"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo"),
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(50, ge=1, le=200, description="Tamaño de página"),
    sort: str = Query("empresa", pattern="^(empresa|nit|created_at)$", description="Campo de ordenamiento"),
    session: AsyncSession = Depends(get_session)
):
    """
    Listar proveedores con filtros y paginación
    
    **Filtros disponibles:**
    - q: Búsqueda por empresa o NIT
    - pais: Código ISO del país
    - activo: true/false
    
    **Retorna:**
    - Lista de proveedores con metadata de paginación
    """
    logger.info(f"🔍 Listando proveedores: q={q}, pais={pais}, activo={activo}, page={page}")
    started = time.perf_counter_ns()
    
    try:
        # Construir query base
        stmt = select(Proveedor)
        
        # Aplicar filtros
        if q:
            stmt = stmt.where(
                or_(
                    func.lower(Proveedor.empresa).like(f"%{q.lower()}%"),
                    func.lower(Proveedor.nit).like(f"%{q.lower()}%")
                )
            )
        
        if pais:
            stmt = stmt.where(Proveedor.pais == pais.upper())
        
        if activo is not None:
            stmt = stmt.where(Proveedor.activo == activo)
        
        # Contar total (query separada sin order by)
        count_stmt = select(func.count()).select_from(Proveedor)
        if q:
            count_stmt = count_stmt.where(
                or_(
                    func.lower(Proveedor.empresa).like(f"%{q.lower()}%"),
                    func.lower(Proveedor.nit).like(f"%{q.lower()}%")
                )
            )
        if pais:
            count_stmt = count_stmt.where(Proveedor.pais == pais.upper())
        if activo is not None:
            count_stmt = count_stmt.where(Proveedor.activo == activo)
        
        total = (await session.execute(count_stmt)).scalar_one()
        
        # Aplicar ordenamiento
        if sort == "nit":
            stmt = stmt.order_by(Proveedor.nit.asc())
        elif sort == "created_at":
            stmt = stmt.order_by(Proveedor.created_at.desc())
        else:  # empresa (default)
            stmt = stmt.order_by(Proveedor.empresa.asc())
        
        # Aplicar paginación
        stmt = stmt.offset((page - 1) * size).limit(size)
        
        # Ejecutar query
        result = await session.execute(stmt)
        proveedores = result.scalars().all()
        
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        logger.info(f"✅ {len(proveedores)} proveedores encontrados en {took_ms}ms")
        
        return ProveedorListResponse(
            items=[ProveedorResponse.model_validate(p) for p in proveedores],
            meta=Meta(page=page, size=size, total=total, tookMs=took_ms)
        )
        
    except Exception as e:
        logger.error(f"❌ Error listando proveedores: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al listar proveedores"
        )


@router.get("/{proveedor_id}", response_model=ProveedorResponse)
async def obtener_proveedor(
    proveedor_id: str,  # Recibe como string desde URL
    session: AsyncSession = Depends(get_session)
):
    """
    Obtener un proveedor por ID
    
    **Retorna:**
    - 200: Proveedor encontrado
    - 400: ID inválido
    - 404: Proveedor no encontrado
    """
    logger.info(f"🔍 Obteniendo proveedor: {proveedor_id}")
    
    try:
        # Convertir string a UUID
        uuid_id = UUID(proveedor_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_UUID",
                "message": f"ID '{proveedor_id}' no es un UUID válido"
            }
        )
    
    proveedor = (await session.execute(
        select(Proveedor).where(Proveedor.id == uuid_id)
    )).scalar_one_or_none()
    
    if not proveedor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "PROVEEDOR_NOT_FOUND",
                "message": f"Proveedor {proveedor_id} no encontrado"
            }
        )
    
    return ProveedorResponse.model_validate(proveedor)


@router.put("/{proveedor_id}", response_model=ProveedorResponse)
async def actualizar_proveedor(
    proveedor_id: str,  # Recibe como string desde URL
    proveedor_data: ProveedorUpdate,
    session: AsyncSession = Depends(get_session)
):
    """
    Actualizar un proveedor existente
    
    **Retorna:**
    - 200: Proveedor actualizado
    - 400: ID inválido
    - 404: Proveedor no encontrado
    - 409: NIT o email duplicado
    """
    logger.info(f"✏️ Actualizando proveedor: {proveedor_id}")
    started = time.perf_counter_ns()
    
    try:
        # Convertir string a UUID
        uuid_id = UUID(proveedor_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_UUID", "message": f"ID '{proveedor_id}' no es un UUID válido"}
        )
    
    try:
        # Buscar proveedor
        proveedor = (await session.execute(
            select(Proveedor).where(Proveedor.id == uuid_id)
        )).scalar_one_or_none()
        
        if not proveedor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "PROVEEDOR_NOT_FOUND", "message": f"Proveedor {proveedor_id} no encontrado"}
            )
        
        # Validar NIT único (si se actualiza)
        if proveedor_data.nit and proveedor_data.nit != proveedor.nit:
            existing_nit = (await session.execute(
                select(Proveedor).where(Proveedor.nit == proveedor_data.nit)
            )).scalar_one_or_none()
            if existing_nit:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"error": "NIT_ALREADY_EXISTS", "message": f"NIT {proveedor_data.nit} ya existe"}
                )
        
        # Validar email único (si se actualiza)
        if proveedor_data.contacto_email and proveedor_data.contacto_email != proveedor.contacto_email:
            existing_email = (await session.execute(
                select(Proveedor).where(Proveedor.contacto_email == proveedor_data.contacto_email)
            )).scalar_one_or_none()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"error": "EMAIL_ALREADY_EXISTS", "message": f"Email {proveedor_data.contacto_email} ya existe"}
                )
        
        # Actualizar campos
        update_data = proveedor_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(proveedor, key, value)
        
        await session.commit()
        await session.refresh(proveedor)
        
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        logger.info(f"✅ Proveedor actualizado: {proveedor_id} en {took_ms}ms")
        
        return ProveedorResponse.model_validate(proveedor)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error actualizando proveedor: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar proveedor"
        )


@router.delete("/{proveedor_id}", status_code=status.HTTP_200_OK)
async def desactivar_proveedor(
    proveedor_id: str,  # Recibe como string desde URL
    session: AsyncSession = Depends(get_session)
):
    """
    Desactivar un proveedor (soft delete)
    
    No se eliminan físicamente los proveedores, solo se marcan como inactivos.
    
    **Retorna:**
    - 200: Proveedor desactivado
    - 400: ID inválido
    - 404: Proveedor no encontrado
    """
    logger.info(f"🗑️ Desactivando proveedor: {proveedor_id}")
    
    try:
        uuid_id = UUID(proveedor_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_UUID", "message": f"ID '{proveedor_id}' no es un UUID válido"}
        )
    
    proveedor = (await session.execute(
        select(Proveedor).where(Proveedor.id == uuid_id)
    )).scalar_one_or_none()
    
    if not proveedor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "PROVEEDOR_NOT_FOUND", "message": f"Proveedor {proveedor_id} no encontrado"}
        )
    
    proveedor.activo = False
    await session.commit()
    
    logger.info(f"✅ Proveedor desactivado: {proveedor_id}")
    
    return {"message": f"Proveedor {proveedor_id} desactivado exitosamente"}


@router.get("/{proveedor_id}/productos", response_model=dict)
async def obtener_productos_proveedor(
    proveedor_id: str,  # Recibe como string desde URL
    session: AsyncSession = Depends(get_session)
):
    """
    Obtener todos los productos de un proveedor
    
    **Retorna:**
    - Lista de productos del proveedor
    - 400: ID inválido
    - 404: Proveedor no encontrado
    """
    from app.models.catalogo_model import Producto
    
    logger.info(f"🔍 Obteniendo productos del proveedor: {proveedor_id}")
    
    try:
        uuid_id = UUID(proveedor_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_UUID", "message": f"ID '{proveedor_id}' no es un UUID válido"}
        )
    
    # Verificar que el proveedor existe
    proveedor = (await session.execute(
        select(Proveedor).where(Proveedor.id == uuid_id)
    )).scalar_one_or_none()
    
    if not proveedor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "PROVEEDOR_NOT_FOUND", "message": f"Proveedor {proveedor_id} no encontrado"}
        )
    
    # Obtener productos
    productos = (await session.execute(
        select(Producto).where(Producto.proveedor_id == uuid_id)
    )).scalars().all()
    
    return {
        "proveedor_id": str(proveedor_id),
        "proveedor_empresa": proveedor.empresa,
        "total_productos": len(productos),
        "productos": [
            {
                "id": p.id,
                "codigo": p.codigo,
                "nombre": p.nombre,
                "precio_unitario": float(p.precio_unitario),
                "activo": p.activo
            }
            for p in productos
        ]
    }


# ============================================================================
# ENDPOINTS DE CARGA MASIVA DE PROVEEDORES
# ============================================================================

@router.post("/bulk-upload", status_code=status.HTTP_202_ACCEPTED)
async def bulk_upload_proveedores(
    file: UploadFile = File(...),
    reemplazar_duplicados: bool = Query(False, description="Si es true, reemplaza proveedores duplicados"),
    session: AsyncSession = Depends(get_session)
):
    """
    Carga masiva de proveedores desde Excel o CSV
    
    **Formato del archivo:**
    - Columnas requeridas: nombre/empresa, nit, email/contacto_email
    - Columnas opcionales: telefono/contacto_telefono, contacto_nombre, direccion, pais, activo
    
    **Retorna:**
    - 202: Carga iniciada (procesamiento asíncrono)
    - 400: Archivo inválido o formato incorrecto
    - 500: Error interno
    """
    import pandas as pd
    import io
    from uuid import uuid4
    
    logger.info(f"📤 Iniciando carga masiva de proveedores: {file.filename}")
    started = time.perf_counter_ns()
    
    # Validar extensión del archivo
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "NO_FILENAME", "message": "No se proporcionó nombre de archivo"}
        )
    
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in ['xlsx', 'xls', 'csv']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_FILE_FORMAT",
                "message": "El archivo debe ser Excel (.xlsx, .xls) o CSV (.csv)"
            }
        )
    
    try:
        # Leer archivo
        contents = await file.read()
        
        if file_ext == 'csv':
            df = pd.read_csv(io.BytesIO(contents))
        else:  # xlsx o xls
            df = pd.read_excel(io.BytesIO(contents))
        
        logger.info(f"📊 Archivo leído: {len(df)} filas")
        
        # Validar columnas requeridas (con nombres flexibles)
        required_columns = {
            'nombre': ['nombre', 'empresa'],
            'nit': ['nit'],
            'email': ['email', 'contacto_email']
        }
        
        # Mapear columnas del DataFrame a nombres estándar
        column_mapping = {}
        for standard_name, possible_names in required_columns.items():
            found = False
            for col in df.columns:
                if col.lower() in possible_names:
                    column_mapping[col] = standard_name
                    found = True
                    break
            if not found:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "MISSING_REQUIRED_COLUMN",
                        "message": f"Falta columna requerida: {standard_name} (posibles nombres: {', '.join(possible_names)})"
                    }
                )
        
        # Renombrar columnas
        df = df.rename(columns=column_mapping)
        
        # Procesar proveedores
        task_id = str(uuid4())
        resultados = {
            "task_id": task_id,
            "status": "processing",
            "total": len(df),
            "procesados": 0,
            "exitosos": 0,
            "fallidos": 0,
            "errores": []
        }
        
        for idx, row in df.iterrows():
            row_num = idx + 2  # +2 porque Excel empieza en 1 y tiene header
            
            try:
                # Validar campos requeridos
                if pd.isna(row['nombre']) or not str(row['nombre']).strip():
                    resultados["errores"].append({
                        "fila": row_num,
                        "error": "Campo 'nombre' es requerido"
                    })
                    resultados["fallidos"] += 1
                    resultados["procesados"] += 1
                    continue
                
                if pd.isna(row['nit']) or not str(row['nit']).strip():
                    resultados["errores"].append({
                        "fila": row_num,
                        "error": "Campo 'nit' es requerido"
                    })
                    resultados["fallidos"] += 1
                    resultados["procesados"] += 1
                    continue
                
                if pd.isna(row['email']) or not str(row['email']).strip():
                    resultados["errores"].append({
                        "fila": row_num,
                        "error": "Campo 'email' es requerido"
                    })
                    resultados["fallidos"] += 1
                    resultados["procesados"] += 1
                    continue
                
                nit = str(row['nit']).strip()
                nombre = str(row['nombre']).strip()
                email = str(row['email']).strip()
                
                # Verificar si ya existe
                existing = (await session.execute(
                    select(Proveedor).where(Proveedor.nit == nit)
                )).scalar_one_or_none()
                
                if existing:
                    if reemplazar_duplicados:
                        # Actualizar proveedor existente
                        existing.empresa = nombre
                        existing.contacto_email = email
                        existing.contacto_telefono = str(row.get('telefono', row.get('contacto_telefono', ''))).strip() if not pd.isna(row.get('telefono', row.get('contacto_telefono'))) else None
                        existing.contacto_nombre = str(row.get('contacto_nombre', '')).strip() if not pd.isna(row.get('contacto_nombre')) else None
                        existing.direccion = str(row.get('direccion', '')).strip() if not pd.isna(row.get('direccion')) else None
                        existing.pais = str(row.get('pais', '')).strip().upper() if not pd.isna(row.get('pais')) else None
                        
                        if 'activo' in row and not pd.isna(row['activo']):
                            activo_val = row['activo']
                            if isinstance(activo_val, str):
                                existing.activo = activo_val.lower() in ['true', '1', 'yes', 'si', 'sí']
                            else:
                                existing.activo = bool(activo_val)
                        
                        logger.info(f"✏️ Actualizando proveedor: {nit}")
                    else:
                        resultados["errores"].append({
                            "fila": row_num,
                            "error": f"NIT {nit} ya existe (use reemplazar_duplicados=true para actualizar)"
                        })
                        resultados["fallidos"] += 1
                        resultados["procesados"] += 1
                        continue
                else:
                    # Crear nuevo proveedor
                    nuevo_proveedor = Proveedor(
                        nit=nit,
                        empresa=nombre,
                        contacto_email=email,
                        contacto_telefono=str(row.get('telefono', row.get('contacto_telefono', ''))).strip() if not pd.isna(row.get('telefono', row.get('contacto_telefono'))) else None,
                        contacto_nombre=str(row.get('contacto_nombre', '')).strip() if not pd.isna(row.get('contacto_nombre')) else None,
                        direccion=str(row.get('direccion', '')).strip() if not pd.isna(row.get('direccion')) else None,
                        pais=str(row.get('pais', '')).strip().upper() if not pd.isna(row.get('pais')) else None,
                        activo=True
                    )
                    
                    # Procesar campo activo si existe
                    if 'activo' in row and not pd.isna(row['activo']):
                        activo_val = row['activo']
                        if isinstance(activo_val, str):
                            nuevo_proveedor.activo = activo_val.lower() in ['true', '1', 'yes', 'si', 'sí']
                        else:
                            nuevo_proveedor.activo = bool(activo_val)
                    
                    session.add(nuevo_proveedor)
                    logger.info(f"✅ Creando proveedor: {nit}")
                
                await session.commit()
                resultados["exitosos"] += 1
                resultados["procesados"] += 1
                
            except Exception as e:
                logger.error(f"❌ Error en fila {row_num}: {e}")
                resultados["errores"].append({
                    "fila": row_num,
                    "error": str(e)
                })
                resultados["fallidos"] += 1
                resultados["procesados"] += 1
                await session.rollback()
                continue
        
        resultados["status"] = "completed"
        took_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        
        logger.info(f"✅ Carga masiva completada: {resultados['exitosos']}/{resultados['total']} exitosos en {took_ms}ms")
        
        return {
            "task_id": task_id,
            "status": "completed",
            "message": "Carga masiva completada",
            "progress": {
                "total": resultados["total"],
                "processed": resultados["procesados"],
                "successful": resultados["exitosos"],
                "failed": resultados["fallidos"]
            },
            "result": {
                "proveedores_procesados": resultados["exitosos"],
                "errores": resultados["errores"][:50]  # Limitar a 50 errores para no saturar response
            },
            "took_ms": took_ms
        }
        
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "EMPTY_FILE", "message": "El archivo está vacío"}
        )
    except Exception as e:
        logger.error(f"❌ Error en carga masiva: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "BULK_UPLOAD_ERROR",
                "message": f"Error al procesar archivo: {str(e)}"
            }
        )

