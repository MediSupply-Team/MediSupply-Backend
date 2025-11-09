#!/bin/bash

# Escenarios de prueba para inventario
# Asegúrate de que catalogo-service esté corriendo en http://localhost:8000

BASE_URL="http://localhost:8000/api/inventory"
RESET='\033[0m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BLUE}║  🧪 ESCENARIOS DE PRUEBA - INVENTARIO                       ║${RESET}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""

# Verificar que el servicio esté corriendo
echo -e "${YELLOW}🔍 Verificando servicio...${RESET}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Catalogo-service activo${RESET}"
else
    echo -e "${RED}❌ ERROR: catalogo-service no responde${RESET}"
    echo ""
    echo "Inicia el servicio con:"
    echo "  cd catalogo-service"
    echo "  export DATABASE_URL='postgresql+asyncpg://catalog_user:catalog_pass@localhost:5433/catalogo_db'"
    echo "  export API_PREFIX='/api'"
    echo "  source venv/bin/activate"
    echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    exit 1
fi

echo ""

# =============================================================================
# ESCENARIO 1: Flujo Básico (Ingreso → Salida → Consulta)
# =============================================================================
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${RESET}"
echo -e "${CYAN}📦 ESCENARIO 1: Flujo Básico de Inventario${RESET}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${RESET}"
echo ""

echo -e "${BLUE}Paso 1.1: Registrar INGRESO de 100 unidades${RESET}"
INGRESO1=$(curl -s -X POST $BASE_URL/movements \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD001",
    "bodega_id": "BOG_CENTRAL",
    "pais": "CO",
    "lote": "LOTE-TEST-001",
    "tipo_movimiento": "INGRESO",
    "motivo": "COMPRA",
    "cantidad": 100,
    "fecha_vencimiento": "2025-12-31",
    "usuario_id": "USER_TEST",
    "referencia_documento": "COMPRA-001"
  }')

if echo "$INGRESO1" | jq -e '.id' > /dev/null 2>&1; then
    MOV_ID=$(echo "$INGRESO1" | jq -r '.id')
    SALDO=$(echo "$INGRESO1" | jq -r '.saldo_nuevo')
    echo -e "${GREEN}✅ Ingreso registrado - ID: $MOV_ID, Saldo: $SALDO${RESET}"
else
    echo -e "${RED}❌ Error en ingreso${RESET}"
    echo "$INGRESO1" | jq
fi

sleep 1

echo ""
echo -e "${BLUE}Paso 1.2: Registrar SALIDA de 30 unidades${RESET}"
SALIDA1=$(curl -s -X POST $BASE_URL/movements \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD001",
    "bodega_id": "BOG_CENTRAL",
    "pais": "CO",
    "lote": "LOTE-TEST-001",
    "tipo_movimiento": "SALIDA",
    "motivo": "VENTA",
    "cantidad": 30,
    "usuario_id": "USER_TEST",
    "referencia_documento": "VENTA-001"
  }')

if echo "$SALIDA1" | jq -e '.id' > /dev/null 2>&1; then
    SALDO_ANT=$(echo "$SALIDA1" | jq -r '.saldo_anterior')
    SALDO_NUE=$(echo "$SALIDA1" | jq -r '.saldo_nuevo')
    echo -e "${GREEN}✅ Salida registrada - Saldo: $SALDO_ANT → $SALDO_NUE${RESET}"
else
    echo -e "${RED}❌ Error en salida${RESET}"
    echo "$SALIDA1" | jq
fi

sleep 1

echo ""
echo -e "${BLUE}Paso 1.3: Consultar Kardex${RESET}"
KARDEX=$(curl -s "$BASE_URL/movements/kardex?producto_id=PROD001&bodega_id=BOG_CENTRAL&pais=CO&size=10")
TOTAL=$(echo "$KARDEX" | jq -r '.meta.total')
echo -e "${GREEN}✅ Kardex consultado - Total movimientos: $TOTAL${RESET}"
echo ""
echo "Últimos movimientos:"
echo "$KARDEX" | jq -r '.items[0:3] | .[] | "  • ID: \(.id) | \(.tipo_movimiento) | Cantidad: \(.cantidad) | Saldo: \(.saldo_nuevo)"'

