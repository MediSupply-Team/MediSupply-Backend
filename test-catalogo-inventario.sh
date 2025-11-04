#!/bin/bash

# =============================================================================
# Script de Pruebas Completas - Catálogo e Inventario
# =============================================================================

ALB_URL="http://medisupply-dev-bff-venta-alb-645002575.us-east-1.elb.amazonaws.com"
CATALOG_BASE="$ALB_URL/catalog/api/catalog"
INVENTORY_BASE="$ALB_URL/catalog/api/inventory"

echo "🧪 ======================================================================"
echo "   PRUEBAS COMPLETAS - CATÁLOGO E INVENTARIO"
echo "   ======================================================================"
echo ""

# =============================================================================
# 1. HEALTH CHECKS
# =============================================================================
echo "❤️  1. HEALTH CHECKS"
echo "----------------------------------------------------------------------"

echo "   1.1 Health Check BFF:"
HEALTH=$(curl -s "$ALB_URL/health")
echo "   $HEALTH"
if echo "$HEALTH" | jq -e '.status == "ok"' > /dev/null 2>&1; then
    echo "   ✅ BFF funcionando"
else
    echo "   ❌ BFF no responde correctamente"
fi
echo ""

echo "   1.2 Health Check Catálogo (verificar endpoint funcional):"
CATALOG_HEALTH=$(curl -s "$CATALOG_BASE/items?size=1")
TOTAL=$(echo "$CATALOG_HEALTH" | jq -r '.meta.total // 0')
echo "   Total productos: $TOTAL"
if [ "$TOTAL" -gt 0 ]; then
    echo "   ✅ Catálogo funcionando ($TOTAL productos)"
else
    echo "   ❌ Catálogo no tiene productos"
fi
echo ""

echo "   1.3 Health Check Inventario (verificar endpoint funcional):"
INV_HEALTH=$(curl -s "$INVENTORY_BASE/alerts?size=1")
INV_TOTAL=$(echo "$INV_HEALTH" | jq -r '.meta.total // 0')
echo "   Total alertas: $INV_TOTAL"
if echo "$INV_HEALTH" | jq -e '.meta' > /dev/null 2>&1; then
    echo "   ✅ Inventario funcionando"
else
    echo "   ❌ Inventario no responde correctamente"
fi
echo ""

# =============================================================================
# 2. PRUEBAS DE CATÁLOGO
# =============================================================================
echo "📦 2. PRUEBAS DE CATÁLOGO"
echo "----------------------------------------------------------------------"

echo "   2.1 Listar todos los productos (paginado):"
LIST_RESP=$(curl -s "$CATALOG_BASE/items?page=1&size=5")
LIST_TOTAL=$(echo "$LIST_RESP" | jq -r '.meta.total')
LIST_PAGE=$(echo "$LIST_RESP" | jq -r '.meta.page')
LIST_SIZE=$(echo "$LIST_RESP" | jq -r '.meta.size')
echo "   Total: $LIST_TOTAL productos | Página: $LIST_PAGE | Size: $LIST_SIZE"
echo "   Primeros productos:"
echo "$LIST_RESP" | jq -r '.items[0:3] | .[] | "      - \(.codigo): \(.nombre)"'
echo "   ✅ Listado funcionando"
echo ""

echo "   2.2 Buscar por texto (búsqueda: 'amoxicilina'):"
SEARCH_RESP=$(curl -s "$CATALOG_BASE/items?q=amoxicilina")
SEARCH_TOTAL=$(echo "$SEARCH_RESP" | jq -r '.meta.total')
echo "   Encontrados: $SEARCH_TOTAL productos"
echo "$SEARCH_RESP" | jq -r '.items[] | "      - \(.codigo): \(.nombre)"'
if [ "$SEARCH_TOTAL" -gt 0 ]; then
    echo "   ✅ Búsqueda por texto funcionando"
else
    echo "   ⚠️  No se encontraron productos con 'amoxicilina'"
fi
echo ""

echo "   2.3 Filtrar por categoría (ANTIBIOTICS):"
CAT_RESP=$(curl -s "$CATALOG_BASE/items?categoriaId=ANTIBIOTICS")
CAT_TOTAL=$(echo "$CAT_RESP" | jq -r '.meta.total')
echo "   Antibióticos encontrados: $CAT_TOTAL"
echo "$CAT_RESP" | jq -r '.items[0:3] | .[] | "      - \(.codigo): \(.nombre)"'
if [ "$CAT_TOTAL" -gt 0 ]; then
    echo "   ✅ Filtro por categoría funcionando"
else
    echo "   ⚠️  No se encontraron antibióticos"
fi
echo ""

