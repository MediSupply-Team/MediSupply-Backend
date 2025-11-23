from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from enum import Enum
from uuid import UUID

class InventarioResumen(BaseModel):
    cantidadTotal: int
    paises: List[str] = []

class Product(BaseModel):
    id: str
    nombre: str
    codigo: str
    categoria: str
    presentacion: Optional[str] = None
    precioUnitario: float
    requisitosAlmacenamiento: Optional[str] = None
    inventarioResumen: Optional[InventarioResumen] = None

class StockItem(BaseModel):
    pais: str
    bodegaId: str
    lote: str
    cantidad: int
    vence: str
    condiciones: str | None = None

class Meta(BaseModel):
    page: int
    size: int
    total: int
    tookMs: int

class SearchResponse(BaseModel):
    items: List[Product]
    meta: Meta

class BodegaInicial(BaseModel):
    """Bodega donde se habilitará el producto inicialmente"""
    bodega_id: str = Field(..., min_length=1, max_length=64, description="ID de la bodega")
    pais: str = Field(..., min_length=2, max_length=2, description="Código de país (2 letras)")
    lote: Optional[str] = Field(None, max_length=64, description="Lote inicial (opcional, se genera automático si no se provee)")
    fecha_vencimiento: Optional[date] = Field(None, description="Fecha de vencimiento inicial (opcional)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "bodega_id": "BOG_CENTRAL",
                "pais": "CO",
                "lote": "LOTE-INICIAL-001",
                "fecha_vencimiento": "2099-12-31"
            }
        }


class ProductCreate(BaseModel):
    id: Optional[str] = Field(None, description="ID del producto (UUID). Si no se proporciona, se genera automáticamente")
    nombre: str
    codigo: str
    categoria: str
    presentacion: Optional[str] = None
    precioUnitario: float
    requisitosAlmacenamiento: Optional[str] = None
    
    # Campos opcionales para gestión de inventario
    stockMinimo: Optional[int] = Field(10, ge=0, description="Stock mínimo antes de generar alerta")
    stockCritico: Optional[int] = Field(5, ge=0, description="Stock crítico (alerta crítica)")
    requiereLote: Optional[bool] = Field(False, description="Indica si requiere número de lote")
    requiereVencimiento: Optional[bool] = Field(True, description="Indica si requiere fecha de vencimiento")
    
    # HU021 - Campos para proveedores
    certificadoSanitario: Optional[str] = Field(None, max_length=255, description="Número o referencia del certificado sanitario")
    tiempoEntregaDias: Optional[int] = Field(None, ge=1, description="Tiempo estimado de entrega en días")
    proveedorId: Optional[str] = Field(None, max_length=64, description="ID del proveedor")
    
    # Bodegas iniciales donde estará disponible el producto
    bodegasIniciales: Optional[List[BodegaInicial]] = Field(
        None, 
        description="Lista de bodegas donde se habilitará el producto con stock inicial en 0. Si no se especifica, no se crea inventario inicial."
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "PROD026",
                "nombre": "Amoxicilina 500mg",
                "codigo": "AMX500",
                "categoria": "ANTIBIOTICS",
                "presentacion": "Cápsula",
                "precioUnitario": 1250.00,
                "requisitosAlmacenamiento": "Temperatura ambiente, lugar seco",
                "stockMinimo": 50,
                "stockCritico": 20,
                "requiereLote": True,
                "requiereVencimiento": True,
                "bodegasIniciales": [
                    {
                        "bodega_id": "BOG_CENTRAL",
                        "pais": "CO",
                        "lote": "LOTE-INICIAL-001",
                        "fecha_vencimiento": "2099-12-31"
                    },
                    {
                        "bodega_id": "MED_SUR",
                        "pais": "CO"
                    }
                ]
            }
        }

class ProductUpdate(BaseModel):
    nombre: Optional[str] = None
    codigo: Optional[str] = None
    categoria: Optional[str] = None
    presentacion: Optional[str] = None
    precioUnitario: Optional[float] = None
    requisitosAlmacenamiento: Optional[str] = None


# ============================================================================
# SCHEMAS PARA GESTIÓN DE MOVIMIENTOS DE INVENTARIO
# ============================================================================

class TipoMovimiento(str, Enum):
    """Tipos de movimiento de inventario"""
    INGRESO = "INGRESO"
    SALIDA = "SALIDA"
    TRANSFERENCIA_SALIDA = "TRANSFERENCIA_SALIDA"
    TRANSFERENCIA_INGRESO = "TRANSFERENCIA_INGRESO"