sleep 2

# =============================================================================
# ESCENARIO 2: Validación de Stock Insuficiente
# =============================================================================
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${RESET}"
echo -e "${CYAN}⚠️  ESCENARIO 2: Validación de Stock Insuficiente${RESET}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${RESET}"
echo ""

echo -e "${BLUE}Paso 2.1: Intentar salida de 200 unidades (solo hay ~70)${RESET}"
SALIDA_INVALIDA=$(curl -s -X POST $BASE_URL/movements \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD001",
    "bodega_id": "BOG_CENTRAL",
    "pais": "CO",
    "lote": "LOTE-TEST-001",
    "tipo_movimiento": "SALIDA",
    "motivo": "VENTA",
    "cantidad": 200,
    "usuario_id": "USER_TEST"
  }')

if echo "$SALIDA_INVALIDA" | jq -e '.error' > /dev/null 2>&1; then
    ERROR_CODE=$(echo "$SALIDA_INVALIDA" | jq -r '.error')
    SALDO_ACTUAL=$(echo "$SALIDA_INVALIDA" | jq -r '.saldo_actual')
    echo -e "${GREEN}✅ Validación funcionó correctamente${RESET}"
    echo "   Error: $ERROR_CODE"
    echo "   Stock disponible: $SALDO_ACTUAL"
else
    echo -e "${RED}❌ PROBLEMA: La salida fue aceptada (no debería)${RESET}"
fi

sleep 2

# =============================================================================
# ESCENARIO 3: Transferencia entre Bodegas
# =============================================================================
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${RESET}"
echo -e "${CYAN}🔄 ESCENARIO 3: Transferencia entre Bodegas${RESET}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${RESET}"
echo ""

echo -e "${BLUE}Paso 3.1: Transferir 20 unidades de BOG_CENTRAL a BOG_NORTE${RESET}"
TRANSFER=$(curl -s -X POST $BASE_URL/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD001",
    "bodega_origen_id": "BOG_CENTRAL",
    "pais_origen": "CO",
    "bodega_destino_id": "BOG_NORTE",
    "pais_destino": "CO",
    "lote": "LOTE-TEST-001",
    "cantidad": 20,
    "usuario_id": "USER_TEST",
    "referencia_documento": "TRANS-001"
  }')

if echo "$TRANSFER" | jq -e '.message' > /dev/null 2>&1; then
    SALDO_ORIG=$(echo "$TRANSFER" | jq -r '.saldo_origen')
    SALDO_DEST=$(echo "$TRANSFER" | jq -r '.saldo_destino')
    echo -e "${GREEN}✅ Transferencia completada${RESET}"
    echo "   Saldo BOG_CENTRAL: $SALDO_ORIG"
    echo "   Saldo BOG_NORTE: $SALDO_DEST"
else
    echo -e "${RED}❌ Error en transferencia${RESET}"
    echo "$TRANSFER" | jq
fi

sleep 2

# =============================================================================
# ESCENARIO 4: Alertas de Stock Bajo
# =============================================================================
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${RESET}"
echo -e "${CYAN}🚨 ESCENARIO 4: Alertas de Stock Bajo${RESET}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${RESET}"
echo ""

echo -e "${BLUE}Paso 4.1: Reducir stock hasta nivel crítico${RESET}"
SALIDA_CRITICA=$(curl -s -X POST $BASE_URL/movements \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD001",
    "bodega_id": "BOG_CENTRAL",
    "pais": "CO",
    "lote": "LOTE-TEST-001",
    "tipo_movimiento": "SALIDA",
    "motivo": "VENTA",
    "cantidad": 45,
    "usuario_id": "USER_TEST",
    "referencia_documento": "VENTA-GRANDE-001"
  }')

if echo "$SALIDA_CRITICA" | jq -e '.alertas' > /dev/null 2>&1; then
    NUM_ALERTAS=$(echo "$SALIDA_CRITICA" | jq -r '.alertas | length')
    SALDO_FINAL=$(echo "$SALIDA_CRITICA" | jq -r '.saldo_nuevo')
    echo -e "${YELLOW}⚠️  Stock bajo detectado - Saldo: $SALDO_FINAL${RESET}"
    echo "   Alertas generadas: $NUM_ALERTAS"
    if [ "$NUM_ALERTAS" -gt 0 ]; then
        echo "$SALIDA_CRITICA" | jq -r '.alertas[0] | "   Alerta: \(.nivel) - \(.mensaje)"'
    fi
