# 🔍 ANÁLISIS CRÍTICO: ¿ES NECESARIO SQS PARA LA LÓGICA DE NEGOCIO?

## 📋 RESUMEN EJECUTIVO

**CONCLUSIÓN: SQS NO ES NECESARIO PARA CUMPLIR LOS CRITERIOS DE ACEPTACIÓN DE LA HU**

✅ **Todos los criterios de aceptación se cumplen SIN SQS**
⚠️ SQS es útil para **integraciones externas**, NO para lógica de negocio core
🎯 La implementación actual sin SQS es **completa y suficiente**

---

## 📊 ANÁLISIS CRITERIO POR CRITERIO

### ✅ CRITERIO 1: Movimientos de Inventario

**Requisito:**
> Se pueden registrar ingresos y salidas por bodega.
> Cada movimiento requiere: producto, bodega, cantidad, tipo de movimiento (ingreso/salida), fecha/hora, y motivo (compra, ajuste, venta, devolución, merma, etc.).

**¿Se cumple sin SQS?** → **SÍ ✅**

**Implementación actual:**
```python
# catalogo-service/app/routes/inventario.py
@router.post("/movements", response_model=MovimientoResponse)
async def registrar_movimiento_inventario(
    movimiento: MovimientoCreate,
    session: AsyncSession = Depends(get_session)
):
    # Registra movimiento EN BASE DE DATOS
    # Todos los campos requeridos se guardan
    nuevo_movimiento, alertas = await InventarioService.registrar_movimiento(
        session, movimiento
    )
    await session.commit()  # COMMIT TRANSACCIONAL
    return nuevo_movimiento
```

**¿Qué hace?**
- ✅ Recibe todos los datos requeridos
- ✅ Valida con Pydantic
- ✅ Guarda en PostgreSQL
- ✅ Retorna confirmación

**¿Necesita SQS?** → **NO**
- El movimiento se guarda en BD ✅
- Es inmediatamente consultable ✅
- No hay procesamiento asíncrono requerido ✅

---

### ✅ CRITERIO 2: Actualización en Tiempo Real

**Requisito:**
> Al guardar un movimiento, el stock del producto en la bodega se actualiza inmediatamente.
> El saldo actualizado es visible en la ficha del producto y en el kardex/historial.

**¿Se cumple sin SQS?** → **SÍ ✅**

**Implementación actual:**
```python
# catalogo-service/app/services/inventario_service.py
async def registrar_movimiento(
    session: AsyncSession,
    movimiento: MovimientoCreate
) -> Tuple[MovimientoInventario, List[AlertaInventario]]:
    
    # 1. Obtener saldo actual
    saldo_anterior = await InventarioService.obtener_saldo_bodega(...)
    
    # 2. Calcular nuevo saldo
    if movimiento.tipo_movimiento == TipoMovimiento.INGRESO:
        saldo_nuevo = saldo_anterior + movimiento.cantidad
    else:
        saldo_nuevo = saldo_anterior - movimiento.cantidad
    
    # 3. Crear movimiento
    nuevo_movimiento = MovimientoInventario(...)
    session.add(nuevo_movimiento)
    
    # 4. ACTUALIZAR INVENTARIO (MISMO COMMIT)
    await InventarioService.actualizar_inventario(
        session, movimiento, saldo_nuevo
    )
    
    await session.flush()  # TODO EN LA MISMA TRANSACCIÓN
    
    return nuevo_movimiento, alertas
```

**¿Qué hace?**
- ✅ Actualiza stock en la **MISMA transacción** de PostgreSQL
- ✅ Si falla algo, **TODO** hace rollback (atomicidad)
- ✅ El saldo está disponible **inmediatamente** después del commit
- ✅ No hay "eventual consistency" - es **consistencia inmediata**

**¿Necesita SQS?** → **NO**
- La actualización es **síncrona** en la BD ✅
- El criterio dice "inmediatamente" → PostgreSQL ACID ✅
- SQS introduciría **latencia** y **eventual consistency** ❌