class MotivoMovimiento(str, Enum):
    """Motivos de movimiento de inventario"""
    COMPRA = "COMPRA"
    AJUSTE = "AJUSTE"
    VENTA = "VENTA"
    DEVOLUCION = "DEVOLUCION"
    MERMA = "MERMA"
    TRANSFERENCIA = "TRANSFERENCIA"
    PRODUCCION = "PRODUCCION"
    INVENTARIO_INICIAL = "INVENTARIO_INICIAL"


class EstadoMovimiento(str, Enum):
    """Estados de un movimiento"""
    ACTIVO = "ACTIVO"
    ANULADO = "ANULADO"


class MovimientoCreate(BaseModel):
    """Schema para crear un nuevo movimiento de inventario"""
    producto_id: str = Field(..., min_length=1, max_length=64, description="ID del producto")
    bodega_id: str = Field(..., min_length=1, max_length=64, description="ID de la bodega")
    pais: str = Field(..., min_length=2, max_length=2, description="Código de país (2 letras)")
    lote: Optional[str] = Field(None, max_length=64, description="Número de lote (opcional)")
    
    tipo_movimiento: TipoMovimiento = Field(..., description="Tipo de movimiento")
    motivo: MotivoMovimiento = Field(..., description="Motivo del movimiento")
    cantidad: int = Field(..., gt=0, description="Cantidad a mover (debe ser > 0)")
    fecha_vencimiento: Optional[date] = Field(None, description="Fecha de vencimiento (para ingresos)")
    
    usuario_id: str = Field(..., min_length=1, max_length=64, description="ID del usuario que registra")
    referencia_documento: Optional[str] = Field(None, max_length=128, description="N° de documento (PO, factura, etc)")
    observaciones: Optional[str] = Field(None, description="Observaciones adicionales")
    
    # Validación de permisos para stock negativo
    permitir_stock_negativo: bool = Field(False, description="Permite dejar stock negativo (requiere permiso)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "producto_id": "PROD001",
                "bodega_id": "BOG_CENTRAL",
                "pais": "CO",
                "lote": "AMX001_2024",
                "tipo_movimiento": "INGRESO",
                "motivo": "COMPRA",
                "cantidad": 100,
                "fecha_vencimiento": "2025-12-31",
                "usuario_id": "USER001",
                "referencia_documento": "PO-2024-100",
                "observaciones": "Compra a proveedor XYZ",
                "permitir_stock_negativo": False
            }
        }


class MovimientoResponse(BaseModel):
    """Schema de respuesta de un movimiento"""
    id: int
    producto_id: str
    bodega_id: str
    pais: str
    lote: Optional[str]
    
    tipo_movimiento: str
    motivo: str
    cantidad: int
    fecha_vencimiento: Optional[date]
    
    saldo_anterior: int
    saldo_nuevo: int
    
    usuario_id: str
    referencia_documento: Optional[str]
    observaciones: Optional[str]
    
    created_at: datetime
    estado: str
    
    class Config:
        from_attributes = True


class TransferenciaCreate(BaseModel):
    """Schema para crear una transferencia entre bodegas"""
    producto_id: str = Field(..., min_length=1, max_length=64)
    lote: Optional[str] = Field(None, max_length=64)
    cantidad: int = Field(..., gt=0)
    
    bodega_origen_id: str = Field(..., min_length=1, max_length=64)
    pais_origen: str = Field(..., min_length=2, max_length=2)
    
    bodega_destino_id: str = Field(..., min_length=1, max_length=64)
    pais_destino: str = Field(..., min_length=2, max_length=2)
    
    usuario_id: str = Field(..., min_length=1, max_length=64)
    referencia_documento: Optional[str] = Field(None, max_length=128)
    observaciones: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "producto_id": "PROD001",
                "lote": "AMX001_2024",
                "cantidad": 50,
                "bodega_origen_id": "BOG_CENTRAL",
                "pais_origen": "CO",
                "bodega_destino_id": "MED_SUR",
                "pais_destino": "CO",
                "usuario_id": "USER001",
                "referencia_documento": "TRANS-2024-001",
                "observaciones": "Transferencia por demanda"
            }
        }


