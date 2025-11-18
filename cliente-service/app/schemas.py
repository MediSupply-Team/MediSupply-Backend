"""
Esquemas Pydantic para cliente-service
Payloads de entrada y salida para la HU07: Consultar Cliente y HU: Registrar Vendedor
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


# ==========================================
# ESQUEMAS DE ENTRADA (REQUEST PAYLOADS)
# ==========================================

class ClienteCreate(BaseModel):
    """Payload para crear un nuevo cliente (id y codigo_unico se generan automáticamente)"""
    nit: str = Field(..., min_length=5, max_length=32, description="NIT del cliente", example="900555666-7")
    nombre: str = Field(..., min_length=3, max_length=255, description="Nombre del cliente", example="Farmacia Los Andes")
    codigo_unico: Optional[str] = Field(None, min_length=3, max_length=64, description="Código único del cliente (se genera automáticamente si no se proporciona)", example="ABC123")
    email: Optional[str] = Field(None, max_length=255, description="Email del cliente", example="contacto@losandes.com")
    telefono: Optional[str] = Field(None, max_length=32, description="Teléfono del cliente", example="+57-1-3456789")
    direccion: Optional[str] = Field(None, max_length=512, description="Dirección del cliente", example="Calle 45 #12-34")
    ciudad: Optional[str] = Field(None, max_length=128, description="Ciudad del cliente", example="Medellín")
    pais: Optional[str] = Field(default="CO", max_length=8, description="País del cliente", example="CO")
    activo: bool = Field(default=True, description="Si el cliente está activo")
    vendedor_id: Optional[str] = Field(None, description="ID del vendedor (UUID como string) - Opcional", example="550e8400-e29b-41d4-a716-446655440000")


class ClienteUpdate(BaseModel):
    """Payload para actualizar un cliente existente"""
    nombre: Optional[str] = Field(None, min_length=3, max_length=255, description="Nombre del cliente")
    email: Optional[str] = Field(None, max_length=255, description="Email del cliente")
    telefono: Optional[str] = Field(None, max_length=32, description="Teléfono del cliente")
    direccion: Optional[str] = Field(None, max_length=512, description="Dirección del cliente")
    ciudad: Optional[str] = Field(None, max_length=128, description="Ciudad del cliente")
    pais: Optional[str] = Field(None, max_length=8, description="País del cliente")
    activo: Optional[bool] = Field(None, description="Si el cliente está activo")
    vendedor_id: Optional[str] = Field(None, description="ID del vendedor asignado al cliente (UUID) - Opcional", example="550e8400-e29b-41d4-a716-446655440000")


class AsociarClientesRequest(BaseModel):
    """Payload para asociar múltiples clientes a un vendedor"""
    clientes_ids: List[str] = Field(
        ...,
        min_length=1,
        description="Lista de IDs de clientes (UUIDs) a asociar con el vendedor",
        example=["550e8400-e29b-41d4-a716-446655440001", "550e8400-e29b-41d4-a716-446655440002"]
    )


class AsociarClientesResponse(BaseModel):
    """Respuesta al asociar clientes a un vendedor"""
    vendedor_id: UUID = Field(..., description="ID del vendedor")
    vendedor_nombre: str = Field(..., description="Nombre del vendedor")
    clientes_asociados: int = Field(..., description="Cantidad de clientes asociados exitosamente")
    clientes_no_encontrados: List[str] = Field(default_factory=list, description="IDs de clientes que no fueron encontrados")
    clientes_inactivos: List[str] = Field(default_factory=list, description="IDs de clientes que están inactivos")
    clientes_con_vendedor: List[str] = Field(default_factory=list, description="IDs de clientes que ya tenían un vendedor asociado")
    mensaje: str = Field(..., description="Mensaje de resultado")


class ClienteBusquedaRequest(BaseModel):
    """Payload para búsqueda de cliente por NIT, nombre o código único"""
    termino_busqueda: str = Field(
        ..., 
        min_length=2, 
        max_length=255,
        description="NIT, nombre o código único del cliente a buscar",
        example="900123456-7"
    )
    vendedor_id: str = Field(
        ..., 
        min_length=1, 
        max_length=64,
        description="ID del vendedor que realiza la consulta (para trazabilidad)",
        example="VEN001"
    )
    
    @field_validator('termino_busqueda')
    @classmethod
    def validar_termino_busqueda(cls, v):
        if not v or v.strip() == "":
            raise ValueError("El término de búsqueda no puede estar vacío")
        return v.strip()


class HistoricoClienteRequest(BaseModel):
    """Payload para consultar histórico completo de un cliente"""
    cliente_id: str = Field(
        ..., 
        min_length=1, 
        max_length=64,
        description="ID único del cliente",
        example="CLI001"
    )
    vendedor_id: str = Field(
        ..., 
        min_length=1, 
        max_length=64,
        description="ID del vendedor que realiza la consulta",
        example="VEN001"
    )
    incluir_devoluciones: bool = Field(
        default=True,
        description="Si incluir o no las devoluciones en el histórico"
    )
    limite_meses: int = Field(
        default=12,
        ge=1,
        le=60,
        description="Número de meses hacia atrás para el histórico (máximo 60)"
    )


# ==========================================
# ESQUEMAS DE SALIDA (RESPONSE PAYLOADS)
# ==========================================

class ClienteBasicoResponse(BaseModel):
    """Información básica del cliente encontrado en la búsqueda"""
    id: UUID = Field(..., description="ID único del cliente (UUID)")
    nit: str = Field(..., description="NIT del cliente")
    nombre: str = Field(..., description="Nombre completo del cliente")
    codigo_unico: str = Field(..., description="Código único del cliente")
    email: Optional[str] = Field(None, description="Email del cliente")
    telefono: Optional[str] = Field(None, description="Teléfono del cliente")
    direccion: Optional[str] = Field(None, description="Dirección del cliente")
    ciudad: Optional[str] = Field(None, description="Ciudad del cliente")
    pais: Optional[str] = Field(None, description="País del cliente")
    rol: str = Field(default="cliente", description="Rol del cliente")
    activo: bool = Field(default=True, description="Si el cliente está activo")
    vendedor_id: Optional[UUID] = Field(None, description="ID del vendedor asignado al cliente (opcional)")
    created_at: Optional[datetime] = Field(None, description="Fecha de creación")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "CLI001",
                "nit": "900123456-7",
                "nombre": "Farmacia San José",
                "codigo_unico": "FSJ001",
                "email": "contacto@farmaciasanjose.com",
                "telefono": "+57-1-2345678",
                "direccion": "Calle 123 #45-67",
                "ciudad": "Bogotá",
                "pais": "CO",
                "activo": True,
                "vendedor_id": "550e8400-e29b-41d4-a716-446655440000",
                "created_at": "2023-06-15T10:30:00Z",
                "updated_at": "2024-09-15T10:30:00Z"
            }
        }
    }


class CompraHistoricoItem(BaseModel):
    """Item individual del histórico de compras"""
    id: str = Field(..., description="ID del registro de compra")
    orden_id: str = Field(..., description="ID de la orden de compra")
    producto_id: str = Field(..., description="ID del producto comprado")
    producto_nombre: str = Field(..., description="Nombre del producto")
    categoria_producto: Optional[str] = Field(None, description="Categoría del producto")
    cantidad: int = Field(..., ge=1, description="Cantidad comprada")
    precio_unitario: Decimal = Field(..., description="Precio unitario del producto")
    precio_total: Decimal = Field(..., description="Precio total de la línea")
    fecha_compra: date = Field(..., description="Fecha de la compra")
    estado_orden: Optional[str] = Field(None, description="Estado de la orden")
    created_at: Optional[datetime] = Field(None, description="Fecha de creación del registro")
    
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            Decimal: lambda v: float(v)
        },
        "json_schema_extra": {
            "example": {
                "id": "CH001",
                "orden_id": "ORD001",
                "producto_id": "PROD123",
                "producto_nombre": "Acetaminofén 500mg",
                "categoria_producto": "Analgésicos",
                "cantidad": 100,
                "precio_unitario": 150.50,
                "precio_total": 15050.00,
                "fecha_compra": "2024-09-15",
                "estado_orden": "completada",
                "created_at": "2024-09-15T10:30:00Z"
            }
        }
    }


class ProductoPreferidoItem(BaseModel):
    """Producto preferido con estadísticas de compra"""
    id: str = Field(..., description="ID del registro")
    cliente_id: str = Field(..., description="ID del cliente")
    producto_id: str = Field(..., description="ID del producto")
    producto_nombre: str = Field(..., description="Nombre del producto")
    categoria_producto: Optional[str] = Field(None, description="Categoría del producto")
    frecuencia_compra: int = Field(..., ge=1, description="Número de veces comprado")
    cantidad_total: int = Field(..., ge=1, description="Cantidad total comprada")
    cantidad_promedio: Decimal = Field(..., ge=0, description="Cantidad promedio por compra")
    ultima_compra: Optional[date] = Field(None, description="Fecha de la última compra")
    meses_desde_ultima_compra: int = Field(..., ge=0, description="Meses desde última compra")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "producto_id": "PROD123",
                "producto_nombre": "Acetaminofén 500mg",
                "categoria_producto": "Analgésicos",
                "frecuencia_compra": 8,
                "cantidad_total": 800,
                "cantidad_promedio": 100.0,
                "ultima_compra": "2024-09-15",
                "meses_desde_ultima_compra": 1
            }
        }


class DevolucionItem(BaseModel):
    """Item de devolución del cliente"""
    id: str = Field(..., description="ID de la devolución")
    cliente_id: str = Field(..., description="ID del cliente")
    compra_orden_id: Optional[str] = Field(None, description="ID de la orden original")
    producto_id: str = Field(..., description="ID del producto devuelto")
    producto_nombre: str = Field(..., description="Nombre del producto devuelto")
    cantidad_devuelta: int = Field(..., ge=1, description="Cantidad devuelta")
    motivo: str = Field(..., description="Motivo de la devolución")
    categoria_motivo: Optional[str] = Field(None, description="Categoría del motivo")
    fecha_devolucion: date = Field(..., description="Fecha de la devolución")
    estado: Optional[str] = Field(None, description="Estado de la devolución")
    created_at: Optional[datetime] = Field(None, description="Fecha de creación del registro")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "DEV001",
                "compra_orden_id": "ORD001",
                "producto_id": "PROD123",
                "producto_nombre": "Acetaminofén 500mg",
                "cantidad_devuelta": 10,
                "motivo": "Producto vencido",
                "categoria_motivo": "calidad",
                "fecha_devolucion": "2024-09-20",
                "estado": "procesada"
            }
        }


class EstadisticasClienteResponse(BaseModel):
    """Estadísticas resumidas del cliente"""
    cliente_id: str = Field(..., description="ID del cliente")
    total_compras: int = Field(..., ge=0, description="Total de compras realizadas")
    total_productos_unicos: int = Field(..., ge=0, description="Total de productos únicos comprados")
    total_devoluciones: int = Field(..., ge=0, description="Total de devoluciones realizadas")
    valor_total_compras: Decimal = Field(..., description="Valor total de todas las compras")
    promedio_orden: Decimal = Field(..., description="Valor promedio por orden")
    frecuencia_compra_mensual: Decimal = Field(..., ge=0, description="Frecuencia de compra mensual")
    tasa_devolucion: Decimal = Field(..., ge=0, le=100, description="Tasa de devolución en porcentaje")
    cliente_desde: Optional[date] = Field(None, description="Fecha de primera compra")
    ultima_compra: Optional[date] = Field(None, description="Fecha de última compra")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }
        json_schema_extra = {
            "example": {
                "total_compras": 25,
                "total_productos_unicos": 15,
                "total_devoluciones": 2,
                "valor_total_compras": 1250000.50,
                "promedio_orden": 50000.02,
                "frecuencia_compra_mensual": 2.1,
                "tasa_devolucion": 8.0,
                "cliente_desde": "2023-06-15",
                "ultima_compra": "2024-09-15"
            }
        }


class HistoricoCompletoResponse(BaseModel):
    """Respuesta completa del histórico del cliente"""
    cliente: ClienteBasicoResponse = Field(..., description="Información básica del cliente")
    historico_compras: List[CompraHistoricoItem] = Field(
        default=[], 
        description="Histórico de compras del cliente"
    )
    productos_preferidos: List[ProductoPreferidoItem] = Field(
        default=[], 
        description="Productos preferidos y frecuencia de compra"
    )
    devoluciones: List[DevolucionItem] = Field(
        default=[], 
        description="Devoluciones realizadas con motivos"
    )
    estadisticas: EstadisticasClienteResponse = Field(
        ..., 
        description="Estadísticas resumidas del cliente"
    )
    metadatos: Dict[str, Any] = Field(
        default={}, 
        description="Metadatos de la consulta (tiempo de respuesta, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "cliente": {
                    "id": "CLI001",
                    "nit": "900123456-7",
                    "nombre": "Farmacia San José",
                    "codigo_unico": "FSJ001",
                    "email": "contacto@farmaciasanjose.com",
                    "ciudad": "Bogotá",
                    "pais": "CO",
                    "activo": True
                },
                "historico_compras": [],
                "productos_preferidos": [],
                "devoluciones": [],
                "estadisticas": {
                    "total_compras": 25,
                    "total_productos_unicos": 15,
                    "total_devoluciones": 2
                },
                "metadatos": {
                    "consulta_took_ms": 850,
                    "fecha_consulta": "2024-10-11T10:30:00Z",
                    "limite_meses": 12,
                    "vendedor_id": "VEN001"
                }
            }
        }


# ==========================================
# ESQUEMAS DE AUDITORIA Y TRAZABILIDAD
# ==========================================

class ConsultaAuditoriaResponse(BaseModel):
    """Respuesta de registro de auditoría de consulta"""
    id: int = Field(..., description="ID del registro de auditoría")
    vendedor_id: str = Field(..., description="ID del vendedor")
    cliente_id: str = Field(..., description="ID del cliente consultado")
    tipo_consulta: str = Field(..., description="Tipo de consulta realizada")
    termino_busqueda: Optional[str] = Field(None, description="Término usado en la búsqueda")
    took_ms: int = Field(..., description="Tiempo de respuesta en milisegundos")
    timestamp: datetime = Field(..., description="Timestamp de la consulta")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 123,
                "vendedor_id": "VEN001",
                "cliente_id": "CLI001",
                "tipo_consulta": "busqueda_por_nit",
                "termino_busqueda": "900123456-7",
                "took_ms": 850,
                "timestamp": "2024-10-11T10:30:00Z"
            }
        }


# ==========================================
# ESQUEMAS DE ERROR Y VALIDACIÓN
# ==========================================

class ErrorResponse(BaseModel):
    """Esquema estándar de respuesta de error"""
    error: str = Field(..., description="Tipo de error")
    message: str = Field(..., description="Mensaje de error")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales del error")
    timestamp: Optional[str] = Field(None, description="Timestamp del error")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "CLIENT_NOT_FOUND",
                "message": "Cliente no encontrado con el término de búsqueda proporcionado",
                "details": {
                    "termino_busqueda": "900999999-9",
                    "sugerencias": ["Verificar el NIT", "Usar nombre completo", "Probar código único"]
                },
                "timestamp": "2024-10-11T10:30:00Z"
            }
        }


class ValidacionResponse(BaseModel):
    """Respuesta de validación de performance"""
    cumple_sla: bool = Field(..., description="Si cumple el SLA de ≤ 2 segundos")
    tiempo_respuesta_ms: int = Field(..., description="Tiempo de respuesta en milisegundos")
    limite_sla_ms: int = Field(default=2000, description="Límite SLA en milisegundos")
    advertencias: List[str] = Field(default=[], description="Advertencias de performance")
    
    class Config:
        json_schema_extra = {
            "example": {
                "cumple_sla": True,
                "tiempo_respuesta_ms": 850,
                "limite_sla_ms": 2000,
                "advertencias": []
            }
        }


# ==========================================
# SCHEMAS PARA VENDEDORES (HU: Registrar Vendedor)
# ==========================================

class VendedorCreate(BaseModel):
    """Schema para crear un vendedor (id se genera automáticamente con UUID) - Fase 2 Extendido"""
    # Campos principales (requeridos)
    identificacion: str = Field(..., min_length=5, max_length=32, description="Cédula o identificación", example="1234567890")
    nombre_completo: str = Field(..., min_length=3, max_length=255, description="Nombre completo del vendedor", example="Juan Pérez Gómez")
    email: str = Field(..., min_length=5, max_length=255, description="Email del vendedor", example="juan.perez@medisupply.com")
    telefono: str = Field(..., min_length=7, max_length=32, description="Teléfono del vendedor", example="+57-300-1234567")
    pais: str = Field(..., min_length=2, max_length=2, description="Código ISO del país", example="CO")
    
    # Campos de credenciales (opcionales)
    username: Optional[str] = Field(None, min_length=3, max_length=64, description="Nombre de usuario para login", example="jperez")
    password_hash: Optional[str] = Field(None, description="Hash de contraseña (opcional)")
    
    # Campos de plan y rol (opcionales)
    rol: str = Field(default="seller", description="Rol del vendedor en orders-service", example="seller")
    rol_vendedor_id: Optional[str] = Field(None, description="ID del tipo de rol vendedor (UUID)", example="550e8400-e29b-41d4-a716-446655440000")
    
    # Campos de asignación geográfica y jerarquía (opcionales)
    territorio_id: Optional[str] = Field(None, description="ID del territorio asignado (UUID)", example="550e8400-e29b-41d4-a716-446655440001")
    supervisor_id: Optional[str] = Field(None, description="ID del supervisor (UUID)", example="550e8400-e29b-41d4-a716-446655440002")
    
    # Campos adicionales (opcionales)
    fecha_ingreso: Optional[date] = Field(None, description="Fecha de ingreso al equipo", example="2024-01-15")
    observaciones: Optional[str] = Field(None, description="Observaciones adicionales", example="Vendedor con experiencia en sector hospitalario")
    
    # Plan de Venta (OPCIONAL - se crea en cascada si se envía)
    plan_venta: Optional["PlanVentaCreateNested"] = Field(None, description="Plan de venta del vendedor (se crea automáticamente)")
    
    # Campos de auditoría
    activo: bool = Field(default=True, description="Si el vendedor está activo")
    created_by_user_id: Optional[str] = Field(None, max_length=64, description="ID del usuario que crea el vendedor")
    
    class Config:
        json_schema_extra = {
            "example": {
                "identificacion": "1234567890",
                "nombre_completo": "Juan Pérez Gómez",
                "email": "juan.perez@medisupply.com",
                "telefono": "+57-300-1234567",
                "pais": "CO",
                "username": "jperez",
                "rol_vendedor_id": "550e8400-e29b-41d4-a716-446655440000",
                "territorio_id": "550e8400-e29b-41d4-a716-446655440001",
                "fecha_ingreso": "2024-01-15",
                "rol": "seller",
                "activo": True,
                "plan_venta": {
                    "tipo_plan_id": "550e8400-e29b-41d4-a716-446655440001",
                    "nombre_plan": "Plan Premium Q1 2024",
                    "fecha_inicio": "2024-01-01",
                    "fecha_fin": "2024-03-31",
                    "meta_ventas": 150000.00,
                    "comision_base": 8.0,
                    "estructura_bonificaciones": {"70": 2, "90": 5, "100": 10},
                    "productos": [
                        {
                            "producto_id": "PROD001",
                            "meta_cantidad": 100,
                            "precio_unitario": 1500.00
                        }
                    ],
                    "region_ids": ["550e8400-e29b-41d4-a716-446655440002"],
                    "zona_ids": ["550e8400-e29b-41d4-a716-446655440003"]
                }
            }
        }


class VendedorUpdate(BaseModel):
    """Schema para actualizar un vendedor existente - Fase 2 Extendido"""
    # Campos principales
    identificacion: Optional[str] = Field(None, min_length=5, max_length=32)
    nombre_completo: Optional[str] = Field(None, min_length=3, max_length=255)
    email: Optional[str] = Field(None, min_length=5, max_length=255)
    telefono: Optional[str] = Field(None, min_length=7, max_length=32)
    pais: Optional[str] = Field(None, min_length=2, max_length=2)
    
    # Campos de credenciales
    username: Optional[str] = Field(None, min_length=3, max_length=64)
    password_hash: Optional[str] = None
    
    # Campos de plan y rol
    rol: Optional[str] = None
    rol_vendedor_id: Optional[str] = Field(None, description="ID del tipo de rol vendedor (UUID)")
    
    # Campos de asignación geográfica y jerarquía
    territorio_id: Optional[str] = Field(None, description="ID del territorio asignado (UUID)")
    supervisor_id: Optional[str] = Field(None, description="ID del supervisor (UUID)")
    
    # Campos adicionales
    fecha_ingreso: Optional[date] = Field(None, description="Fecha de ingreso al equipo")
    observaciones: Optional[str] = Field(None, description="Observaciones adicionales")
    
    # Campos de auditoría
    activo: Optional[bool] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "telefono": "+57-311-7654321",
                "territorio_id": "550e8400-e29b-41d4-a716-446655440001",
                "observaciones": "Vendedor ascendido a Senior",
                "activo": True
            }
        }


class VendedorResponse(BaseModel):
    """Schema de respuesta de un vendedor - Fase 2 Extendido"""
    # Campos principales
    id: UUID
    identificacion: str
    nombre_completo: str
    email: str
    telefono: str
    pais: str
    
    # Campos de credenciales (sin password_hash por seguridad)
    username: Optional[str] = None
    
    # Campos de plan y rol
    rol: str
    rol_vendedor_id: Optional[UUID] = None
    
    # Campos de asignación geográfica y jerarquía
    territorio_id: Optional[UUID] = None
    supervisor_id: Optional[UUID] = None
    
    # Campos adicionales
    fecha_ingreso: Optional[date] = None
    observaciones: Optional[str] = None
    
    # Campos de auditoría
    activo: bool
    created_at: datetime
    updated_at: datetime
    created_by_user_id: Optional[str] = None
    
    # ID del Plan de Venta asociado (1:1, se obtiene completo en /vendedores/{id}/detalle)
    plan_venta_id: Optional[UUID] = Field(None, description="ID del plan de venta asociado (si existe)")
    
    class Config:
        from_attributes = True


class VendedorListResponse(BaseModel):
    """Respuesta con lista de vendedores paginada"""
    items: List[VendedorResponse]
    total: int = Field(..., description="Total de vendedores encontrados")
    page: int = Field(..., description="Página actual")
    size: int = Field(..., description="Tamaño de página")
    took_ms: int = Field(..., description="Tiempo de respuesta en ms")


class VendedorDetalleResponse(BaseModel):
    """
    Schema de respuesta COMPLETA de un vendedor con TODO su plan de venta anidado
    Usado en GET /vendedores/{id}/detalle
    """
    # Campos principales del vendedor
    id: UUID
    identificacion: str
    nombre_completo: str
    email: str
    telefono: str
    pais: str
    username: Optional[str] = None
    rol: str
    rol_vendedor_id: Optional[UUID] = None
    territorio_id: Optional[UUID] = None
    supervisor_id: Optional[UUID] = None
    fecha_ingreso: Optional[date] = None
    observaciones: Optional[str] = None
    activo: bool
    created_at: datetime
    updated_at: datetime
    created_by_user_id: Optional[str] = None
    
    # Plan de Venta COMPLETO (se carga con todos sus detalles)
    plan_venta: Optional["PlanVentaResponse"] = Field(None, description="Plan de venta completo con productos, regiones y zonas")
    
    class Config:
        from_attributes = True


# ============================================================================
# SCHEMAS PARA CATÁLOGOS DE SOPORTE (HU: Registrar Vendedor - Extensión)
# ============================================================================

# ---------- TipoRolVendedor ----------
class TipoRolVendedorCreate(BaseModel):
    """Schema para crear un tipo de rol de vendedor"""
    codigo: str = Field(..., min_length=2, max_length=64, description="Código único del rol")
    nombre: str = Field(..., min_length=3, max_length=255, description="Nombre del rol")
    descripcion: Optional[str] = Field(None, description="Descripción del rol")
    nivel_jerarquia: int = Field(..., ge=1, le=10, description="Nivel jerárquico (1=más alto)")
    permisos: Optional[dict] = Field(None, description="Permisos del rol en formato JSON")
    activo: bool = Field(default=True, description="Estado del rol")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "codigo": "GERENTE_REG",
                "nombre": "Gerente Regional",
                "descripcion": "Gerente responsable de una región completa",
                "nivel_jerarquia": 1,
                "permisos": {"ver_reportes": True, "aprobar_descuentos": True, "gestionar_vendedores": True},
                "activo": True
            }
        }
    )


class TipoRolVendedorResponse(BaseModel):
    """Schema de respuesta de un tipo de rol de vendedor"""
    id: UUID = Field(..., description="ID único del rol")
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    nivel_jerarquia: int
    permisos: Optional[dict] = None
    activo: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TipoRolVendedorListResponse(BaseModel):
    """Schema de respuesta de lista paginada de tipos de rol"""
    tipos_rol: List[TipoRolVendedorResponse] = Field(default_factory=list)
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    size: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=0)


# ---------- Territorio ----------
class TerritorioCreate(BaseModel):
    """Schema para crear un territorio"""
    codigo: str = Field(..., min_length=2, max_length=64, description="Código único del territorio")
    nombre: str = Field(..., min_length=3, max_length=255, description="Nombre del territorio")
    pais: str = Field(..., min_length=2, max_length=2, description="Código ISO del país")
    descripcion: Optional[str] = Field(None, description="Descripción del territorio")
    activo: bool = Field(default=True, description="Estado del territorio")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "codigo": "BOG-NORTE",
                "nombre": "Bogotá Norte",
                "pais": "CO",
                "descripcion": "Zona norte de Bogotá",
                "activo": True
            }
        }
    )


class TerritorioResponse(BaseModel):
    """Schema de respuesta de un territorio"""
    id: UUID = Field(..., description="ID único del territorio")
    codigo: str
    nombre: str
    pais: str
    descripcion: Optional[str] = None
    activo: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TerritorioListResponse(BaseModel):
    """Schema de respuesta de lista paginada de territorios"""
    territorios: List[TerritorioResponse] = Field(default_factory=list)
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    size: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=0)


# ---------- TipoPlan ----------
class TipoPlanCreate(BaseModel):
    """Schema para crear un tipo de plan"""
    codigo: str = Field(..., min_length=2, max_length=64, description="Código único del tipo de plan")
    nombre: str = Field(..., min_length=3, max_length=255, description="Nombre del tipo de plan")
    descripcion: Optional[str] = Field(None, description="Descripción del tipo de plan")
    comision_base_defecto: Decimal = Field(..., ge=0, le=100, description="Comisión base en porcentaje")
    activo: bool = Field(default=True, description="Estado del tipo de plan")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "codigo": "PREMIUM",
                "nombre": "Plan Premium",
                "descripcion": "Plan para vendedores de alto rendimiento",
                "comision_base_defecto": 10.0,
                "activo": True
            }
        }
    )


class TipoPlanResponse(BaseModel):
    """Schema de respuesta de un tipo de plan"""
    id: UUID = Field(..., description="ID único del tipo de plan")
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    comision_base_defecto: Decimal
    activo: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TipoPlanListResponse(BaseModel):
    """Schema de respuesta de lista paginada de tipos de plan"""
    tipos_plan: List[TipoPlanResponse] = Field(default_factory=list)
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    size: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=0)


# ---------- Region ----------
class RegionCreate(BaseModel):
    """Schema para crear una región"""
    codigo: str = Field(..., min_length=2, max_length=64, description="Código único de la región")
    nombre: str = Field(..., min_length=3, max_length=255, description="Nombre de la región")
    pais: str = Field(..., min_length=2, max_length=2, description="Código ISO del país")
    descripcion: Optional[str] = Field(None, description="Descripción de la región")
    activo: bool = Field(default=True, description="Estado de la región")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "codigo": "REG-NORTE",
                "nombre": "Región Norte",
                "pais": "CO",
                "descripcion": "Región norte del país",
                "activo": True
            }
        }
    )


class RegionResponse(BaseModel):
    """Schema de respuesta de una región"""
    id: UUID = Field(..., description="ID único de la región")
    codigo: str
    nombre: str
    pais: str
    descripcion: Optional[str] = None
    activo: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RegionListResponse(BaseModel):
    """Schema de respuesta de lista paginada de regiones"""
    regiones: List[RegionResponse] = Field(default_factory=list)
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    size: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=0)


# ---------- Zona ----------
class ZonaCreate(BaseModel):
    """Schema para crear una zona"""
    codigo: str = Field(..., min_length=2, max_length=64, description="Código único de la zona")
    nombre: str = Field(..., min_length=3, max_length=255, description="Nombre de la zona")
    tipo: str = Field(..., min_length=3, max_length=64, description="Tipo de zona")
    descripcion: Optional[str] = Field(None, description="Descripción de la zona")
    activo: bool = Field(default=True, description="Estado de la zona")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "codigo": "ZONA-IND",
                "nombre": "Zona Industrial",
                "tipo": "industrial",
                "descripcion": "Zona industrial con empresas manufactureras",
                "activo": True
            }
        }
    )


class ZonaResponse(BaseModel):
    """Schema de respuesta de una zona"""
    id: UUID = Field(..., description="ID único de la zona")
    codigo: str
    nombre: str
    tipo: str
    descripcion: Optional[str] = None
    activo: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ZonaListResponse(BaseModel):
    """Schema de respuesta de lista paginada de zonas"""
    zonas: List[ZonaResponse] = Field(default_factory=list)
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    size: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=0)


# ============================================================================
# SCHEMAS PARA PLAN DE VENTA (HU: Registrar Vendedor - FASE 3)
# ============================================================================

# ---------- Producto Asignado al Plan ----------
class PlanProductoItem(BaseModel):
    """Schema para un producto asignado al plan de venta (solo IDs, frontend consulta catalogo-service)"""
    producto_id: str = Field(..., description="ID del producto (desde catalogo-service)")
    meta_cantidad: int = Field(..., ge=0, description="Cantidad meta a vender")
    precio_unitario: Decimal = Field(..., ge=0, description="Precio unitario en el plan")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "producto_id": "PROD001",
                "meta_cantidad": 100,
                "precio_unitario": 1500.00
            }
        }
    )


class PlanProductoItemResponse(BaseModel):
    """Schema de respuesta de un producto asignado (solo IDs, frontend consulta catalogo-service)"""
    id: UUID
    producto_id: str  # Solo ID, el frontend consultará a catalogo-service para obtener nombre, descripción, etc.
    meta_cantidad: int
    precio_unitario: Decimal
    created_at: datetime
    
    @property
    def total_producto(self) -> Decimal:
        """Calcula el total del producto (meta_cantidad * precio_unitario)"""
        return Decimal(self.meta_cantidad) * self.precio_unitario
    
    model_config = ConfigDict(from_attributes=True)


# ---------- Plan de Venta CREATE NESTED (sin vendedor_id) ----------
class PlanVentaCreateNested(BaseModel):
    """Schema para crear un plan de venta DENTRO del vendedor (sin vendedor_id)"""
    # Relaciones
    tipo_plan_id: Optional[str] = Field(None, description="ID del tipo de plan (UUID)")
    
    # Información básica
    nombre_plan: str = Field(..., min_length=3, max_length=255, description="Nombre del plan")
    fecha_inicio: date = Field(..., description="Fecha de inicio del plan")
    fecha_fin: date = Field(..., description="Fecha de fin del plan")
    
    # Metas y comisiones
    meta_ventas: Decimal = Field(..., ge=0, description="Meta de ventas en dinero")
    comision_base: Decimal = Field(..., ge=0, le=100, description="Comisión base (%)")
    
    # Estructura de bonificaciones (JSON: {70: 2, 90: 5, 100: 10})
    estructura_bonificaciones: Optional[dict] = Field(
        None,
        description="Bonificaciones por meta alcanzada: {porcentaje_meta: bono_adicional}",
        json_schema_extra={"example": {"70": 2, "90": 5, "100": 10}}
    )
    
    # Productos asignados
    productos: List[PlanProductoItem] = Field(default_factory=list, description="Productos asignados al plan")
    
    # Regiones y zonas (IDs)
    region_ids: List[str] = Field(default_factory=list, description="IDs de regiones asignadas")
    zona_ids: List[str] = Field(default_factory=list, description="IDs de zonas asignadas")
    
    # Campos adicionales
    observaciones: Optional[str] = Field(None, description="Observaciones del plan")
    activo: bool = Field(default=True, description="Si el plan está activo")
    created_by_user_id: Optional[str] = Field(None, description="ID del usuario creador")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tipo_plan_id": "550e8400-e29b-41d4-a716-446655440001",
                "nombre_plan": "Plan Premium Q1 2024",
                "fecha_inicio": "2024-01-01",
                "fecha_fin": "2024-03-31",
                "meta_ventas": 150000.00,
                "comision_base": 8.0,
                "estructura_bonificaciones": {"70": 2, "90": 5, "100": 10},
                "productos": [
                    {
                        "producto_id": "PROD001",
                        "meta_cantidad": 100,
                        "precio_unitario": 1500.00
                    }
                ],
                "region_ids": ["550e8400-e29b-41d4-a716-446655440002"],
                "zona_ids": ["550e8400-e29b-41d4-a716-446655440003"],
                "observaciones": "Plan especial sector hospitalario",
                "activo": True
            }
        }
    )


# ---------- Plan de Venta UPDATE ----------
class PlanVentaUpdate(BaseModel):
    """Schema para actualizar un plan de venta"""
    tipo_plan_id: Optional[str] = None
    nombre_plan: Optional[str] = Field(None, min_length=3, max_length=255)
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    meta_ventas: Optional[Decimal] = Field(None, ge=0)
    comision_base: Optional[Decimal] = Field(None, ge=0, le=100)
    estructura_bonificaciones: Optional[dict] = None
    productos: Optional[List[PlanProductoItem]] = None
    region_ids: Optional[List[str]] = None
    zona_ids: Optional[List[str]] = None
    observaciones: Optional[str] = None
    activo: Optional[bool] = None


# ---------- Plan de Venta RESPONSE (Completo) ----------
class PlanVentaResponse(BaseModel):
    """Schema de respuesta completa de un plan de venta con todos sus detalles"""
    # Campos principales
    id: UUID
    vendedor_id: UUID
    tipo_plan_id: Optional[UUID] = None
    nombre_plan: str
    fecha_inicio: date
    fecha_fin: date
    meta_ventas: Decimal
    comision_base: Decimal
    estructura_bonificaciones: Optional[dict] = None
    observaciones: Optional[str] = None
    activo: bool
    created_at: datetime
    updated_at: datetime
    created_by_user_id: Optional[str] = None
    
    # Relaciones anidadas (se cargan dinámicamente en el endpoint)
    tipo_plan: Optional[TipoPlanResponse] = None
    productos_asignados: List[PlanProductoItemResponse] = Field(default_factory=list)
    regiones_asignadas: List[RegionResponse] = Field(default_factory=list)
    zonas_asignadas: List[ZonaResponse] = Field(default_factory=list)
    
    @property
    def total_plan(self) -> Decimal:
        """Calcula el total del plan sumando todos los productos"""
        return sum((Decimal(p.meta_cantidad) * p.precio_unitario) for p in self.productos_asignados)
    
    model_config = ConfigDict(from_attributes=True)


# ---------- Plan de Venta BASIC Response (Sin detalles anidados) ----------
class PlanVentaBasicResponse(BaseModel):
    """Schema de respuesta básica de un plan de venta (sin detalles)"""
    id: UUID
    vendedor_id: UUID
    nombre_plan: str
    fecha_inicio: date
    fecha_fin: date
    meta_ventas: Decimal
    comision_base: Decimal
    activo: bool
    
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# ACTUALIZAR FORWARD REFERENCES
# ==========================================
# Resolver forward references para schemas con relaciones anidadas
VendedorCreate.model_rebuild()
VendedorDetalleResponse.model_rebuild()  # Solo el detalle tiene plan completo
PlanVentaCreateNested.model_rebuild()
PlanVentaResponse.model_rebuild()
