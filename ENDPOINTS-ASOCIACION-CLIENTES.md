# 📋 Endpoints de Asociación de Clientes y Vendedores

## 🎯 Endpoints Implementados (2)

---

## 1️⃣ Listar Clientes Sin Vendedor

**Descripción:** Obtiene la lista de todos los clientes que NO tienen un vendedor asignado.

### Endpoint
```
GET http://localhost:8002/api/v1/cliente/sin-vendedor
```

### Parámetros Query (opcionales)
| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `limite` | int | 50 | Número máximo de clientes a retornar (1-500) |
| `offset` | int | 0 | Número de registros a saltar (paginación) |
| `activos_solo` | bool | true | Si mostrar solo clientes activos |

### Ejemplos de Uso

#### Ejemplo 1: Listar todos los clientes sin vendedor (solo activos)
```bash
curl http://localhost:8002/api/v1/cliente/sin-vendedor
```

#### Ejemplo 2: Listar incluyendo clientes inactivos
```bash
curl "http://localhost:8002/api/v1/cliente/sin-vendedor?activos_solo=false"
```

#### Ejemplo 3: Con paginación
```bash
curl "http://localhost:8002/api/v1/cliente/sin-vendedor?limite=10&offset=0"
```

### Respuesta Exitosa (200)
```json
[
  {
    "id": "47e050ee-08e4-45b5-9cc0-1f2c56cb9fa4",
    "nit": "999888777-6",
    "nombre": "Farmacia BFF Test Sin Vendedor",
    "codigo_unico": "XSF738",
    "email": "sinvendedor@bfftest.com",
    "telefono": "+57-300-9999999",
    "direccion": "Calle BFF Test 999",
    "ciudad": "Cali",
    "pais": "CO",
    "activo": true,
    "vendedor_id": null,
    "rol": "cliente",
    "created_at": "2025-11-18T01:22:01.212295",
    "updated_at": "2025-11-18T01:22:01.212299"
  },
  {
    "id": "2295c9c3-d7d4-45db-857b-3d8da53a75d6",
    "nit": "666777888-9",
    "nombre": "Farmacia Auto Código Test 2",
    "codigo_unico": "MUY729",
    "email": "autocodigo2@test.com",
    "telefono": "+57-300-2222222",
    "direccion": "Calle Auto 222",
    "ciudad": "Medellín",
    "pais": "CO",
    "activo": true,
    "vendedor_id": null,
    "rol": "cliente",
    "created_at": "2025-11-18T01:35:05.960988",
    "updated_at": "2025-11-18T01:35:05.960993"
  }
]
```

### Casos de Uso
- 📊 Reportes de cobertura de vendedores
- 🔍 Identificar clientes sin asignar
- 📝 Dashboard de administración
- 🎯 Asignación masiva de vendedores

---

## 2️⃣ Asociar Clientes a un Vendedor

**Descripción:** Asocia múltiples clientes a un vendedor específico. Solo asocia clientes que:
- Existen en el sistema
- Están activos
- NO tienen vendedor previamente asignado

### Endpoint
```
POST http://localhost:8002/api/v1/vendedores/{vendedor_id}/clientes/asociar
```

### Parámetros URL
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `vendedor_id` | UUID | Sí | ID del vendedor (UUID) |

### Body Request
```json
{
  "clientes_ids": [
    "uuid-cliente-1",
    "uuid-cliente-2",
    "uuid-cliente-3"
  ]
}
```

### Ejemplos de Uso

#### Ejemplo 1: Asociar 2 clientes al vendedor Carlos Mendoza
```bash
curl -X POST "http://localhost:8002/api/v1/vendedores/11111111-1111-1111-1111-111111111111/clientes/asociar" \
  -H "Content-Type: application/json" \
  -d '{
    "clientes_ids": [
      "47e050ee-08e4-45b5-9cc0-1f2c56cb9fa4",
      "2295c9c3-d7d4-45db-857b-3d8da53a75d6"
    ]
  }'
```

