from fastapi import APIRouter, HTTPException, Query, status
from typing import List
from sqlmodel import Session, select
from datetime import datetime

from database import engine
from models import Ruta
from schemas_rutas import (
    RutaCreate, 
    RutaResponse,
    RutaListItemResponse,
    RutaCreatedResponse,
    RutaListResponse,
    RutaUpdate,
    AssignDriver,
    UpdateStatus
)

router = APIRouter(prefix="/rutas", tags=["Rutas Optimizadas"])


@router.post(
    "",
    response_model=RutaCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear ruta optimizada",
    description="Crea una nueva ruta optimizada recibiendo directamente los datos del servicio optimizador",
    response_description="Ruta creada exitosamente con su ID único"
)
def create_ruta(ruta_data: RutaCreate):
    """
    Crear una nueva ruta optimizada:
    
    - **secuencia_entregas**: Array con las entregas ordenadas (cliente, dirección, coordenadas, etc.)
    - **resumen**: Objeto con distancia total, tiempo, costo, capacidad usada, etc.
    - **geometria**: (Opcional) GeoJSON LineString con las coordenadas de la ruta completa
    - **alertas**: (Opcional) Array de alertas o advertencias de la optimización
    - **optimized_by**: (Opcional) Usuario que solicitó la optimización
    - **notes**: (Opcional) Notas adicionales sobre la ruta
    """
    try:
        with Session(engine) as session:
            ruta = Ruta(**ruta_data.model_dump())
            
            session.add(ruta)
            session.commit()
            session.refresh(ruta)
            
            return RutaCreatedResponse(
                id=ruta.id,
                created_at=ruta.created_at,
                message="Route created successfully"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating route: {str(e)}"
        )


@router.get(
    "",
    response_model=RutaListResponse,
    summary="Listar rutas",
    description="Obtiene una lista paginada de rutas con filtros opcionales. **La geometría se excluye para optimizar el tamaño de respuesta.**",
    response_description="Lista de rutas sin geometría (use GET /{id} para obtener geometría completa)"
)
def list_rutas(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=100, description="Cantidad máxima de rutas a retornar"),
    status: str | None = Query(None, description="Filtrar por estado (pending, in_progress, completed, cancelled)")
):
    """
    Listar todas las rutas con paginación y filtros opcionales:
    
    - **skip**: Número de registros a saltar (para paginación)
    - **limit**: Cantidad máxima de rutas a retornar (máx: 100)
    - **status**: Filtrar por estado específico
    
    **Optimización**: La geometría NO se incluye en las listas para reducir el tamaño.
    Para obtener la geometría completa, use `GET /rutas/{id}`
    """
    with Session(engine) as session:
        query = select(Ruta)
        
        if status:
            query = query.where(Ruta.status == status)
        
        # Obtener total
        total = len(session.exec(query).all())
        
        # Aplicar paginación
        query = query.offset(skip).limit(limit)
        rutas = session.exec(query).all()
        
        # ✅ Usar schema sin geometría
        return RutaListResponse(
            total=total,
            routes=[RutaListItemResponse.model_validate(r) for r in rutas]
        )


@router.get(
    "/{ruta_id}",
    response_model=RutaResponse,
    summary="Obtener ruta por ID",
    description="Obtiene los detalles completos de una ruta específica **incluyendo la geometría para visualización en mapa**",
    responses={
        200: {"description": "Ruta encontrada con geometría completa"},
        404: {"description": "Ruta no encontrada"}
    }
)
def get_ruta(ruta_id: str):
    """
    Obtener una ruta por su ID único:
    
    - **ruta_id**: ID único de la ruta (UUID)
    
    Retorna todos los detalles **incluyendo geometría completa** para:
    - Visualización en mapa (Leaflet, Mapbox, etc.)
    - Exportación a PDF
    - Análisis detallado de la ruta
    """
    with Session(engine) as session:
        ruta = session.get(Ruta, ruta_id)
        if not ruta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found"
            )
        return RutaResponse.model_validate(ruta)