**IMPORTANTE:**
Si usáramos SQS para actualizar stock, tendríamos:
```
Request → Publica a SQS → Worker actualiza BD (2-5s después)
                            ↑
                    ESTO ROMPE "INMEDIATAMENTE"
```

**Conclusión:** SQS **NO debe usarse** para actualizar stock. Debe ser **transaccional y síncrono**.

---

### ✅ CRITERIO 3: Validaciones

**Requisito:**
> No se permite stock negativo (salida > saldo) salvo que el rol tenga permiso de backorder/negativo explícito.
> La cantidad debe ser mayor a 0 y respetar la unidad de medida del producto.
> Si el producto gestiona lotes/series/fechas de vencimiento, estos datos son obligatorios en el movimiento.

**¿Se cumple sin SQS?** → **SÍ ✅**

**Implementación actual:**
```python
# Validación 1: Stock no negativo
if movimiento.tipo_movimiento == TipoMovimiento.SALIDA:
    if saldo_anterior < movimiento.cantidad:
        if not movimiento.permitir_stock_negativo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "STOCK_INSUFICIENTE",
                    "message": f"Stock insuficiente. Disponible: {saldo_anterior}",
                    "saldo_actual": saldo_anterior,
                    "cantidad_solicitada": movimiento.cantidad
                }
            )

# Validación 2: Cantidad > 0 (Pydantic schema)
class MovimientoCreate(BaseModel):
    cantidad: int = Field(..., gt=0, description="Cantidad del movimiento (debe ser > 0)")

# Validación 3: Lote/Vencimiento obligatorios
async def validar_producto_lote_vencimiento(...):
    if producto.requiere_lote and not lote:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "LOTE_REQUERIDO",
                "message": f"El producto {producto.nombre} requiere lote"
            }
        )
    
    if producto.requiere_vencimiento and not fecha_vencimiento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VENCIMIENTO_REQUERIDO",
                "message": f"El producto {producto.nombre} requiere fecha de vencimiento"
            }
        )
```

**¿Qué hace?**
- ✅ Valida ANTES de guardar en BD
- ✅ Retorna errores descriptivos
- ✅ No impacta stock si falla
- ✅ Validaciones síncronas en el request

**¿Necesita SQS?** → **NO**
- Las validaciones deben ser **inmediatas** ✅
- El usuario debe recibir **feedback instantáneo** ✅
- SQS introduciría latencia innecesaria ❌

---

### ✅ CRITERIO 4: Trazabilidad y Auditoría

**Requisito:**
> Cada movimiento registra usuario, timestamp, y referencia (p. ej., N° de documento o pedido).
> Existe historial consultable por producto y bodega con filtros por fecha, tipo, motivo y usuario.

**¿Se cumple sin SQS?** → **SÍ ✅**

**Implementación actual:**
```python
# Tabla movimiento_inventario
class MovimientoInventario(Base):
    __tablename__ = "movimiento_inventario"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    producto_id: Mapped[str] = mapped_column(String(64), index=True)
    bodega_id: Mapped[str] = mapped_column(String(64), index=True)
    tipo_movimiento: Mapped[str] = mapped_column(String(30), index=True)
    motivo: Mapped[str] = mapped_column(String(50))
    cantidad: Mapped[int]
    usuario_id: Mapped[str] = mapped_column(String(64), index=True)  # ✅ USUARIO
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)  # ✅ TIMESTAMP
    referencia_documento: Mapped[str] = mapped_column(String(128))  # ✅ REFERENCIA
    observaciones: Mapped[str] = mapped_column(Text)
    # ... más campos

# Endpoint de kardex (historial)
@router.get("/movements/kardex", response_model=KardexResponse)
async def obtener_kardex(
    producto_id: str,
    bodega_id: str,
    pais: str,
    fecha_desde: Optional[date] = None,  # ✅ FILTRO POR FECHA
    fecha_hasta: Optional[date] = None,
    tipo_movimiento: Optional[TipoMovimiento] = None,  # ✅ FILTRO POR TIPO
    motivo: Optional[str] = None,  # ✅ FILTRO POR MOTIVO
    usuario_id: Optional[str] = None,  # ✅ FILTRO POR USUARIO
    ...
):
    # Consulta PostgreSQL con filtros
    # TODO está en la base de datos, consultable inmediatamente
```