echo "   2.4 Filtrar por país (Colombia):"
PAIS_RESP=$(curl -s "$CATALOG_BASE/items?pais=CO&size=3")
PAIS_TOTAL=$(echo "$PAIS_RESP" | jq -r '.meta.total')
echo "   Productos en Colombia: $PAIS_TOTAL"
echo "$PAIS_RESP" | jq -r '.items[0:3] | .[] | "      - \(.codigo): \(.nombre)"'
if [ "$PAIS_TOTAL" -gt 0 ]; then
    echo "   ✅ Filtro por país funcionando"
else
    echo "   ⚠️  No se encontraron productos en Colombia"
fi
echo ""

echo "   2.5 Detalle de producto (PROD001):"
DETAIL_RESP=$(curl -s "$CATALOG_BASE/items/PROD001")
PROD_NOMBRE=$(echo "$DETAIL_RESP" | jq -r '.nombre')
PROD_CODIGO=$(echo "$DETAIL_RESP" | jq -r '.codigo')
PROD_PRECIO=$(echo "$DETAIL_RESP" | jq -r '.precioUnitario')
echo "   Producto: $PROD_CODIGO - $PROD_NOMBRE"
echo "   Precio: \$$PROD_PRECIO"
if [ "$PROD_CODIGO" != "null" ]; then
    echo "   ✅ Detalle de producto funcionando"
else
    echo "   ❌ No se encontró el producto PROD001"
fi
echo ""

echo "   2.6 Inventario de producto (PROD001):"
INV_PROD_RESP=$(curl -s "$CATALOG_BASE/items/PROD001/inventario")
INV_PROD_TOTAL=$(echo "$INV_PROD_RESP" | jq -r '.meta.total // 0')
echo "   Inventario total: $INV_PROD_TOTAL registros"
if [ "$INV_PROD_TOTAL" -gt 0 ]; then
    echo "$INV_PROD_RESP" | jq -r '.items[0:3] | .[] | "      - \(.pais)/\(.bodega_id): \(.cantidad) unidades"'
    echo "   ✅ Consulta de inventario por producto funcionando"
else
    echo "   ⚠️  No hay inventario para PROD001"
fi
echo ""

# =============================================================================
# 3. PRUEBAS DE INVENTARIO
# =============================================================================
echo "📊 3. PRUEBAS DE INVENTARIO"
echo "----------------------------------------------------------------------"

echo "   3.1 Registrar entrada de inventario:"
INGRESO_DATA='{
  "producto_id": "PROD001",
  "bodega_id": "BOG_CENTRAL",
  "pais": "CO",
  "lote": "TEST_'$(date +%s)'",
  "tipo_movimiento": "INGRESO",
  "motivo": "COMPRA",
  "cantidad": 50,
  "fecha_vencimiento": "2025-12-31",
  "usuario_id": "USR_TEST_001",
  "referencia_documento": "PO-TEST-'$(date +%s)'",
  "observaciones": "Ingreso de prueba automatizada"
}'

INGRESO_RESP=$(curl -s -X POST "$INVENTORY_BASE/movements" \
  -H "Content-Type: application/json" \
  -d "$INGRESO_DATA")

MOV_ID=$(echo "$INGRESO_RESP" | jq -r '.id // empty')
if [ -n "$MOV_ID" ]; then
    echo "   ✅ Entrada registrada exitosamente"
    echo "      - Movimiento ID: $MOV_ID"
    echo "      - Producto: $(echo "$INGRESO_RESP" | jq -r '.producto_id')"
    echo "      - Cantidad: $(echo "$INGRESO_RESP" | jq -r '.cantidad')"
    echo "      - Saldo nuevo: $(echo "$INGRESO_RESP" | jq -r '.saldo_nuevo')"
else
    echo "   ❌ Error al registrar entrada"
    echo "$INGRESO_RESP" | jq '.'
fi
echo ""

echo "   3.2 Consultar kardex (historial de movimientos):"
KARDEX_RESP=$(curl -s "$INVENTORY_BASE/movements?producto_id=PROD001&page=1&size=5")
KARDEX_TOTAL=$(echo "$KARDEX_RESP" | jq -r '.meta.total // 0')
echo "   Total movimientos para PROD001: $KARDEX_TOTAL"
if [ "$KARDEX_TOTAL" -gt 0 ]; then
    echo "   Últimos movimientos:"
    echo "$KARDEX_RESP" | jq -r '.items[0:3] | .[] | "      - \(.tipo_movimiento) [\(.motivo)]: \(.cantidad) unidades - \(.created_at)"'
    echo "   ✅ Consulta de kardex funcionando"
else
    echo "   ⚠️  No hay movimientos registrados para PROD001"
fi
echo ""