class TransferenciaResponse(BaseModel):
    """Schema de respuesta de una transferencia"""
    message: str
    movimiento_salida_id: int
    movimiento_ingreso_id: int
    saldo_origen: int
    saldo_destino: int


class AnularMovimientoRequest(BaseModel):
    """Schema para anular un movimiento"""
    motivo_anulacion: str = Field(..., min_length=10, description="Motivo de la anulación (mínimo 10 caracteres)")
    usuario_id: str = Field(..., min_length=1, max_length=64, description="ID del usuario que anula")
    
    class Config:
        json_schema_extra = {
            "example": {
                "motivo_anulacion": "Error en la cantidad registrada, se duplicó el movimiento",
                "usuario_id": "ADMIN001"
            }
        }


class KardexItem(BaseModel):
    """Item del kardex (historial de movimientos)"""
    id: int
    producto_id: str
    producto_nombre: str
    bodega_id: str
    pais: str
    lote: Optional[str]
    tipo_movimiento: str
    motivo: str
    cantidad: int
    saldo_anterior: int
    saldo_nuevo: int
    usuario_id: str
    referencia_documento: Optional[str]
    created_at: datetime
    estado: str


class KardexResponse(BaseModel):
    """Respuesta con historial de movimientos"""
    items: List[KardexItem]
    meta: Meta


class AlertaResponse(BaseModel):
    """Schema de una alerta de inventario"""
    id: int
    producto_id: str
    producto_nombre: str
    bodega_id: str
    pais: str
    tipo_alerta: str
    nivel: str
    mensaje: str
    stock_actual: Optional[int]
    stock_minimo: Optional[int]
    leida: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AlertasListResponse(BaseModel):
    """Respuesta con lista de alertas"""
    items: List[AlertaResponse]
    meta: Meta


class SaldoBodega(BaseModel):
    """Saldo de un producto en una bodega"""
    producto_id: str
    producto_nombre: str
    producto_codigo: str
    bodega_id: str
    pais: str
    lote: str
    cantidad_total: int
    fecha_vencimiento_proxima: Optional[date]
    stock_minimo: int
    stock_critico: int
    estado_stock: str  # NORMAL, BAJO, CRITICO


class ReporteSaldosResponse(BaseModel):
    """Reporte de saldos por bodega"""
    items: List[SaldoBodega]
    meta: Meta


# ==========================================
# SCHEMAS PARA PROVEEDORES (HU: Registrar Proveedor)
# ==========================================

class ProveedorCreate(BaseModel):
    """Schema para crear un proveedor (id se genera automáticamente con UUID)"""
    nit: str = Field(..., min_length=5, max_length=32, description="NIT o identificación fiscal", example="900123456-7")
    empresa: str = Field(..., min_length=3, max_length=255, description="Nombre de la empresa", example="Suministros Médicos Global")
    contacto_nombre: str = Field(..., min_length=3, max_length=255, description="Nombre del contacto", example="Ana López")
    contacto_email: str = Field(..., min_length=5, max_length=255, description="Email del contacto", example="ana.lopez@suministros.com")
    contacto_telefono: Optional[str] = Field(None, max_length=32, description="Teléfono del contacto", example="+57-1-3456789")
    contacto_cargo: Optional[str] = Field(None, max_length=128, description="Cargo del contacto", example="Gerente de Ventas")
    direccion: Optional[str] = Field(None, max_length=512, description="Dirección del proveedor", example="Calle 45 #12-34, Bogotá")
    pais: str = Field(..., min_length=2, max_length=2, description="Código ISO del país", example="CO")
    activo: bool = Field(default=True, description="Si el proveedor está activo")
    notas: Optional[str] = Field(None, description="Notas adicionales sobre el proveedor")
    created_by_user_id: Optional[str] = Field(None, max_length=64, description="ID del usuario que crea el proveedor")
    
    class Config:
        json_schema_extra = {
            "example": {
                "nit": "900123456-7",
                "empresa": "Suministros Médicos Global",
                "contacto_nombre": "Ana López",
                "contacto_email": "ana.lopez@suministros.com",
                "contacto_telefono": "+57-1-3456789",
                "contacto_cargo": "Gerente de Ventas",
                "direccion": "Calle 45 #12-34, Bogotá",
                "pais": "CO",
                "activo": True,
                "notas": "Proveedor principal de antibióticos",
                "created_by_user_id": "ADMIN001"
            }
        }


