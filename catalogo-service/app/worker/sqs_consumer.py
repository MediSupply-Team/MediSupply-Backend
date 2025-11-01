"""
Worker/Consumer para procesar mensajes de carga masiva desde SQS
HU021 - Procesamiento asíncrono con alta disponibilidad
"""
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import io
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.models.catalogo_model import Producto
from app.services.aws_service import aws_service
from app.services.task_service import task_service, TaskStatus

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BulkUploadWorker:
    """Worker para procesar cargas masivas de productos desde SQS"""
    
    def __init__(self):
        # Configurar conexión a base de datos
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL no configurada")
        
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("✅ Worker inicializado")
    
    async def process_bulk_upload(
        self,
        task_id: str,
        s3_key: str,
        s3_bucket: str,
        filename: str,
        proveedor_id: str,
        reemplazar_duplicados: bool
    ):
        """
        Procesa un archivo de carga masiva
        
        Args:
            task_id: ID de la tarea
            s3_key: Key del archivo en S3
            s3_bucket: Bucket S3
            filename: Nombre del archivo
            proveedor_id: ID del proveedor
            reemplazar_duplicados: Si debe reemplazar duplicados
        """
        logger.info(f"🔄 Procesando tarea {task_id} - Archivo: {filename}")
        
        try:
            # Actualizar estado a PROCESSING
            await task_service.update_task_status(
                task_id,
                TaskStatus.PROCESSING
            )
            
            # Descargar archivo de S3
            logger.info(f"📥 Descargando archivo de S3: {s3_key}")
            file_content = aws_service.download_file_from_s3(s3_key)
            
            # Leer archivo Excel/CSV
            if filename.endswith('.xlsx'):
                df = pd.read_excel(io.BytesIO(file_content))
            else:
                df = pd.read_csv(io.BytesIO(file_content))
            
            logger.info(f"   📊 Archivo leído: {len(df)} filas")
            
            # Validar columnas requeridas
            columnas_requeridas = [
                'id', 'nombre', 'codigo', 'categoria', 'precio_unitario',
                'certificado_sanitario', 'condiciones_almacenamiento', 'tiempo_entrega_dias'
            ]
            
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
            if columnas_faltantes:
                error_msg = f"Columnas faltantes: {', '.join(columnas_faltantes)}"
                logger.error(f"❌ {error_msg}")
                await task_service.fail_task(task_id, error_msg)
                return
            
            # Actualizar progreso inicial
            total = len(df)
            await task_service.update_progress(
                task_id,
                total=total,
                processed=0,
                successful=0,
                failed=0
            )
            
            # Contadores
            exitosos = 0
            rechazados = 0
            duplicados_count = 0
            errores = []
            productos_creados = []
            productos_actualizados = []
            
            # Procesar cada fila
            async with self.async_session() as session:
                for idx, row in df.iterrows():
                    fila_num = idx + 2  # +2 porque Excel empieza en 1 y tiene header
                    
                    try:
                        # Validar campos obligatorios
                        campos_vacios = []
                        for campo in columnas_requeridas:
                            if pd.isna(row[campo]) or str(row[campo]).strip() == '':
                                campos_vacios.append(campo)
                        
                        if campos_vacios:
                            errores.append({
                                "fila": fila_num,
                                "error": f"Campos obligatorios vacíos: {', '.join(campos_vacios)}"
                            })
                            rechazados += 1
                            continue
                        
                        # Verificar si el producto ya existe
                        producto_id = str(row['id']).strip()
                        codigo = str(row['codigo']).strip()
                        
                        existing = (await session.execute(
                            select(Producto).where(
                                (Producto.id == producto_id) | (Producto.codigo == codigo)
                            )
                        )).scalar_one_or_none()
                        
                        if existing:
                            duplicados_count += 1
                            
                            if not reemplazar_duplicados:
                                errores.append({
                                    "fila": fila_num,
                                    "error": f"Producto duplicado (ID: {producto_id} o Código: {codigo})"
                                })
                                rechazados += 1
                                continue
                            else:
                                # Actualizar producto existente
                                existing.nombre = str(row['nombre']).strip()
                                existing.codigo = codigo
                                existing.categoria_id = str(row['categoria']).strip()
                                existing.precio_unitario = float(row['precio_unitario'])
                                existing.certificado_sanitario = str(row['certificado_sanitario']).strip()
                                existing.requisitos_almacenamiento = str(row['condiciones_almacenamiento']).strip()
                                existing.tiempo_entrega_dias = int(row['tiempo_entrega_dias'])
                                existing.proveedor_id = proveedor_id
                                
                                # Campos opcionales
                                if 'presentacion' in df.columns and not pd.isna(row['presentacion']):
                                    existing.presentacion = str(row['presentacion']).strip()
                                
                                if 'stock_minimo' in df.columns and not pd.isna(row['stock_minimo']):
                                    existing.stock_minimo = int(row['stock_minimo'])
                                
                                if 'stock_critico' in df.columns and not pd.isna(row['stock_critico']):
                                    existing.stock_critico = int(row['stock_critico'])
                                
                                if 'requiere_lote' in df.columns and not pd.isna(row['requiere_lote']):
                                    existing.requiere_lote = str(row['requiere_lote']).lower() in ['true', '1', 'si', 'yes']
                                
                                if 'requiere_vencimiento' in df.columns and not pd.isna(row['requiere_vencimiento']):
                                    existing.requiere_vencimiento = str(row['requiere_vencimiento']).lower() in ['true', '1', 'si', 'yes']
                                
                                session.add(existing)
                                productos_actualizados.append(producto_id)
                                exitosos += 1
                                logger.info(f"      ✓ Fila {fila_num}: Producto {producto_id} actualizado")
                                continue
                        
                        # Crear nuevo producto
                        nuevo_producto = Producto(
                            id=producto_id,
                            codigo=codigo,
                            nombre=str(row['nombre']).strip(),
                            categoria_id=str(row['categoria']).strip(),
                            precio_unitario=float(row['precio_unitario']),
                            certificado_sanitario=str(row['certificado_sanitario']).strip(),
                            requisitos_almacenamiento=str(row['condiciones_almacenamiento']).strip(),
                            tiempo_entrega_dias=int(row['tiempo_entrega_dias']),
                            proveedor_id=proveedor_id
                        )
                        
                        # Campos opcionales
                        if 'presentacion' in df.columns and not pd.isna(row['presentacion']):
                            nuevo_producto.presentacion = str(row['presentacion']).strip()
                        
                        if 'stock_minimo' in df.columns and not pd.isna(row['stock_minimo']):
                            nuevo_producto.stock_minimo = int(row['stock_minimo'])
                        else:
                            nuevo_producto.stock_minimo = 10
                        
                        if 'stock_critico' in df.columns and not pd.isna(row['stock_critico']):
                            nuevo_producto.stock_critico = int(row['stock_critico'])
                        else:
                            nuevo_producto.stock_critico = 5
                        
                        if 'requiere_lote' in df.columns and not pd.isna(row['requiere_lote']):
                            nuevo_producto.requiere_lote = str(row['requiere_lote']).lower() in ['true', '1', 'si', 'yes']
                        else:
                            nuevo_producto.requiere_lote = False
                        
                        if 'requiere_vencimiento' in df.columns and not pd.isna(row['requiere_vencimiento']):
                            nuevo_producto.requiere_vencimiento = str(row['requiere_vencimiento']).lower() in ['true', '1', 'si', 'yes']
                        else:
                            nuevo_producto.requiere_vencimiento = True
                        
                        session.add(nuevo_producto)
                        productos_creados.append(producto_id)
                        exitosos += 1
                        logger.info(f"      ✓ Fila {fila_num}: Producto {producto_id} creado")
                        
                    except Exception as e:
                        errores.append({
                            "fila": fila_num,
                            "error": str(e)
                        })
                        rechazados += 1
                        logger.error(f"      ✗ Error en fila {fila_num}: {e}")
                    
                    # Actualizar progreso cada 10 filas
                    if (idx + 1) % 10 == 0:
                        await task_service.update_progress(
                            task_id,
                            processed=idx + 1,
                            successful=exitosos,
                            failed=rechazados
                        )
                
                # Commit de todos los cambios
                await session.commit()
            
            logger.info(f"✅ Carga masiva completada - Exitosos: {exitosos}, Rechazados: {rechazados}, Duplicados: {duplicados_count}")
            
            # Marcar tarea como completada
            result = {
                "mensaje": "Carga masiva completada",
                "resumen": {
                    "total": total,
                    "exitosos": exitosos,
                    "rechazados": rechazados,
                    "duplicados": duplicados_count,
                    "productos_creados": len(productos_creados),
                    "productos_actualizados": len(productos_actualizados)
                },
                "productos_creados": productos_creados,
                "productos_actualizados": productos_actualizados,
                "errores": errores if errores else None
            }
            
            await task_service.complete_task(task_id, result)
            
        except Exception as e:
            logger.error(f"❌ Error procesando tarea {task_id}: {e}", exc_info=True)
            await task_service.fail_task(task_id, str(e))
    
    async def run(self):
        """Loop principal del worker"""
        logger.info("🚀 Worker iniciado - Escuchando mensajes de SQS...")
        
        while True:
            try:
                # Recibir mensajes de SQS
                messages = aws_service.receive_messages(max_messages=1, wait_time=20)
                
                for message in messages:
                    try:
                        # Parsear mensaje
                        body = json.loads(message['Body'])
                        
                        task_id = body['task_id']
                        s3_key = body['s3_key']
                        s3_bucket = body['s3_bucket']
                        filename = body['filename']
                        proveedor_id = body['proveedor_id']
                        reemplazar_duplicados = body['reemplazar_duplicados']
                        
                        logger.info(f"📬 Mensaje recibido - Task: {task_id}")
                        
                        # Procesar mensaje
                        await self.process_bulk_upload(
                            task_id=task_id,
                            s3_key=s3_key,
                            s3_bucket=s3_bucket,
                            filename=filename,
                            proveedor_id=proveedor_id,
                            reemplazar_duplicados=reemplazar_duplicados
                        )
                        
                        # Eliminar mensaje de SQS (solo si procesó exitosamente)
                        aws_service.delete_message(message['ReceiptHandle'])
                        logger.info(f"🗑️ Mensaje eliminado de SQS - Task: {task_id}")
                        
                    except Exception as e:
                        logger.error(f"❌ Error procesando mensaje: {e}", exc_info=True)
                        # El mensaje volverá a la cola después del visibility timeout
                
            except KeyboardInterrupt:
                logger.info("⏹️ Worker detenido por usuario")
                break
            except Exception as e:
                logger.error(f"❌ Error en loop principal: {e}", exc_info=True)
                # Esperar un poco antes de reintentar
                await asyncio.sleep(5)


async def main():
    """Función principal"""
    worker = BulkUploadWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())

