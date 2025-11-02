# 📊 Análisis de Rutas: BFF-Venta → Catálogo-Service

## ✅ Configuración Actual (CORRECTA)

### 1. BFF-Venta construye URLs:
**Catalog endpoints:**
```
{catalogo_url}/api/catalog/items
{catalogo_url}/api/catalog/items/{id}
{catalogo_url}/api/catalog/items/{id}/inventario
{catalogo_url}/api/catalog/items/bulk-upload
{catalogo_url}/api/catalog/bulk-upload/status/{task_id}
```

**Inventory endpoints:**
```
{catalogo_url}/api/inventory/movements
{catalogo_url}/api/inventory/transfers
{catalogo_url}/api/inventory/movements/kardex
{catalogo_url}/api/inventory/movements/{id}/anular
{catalogo_url}/api/inventory/alerts
{catalogo_url}/api/inventory/alerts/{id}/marcar-leida
{catalogo_url}/api/inventory/reports/saldos
{catalogo_url}/api/inventory/bodega/{id}/productos
```

### 2. Variable de Entorno del BFF:
```
CATALOGO_SERVICE_URL = http://medisupply-dev-bff-venta-alb-XXXXX.us-east-1.elb.amazonaws.com/catalog
```

### 3. URLs Finales (lo que llega al ALB):
```
http://ALB/catalog/api/catalog/items
http://ALB/catalog/api/inventory/movements
...etc
```

### 4. Configuración del ALB (Terraform):
**Listener Rule:**
```terraform
path-pattern = ["/catalog/*", "/catalogo/*"]
→ rutea al target group: medisupply-dev-catalogo-tg (puerto 3000)
```

### 5. Lo que recibe el servicio de catálogo:
```
/catalog/api/catalog/items
/catalog/api/inventory/movements
...etc
```

### 6. Prefijos en catalogo-service/app/main.py:
```python
app.include_router(catalog_router, prefix="/catalog/api/catalog")
app.include_router(inventario_router, prefix="/catalog/api/inventory")
```

### 7. Endpoints en los routers:
**catalog.py:**
```python
@router.get("/items")          → /catalog/api/catalog/items ✅
@router.get("/items/{id}")     → /catalog/api/catalog/items/{id} ✅
@router.post("/items")         → /catalog/api/catalog/items ✅
...
```

**inventario.py:**
```python
@router.post("/movements")      → /catalog/api/inventory/movements ✅
@router.post("/transfers")      → /catalog/api/inventory/transfers ✅
@router.get("/movements/kardex") → /catalog/api/inventory/movements/kardex ✅
...
```

## 🎯 MAPEO COMPLETO DE RUTAS

| BFF Endpoint | BFF construye | URL Final (ALB) | Servicio recibe | Router final | ✅ |
|--------------|---------------|-----------------|-----------------|--------------|-----|
| `/api/v1/catalog/items` | `{url}/api/catalog/items` | `/catalog/api/catalog/items` | `/catalog/api/catalog/items` | `/catalog/api/catalog` + `/items` | ✅ |
| `/api/v1/inventory/movements` | `{url}/api/inventory/movements` | `/catalog/api/inventory/movements` | `/catalog/api/inventory/movements` | `/catalog/api/inventory` + `/movements` | ✅ |

## ✅ CONCLUSIÓN

**TODAS LAS RUTAS COINCIDEN PERFECTAMENTE** 🎉

El problema actual **NO es de configuración de rutas**, sino que:
1. La imagen Docker vieja aún está ejecutándose
2. Necesitamos forzar un nuevo despliegue con la imagen actualizada
3. O ejecutar el workflow de GitHub Actions manualmente

## 📝 Configuración de Puertos

- **Dockerfile:** Puerto 3000 ✅
- **ECS Task Definition:** Puerto 3000 ✅
- **Target Group:** Puerto 3000 ✅
- **Health check:** `/health` en puerto 3000 ✅

## 🔧 Próximos Pasos

1. ✅ Detener tasks viejas (YA HECHO)
2. ⏳ Esperar a que ECS cree nuevas tasks con la imagen actualizada
3. ✅ Verificar que las nuevas tasks usen los prefijos correctos
4. ✅ Probar endpoint: `http://ALB/api/v1/catalog/items`

