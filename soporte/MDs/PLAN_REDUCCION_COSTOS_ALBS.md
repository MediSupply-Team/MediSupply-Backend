# 📊 Plan de Reducción de Costos - Eliminación de ALBs

## Estado Actual: 4 ALBs (~$64-72/mes)

1. **BFF Venta ALB** (público) - $16-18/mes
2. **BFF Cliente ALB** (público) - $16-18/mes
3. **Orders ALB** (interno) - $16-18/mes ❌ ELIMINAR
4. **Cliente Service ALB** (interno) - $16-18/mes ❌ ELIMINAR

## Objetivo: 2 ALBs (~$32-36/mes)

**Ahorro potencial: $32-36/mes (50% reducción)**

---

## 🎯 Estrategia de Consolidación

### Opción 1: Usar Service Connect (RECOMENDADO)
- Los servicios internos (Orders, Cliente Service) se comunican directamente vía Service Connect
- Solo necesitas los 2 ALBs públicos (BFF Venta y BFF Cliente)
- Sin cambios en la arquitectura, solo quitas los ALBs internos

**Ventajas:**
- ✅ Menor latencia (sin pasar por ALB)
- ✅ Menos costos
- ✅ Service Connect ya está configurado
- ✅ No requiere cambios en el código

### Opción 2: Consolidar ALBs Públicos
- Usar 1 solo ALB público con path-based routing
- `/venta/*` → BFF Venta
- `/cliente/*` → BFF Cliente

**Ventajas:**
- ✅ Ahorro adicional de $16-18/mes
- ✅ 1 solo punto de entrada

**Desventajas:**
- ⚠️ Requiere cambios en rutas del frontend
- ⚠️ Mayor complejidad en routing

---

## 📝 Implementación Recomendada: Opción 1

### Paso 1: Verificar Service Connect está habilitado
Ya tienes configurado Service Connect en `main.tf`:
```terraform
service_connect_namespace_name = aws_service_discovery_private_dns_namespace.svc[0].name
```

### Paso 2: Modificar Orders Service
**Archivo:** `modules/orders/main.tf`

**Cambios:**
1. Comentar/eliminar el recurso `aws_lb` "orders_alb"
2. Comentar/eliminar el listener HTTP
3. Comentar/eliminar el target group
4. Mantener **solo el Service Connect** en la task definition

**Resultado:** Orders será accesible vía `http://orders.svc.local:8000`

### Paso 3: Modificar Cliente Service
**Archivo:** `modules/cliente-service/main.tf`

**Cambios:**
1. Comentar/eliminar el recurso `aws_lb` "cliente_alb"
2. Comentar/eliminar el listener HTTP
3. Comentar/eliminar el target group
4. Mantener **solo el Service Connect**

**Resultado:** Cliente será accesible vía `http://cliente.svc.local:8000`

### Paso 4: Actualizar Referencias en main.tf
**Archivo:** `main.tf`

**BFF Cliente - Cambiar URL de cliente_service_url:**
```terraform
# ANTES:
cliente_service_url = local.is_local ? "http://cliente:8000" : "http://${module.cliente_service.alb_dns_name}"

# DESPUÉS:
cliente_service_url = local.is_local ? "http://cliente:8000" : "http://cliente.svc.local:8000"
```

**BFF Venta - Cambiar URL de orders_service_url:**
```terraform
# ANTES:
orders_service_url = "http://${module.orders.alb_dns_name}"

# DESPUÉS:
orders_service_url = "http://orders.svc.local:8000"
```

### Paso 5: Aplicar cambios
```bash
cd infra/terraform
terraform plan -var-file=deploy.tfvars
terraform apply -var-file=deploy.tfvars
```

---

## 🔍 Verificación Post-Implementación

### 1. Verificar que los servicios están registrados en Service Connect:
```bash
aws ecs list-services --cluster orders-cluster
aws servicediscovery list-services
```

### 2. Probar conectividad interna:
```bash
# Conectarse a un contenedor BFF Venta
aws ecs execute-command --cluster orders-cluster \
  --task <task-id> \
  --container bff-venta \
  --interactive \
  --command "/bin/sh"

# Dentro del contenedor, probar:
curl http://orders.svc.local:8000/health
curl http://cliente.svc.local:8000/health
```

### 3. Verificar logs en CloudWatch
```bash
aws logs tail /ecs/medisupply-dev-bff-venta --follow
aws logs tail /ecs/medisupply-dev-orders --follow
```

---

## 📊 Costos Proyectados

### Antes (4 ALBs):
- BFF Venta ALB: $16-18/mes
- BFF Cliente ALB: $16-18/mes
- Orders ALB: $16-18/mes
- Cliente ALB: $16-18/mes
- **TOTAL: $64-72/mes**

### Después (2 ALBs):
- BFF Venta ALB: $16-18/mes
- BFF Cliente ALB: $16-18/mes
- **TOTAL: $32-36/mes**

### **AHORRO: $32-36/mes (50%)**

---

## ⚠️ Consideraciones Importantes

1. **Service Connect debe estar habilitado** en todos los servicios que necesitan comunicarse
2. **Health checks** cambiarán de ALB a ECS service health checks
3. **DNS interno** `.svc.local` solo funciona dentro de la VPC
4. **Métricas de ALB** ya no estarán disponibles para servicios internos (usa métricas de ECS)

---

## 🚀 Alternativa Adicional (Opcional)

Si además quieres consolidar los 2 ALBs públicos en 1 solo:

### Ahorro adicional: $16-18/mes más
### Total con 1 solo ALB: $48-54/mes ahorrados

**Arquitectura final:**
```
Internet
    ↓
[1 ALB Único]
    ├── /venta/*  → BFF Venta (ECS)
    └── /cliente/* → BFF Cliente (ECS)
        ↓
    Service Connect (interno)
        ├── orders.svc.local
        ├── cliente.svc.local
        └── catalogo.svc.local
```

---

## 📌 Próximos Pasos

1. ✅ Revisar este plan
2. ⬜ Hacer backup de la configuración actual
3. ⬜ Implementar cambios en Terraform
4. ⬜ Aplicar en ambiente de desarrollo primero
5. ⬜ Validar funcionalidad
6. ⬜ Aplicar en producción (si aplica)

📊 Resumen Rápido:
Sí, eliminar 2 balanceadores te ahorrará ~$32-36/mes (50% de reducción en costos de ALB)

Tu situación actual:
✅ BFF Venta ALB (público) - MANTENER
✅ BFF Cliente ALB (público) - MANTENER
❌ Orders ALB (interno) - ELIMINAR
❌ Cliente Service ALB (interno) - ELIMINAR
La solución:
Usar Service Connect (que ya tienes configurado) para comunicación interna entre servicios. Los servicios internos no necesitan ALB porque no reciben tráfico desde internet.

Cambios necesarios:
Los servicios Orders y Cliente Service se comunican vía http://orders.svc.local:8000 y http://cliente.svc.local:8000
Eliminar los ALBs internos de estos servicios
Mantener solo los 2 ALBs públicos (BFF Venta y BFF Cliente)
Beneficios adicionales:
💰 Ahorro: $32-36/mes
⚡ Menor latencia (sin pasar por ALB)
🔒 Más seguro (servicios internos no expuestos)