# 🧪 GUÍA DE PRUEBAS - VENDEDOR Y PLAN DE VENTA

## 📋 Pre-requisitos

- Docker y Docker Compose instalados
- Postman, Insomnia o REST Client (VS Code)
- Archivo `.env` configurado

---

## 🚀 PASO 1: Levantar entorno local

### 1.1 Configurar variables de entorno

Crear archivo `.env` en la raíz del proyecto:

```bash
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123

# Redis
REDIS_PASSWORD=redis

# Orders Service
PORT=8000
DATABASE_URL=postgresql+asyncpg://orders_user:orders_pass@orders-db:5432/orders

# AWS (para SQS - opcional)
AWS_REGION=us-east-1
SQS_QUEUE_URL=your-queue-url-here

# App Profile
APP_PROFILE=dev

# Flask
FLASK_ENV=development
```

### 1.2 Levantar servicios

```bash
# Desde la raíz del proyecto MediSupply-Backend

# Opción 1: Levantar todos los servicios
docker-compose --profile dev up -d

# Opción 2: Levantar solo lo necesario para vendedores
docker-compose up -d redis cliente-db cliente-service catalog-db catalog-service
```

### 1.3 Verificar que los servicios estén funcionando

```bash
# Ver logs de cliente-service
docker-compose logs -f cliente-service

# Verificar salud de los servicios
curl http://localhost:8002/health       # Cliente Service (BFF)
curl http://localhost:3003/health       # Cliente Service (directo)
curl http://localhost:3001/health       # Catalog Service
```

**Mapeo de puertos:**
- `8002` → BFF Cliente (Flask) → Cliente Service
- `3003` → Cliente Service (FastAPI directo)
- `3001` → Catalog Service (FastAPI)
- `5435` → Base de datos cliente-service (PostgreSQL)
- `5433` → Base de datos catalogo-service (PostgreSQL)

---

## 🧪 PASO 2: Poblar base de datos (Automático)

Al levantar `cliente-service`, el script `populate_db.py` se ejecuta automáticamente y:

1. ✅ Crea todas las tablas
2. ✅ Ejecuta migraciones SQL (001_init.sql, 002_vendedores.sql, etc.)
3. ✅ Carga datos de ejemplo (catálogos, vendedores, clientes)

**Verificar que se ejecutó correctamente:**

```bash
# Ver logs del contenedor
docker-compose logs cliente-service | grep "Migración"

# Deberías ver:
# ✅ Migración 001: Estructura inicial
# ✅ Migración 002: Vendedores
# ✅ Migración 003: UUID y rol
# ✅ Migración 004: Catálogos (Fase 1)
# ✅ Migración 005: Vendedor extendido (Fase 2)
# ✅ Migración 006: Plan de Venta (Fase 3)
```

---

## 🔬 PASO 3: Probar endpoints (Orden recomendado)

### **IMPORTANTE: Usar puerto 8002 (BFF) o 3003 (Directo)**

Los ejemplos usarán `localhost:3003` (directo) para simplificar. Si usas BFF, cambia a `localhost:8002`.

---

### 3.1 **Listar catálogos pre-cargados**

```bash
# Tipos de Rol Vendedor (pre-cargado: GERENTE_REG, VENDEDOR_SR, etc.)
curl http://localhost:3003/api/v1/catalogos/tipos-rol

# Territorios (pre-cargado: BOG-NORTE, BOG-SUR, etc.)
curl http://localhost:3003/api/v1/catalogos/territorios

# Tipos de Plan (pre-cargado: PLAN_PREMIUM, PLAN_BASICO, etc.)
curl http://localhost:3003/api/v1/catalogos/tipos-plan

# Regiones (pre-cargado: REG-CENTRAL, REG-CARIBE, etc.)
curl http://localhost:3003/api/v1/catalogos/regiones

# Zonas (pre-cargado: ZONA-NORTE-BOG, ZONA-SUR-BOG, etc.)
curl http://localhost:3003/api/v1/catalogos/zonas
```