#### Ejemplo 2: Asociar clientes al vendedor María Fernández
```bash
curl -X POST "http://localhost:8002/api/v1/vendedores/22222222-2222-2222-2222-222222222222/clientes/asociar" \
  -H "Content-Type: application/json" \
  -d '{
    "clientes_ids": [
      "3fdbd798-77a2-4f15-80ab-6fa315b8ad86",
      "51d74c64-7cc2-4629-ad2d-15a0d0267d13"
    ]
  }'
```

#### Ejemplo 3: Asociar clientes al vendedor Andrés Ramírez
```bash
curl -X POST "http://localhost:8002/api/v1/vendedores/33333333-3333-3333-3333-333333333333/clientes/asociar" \
  -H "Content-Type: application/json" \
  -d '{
    "clientes_ids": [
      "a147ff35-1822-4fd6-a879-ce3a686e4008"
    ]
  }'
```

### Respuesta Exitosa (200)
```json
{
  "vendedor_id": "11111111-1111-1111-1111-111111111111",
  "vendedor_nombre": "Carlos Mendoza Pérez",
  "clientes_asociados": 2,
  "clientes_no_encontrados": [],
  "clientes_inactivos": [],
  "clientes_con_vendedor": [],
  "mensaje": "2 cliente(s) asociado(s) exitosamente"
}
```

### Respuesta con Validaciones (200)
Cuando algunos clientes no se pueden asociar:
```json
{
  "vendedor_id": "11111111-1111-1111-1111-111111111111",
  "vendedor_nombre": "Carlos Mendoza Pérez",
  "clientes_asociados": 1,
  "clientes_no_encontrados": [
    "00000000-0000-0000-0000-000000000000"
  ],
  "clientes_inactivos": [
    "aaaaaaaa-aaaa-aaaa-aaaa-000000000001"
  ],
  "clientes_con_vendedor": [
    "bbbbbbbb-bbbb-bbbb-bbbb-000000000004"
  ],
  "mensaje": "1 cliente(s) asociado(s) exitosamente. 1 cliente(s) no encontrado(s). 1 cliente(s) inactivo(s). 1 cliente(s) ya tenían vendedor asociado"
}
```

### Errores Posibles

#### Error 400: Vendedor ID inválido
```json
{
  "error": "INVALID_VENDEDOR_UUID",
  "message": "ID de vendedor 'abc123' no es un UUID válido"
}
```

#### Error 404: Vendedor no encontrado
```json
{
  "error": "VENDEDOR_NOT_FOUND",
  "message": "Vendedor 99999999-9999-9999-9999-999999999999 no encontrado"
}
```

#### Error 400: Vendedor inactivo
```json
{
  "error": "VENDEDOR_INACTIVE",
  "message": "Vendedor Carlos Mendoza Pérez está inactivo y no puede tener clientes asociados"
}
```

### Validaciones Realizadas

| Validación | Descripción | Acción |
|------------|-------------|--------|
| ✅ Vendedor existe | Verifica que el vendedor exista en BD | Error 404 si no existe |
| ✅ Vendedor activo | Verifica que `activo = true` | Error 400 si inactivo |
| ✅ Cliente existe | Verifica que cada cliente exista | Se reporta en `clientes_no_encontrados` |
| ✅ Cliente activo | Verifica que `activo = true` | Se reporta en `clientes_inactivos` |
| ✅ Cliente sin vendedor | Verifica que `vendedor_id = null` | Se reporta en `clientes_con_vendedor` |
| ✅ UUIDs válidos | Valida formato UUID | Se reporta en `clientes_no_encontrados` |

### Casos de Uso
- 📦 Asignación masiva de clientes nuevos
- 🔄 Redistribución de cartera de clientes
- 👥 Onboarding de nuevos vendedores
- 📊 Balanceo de carga entre vendedores

---

## 🔄 Flujo Completo de Uso