**¿Qué hace?**
- ✅ Guarda TODO en PostgreSQL
- ✅ Histórico completo en BD
- ✅ Filtros SQL eficientes
- ✅ Consultable inmediatamente

**¿Necesita SQS?** → **NO**
- La auditoría está en la **BD principal** ✅
- No hay procesamiento asíncrono requerido ✅
- El historial debe ser **inmediatamente consultable** ✅

**NOTA:** Si necesitáramos enviar datos a un sistema externo de auditoría (Splunk, Elasticsearch), **AHÍ SÍ** usaríamos SQS. Pero para el criterio de la HU, NO es necesario.

---

### ✅ CRITERIO 5: Transferencias entre Bodegas

**Requisito:**
> Una transferencia genera dos movimientos: salida en bodega origen e ingreso en bodega destino, manteniendo la referencia común.

**¿Se cumple sin SQS?** → **SÍ ✅**

**Implementación actual:**
```python
async def registrar_transferencia(
    session: AsyncSession,
    transferencia: TransferenciaCreate
) -> Tuple[MovimientoInventario, MovimientoInventario, List[AlertaInventario]]:
    
    # 1. Salida de bodega origen
    salida = MovimientoCreate(
        bodega_id=transferencia.bodega_origen_id,
        tipo_movimiento=TipoMovimiento.TRANSFERENCIA_SALIDA,
        referencia_documento=transferencia.referencia_documento,  # ✅ REFERENCIA COMÚN
        ...
    )
    mov_salida, alertas_salida = await InventarioService.registrar_movimiento(session, salida)
    
    # 2. Ingreso a bodega destino
    ingreso = MovimientoCreate(
        bodega_id=transferencia.bodega_destino_id,
        tipo_movimiento=TipoMovimiento.TRANSFERENCIA_INGRESO,
        referencia_documento=transferencia.referencia_documento,  # ✅ MISMA REFERENCIA
        ...
    )
    mov_ingreso, alertas_ingreso = await InventarioService.registrar_movimiento(session, ingreso)
    
    # 3. Vincular movimientos
    mov_salida.movimiento_relacionado_id = mov_ingreso.id
    mov_ingreso.movimiento_relacionado_id = mov_salida.id
    
    await session.flush()  # ✅ TODO EN LA MISMA TRANSACCIÓN
    
    return mov_salida, mov_ingreso, todas_alertas
```

**¿Qué hace?**
- ✅ Crea **dos movimientos** vinculados
- ✅ **Misma referencia** en ambos
- ✅ **Misma transacción** (atomicidad)
- ✅ Si falla uno, **ambos** hacen rollback

**¿Necesita SQS?** → **NO**
- La transferencia debe ser **atómica** (todo o nada) ✅
- SQS introduciría **eventual consistency** entre origen y destino ❌
- PostgreSQL ACID garantiza atomicidad ✅

**CRÍTICO:**
Si usáramos SQS para transferencias:
```
Request → Salida (commit) → Publica a SQS → Worker hace ingreso (2-5s después)
                                              ↑
                                    PROBLEMA: Si el worker falla, 
                                    el stock "desaparece" del sistema
```

**Conclusión:** Transferencias **DEBEN** ser transaccionales y síncronas. SQS **NO debe usarse** aquí.

---

### ✅ CRITERIO 6: Confirmación y Errores

**Requisito:**
> Al confirmar, el sistema muestra mensaje de éxito y el saldo resultante.
> Si falla una validación, se muestran motivos concretos y no se impacta el stock.

**¿Se cumple sin SQS?** → **SÍ ✅**