**📝 Guardar IDs** de los catálogos que usarás para crear el vendedor.

---

### 3.2 **Crear un vendedor CON plan completo**

```bash
curl -X POST http://localhost:3003/api/v1/vendedores \
  -H "Content-Type: application/json" \
  -d '{
    "identificacion": "9876543210",
    "nombre_completo": "María García López",
    "email": "maria.garcia@medisupply.com",
    "telefono": "+57-311-9876543",
    "pais": "CO",
    "username": "mgarcia",
    "rol": "seller",
    "rol_vendedor_id": "UUID-DEL-ROL-AQUI",
    "territorio_id": "UUID-DEL-TERRITORIO-AQUI",
    "fecha_ingreso": "2024-11-01",
    "observaciones": "Vendedora nueva con potencial",
    "activo": true,
    "plan_venta": {
      "tipo_plan_id": "UUID-DEL-TIPO-PLAN-AQUI",
      "nombre_plan": "Plan Starter Q4 2024",
      "fecha_inicio": "2024-11-01",
      "fecha_fin": "2024-12-31",
      "meta_ventas": 80000.00,
      "comision_base": 5.0,
      "estructura_bonificaciones": {
        "80": 1,
        "90": 3,
        "100": 7
      },
      "observaciones": "Plan inicial para vendedora nueva",
      "productos": [
        {
          "producto_id": "PROD001",
          "meta_cantidad": 50,
          "precio_unitario": 1600.00
        }
      ],
      "region_ids": ["UUID-REGION-AQUI"],
      "zona_ids": ["UUID-ZONA-AQUI"]
    }
  }'
```

**✅ Respuesta esperada:** JSON con el vendedor creado y **`plan_venta_id`**.

**📝 Guardar:** `id` del vendedor y `plan_venta_id`.

---

### 3.3 **Listar vendedores**

```bash
# Listar todos los vendedores activos
curl http://localhost:3003/api/v1/vendedores?activo=true&page=1&size=50

# Buscar por nombre
curl http://localhost:3003/api/v1/vendedores?q=María

# Filtrar por país
curl http://localhost:3003/api/v1/vendedores?pais=CO
```

**Verás:** Lista con `plan_venta_id` pero SIN el plan completo.

---

### 3.4 **Obtener vendedor básico**

```bash
curl http://localhost:3003/api/v1/vendedores/{VENDEDOR_ID}
```

**Verás:** Vendedor con `plan_venta_id`, pero SIN plan completo.

---

### 3.5 **Obtener DETALLE COMPLETO del vendedor** ⭐

```bash
curl http://localhost:3003/api/v1/vendedores/{VENDEDOR_ID}/detalle
```

**Verás:** Vendedor con TODO el plan completo incluyendo:
- ✅ Tipo de plan (objeto completo)
- ✅ Productos asignados (solo `producto_id`, sin nombre)
- ✅ Regiones asignadas (objetos completos)
- ✅ Zonas asignadas (objetos completos)
- ✅ Estructura de bonificaciones

---

### 3.6 **Actualizar vendedor**

```bash
curl -X PUT http://localhost:3003/api/v1/vendedores/{VENDEDOR_ID} \
  -H "Content-Type: application/json" \
  -d '{
    "telefono": "+57-311-1111111",
    "observaciones": "Actualización de contacto",
    "activo": true
  }'
```

---

### 3.7 **Listar clientes del vendedor**

```bash
curl http://localhost:3003/api/v1/vendedores/{VENDEDOR_ID}/clientes
```

---

### 3.8 **Desactivar vendedor (soft delete)**

```bash
curl -X DELETE http://localhost:3003/api/v1/vendedores/{VENDEDOR_ID}
```

---

## 📊 PASO 4: Verificar en base de datos