@router.patch(
    "/{ruta_id}",
    response_model=RutaResponse,
    summary="Actualizar notas",
    description="Actualiza las notas de una ruta existente",
    responses={
        200: {"description": "Ruta actualizada"},
        404: {"description": "Ruta no encontrada"}
    }
)
def update_ruta(ruta_id: str, ruta_update: RutaUpdate):
    """
    Actualizar las notas de una ruta:
    
    - **ruta_id**: ID único de la ruta
    - **notes**: Nuevas notas para la ruta
    """
    with Session(engine) as session:
        ruta = session.get(Ruta, ruta_id)
        if not ruta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found"
            )
        
        if ruta_update.notes is not None:
            ruta.notes = ruta_update.notes
        
        ruta.updated_at = datetime.utcnow()
        session.add(ruta)
        session.commit()
        session.refresh(ruta)
        
        return RutaResponse.model_validate(ruta)


@router.patch(
    "/{ruta_id}/assign-driver",
    response_model=RutaResponse,
    summary="Asignar conductor",
    description="Asigna un conductor a una ruta específica",
    responses={
        200: {"description": "Conductor asignado"},
        404: {"description": "Ruta no encontrada"}
    }
)
def assign_driver(ruta_id: str, driver_data: AssignDriver):
    """
    Asignar un conductor a una ruta:
    
    - **ruta_id**: ID único de la ruta
    - **driver_id**: ID del conductor
    - **driver_name**: Nombre completo del conductor
    """
    with Session(engine) as session:
        ruta = session.get(Ruta, ruta_id)
        if not ruta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found"
            )
        
        ruta.driver_id = driver_data.driver_id
        ruta.driver_name = driver_data.driver_name
        ruta.updated_at = datetime.utcnow()
        
        session.add(ruta)
        session.commit()
        session.refresh(ruta)
        
        return RutaResponse.model_validate(ruta)


@router.patch(
    "/{ruta_id}/status",
    response_model=RutaResponse,
    summary="Actualizar estado",
    description="Actualiza el estado de una ruta (pending → in_progress → completed/cancelled)",
    responses={
        200: {"description": "Estado actualizado"},
        404: {"description": "Ruta no encontrada"}
    }
)
def update_status(ruta_id: str, status_data: UpdateStatus):
    """
    Actualizar el estado de una ruta:
    
    - **ruta_id**: ID único de la ruta
    - **status**: Nuevo estado (pending, in_progress, completed, cancelled)
    
    Estados válidos:
    - **pending**: Ruta creada, esperando asignación
    - **in_progress**: Ruta en curso de ejecución
    - **completed**: Ruta completada exitosamente
    - **cancelled**: Ruta cancelada
    """
    with Session(engine) as session:
        ruta = session.get(Ruta, ruta_id)
        if not ruta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found"
            )
        
        ruta.status = status_data.status
        ruta.updated_at = datetime.utcnow()
        
        session.add(ruta)
        session.commit()
        session.refresh(ruta)
        
        return RutaResponse.model_validate(ruta)


@router.delete(
    "/{ruta_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar ruta",
    description="Elimina permanentemente una ruta del sistema",
    responses={
        204: {"description": "Ruta eliminada exitosamente"},
        404: {"description": "Ruta no encontrada"}
    }
)
def delete_ruta(ruta_id: str):
    """
    Eliminar una ruta:
    
    - **ruta_id**: ID único de la ruta a eliminar
    
      Esta acción es permanente y no se puede deshacer.
    """
    with Session(engine) as session:
        ruta = session.get(Ruta, ruta_id)
        if not ruta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found"
            )
        
        session.delete(ruta)
        session.commit()
        
        return None


@router.get(
    "/driver/{driver_id}",
    response_model=RutaListResponse,
    summary="Rutas por conductor",
    description="Obtiene todas las rutas asignadas a un conductor específico (sin geometría)",
    response_description="Lista de rutas del conductor sin geometría"
)
def get_rutas_by_driver(driver_id: str):
    """
    Obtener todas las rutas de un conductor:
    
    - **driver_id**: ID del conductor
    
    Retorna todas las rutas asignadas a este conductor, sin importar su estado.
    
    ⚡ **Optimización**: La geometría NO se incluye. Use `GET /rutas/{id}` para geometría completa.
    """
    with Session(engine) as session:
        query = select(Ruta).where(Ruta.driver_id == driver_id)
        rutas = session.exec(query).all()
        
        # ✅ Usar schema sin geometría
        return RutaListResponse(
            total=len(rutas),
            routes=[RutaListItemResponse.model_validate(r) for r in rutas]
        )