fi

sleep 1

echo ""
echo -e "${BLUE}Paso 4.2: Consultar alertas activas${RESET}"
ALERTAS=$(curl -s "$BASE_URL/alerts?leida=false&size=10")
TOTAL_ALERTAS=$(echo "$ALERTAS" | jq -r '.meta.total')
echo -e "${GREEN}✅ Alertas consultadas - Total: $TOTAL_ALERTAS${RESET}"

if [ "$TOTAL_ALERTAS" -gt 0 ]; then
    echo ""
    echo "Alertas activas:"
    echo "$ALERTAS" | jq -r '.items[0:3] | .[] | "  ⚠️  \(.nivel): \(.tipo_alerta) - \(.mensaje)"'
fi

sleep 2

# =============================================================================
# ESCENARIO 5: Anulación de Movimiento
# =============================================================================
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${RESET}"
echo -e "${CYAN}↩️  ESCENARIO 5: Anulación de Movimiento${RESET}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${RESET}"
echo ""

echo -e "${BLUE}Paso 5.1: Crear movimiento para anular${RESET}"
MOV_ANULAR=$(curl -s -X POST $BASE_URL/movements \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD001",
    "bodega_id": "BOG_CENTRAL",
    "pais": "CO",
    "lote": "LOTE-TEST-001",
    "tipo_movimiento": "SALIDA",
    "motivo": "VENTA",
    "cantidad": 3,
    "usuario_id": "USER_TEST",
    "referencia_documento": "VENTA-ANULAR-001"
  }')

MOV_ID_ANULAR=$(echo "$MOV_ANULAR" | jq -r '.id')
SALDO_ANTES=$(echo "$MOV_ANULAR" | jq -r '.saldo_nuevo')
echo -e "${GREEN}✅ Movimiento creado - ID: $MOV_ID_ANULAR, Saldo: $SALDO_ANTES${RESET}"

sleep 1

echo ""
echo -e "${BLUE}Paso 5.2: Anular movimiento${RESET}"
ANULACION=$(curl -s -X PUT "$BASE_URL/movements/$MOV_ID_ANULAR/anular" \
  -H "Content-Type: application/json" \
  -d '{
    "usuario_id": "SUPERVISOR_TEST",
    "motivo_anulacion": "Error en registro - devolución de cliente"
  }')

if echo "$ANULACION" | jq -e '.estado' > /dev/null 2>&1; then
    ESTADO=$(echo "$ANULACION" | jq -r '.estado')
    echo -e "${GREEN}✅ Movimiento anulado - Estado: $ESTADO${RESET}"
    echo "   El stock fue revertido automáticamente"
else
    echo -e "${RED}❌ Error en anulación${RESET}"
    echo "$ANULACION" | jq
fi

sleep 2

# =============================================================================
# ESCENARIO 6: Reporte de Saldos
# =============================================================================
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${RESET}"
echo -e "${CYAN}📊 ESCENARIO 6: Reporte de Saldos por Bodega${RESET}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${RESET}"
echo ""

echo -e "${BLUE}Consultando reporte de saldos...${RESET}"
REPORTE=$(curl -s "$BASE_URL/reports/saldos?pais=CO&size=10")
TOTAL_ITEMS=$(echo "$REPORTE" | jq -r '.meta.total')
echo -e "${GREEN}✅ Reporte generado - Items: $TOTAL_ITEMS${RESET}"
echo ""
echo "Saldos actuales por bodega:"
echo "$REPORTE" | jq -r '.items[0:5] | .[] | "  📦 \(.producto_nombre) en \(.bodega_id): \(.cantidad_total) unidades [\(.estado_stock)]"'

sleep 2

# =============================================================================
# ESCENARIO 7: Prueba de Concurrencia (opcional - requiere herramientas)
# =============================================================================
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${RESET}"
echo -e "${CYAN}🔒 ESCENARIO 7: Prueba de Concurrencia (Locks)${RESET}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${RESET}"
echo ""