### Paso 1: Listar clientes sin vendedor
```bash
curl http://localhost:8002/api/v1/cliente/sin-vendedor
```

### Paso 2: Copiar los IDs de los clientes a asignar
```json
[
  {"id": "47e050ee-08e4-45b5-9cc0-1f2c56cb9fa4", "nombre": "Farmacia A"},
  {"id": "2295c9c3-d7d4-45db-857b-3d8da53a75d6", "nombre": "Farmacia B"}
]
```

### Paso 3: Asociar clientes a un vendedor
```bash
curl -X POST "http://localhost:8002/api/v1/vendedores/11111111-1111-1111-1111-111111111111/clientes/asociar" \
  -H "Content-Type: application/json" \
  -d '{
    "clientes_ids": [
      "47e050ee-08e4-45b5-9cc0-1f2c56cb9fa4",
      "2295c9c3-d7d4-45db-857b-3d8da53a75d6"
    ]
  }'
```

### Paso 4: Verificar asociación
```bash
# Ver clientes del vendedor
curl "http://localhost:8002/api/v1/vendedores/11111111-1111-1111-1111-111111111111/clientes"

# Ver clientes restantes sin vendedor
curl "http://localhost:8002/api/v1/cliente/sin-vendedor"
```

---

## 📊 Vendedores Precargados

| ID | Nombre | Email |
|----|--------|-------|
| `11111111-1111-1111-1111-111111111111` | Carlos Mendoza Pérez | carlos.mendoza@medisupply.com |
| `22222222-2222-2222-2222-222222222222` | María Fernández López | maria.fernandez@medisupply.com |
| `33333333-3333-3333-3333-333333333333` | Andrés Ramírez Silva | andres.ramirez@medisupply.com |

---

## 🧪 Scripts de Prueba

### Script completo de prueba con jq
```bash
#!/bin/bash

echo "1️⃣ Listar clientes sin vendedor"
curl -s "http://localhost:8002/api/v1/cliente/sin-vendedor" | jq '.[] | {id, nombre, vendedor_id}'

echo ""
echo "2️⃣ Asociar clientes al vendedor Carlos Mendoza"
curl -s -X POST "http://localhost:8002/api/v1/vendedores/11111111-1111-1111-1111-111111111111/clientes/asociar" \
  -H "Content-Type: application/json" \
  -d '{
    "clientes_ids": [
      "47e050ee-08e4-45b5-9cc0-1f2c56cb9fa4",
      "2295c9c3-d7d4-45db-857b-3d8da53a75d6"
    ]
  }' | jq '.'

echo ""
echo "3️⃣ Verificar clientes del vendedor"
curl -s "http://localhost:8002/api/v1/vendedores/11111111-1111-1111-1111-111111111111/clientes" | jq '.'

echo ""
echo "4️⃣ Verificar clientes restantes sin vendedor"
curl -s "http://localhost:8002/api/v1/cliente/sin-vendedor" | jq 'length'
```

---

## ⚙️ Notas Técnicas

### Performance
- ✅ Asociación múltiple en una sola transacción
- ✅ Validación de UUIDs antes de consultas
- ✅ Paginación en listado de clientes sin vendedor
- ✅ Índices en `vendedor_id` para búsquedas rápidas

### Seguridad
- ✅ Validación de UUIDs
- ✅ Validación de existencia de entidades
- ✅ Logs de auditoría para trazabilidad
- ✅ Respuestas detalladas sin exponer información sensible

### Idempotencia
- ✅ Se puede ejecutar múltiples veces
- ✅ Clientes ya asociados se reportan, no fallan
- ✅ No se pierden datos en reintentos

---

## 📝 Changelog

### v1.0.0 (2025-11-18)
- ✅ Endpoint para listar clientes sin vendedor
- ✅ Endpoint para asociar múltiples clientes a vendedor
- ✅ Validación de clientes sin vendedor previo
- ✅ Reportes detallados de éxitos y fallos
- ✅ Generación automática de `codigo_unico`