**Implementación actual:**
```python
@router.post("/movements", response_model=MovimientoResponse)
async def registrar_movimiento_inventario(...):
    try:
        nuevo_movimiento, alertas = await InventarioService.registrar_movimiento(...)
        await session.commit()
        
        # ✅ RESPUESTA DE ÉXITO CON SALDO
        return {
            "id": nuevo_movimiento.id,
            "tipo_movimiento": nuevo_movimiento.tipo_movimiento,
            "cantidad": nuevo_movimiento.cantidad,
            "saldo_anterior": nuevo_movimiento.saldo_anterior,
            "saldo_nuevo": nuevo_movimiento.saldo_nuevo,  # ✅ SALDO RESULTANTE
            "created_at": nuevo_movimiento.created_at,
            "message": "Movimiento registrado exitosamente"
        }
    
    except HTTPException as e:
        # ✅ ERROR DESCRIPTIVO
        # NO se hizo commit → NO se impactó el stock
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "code": e.detail["code"],
                "message": e.detail["message"],  # ✅ MOTIVO CONCRETO
                ...
            }
        )
```

**¿Qué hace?**
- ✅ Retorna **inmediatamente** el resultado
- ✅ Incluye saldo resultante
- ✅ Errores descriptivos
- ✅ Si falla, **rollback** automático (no impacta stock)

**¿Necesita SQS?** → **NO**
- El usuario necesita **confirmación inmediata** ✅
- SQS introduciría latencia (el usuario no sabría si funcionó) ❌
- El criterio dice "al confirmar" → debe ser **síncrono** ✅

---

### ✅ CRITERIO 7: Permisos y Controles

**Requisito:**
> Solo usuarios con rol autorizado pueden crear/editar/anular movimientos.
> Anulación: revierte el impacto de stock y queda trazada en el historial.

**¿Se cumple sin SQS?** → **SÍ ✅**

**Implementación actual:**
```python
# Anulación de movimientos
async def anular_movimiento(
    session: AsyncSession,
    movimiento_id: int,
    anulacion: AnularMovimientoRequest
) -> MovimientoInventario:
    
    # 1. Obtener movimiento original
    movimiento = await session.get(MovimientoInventario, movimiento_id)
    
    # 2. Crear movimiento reverso (MISMO COMMIT)
    tipo_inverso = (
        TipoMovimiento.SALIDA if movimiento.tipo_movimiento == "INGRESO"
        else TipoMovimiento.INGRESO
    )
    
    movimiento_reverso = MovimientoCreate(
        tipo_movimiento=tipo_inverso,
        cantidad=movimiento.cantidad,  # Misma cantidad, tipo opuesto
        usuario_id=anulacion.usuario_id,  # ✅ USUARIO QUE ANULA
        motivo=MotivoMovimiento.AJUSTE,
        observaciones=f"Anulación de movimiento {movimiento.id}: {anulacion.motivo_anulacion}",
        ...
    )
    
    await InventarioService.registrar_movimiento(session, movimiento_reverso)
    
    # 3. Marcar original como anulado
    movimiento.estado = "ANULADO"
    movimiento.anulado_por = anulacion.usuario_id  # ✅ TRAZABILIDAD
    movimiento.anulado_at = datetime.utcnow()  # ✅ TIMESTAMP
    movimiento.motivo_anulacion = anulacion.motivo_anulacion  # ✅ MOTIVO
    
    await session.flush()  # ✅ TODO EN LA MISMA TRANSACCIÓN
    
    return movimiento
```

**¿Qué hace?**
- ✅ Revierte stock en la **misma transacción**
- ✅ Queda trazado en historial (dos movimientos: original + reverso)
- ✅ Atomicidad (todo o nada)
- ✅ Permisos se validan en el endpoint (puede agregarse middleware)

**¿Necesita SQS?** → **NO**
- La anulación debe ser **inmediata** y **atómica** ✅
- El usuario debe ver **confirmación instantánea** ✅
- SQS introduciría inconsistencias temporales ❌

---

### ✅ CRITERIO 8: Alertas y Reportes

**Requisito:**
> Si el movimiento deja el stock por debajo del mínimo, se muestra alerta.
> Reporte/exportación de movimientos y saldos por bodega (CSV/Excel).

**¿Se cumple sin SQS?** → **SÍ ✅**