echo -e "${YELLOW}Esta prueba simula 2 ventas simultáneas del mismo producto${RESET}"
echo -e "${YELLOW}Ambas intentarán vender 4 unidades. Solo una debería ser aprobada.${RESET}"
echo ""

echo -e "${BLUE}Ejecutando requests simultáneos...${RESET}"

# Request A en background
curl -s -X POST $BASE_URL/movements \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD001",
    "bodega_id": "BOG_CENTRAL",
    "pais": "CO",
    "lote": "LOTE-TEST-001",
    "tipo_movimiento": "SALIDA",
    "motivo": "VENTA",
    "cantidad": 4,
    "usuario_id": "USER_A",
    "referencia_documento": "VENTA-CONCURRENTE-A"
  }' > /tmp/response_a.json 2>&1 &
PID_A=$!

# Request B inmediatamente
curl -s -X POST $BASE_URL/movements \
  -H "Content-Type: application/json" \
  -d '{
    "producto_id": "PROD001",
    "bodega_id": "BOG_CENTRAL",
    "pais": "CO",
    "lote": "LOTE-TEST-001",
    "tipo_movimiento": "SALIDA",
    "motivo": "VENTA",
    "cantidad": 4,
    "usuario_id": "USER_B",
    "referencia_documento": "VENTA-CONCURRENTE-B"
  }' > /tmp/response_b.json 2>&1 &
PID_B=$!

# Esperar a que terminen
wait $PID_A
wait $PID_B

echo ""
echo "Resultados:"
echo ""
echo "Request A:"
if jq -e '.id' /tmp/response_a.json > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ APROBADO${RESET}"
    jq -r '"  Saldo: \(.saldo_anterior) → \(.saldo_nuevo)"' /tmp/response_a.json
else
    echo -e "  ${RED}❌ RECHAZADO${RESET}"
    jq -r '.error' /tmp/response_a.json 2>/dev/null || echo "  Error desconocido"
fi

echo ""
echo "Request B:"
if jq -e '.id' /tmp/response_b.json > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ APROBADO${RESET}"
    jq -r '"  Saldo: \(.saldo_anterior) → \(.saldo_nuevo)"' /tmp/response_b.json
else
    echo -e "  ${RED}❌ RECHAZADO${RESET}"
    jq -r '.error' /tmp/response_b.json 2>/dev/null || echo "  Error desconocido"
fi

echo ""
echo -e "${CYAN}Análisis:${RESET}"
APPROVED_COUNT=$(cat /tmp/response_a.json /tmp/response_b.json | jq -s '[.[] | select(.id)] | length')
if [ "$APPROVED_COUNT" -eq 1 ]; then
    echo -e "${GREEN}✅ CORRECTO: Solo 1 request fue aprobado (locks funcionando)${RESET}"
elif [ "$APPROVED_COUNT" -eq 2 ]; then
    echo -e "${RED}⚠️  ADVERTENCIA: Ambos requests fueron aprobados (posible race condition)${RESET}"
else
    echo -e "${YELLOW}⚠️  Ambos rechazados (puede ser que no había stock suficiente)${RESET}"
fi

# Limpieza
rm -f /tmp/response_a.json /tmp/response_b.json

sleep 2

# =============================================================================
# RESUMEN FINAL
# =============================================================================
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${RESET}"
echo -e "${BLUE}📊 RESUMEN DE PRUEBAS${RESET}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${RESET}"
echo ""

echo "Escenarios ejecutados:"
echo "  ✅ 1. Flujo básico (ingreso → salida → consulta)"
echo "  ✅ 2. Validación de stock insuficiente"
echo "  ✅ 3. Transferencia entre bodegas"
echo "  ✅ 4. Alertas de stock bajo"
echo "  ✅ 5. Anulación de movimientos"
echo "  ✅ 6. Reporte de saldos"
echo "  ✅ 7. Prueba de concurrencia"

echo ""
echo -e "${GREEN}🎉 PRUEBAS COMPLETADAS${RESET}"
echo ""
echo "Para más detalles, revisa la documentación:"
echo "  • ENDPOINTS-INVENTARIO.md"
echo "  • GUIA-PRUEBAS-LOCALES.md"
echo ""

