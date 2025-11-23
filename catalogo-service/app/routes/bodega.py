"""
Router para gestión de bodegas (warehouses).

Endpoints:
- GET /api/v1/bodegas - Listar todas las bodegas únicas que existen en el inventario
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct
from app.db import get_session
from app.models.catalogo_model import Inventario
from typing import List
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Bodegas"])


class BodegaResponse(BaseModel):
    """Respuesta con información de una bodega"""
    bodega_id: str = Field(..., description="ID único de la bodega")
    pais: str = Field(..., description="Código del país (ISO 2 letras)")
    total_productos: int = Field(..., description="Cantidad de productos distintos en esta bodega")
    cantidad_total: int = Field(..., description="Cantidad total de unidades en esta bodega")
    
    class Config:
        json_schema_extra = {
            "example": {
                "bodega_id": "BOG_CENTRAL",
                "pais": "CO",
                "total_productos": 15,
                "cantidad_total": 5420
            }
        }


class BodegasListResponse(BaseModel):
    """Respuesta con lista de bodegas"""
    bodegas: List[BodegaResponse] = Field(..., description="Lista de bodegas")
    total: int = Field(..., description="Total de bodegas encontradas")
    
    class Config:
        json_schema_extra = {
            "example": {
                "bodegas": [
                    {
                        "bodega_id": "BOG_CENTRAL",
                        "pais": "CO",
                        "total_productos": 15,
                        "cantidad_total": 5420
                    },
                    {
                        "bodega_id": "MED_NORTE",
                        "pais": "CO",
                        "total_productos": 8,
                        "cantidad_total": 1200
                    }
                ],
                "total": 2
            }
        }


@router.get("", response_model=BodegasListResponse)
async def listar_bodegas(
    pais: str = Query(None, description="Filtrar por país (código ISO 2 letras)"),
    session: AsyncSession = Depends(get_session)
):
    """
    **Listar todas las bodegas únicas que existen en el inventario**
    
    Este endpoint extrae todas las bodegas únicas que tienen inventario registrado.
    
    ### Información Retornada:
    - `bodega_id`: Identificador único de la bodega
    - `pais`: Código del país donde está ubicada
    - `total_productos`: Cantidad de productos distintos en esta bodega
    - `cantidad_total`: Suma total de unidades en esta bodega
    
    ### Filtros:
    - `pais`: Filtrar bodegas por país (ejemplo: CO, MX, PE)
    
    ### Casos de Uso:
    - Mostrar lista de bodegas al crear/editar productos
    - Dashboard de bodegas disponibles
    - Seleccionar bodega origen/destino en transferencias
    - Validar que una bodega existe antes de registrar movimientos
    
    ### Respuesta:
    - **200**: Lista de bodegas con sus estadísticas
    """
    logger.info(f"📦 Listando bodegas{f' del país {pais}' if pais else ''}")
    
    try:
        # Query para obtener bodegas únicas con estadísticas
        # Agrupa por bodega_id y pais, cuenta productos y suma cantidades
        query = select(
            Inventario.bodega_id,
            Inventario.pais,
            func.count(distinct(Inventario.producto_id)).label('total_productos'),
            func.sum(Inventario.cantidad).label('cantidad_total')
        ).where(
            Inventario.cantidad > 0  # Solo bodegas con stock
        ).group_by(
            Inventario.bodega_id,
            Inventario.pais
        ).order_by(
            Inventario.pais,
            Inventario.bodega_id
        )
        
        # Aplicar filtro de país si se proporciona
        if pais:
            query = query.where(Inventario.pais == pais.upper())
        
        result = await session.execute(query)
        rows = result.all()
        
        # Construir respuesta
        bodegas = []
        for row in rows:
            # Manejar casos donde bodega_id puede ser None (inventario sin bodega asignada)
            bodega_id = row.bodega_id or "SIN_ASIGNAR"
            
            bodegas.append(BodegaResponse(
                bodega_id=bodega_id,
                pais=row.pais,
                total_productos=int(row.total_productos),
                cantidad_total=int(row.cantidad_total)
            ))
        
        logger.info(f"✅ Se encontraron {len(bodegas)} bodega(s)")
        
        return BodegasListResponse(
            bodegas=bodegas,
            total=len(bodegas)
        )
    
    except Exception as e:
        logger.error(f"❌ Error listando bodegas: {e}", exc_info=True)
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "Error al listar bodegas",
                "details": str(e)
            }
        )