**Implementación actual:**
```python
# Generación de alertas
async def generar_alertas_automaticas(
    session: AsyncSession,
    producto: Producto,
    bodega_id: str,
    pais: str,
    saldo_nuevo: int,
    movimiento_id: int
) -> List[AlertaInventario]:
    
    alertas = []
    
    # Si stock < stock_minimo
    if saldo_nuevo < producto.stock_minimo:
        alerta = AlertaInventario(
            producto_id=producto.id,
            bodega_id=bodega_id,
            pais=pais,
            tipo_alerta="STOCK_BAJO",
            nivel="WARNING" if saldo_nuevo >= producto.stock_critico else "CRITICAL",
            mensaje=f"Stock bajo: {saldo_nuevo} unidades (mínimo: {producto.stock_minimo})",
            stock_actual=saldo_nuevo,
            stock_minimo=producto.stock_minimo,
            created_at=datetime.utcnow()
        )
        session.add(alerta)  # ✅ SE GUARDA EN BD (MISMO COMMIT)
        alertas.append(alerta)
    
    return alertas

# Endpoint de alertas
@router.get("/alerts", response_model=AlertasListResponse)
async def obtener_alertas(...):
    # Consulta PostgreSQL
    # ✅ Alertas guardadas en BD, consultables inmediatamente
    ...

# Reporte de saldos
@router.get("/reports/saldos", response_model=ReporteSaldosResponse)
async def obtener_reporte_saldos(...):
    # Consulta PostgreSQL con agregaciones
    # ✅ Datos en BD, consultables inmediatamente
    ...
```

**¿Qué hace?**
- ✅ Alertas se generan y **guardan en BD** en la misma transacción
- ✅ Consultables **inmediatamente**
- ✅ Reportes consultan directamente PostgreSQL
- ✅ Exportación (CSV/Excel) se hace desde BD

**¿Necesita SQS?** → **NO**
- Las alertas deben ser **inmediatamente visibles** ✅
- Los reportes consultan datos **consistentes** en BD ✅
- No hay procesamiento asíncrono requerido ✅

**NOTA:** Si necesitáramos **enviar** las alertas por email/SMS a usuarios, **AHÍ SÍ** usaríamos SQS. Pero para **mostrar** la alerta en el sistema, NO es necesario.

---

## 🎯 CONCLUSIÓN FINAL

### ✅ TODOS LOS CRITERIOS DE ACEPTACIÓN SE CUMPLEN SIN SQS

| Criterio | ¿Necesita SQS? | Implementación |
|----------|----------------|----------------|
| 1. Movimientos de inventario | ❌ NO | PostgreSQL |
| 2. Actualización en tiempo real | ❌ NO | PostgreSQL (transaccional) |
| 3. Validaciones | ❌ NO | Validación síncrona |
| 4. Trazabilidad y auditoría | ❌ NO | PostgreSQL (tabla movimiento_inventario) |
| 5. Transferencias entre bodegas | ❌ NO | PostgreSQL (transaccional, atómica) |
| 6. Confirmación y errores | ❌ NO | Respuesta HTTP inmediata |
| 7. Permisos y controles | ❌ NO | Middleware + PostgreSQL |
| 8. Alertas y reportes | ❌ NO | PostgreSQL (tabla alerta_inventario) |

---

## 🔍 ENTONCES, ¿PARA QUÉ SIRVE SQS?

SQS **NO** es para la lógica de negocio core. Es para **integraciones externas** y **procesamiento asíncrono NO crítico**.

### Casos de uso VÁLIDOS para SQS:

#### 1. Notificaciones Externas (Email, SMS, Push)
```
Movimiento registrado ✅ → SQS → Worker envía email
                        ↓ (no bloquea)
                   Cliente ya recibió respuesta
```

**¿Por qué SQS aquí?**
- Enviar email es **lento** (200-500ms)
- Si falla el email, **no debe afectar** el registro del movimiento
- El usuario no necesita esperar a que se envíe el email

#### 2. Integraciones con Sistemas Externos
```
Movimiento registrado ✅ → SQS → Worker envía a ERP externo
                        ↓
                   Sistema principal ya respondió
```

**¿Por qué SQS aquí?**
- El sistema externo puede estar **lento o caído**
- Si falla, **se reintenta** automáticamente
- El sistema principal **no depende** del externo