```bash
# Conectarse a la base de datos
docker exec -it cliente-db psql -U cliente_user -d cliente_db

# Consultas útiles
\dt                                      # Listar tablas

SELECT * FROM vendedor;                  # Ver vendedores
SELECT * FROM plan_venta;                # Ver planes
SELECT * FROM plan_producto;             # Ver productos asignados
SELECT * FROM plan_region;               # Ver regiones asignadas
SELECT * FROM plan_zona;                 # Ver zonas asignadas

# Query completa para ver vendedor con plan
SELECT 
    v.id as vendedor_id,
    v.nombre_completo,
    v.email,
    pv.id as plan_id,
    pv.nombre_plan,
    pv.meta_ventas,
    pv.comision_base
FROM vendedor v
LEFT JOIN plan_venta pv ON v.id = pv.vendedor_id
WHERE v.activo = true;

# Ver productos del plan
SELECT 
    pp.producto_id,
    pp.meta_cantidad,
    pp.precio_unitario,
    (pp.meta_cantidad * pp.precio_unitario) as total_producto
FROM plan_producto pp
WHERE pp.plan_venta_id = 'UUID-DEL-PLAN';

# Salir
\q
```

---

## 🐛 TROUBLESHOOTING

### Problema: "Service cliente-service no inicia"

```bash
# Ver logs detallados
docker-compose logs cliente-service

# Verificar base de datos
docker exec -it cliente-db pg_isready -U cliente_user -d cliente_db

# Recrear servicio
docker-compose down cliente-service
docker-compose up -d cliente-service
```

### Problema: "No hay catálogos pre-cargados"

```bash
# Ejecutar populate_db manualmente
docker-compose exec cliente-service python -m app.populate_db

# O reconstruir contenedor
docker-compose down cliente-service
docker-compose up -d --build cliente-service
```

### Problema: "Error de FK al crear vendedor"

**Causa:** Los UUIDs de catálogos son incorrectos.

**Solución:**
1. Listar catálogos y copiar IDs exactos
2. Usar esos IDs en el JSON de creación

### Problema: "plan_venta_id es null"

**Causa:** El plan no se creó (error en cascada).

**Solución:**
1. Ver logs: `docker-compose logs cliente-service | grep "ERROR"`
2. Verificar que todos los IDs de catálogos existan
3. Verificar fechas del plan (fecha_fin >= fecha_inicio)

---

## 📝 NOTAS IMPORTANTES

1. **IDs de productos:** Solo se guarda `producto_id`. El frontend debe consultar `/api/v1/productos/{producto_id}` en `catalog-service` para obtener nombre, descripción, etc.

2. **Lazy loading:** El plan completo solo se carga en `/vendedores/{id}/detalle`, no en listados ni GET básico.

3. **UUIDs:** Todos los IDs son UUIDs autogenerados. No se envían en el body al crear.

4. **Transacciones:** La creación de vendedor + plan + productos + regiones + zonas es atómica (todo o nada).

5. **Soft delete:** `DELETE` marca como `activo=false`, no elimina físicamente.

---

## 🎯 CHECKLIST DE PRUEBAS COMPLETO

- [ ] ✅ Servicios levantados y saludables
- [ ] ✅ Migraciones ejecutadas correctamente
- [ ] ✅ Catálogos pre-cargados (tipos-rol, territorios, tipos-plan, regiones, zonas)
- [ ] ✅ Crear vendedor SIN plan (opcional)
- [ ] ✅ Crear vendedor CON plan completo
- [ ] ✅ Listar vendedores (verificar plan_venta_id presente)
- [ ] ✅ GET vendedor básico (verificar plan_venta_id presente)
- [ ] ✅ GET vendedor detalle (verificar plan completo)
- [ ] ✅ Actualizar vendedor
- [ ] ✅ Listar clientes del vendedor
- [ ] ✅ Desactivar vendedor
- [ ] ✅ Verificar datos en PostgreSQL

---

## 📚 RECURSOS ADICIONALES

- **Swagger UI Cliente:** http://localhost:3003/docs
- **Swagger UI Catalogo:** http://localhost:3001/docs
- **Archivo de tests:** `test-vendedor.http` (usar con REST Client en VS Code)
- **Logs en tiempo real:** `docker-compose logs -f cliente-service`

---

¡Buena suerte con las pruebas! 🚀

