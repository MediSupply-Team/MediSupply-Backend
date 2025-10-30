"""
Modelos de Cliente Service
"""
from app.models.client_model import (
    Cliente,
    CompraHistorico,
    DevolucionHistorico,
    ConsultaClienteLog,
    ProductoPreferido,
    EstadisticaCliente,
    Base
)

__all__ = [
    'Cliente',
    'CompraHistorico',
    'DevolucionHistorico',
    'ConsultaClienteLog',
    'ProductoPreferido',
    'EstadisticaCliente',
    'Base'
]