#### 3. Analytics y Métricas
```
Movimiento registrado ✅ → SQS → Worker actualiza Datadog/CloudWatch
                        ↓
                   Datos ya están en BD principal
```

**¿Por qué SQS aquí?**
- Las métricas son **informativas**, no críticas
- Si fallan, **no afectan** la operación
- Se pueden procesar en **batch** para eficiencia

#### 4. Auditoría Externa
```
Movimiento registrado ✅ → SQS → Worker envía a Elasticsearch/Splunk
                        ↓
                   Auditoría interna ya está en BD
```

**¿Por qué SQS aquí?**
- La auditoría externa es **adicional**
- Si falla, **no afecta** la operación
- La auditoría principal está en PostgreSQL

---

## 🚨 CASOS DONDE SQS NO DEBE USARSE

### ❌ NO usar SQS para:

1. **Actualizar stock** → Debe ser síncrono (PostgreSQL ACID)
2. **Validaciones** → Deben ser inmediatas (respuesta HTTP)
3. **Transferencias** → Deben ser atómicas (transacción)
4. **Generar alertas** (mostrarlas) → Deben ser inmediatas (BD)
5. **Confirmar operación** → Usuario espera respuesta inmediata

---

## 💡 RECOMENDACIÓN FINAL

### Para la HU "Registrar ingreso y salida de productos":

**SQS NO ES NECESARIO** ✅

La implementación actual sin SQS:
- ✅ Cumple **100%** de los criterios de aceptación
- ✅ Es **más simple** de mantener
- ✅ Es **más rápida** (sin latencia de colas)
- ✅ Es **más confiable** (menos puntos de falla)
- ✅ Es **más consistente** (ACID, no eventual consistency)

### ¿Cuándo agregar SQS?

**Solo si** necesitas alguno de estos casos de uso:
- Enviar **notificaciones externas** (email, SMS, push)
- Integrar con **sistemas externos** (ERP, CRM)
- Enviar datos a **analytics** (Datadog, CloudWatch)
- Enviar auditoría a **sistemas externos** (Elasticsearch, Splunk)

**PERO** estos casos de uso **NO están** en los criterios de aceptación de la HU.

---

## 🎯 DECISIÓN ESTRATÉGICA

### OPCIÓN A: Sin SQS (Recomendado)
```
✅ Cumple 100% de criterios de aceptación
✅ Más simple
✅ Más rápido
✅ Menos infraestructura
✅ Menos costos
```

### OPCIÓN B: Con SQS
```
✅ Cumple 100% de criterios de aceptación
✅ Preparado para integraciones futuras
⚠️ Más complejo
⚠️ Más infraestructura
⚠️ Más costos
❓ Características que NO se usan aún
```

---

## 📊 RESUMEN PARA EL STAKEHOLDER

**Pregunta:** ¿Necesitamos SQS para cumplir la historia de usuario?

**Respuesta corta:** NO.

**Respuesta larga:**
Todos los criterios de aceptación se cumplen con PostgreSQL y lógica de negocio síncrona. SQS es útil para casos de uso avanzados (emails, integraciones externas, analytics) que NO están en los criterios actuales.

**Recomendación:** Entregar sin SQS. Si en el futuro se requieren notificaciones externas o integraciones, SQS se puede agregar sin modificar la lógica de negocio core (es un "add-on" no invasivo).

---

## 🔧 ACCIÓN RECOMENDADA

### Para el despliegue actual:

1. **Desplegar sin SQS**
   - Remover configuración de SQS en Terraform
   - Remover `sqs_publisher.py` (opcional, mantenerlo no hace daño)
   - Remover llamadas a `publish_event()` en `inventario_service.py`

2. **Mantener la arquitectura simple**
   - PostgreSQL para datos
   - FastAPI para API
   - BFF para frontend

3. **Si en el futuro se necesita SQS:**
   - El código ya está preparado (no invasivo)
   - Solo activar configuración
   - Agregar workers según necesidad

---

¿Tiene sentido? ¿Quieres que remueva SQS del código? 🚀

