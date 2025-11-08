"""
SQS Publisher Service para Catalogo-Service
Publica eventos de inventario a AWS SQS FIFO Queue
"""
import boto3
import json
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import uuid4
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class SQSPublisher:
    """
    Servicio para publicar eventos de inventario a AWS SQS.
    
    Características:
    - FIFO Queue (orden garantizado por MessageGroupId)
    - Deduplicación automática (MessageDeduplicationId)
    - Manejo de errores (no rompe la aplicación)
    - Logging detallado
    """
    
    def __init__(
        self,
        queue_url: Optional[str] = None,
        region_name: Optional[str] = None,
        enabled: bool = True
    ):
        """
        Inicializa el SQS Publisher.
        
        Args:
            queue_url: URL de la cola SQS FIFO
            region_name: Región de AWS
            enabled: Si False, deshabilita SQS (útil para local)
        """
        self.queue_url = queue_url or os.getenv("SQS_QUEUE_URL")
        self.region_name = region_name or os.getenv("SQS_REGION", "us-east-1")
        self.enabled = enabled and bool(self.queue_url)
        
        if not self.enabled:
            logger.info("🔕 SQS Publisher deshabilitado (SQS_QUEUE_URL no configurado)")
            self.client = None
            return
        
        try:
            # Crear cliente SQS
            # En AWS ECS, las credenciales se obtienen del IAM Role automáticamente
            self.client = boto3.client(
                'sqs',
                region_name=self.region_name
            )
            logger.info(f"✅ SQS Publisher inicializado: {self.queue_url}")
        except Exception as e:
            logger.error(f"❌ Error inicializando SQS Publisher: {e}")
            self.client = None
            self.enabled = False
    
    def _generate_message_id(self, event_type: str, data: Dict[str, Any]) -> str:
        """
        Genera un MessageDeduplicationId único para idempotencia.
        
        Usa: event_type + producto_id + timestamp
        Esto permite que eventos similares pero en diferentes momentos
        no se consideren duplicados.
        """
        producto_id = data.get('producto_id', 'unknown')
        timestamp = data.get('timestamp', datetime.utcnow().isoformat())
        return f"{event_type}_{producto_id}_{timestamp}".replace(" ", "_")[:128]
    
    def _generate_group_id(self, data: Dict[str, Any]) -> str:
        """
        Genera un MessageGroupId para FIFO.
        
        Usa producto_id para garantizar que todos los eventos
        del mismo producto se procesen en orden.
        """
        producto_id = data.get('producto_id', 'default')
        return f"producto_{producto_id}"
    
    async def publish_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        message_group_id: Optional[str] = None
    ) -> bool:
        """
        Publica un evento a SQS.
        
        Args:
            event_type: Tipo de evento (e.g., "InventoryMovementCreated")
            data: Datos del evento
            message_group_id: MessageGroupId personalizado (opcional)
        
        Returns:
            True si se publicó exitosamente, False en caso contrario
            
        Note:
            Esta función NO lanza excepciones para no romper el flujo principal.
            Solo loguea errores como WARNING.
        """
        if not self.enabled or not self.client:
            logger.debug(f"🔕 SQS deshabilitado, evento no publicado: {event_type}")
            return False
        
        try:
            # Construir el mensaje
            event_id = str(uuid4())
            message_body = {
                "event_type": event_type,
                "event_id": event_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            
            # IDs para FIFO
            dedup_id = self._generate_message_id(event_type, data)
            group_id = message_group_id or self._generate_group_id(data)
            
            logger.info(
                f"📨 Publicando evento a SQS: {event_type} "
                f"(producto: {data.get('producto_id', 'N/A')})"
            )
            logger.debug(f"   MessageGroupId: {group_id}")
            logger.debug(f"   MessageDeduplicationId: {dedup_id}")
            
            # Enviar a SQS
            response = self.client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message_body),
                MessageGroupId=group_id,
                MessageDeduplicationId=dedup_id,
                MessageAttributes={
                    'event_type': {
                        'DataType': 'String',
                        'StringValue': event_type
                    },
                    'producto_id': {
                        'DataType': 'String',
                        'StringValue': str(data.get('producto_id', 'unknown'))
                    }
                }
            )
            
            logger.info(f"✅ Evento publicado exitosamente: MessageId={response.get('MessageId')}")
            return True
            
        except (ClientError, BotoCoreError) as e:
            # Error de AWS (red, permisos, etc.)
            logger.warning(
                f"⚠️  Error AWS al publicar evento {event_type}: {e}. "
                f"Evento no publicado (transacción principal no afectada)."
            )
            return False
            
        except Exception as e:
            # Error inesperado
            logger.warning(
                f"⚠️  Error inesperado al publicar evento {event_type}: {e}",
                exc_info=True
            )
            return False
    
    async def publish_movement_created(
        self,
        movimiento_id: int,
        producto_id: str,
        producto_nombre: str,
        bodega_id: str,
        pais: str,
        tipo_movimiento: str,
        motivo: str,
        cantidad: int,
        saldo_anterior: int,
        saldo_nuevo: int,
        usuario_id: str,
        referencia_documento: Optional[str] = None
    ) -> bool:
        """
        Publica evento cuando se crea un movimiento de inventario.
        
        Útil para:
        - Analytics (actualizar dashboards)
        - Auditoría (registro de movimientos)
        - Integraciones (ERP, contabilidad)
        """
        return await self.publish_event(
            event_type="InventoryMovementCreated",
            data={
                "movimiento_id": movimiento_id,
                "producto_id": producto_id,
                "producto_nombre": producto_nombre,
                "bodega_id": bodega_id,
                "pais": pais,
                "tipo_movimiento": tipo_movimiento,
                "motivo": motivo,
                "cantidad": cantidad,
                "saldo_anterior": saldo_anterior,
                "saldo_nuevo": saldo_nuevo,
                "usuario_id": usuario_id,
                "referencia_documento": referencia_documento
            }
        )
    
    async def publish_transfer_completed(
        self,
        producto_id: str,
        producto_nombre: str,
        bodega_origen_id: str,
        bodega_destino_id: str,
        pais_origen: str,
        pais_destino: str,
        cantidad: int,
        movimiento_salida_id: int,
        movimiento_ingreso_id: int,
        saldo_origen_final: int,
        saldo_destino_final: int,
        usuario_id: str
    ) -> bool:
        """
        Publica evento cuando se completa una transferencia.
        
        Útil para:
        - Notificar a ambas bodegas
        - Tracking de transferencias
        - Logística
        """
        return await self.publish_event(
            event_type="InventoryTransferCompleted",
            data={
                "producto_id": producto_id,
                "producto_nombre": producto_nombre,
                "bodega_origen": {
                    "id": bodega_origen_id,
                    "pais": pais_origen,
                    "saldo_final": saldo_origen_final
                },
                "bodega_destino": {
                    "id": bodega_destino_id,
                    "pais": pais_destino,
                    "saldo_final": saldo_destino_final
                },
                "cantidad": cantidad,
                "movimiento_salida_id": movimiento_salida_id,
                "movimiento_ingreso_id": movimiento_ingreso_id,
                "usuario_id": usuario_id
            }
        )
    
    async def publish_alert_created(
        self,
        alerta_id: int,
        tipo_alerta: str,
        nivel: str,
        producto_id: str,
        producto_nombre: str,
        bodega_id: str,
        pais: str,
        stock_actual: int,
        stock_minimo: Optional[int],
        mensaje: str
    ) -> bool:
        """
        Publica evento cuando se genera una alerta de inventario.
        
        Útil para:
        - Enviar emails/SMS
        - Push notifications móviles
        - Alertas en tiempo real
        """
        return await self.publish_event(
            event_type="InventoryAlertCreated",
            data={
                "alerta_id": alerta_id,
                "tipo_alerta": tipo_alerta,
                "nivel": nivel,
                "producto_id": producto_id,
                "producto_nombre": producto_nombre,
                "bodega_id": bodega_id,
                "pais": pais,
                "stock_actual": stock_actual,
                "stock_minimo": stock_minimo,
                "mensaje": mensaje
            }
        )
    
    async def publish_movement_cancelled(
        self,
        movimiento_id: int,
        producto_id: str,
        producto_nombre: str,
        bodega_id: str,
        pais: str,
        tipo_movimiento_original: str,
        cantidad: int,
        anulado_por: str,
        motivo_anulacion: str
    ) -> bool:
        """
        Publica evento cuando se anula un movimiento.
        
        Útil para:
        - Auditoría de anulaciones
        - Notificar supervisores
        - Alertas de seguridad
        """
        return await self.publish_event(
            event_type="InventoryMovementCancelled",
            data={
                "movimiento_id": movimiento_id,
                "producto_id": producto_id,
                "producto_nombre": producto_nombre,
                "bodega_id": bodega_id,
                "pais": pais,
                "tipo_movimiento_original": tipo_movimiento_original,
                "cantidad": cantidad,
                "anulado_por": anulado_por,
                "motivo_anulacion": motivo_anulacion
            }
        )


# Instancia global del publisher (singleton)
_sqs_publisher_instance = None


def get_sqs_publisher() -> SQSPublisher:
    """
    Obtiene la instancia global del SQS Publisher (singleton).
    
    Se inicializa en el primer uso.
    """
    global _sqs_publisher_instance
    
    if _sqs_publisher_instance is None:
        _sqs_publisher_instance = SQSPublisher()
    
    return _sqs_publisher_instance