class ProveedorUpdate(BaseModel):
    """Schema para actualizar un proveedor existente"""
    nit: Optional[str] = Field(None, min_length=5, max_length=32)
    empresa: Optional[str] = Field(None, min_length=3, max_length=255)
    contacto_nombre: Optional[str] = Field(None, min_length=3, max_length=255)
    contacto_email: Optional[str] = Field(None, min_length=5, max_length=255)
    contacto_telefono: Optional[str] = Field(None, max_length=32)
    contacto_cargo: Optional[str] = Field(None, max_length=128)
    direccion: Optional[str] = Field(None, max_length=512)
    pais: Optional[str] = Field(None, min_length=2, max_length=2)
    activo: Optional[bool] = None
    notas: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "contacto_telefono": "+57-1-9876543",
                "contacto_cargo": "Director Comercial",
                "activo": True
            }
        }


class ProveedorResponse(BaseModel):
    """Schema de respuesta de un proveedor"""
    id: UUID  # Pydantic lo serializa como string en JSON automáticamente
    nit: str
    empresa: str
    contacto_nombre: str
    contacto_email: str
    contacto_telefono: Optional[str]
    contacto_cargo: Optional[str]
    direccion: Optional[str]
    pais: str
    activo: bool
    notas: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by_user_id: Optional[str]
    
    class Config:
        from_attributes = True


class ProveedorListResponse(BaseModel):
    """Respuesta con lista de proveedores"""
    items: List[ProveedorResponse]
    meta: Meta


# =====================================================
# SCHEMAS PARA BODEGA (WAREHOUSE)
# =====================================================

class BodegaCreate(BaseModel):
    """Schema para crear una bodega"""
    codigo: str = Field(..., min_length=1, max_length=64, description="Código único de la bodega")
    nombre: str = Field(..., min_length=1, max_length=255, description="Nombre de la bodega")
    pais: str = Field(..., min_length=2, max_length=2, description="Código del país (ISO 2 letras)")
    direccion: Optional[str] = Field(None, max_length=512, description="Dirección física")
    ciudad: Optional[str] = Field(None, max_length=128, description="Ciudad")
    responsable: Optional[str] = Field(None, max_length=255, description="Nombre del responsable")
    telefono: Optional[str] = Field(None, max_length=32, description="Teléfono de contacto")
    email: Optional[str] = Field(None, max_length=255, description="Email de contacto")
    capacidad_m3: Optional[float] = Field(None, ge=0, description="Capacidad en metros cúbicos")
    tipo: Optional[str] = Field(None, max_length=64, description="Tipo de bodega (PRINCIPAL, SECUNDARIA, TRANSITO)")
    notas: Optional[str] = Field(None, description="Notas adicionales")
    
    class Config:
        json_schema_extra = {
            "example": {
                "codigo": "BOG_SUR",
                "nombre": "Bodega Sur Bogotá",
                "pais": "CO",
                "direccion": "Av. Boyacá #45-78",
                "ciudad": "Bogotá",
                "responsable": "Juan Pérez",
                "telefono": "+57 301 555 0123",
                "email": "bodega.sur@medisupply.com",
                "tipo": "PRINCIPAL",
                "notas": "Bodega principal para zona sur"
            }
        }


class BodegaUpdate(BaseModel):
    """Schema para actualizar una bodega"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    direccion: Optional[str] = Field(None, max_length=512)
    ciudad: Optional[str] = Field(None, max_length=128)
    responsable: Optional[str] = Field(None, max_length=255)
    telefono: Optional[str] = Field(None, max_length=32)
    email: Optional[str] = Field(None, max_length=255)
    activo: Optional[bool] = None
    capacidad_m3: Optional[float] = Field(None, ge=0)
    tipo: Optional[str] = Field(None, max_length=64)
    notas: Optional[str] = None


class BodegaResponse(BaseModel):
    """Schema de respuesta de una bodega"""
    codigo: str
    nombre: str
    pais: str
    direccion: Optional[str]
    ciudad: Optional[str]
    responsable: Optional[str]
    telefono: Optional[str]
    email: Optional[str]
    activo: bool
    capacidad_m3: Optional[float]
    tipo: Optional[str]
    notas: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by_user_id: Optional[str]
    
    class Config:
        from_attributes = True


class BodegaListResponse(BaseModel):
    """Respuesta con lista de bodegas"""
    items: List[BodegaResponse]
    meta: Meta
