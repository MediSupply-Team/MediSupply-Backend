# 🚀 GUÍA RÁPIDA PARA PROBAR INVENTARIO LOCALMENTE

## ⚡ INICIO RÁPIDO (2 minutos)

### 1️⃣ Iniciar Base de Datos

```bash
cd /Users/nicolasibarra/uniandes/miso-uniandes/semestre4/ciclo\ 2/proyecto\ final\ 2/MediSupply-Backend

# Iniciar PostgreSQL
docker-compose up -d catalog-db

# Esperar 5 segundos
sleep 5
```

### 2️⃣ Iniciar Catalogo-Service

```bash
cd catalogo-service

# Activar entorno virtual
source venv/bin/activate

# Configurar variables de entorno
export DATABASE_URL="postgresql+asyncpg://catalog_user:catalog_pass@localhost:5433/catalogo_db"
export API_PREFIX="/api"

# SQS está deshabilitado (NO configurar SQS_QUEUE_URL)
# Esto es normal y esperado para desarrollo local

# Iniciar servicio
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Espera a ver este log:**
```
INFO: 🔕 SQS Publisher deshabilitado (SQS_QUEUE_URL no configurado)
INFO: Application startup complete.
```

✅ **Si ves esto, todo está correcto!**

### 3️⃣ Ejecutar Pruebas (en otra terminal)

```bash
cd /Users/nicolasibarra/uniandes/miso-uniandes/semestre4/ciclo\ 2/proyecto\ final\ 2/MediSupply-Backend

# Ejecutar todos los escenarios
./test-scenarios-inventario.sh
```

---

## 📋 ESCENARIOS QUE SE PROBARÁN

El script ejecuta automáticamente:

1. **✅ Flujo Básico**
   - Ingreso de 100 unidades
   - Salida de 30 unidades
   - Consulta de kardex

2. **⚠️ Validación de Stock**
   - Intento de salida mayor al disponible
   - Verificación de rechazo

3. **🔄 Transferencias**
   - Transferir entre bodegas
   - Verificar saldos en origen y destino

4. **🚨 Alertas**
   - Reducir stock a nivel crítico
   - Verificar generación de alertas

5. **↩️ Anulaciones**
   - Crear movimiento
   - Anular y revertir stock

6. **📊 Reportes**
   - Generar reporte de saldos

7. **🔒 Concurrencia**
   - 2 ventas simultáneas
   - Verificar locks (SELECT FOR UPDATE)

---

## 🐛 TROUBLESHOOTING

### Problema: "catalogo-service no responde"

**Solución:**
```bash
# Verificar que Docker esté corriendo
docker ps | grep catalog-db

# Si no está, iniciarlo
cd /path/to/MediSupply-Backend
docker-compose up -d catalog-db
```

### Problema: "Connection refused" al iniciar uvicorn

**Solución:**
```bash
# Verificar que el puerto 8000 esté libre
lsof -i :8000

# Si hay algo corriendo, matarlo
kill -9 <PID>
```

### Problema: "Table does not exist"

**Solución:**
```bash
# Recrear base de datos
cd catalogo-service
python app/create_catalogo_db.py
python app/populate_db.py
```

---

## 🎯 PRUEBAS MANUALES ADICIONALES

### Probar un endpoint específico:

```bash
# Crear ingreso
curl -X POST http://localhost:8000/api/inventory/movements \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD001",
    "bodega_id": "BOG_CENTRAL",
    "pais": "CO",
    "lote": "TEST-001",
    "tipo_movimiento": "INGRESO",
    "motivo": "COMPRA",
    "cantidad": 50,
    "fecha_vencimiento": "2025-12-31",
    "usuario_id": "TEST_USER"
  }'

# Consultar kardex
curl "http://localhost:8000/api/inventory/movements/kardex?producto_id=PROD001&bodega_id=BOG_CENTRAL&pais=CO" | jq

# Ver alertas
curl "http://localhost:8000/api/inventory/alerts" | jq

# Reporte de saldos
curl "http://localhost:8000/api/inventory/reports/saldos?pais=CO" | jq
```

---

## 📊 VERIFICAR EN BASE DE DATOS

```bash
# Conectarse a PostgreSQL
docker exec -it $(docker ps -qf "name=catalog-db") \
  psql -U catalog_user -d catalogo_db

# Ver movimientos
SELECT id, producto_id, tipo_movimiento, cantidad, saldo_nuevo, created_at 
FROM movimiento_inventario 
ORDER BY created_at DESC 
LIMIT 10;

# Ver inventario actual
SELECT producto_id, bodega_id, lote, cantidad 
FROM inventario 
ORDER BY producto_id, bodega_id;

# Ver alertas
SELECT id, producto_id, bodega_id, tipo_alerta, nivel, mensaje, leida 
FROM alerta_inventario 
ORDER BY created_at DESC 
LIMIT 10;

# Salir
\q
```

---

## 🎓 CONCEPTOS IMPORTANTES

### SQS Deshabilitado = ✅ Normal

Para desarrollo local, **NO necesitas SQS**.

**¿Qué sigue funcionando?**
- ✅ Todos los endpoints
- ✅ Actualización de stock
- ✅ Validaciones
- ✅ Transferencias
- ✅ Alertas
- ✅ Kardex
- ✅ Reportes

**¿Qué NO funciona?**
- ❌ Notificaciones externas (email, SMS)
- ❌ Integraciones con sistemas externos
- ❌ Analytics en tiempo real

**Pero estos NO están en los criterios de aceptación**, así que está bien.

### Locks (SELECT FOR UPDATE)

El código implementa **locks automáticamente** en operaciones de salida.

**¿Cómo saber si funciona?**
- Ejecuta el Escenario 7 (concurrencia)
- Solo 1 de 2 requests simultáneos debe ser aprobado
- Si ambos son aprobados, hay un problema

---

## 📚 DOCUMENTACIÓN ADICIONAL

- **ENDPOINTS-INVENTARIO.md** → Documentación completa de endpoints
- **GUIA-PRUEBAS-LOCALES.md** → Guía detallada de pruebas
- **SOLUCION-CONCURRENCIA.md** → Cómo funcionan los locks
- **ANALISIS-CRITICO-SQS.md** → Por qué SQS no es necesario

---

## ✅ CHECKLIST ANTES DE DESPLEGAR

- [ ] Todos los escenarios pasan
- [ ] No hay errores en logs
- [ ] Base de datos consistente
- [ ] Locks funcionan (Escenario 7)
- [ ] Alertas se generan correctamente
- [ ] Transferencias son atómicas

---

¿Listo para probar? 🚀

```bash
./test-scenarios-inventario.sh
```

