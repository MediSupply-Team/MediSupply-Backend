#!/usr/bin/env python3
"""
Script para crear el archivo Excel de ejemplo para carga masiva de productos
HU021 - Carga Masiva
"""

import pandas as pd
from datetime import datetime

# Datos de ejemplo
productos_ejemplo = [
    {
        "id": "PROD_BULK_001",
        "nombre": "Amoxicilina 500mg",
        "codigo": "AMX500-BULK",
        "categoria": "ANTIBIOTICS",
        "presentacion": "Cápsula",
        "precio_unitario": 1250.00,
        "certificado_sanitario": "CERT-INVIMA-2024-001",
        "condiciones_almacenamiento": "Temperatura ambiente 15-30°C, lugar seco",
        "tiempo_entrega_dias": 5,
        "stock_minimo": 50,
        "stock_critico": 20,
        "requiere_lote": "true",
        "requiere_vencimiento": "true"
    },
    {
        "id": "PROD_BULK_002",
        "nombre": "Ibuprofeno 400mg",
        "codigo": "IBU400-BULK",
        "categoria": "ANALGESICS",
        "presentacion": "Tableta",
        "precio_unitario": 800.00,
        "certificado_sanitario": "CERT-INVIMA-2024-002",
        "condiciones_almacenamiento": "Temperatura ambiente, proteger de la luz",
        "tiempo_entrega_dias": 3,
        "stock_minimo": 100,
        "stock_critico": 30,
        "requiere_lote": "true",
        "requiere_vencimiento": "true"
    },
    {
        "id": "PROD_BULK_003",
        "nombre": "Acetaminofén 500mg",
        "codigo": "ACE500-BULK",
        "categoria": "ANALGESICS",
        "presentacion": "Tableta",
        "precio_unitario": 500.00,
        "certificado_sanitario": "CERT-INVIMA-2024-003",
        "condiciones_almacenamiento": "Temperatura ambiente, lugar seco",
        "tiempo_entrega_dias": 3,
        "stock_minimo": 150,
        "stock_critico": 50,
        "requiere_lote": "true",
        "requiere_vencimiento": "true"
    },
    {
        "id": "PROD_BULK_004",
        "nombre": "Omeprazol 20mg",
        "codigo": "OME20-BULK",
        "categoria": "GASTROINTESTINAL",
        "presentacion": "Cápsula",
        "precio_unitario": 950.00,
        "certificado_sanitario": "CERT-INVIMA-2024-004",
        "condiciones_almacenamiento": "Temperatura ambiente 15-25°C, proteger de humedad",
        "tiempo_entrega_dias": 7,
        "stock_minimo": 80,
        "stock_critico": 25,
        "requiere_lote": "true",
        "requiere_vencimiento": "true"
    },
    {
        "id": "PROD_BULK_005",
        "nombre": "Loratadina 10mg",
        "codigo": "LOR10-BULK",
        "categoria": "ANTIHISTAMINICOS",
        "presentacion": "Tableta",
        "precio_unitario": 600.00,
        "certificado_sanitario": "CERT-INVIMA-2024-005",
        "condiciones_almacenamiento": "Temperatura ambiente, lugar seco",
        "tiempo_entrega_dias": 4,
        "stock_minimo": 60,
        "stock_critico": 20,
        "requiere_lote": "true",
        "requiere_vencimiento": "true"
    },
    {
        "id": "PROD_BULK_006",
        "nombre": "Metformina 850mg",
        "codigo": "MET850-BULK",
        "categoria": "ANTIDIABETICOS",
        "presentacion": "Tableta",
        "precio_unitario": 700.00,
        "certificado_sanitario": "CERT-INVIMA-2024-006",
        "condiciones_almacenamiento": "Temperatura ambiente 20-25°C, lugar seco",
        "tiempo_entrega_dias": 5,
        "stock_minimo": 100,
        "stock_critico": 30,
        "requiere_lote": "true",
        "requiere_vencimiento": "true"
    },
    {
        "id": "PROD_BULK_007",
        "nombre": "Losartán 50mg",
        "codigo": "LOS50-BULK",
        "categoria": "ANTIHIPERTENSIVOS",
        "presentacion": "Tableta",
        "precio_unitario": 1100.00,
        "certificado_sanitario": "CERT-INVIMA-2024-007",
        "condiciones_almacenamiento": "Temperatura ambiente, proteger de la luz y humedad",
        "tiempo_entrega_dias": 6,
        "stock_minimo": 75,
        "stock_critico": 25,
        "requiere_lote": "true",
        "requiere_vencimiento": "true"
    },
    {
        "id": "PROD_BULK_008",
        "nombre": "Atorvastatina 20mg",
        "codigo": "ATO20-BULK",
        "categoria": "ANTILIPEMICOS",
        "presentacion": "Tableta",
        "precio_unitario": 1500.00,
        "certificado_sanitario": "CERT-INVIMA-2024-008",
        "condiciones_almacenamiento": "Temperatura ambiente 15-30°C, lugar seco",
        "tiempo_entrega_dias": 7,
        "stock_minimo": 60,
        "stock_critico": 20,
        "requiere_lote": "true",
        "requiere_vencimiento": "true"
    },
    {
        "id": "PROD_BULK_009",
        "nombre": "Diclofenaco 50mg",
        "codigo": "DIC50-BULK",
        "categoria": "ANTIINFLAMATORIOS",
        "presentacion": "Tableta",
        "precio_unitario": 850.00,
        "certificado_sanitario": "CERT-INVIMA-2024-009",
        "condiciones_almacenamiento": "Temperatura ambiente, proteger de la luz",
        "tiempo_entrega_dias": 4,
        "stock_minimo": 90,
        "stock_critico": 30,
        "requiere_lote": "true",
        "requiere_vencimiento": "true"
    },
    {
        "id": "PROD_BULK_010",
        "nombre": "Cetirizina 10mg",
        "codigo": "CET10-BULK",
        "categoria": "ANTIHISTAMINICOS",
        "presentacion": "Tableta",
        "precio_unitario": 550.00,
        "certificado_sanitario": "CERT-INVIMA-2024-010",
        "condiciones_almacenamiento": "Temperatura ambiente, lugar seco",
        "tiempo_entrega_dias": 3,
        "stock_minimo": 70,
        "stock_critico": 25,
        "requiere_lote": "true",
        "requiere_vencimiento": "true"
    }
]

# Crear DataFrame
df = pd.DataFrame(productos_ejemplo)

# Guardar como Excel
output_file = "plantilla_productos_ejemplo.xlsx"
df.to_excel(output_file, index=False, engine='openpyxl')

print(f"✅ Archivo creado: {output_file}")
print(f"   📊 Productos: {len(df)}")
print(f"   📋 Columnas: {', '.join(df.columns)}")
print(f"\n💡 Este archivo se puede usar como plantilla para carga masiva")
print(f"   Endpoint: POST /api/catalog/items/bulk-upload")

# También crear una plantilla vacía
plantilla_vacia = pd.DataFrame(columns=df.columns)
plantilla_vacia_file = "plantilla_productos_vacia.xlsx"
plantilla_vacia.to_excel(plantilla_vacia_file, index=False, engine='openpyxl')

print(f"\n✅ Plantilla vacía creada: {plantilla_vacia_file}")