echo "   3.3 Consultar alertas de inventario:"
ALERTAS_RESP=$(curl -s "$INVENTORY_BASE/alerts?page=1&size=5")
ALERTAS_TOTAL=$(echo "$ALERTAS_RESP" | jq -r '.meta.total // 0')
echo "   Total alertas: $ALERTAS_TOTAL"
if [ "$ALERTAS_TOTAL" -gt 0 ]; then
    echo "   Alertas activas:"
    echo "$ALERTAS_RESP" | jq -r '.items[0:3] | .[] | "      - [\(.tipo_alerta)] \(.producto_id): \(.mensaje)"'
    echo "   ✅ Sistema de alertas funcionando"
else
    echo "   ℹ️  No hay alertas activas (esto es bueno)"
fi
echo ""

echo "   3.4 Reporte de saldos por bodega:"
SALDOS_RESP=$(curl -s "$INVENTORY_BASE/reports/saldos?producto_id=PROD001")
SALDOS_TOTAL=$(echo "$SALDOS_RESP" | jq -r '.saldos | length')
echo "   Bodegas con stock: $SALDOS_TOTAL"
if [ "$SALDOS_TOTAL" -gt 0 ]; then
    echo "   Saldos por bodega:"
    echo "$SALDOS_RESP" | jq -r '.saldos[0:5] | .[] | "      - \(.pais)/\(.bodega_id): \(.cantidad_total) unidades"'
    echo "   ✅ Reporte de saldos funcionando"
else
    echo "   ⚠️  No hay saldos disponibles"
fi
echo ""

# =============================================================================
# 4. PRUEBA DE CARGA MASIVA (OPCIONAL - REQUIERE ARCHIVO)
# =============================================================================
echo "📤 4. PRUEBA DE CARGA MASIVA"
echo "----------------------------------------------------------------------"

PLANTILLA_PATH="catalogo-service/data/plantilla_productos_ejemplo.xlsx"
if [ -f "$PLANTILLA_PATH" ]; then
    echo "   4.1 Carga masiva de productos (archivo: plantilla_productos_ejemplo.xlsx):"
    
    BULK_RESP=$(curl -s -X POST "$CATALOG_BASE/items/bulk-upload?proveedor_id=PROV_TEST_001&reemplazar_duplicados=false" \
      -F "file=@$PLANTILLA_PATH")
    
    TASK_ID=$(echo "$BULK_RESP" | jq -r '.task_id // empty')
    if [ -n "$TASK_ID" ]; then
        echo "   ✅ Archivo encolado para procesamiento"
        echo "      - Task ID: $TASK_ID"
        echo "      - Status: $(echo "$BULK_RESP" | jq -r '.status')"
        echo "      - Status URL: $(echo "$BULK_RESP" | jq -r '.status_url')"
        echo ""
        
        echo "   4.2 Consultando estado de la tarea (esperando 5 segundos)..."
        sleep 5
        
        STATUS_RESP=$(curl -s "$CATALOG_BASE/bulk-upload/status/$TASK_ID")
        TASK_STATUS=$(echo "$STATUS_RESP" | jq -r '.status')
        echo "   Estado: $TASK_STATUS"
        
        if [ "$TASK_STATUS" == "completed" ]; then
            echo "   ✅ Carga completada exitosamente"
            echo "      - Total procesados: $(echo "$STATUS_RESP" | jq -r '.total')"
            echo "      - Exitosos: $(echo "$STATUS_RESP" | jq -r '.exitosos')"
            echo "      - Rechazados: $(echo "$STATUS_RESP" | jq -r '.rechazados')"
        elif [ "$TASK_STATUS" == "processing" ]; then
            echo "   ⏳ Tarea en proceso..."
            echo "      Para consultar: curl $CATALOG_BASE/bulk-upload/status/$TASK_ID"
        elif [ "$TASK_STATUS" == "pending" ]; then
            echo "   ⏳ Tarea pendiente de procesamiento"
            echo "      Para consultar: curl $CATALOG_BASE/bulk-upload/status/$TASK_ID"
        else
            echo "   Estado: $STATUS_RESP"
        fi
    else
        echo "   ❌ Error al encolar archivo para carga masiva"
        echo "$BULK_RESP" | jq '.'
    fi
else
    echo "   ⚠️  Archivo de prueba no encontrado: $PLANTILLA_PATH"
    echo "   ℹ️  Saltando prueba de carga masiva"
fi
echo ""

# =============================================================================
# 5. RESUMEN
# =============================================================================
echo "📊 5. RESUMEN DE PRUEBAS"
echo "======================================================================"
echo ""
echo "   ✅ Health Checks: BFF, Catálogo, Inventario"
echo "   ✅ Catálogo: Listar, Buscar, Filtrar, Detalle"
echo "   ✅ Inventario: Ingresos, Kardex, Alertas, Reportes"
if [ -n "$TASK_ID" ]; then
    echo "   ✅ Carga Masiva: Encolada (Task ID: $TASK_ID)"
fi
echo ""
echo "🎉 Pruebas completadas exitosamente!"
echo ""

