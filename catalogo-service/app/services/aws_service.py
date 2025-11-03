"""
Servicio para interactuar con AWS S3 y SQS
Usa LocalStack en desarrollo y AWS real en producción
"""
import boto3
import json
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class AWSService:
    """Servicio para AWS S3 y SQS con soporte para LocalStack"""
    
    def __init__(self):
        # Configuración AWS/LocalStack
        self.endpoint_url = os.getenv("AWS_ENDPOINT_URL")  # None en producción, http://localstack:4566 en dev
        self.region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        self.s3_bucket = os.getenv("S3_BUCKET_NAME", "medisupply-bulk-uploads")
        # Usar URL de cola directamente (configurada por Terraform)
        self._sqs_queue_url = os.getenv("SQS_QUEUE_URL")
        self.sqs_queue_name = os.getenv("SQS_QUEUE_NAME", "medisupply-bulk-upload-queue")  # Fallback para LocalStack
        
        # Clientes AWS
        self._s3_client = None
        self._sqs_client = None
        
        logger.info(f"AWS Service initialized - Endpoint: {self.endpoint_url or 'AWS Real'}, SQS Queue: {self._sqs_queue_url}")
    
    @property
    def s3(self):
        """Cliente S3 lazy-loaded"""
        if self._s3_client is None:
            self._s3_client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                region_name=self.region
            )
            # Crear bucket si no existe (solo en LocalStack)
            if self.endpoint_url:
                try:
                    self._s3_client.create_bucket(Bucket=self.s3_bucket)
                    logger.info(f"✅ Bucket S3 creado: {self.s3_bucket}")
                except self._s3_client.exceptions.BucketAlreadyOwnedByYou:
                    logger.info(f"Bucket S3 ya existe: {self.s3_bucket}")
                except Exception as e:
                    logger.warning(f"No se pudo crear bucket S3: {e}")
        
        return self._s3_client
    
    @property
    def sqs(self):
        """Cliente SQS lazy-loaded"""
        if self._sqs_client is None:
            self._sqs_client = boto3.client(
                'sqs',
                endpoint_url=self.endpoint_url,
                region_name=self.region
            )
        return self._sqs_client
    
    def get_queue_url(self) -> str:
        """Obtiene la URL de la cola SQS, crea la cola si no existe (solo LocalStack)"""
        if self._sqs_queue_url is None:
            try:
                # Intentar obtener URL de cola existente por nombre
                response = self.sqs.get_queue_url(QueueName=self.sqs_queue_name)
                self._sqs_queue_url = response['QueueUrl']
                logger.info(f"✅ Cola SQS encontrada: {self._sqs_queue_url}")
            except self.sqs.exceptions.QueueDoesNotExist:
                # Crear cola solo en LocalStack (en AWS Terraform la crea)
                if self.endpoint_url:
                    response = self.sqs.create_queue(
                        QueueName=self.sqs_queue_name,
                        Attributes={
                            'DelaySeconds': '0',
                            'MessageRetentionPeriod': '86400',  # 1 día
                            'VisibilityTimeout': '300',  # 5 minutos para procesar
                            'ReceiveMessageWaitTimeSeconds': '20'  # Long polling
                        }
                    )
                    self._sqs_queue_url = response['QueueUrl']
                    logger.info(f"✅ Cola SQS creada (LocalStack): {self._sqs_queue_url}")
                else:
                    logger.error(f"❌ Cola SQS no encontrada y SQS_QUEUE_URL no configurado")
                    raise Exception("SQS_QUEUE_URL environment variable not set")
        
        return self._sqs_queue_url
    
    async def upload_file_to_s3(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ) -> str:
        """
        Sube un archivo a S3
        
        Args:
            file_content: Contenido del archivo en bytes
            filename: Nombre del archivo
            content_type: Tipo de contenido MIME
        
        Returns:
            S3 key del archivo subido
        """
        # Generar key único con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        s3_key = f"bulk-uploads/{timestamp}_{filename}"
        
        try:
            self.s3.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type
            )
            
            logger.info(f"✅ Archivo subido a S3: {s3_key}")
            return s3_key
        
        except Exception as e:
            logger.error(f"❌ Error subiendo archivo a S3: {e}")
            raise
    
    async def send_sqs_message(
        self,
        task_id: str,
        s3_key: str,
        filename: str,
        proveedor_id: str,
        reemplazar_duplicados: bool
    ) -> Dict[str, Any]:
        """
        Envía un mensaje a SQS para procesamiento asíncrono
        
        Args:
            task_id: ID único de la tarea
            s3_key: Key del archivo en S3
            filename: Nombre original del archivo
            proveedor_id: ID del proveedor
            reemplazar_duplicados: Si debe reemplazar duplicados
        
        Returns:
            Respuesta de SQS con MessageId
        """
        queue_url = self.get_queue_url()
        
        message_body = {
            'task_id': task_id,
            's3_key': s3_key,
            's3_bucket': self.s3_bucket,
            'filename': filename,
            'proveedor_id': proveedor_id,
            'reemplazar_duplicados': reemplazar_duplicados,
            'timestamp': datetime.now().isoformat(),
            'retry_count': 0
        }
        
        try:
            response = self.sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(message_body),
                MessageAttributes={
                    'task_id': {
                        'DataType': 'String',
                        'StringValue': task_id
                    },
                    'proveedor_id': {
                        'DataType': 'String',
                        'StringValue': proveedor_id
                    }
                }
            )
            
            logger.info(f"✅ Mensaje enviado a SQS - Task: {task_id}, MessageId: {response['MessageId']}")
            return response
        
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje a SQS: {e}")
            raise
    
    def receive_messages(self, max_messages: int = 1, wait_time: int = 20) -> list:
        """
        Recibe mensajes de SQS (para el worker)
        
        Args:
            max_messages: Máximo de mensajes a recibir
            wait_time: Tiempo de espera en segundos (long polling)
        
        Returns:
            Lista de mensajes
        """
        queue_url = self.get_queue_url()
        
        try:
            response = self.sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_time,
                MessageAttributeNames=['All'],
                AttributeNames=['All']
            )
            
            messages = response.get('Messages', [])
            if messages:
                logger.info(f"📬 Recibidos {len(messages)} mensajes de SQS")
            
            return messages
        
        except Exception as e:
            logger.error(f"❌ Error recibiendo mensajes de SQS: {e}")
            raise
    
    def delete_message(self, receipt_handle: str):
        """Elimina un mensaje de SQS después de procesarlo"""
        queue_url = self.get_queue_url()
        
        try:
            self.sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
            logger.info(f"🗑️ Mensaje eliminado de SQS")
        
        except Exception as e:
            logger.error(f"❌ Error eliminando mensaje de SQS: {e}")
            raise
    
    def download_file_from_s3(self, s3_key: str) -> bytes:
        """
        Descarga un archivo de S3
        
        Args:
            s3_key: Key del archivo en S3
        
        Returns:
            Contenido del archivo en bytes
        """
        try:
            response = self.s3.get_object(Bucket=self.s3_bucket, Key=s3_key)
            content = response['Body'].read()
            logger.info(f"📥 Archivo descargado de S3: {s3_key}")
            return content
        
        except Exception as e:
            logger.error(f"❌ Error descargando archivo de S3: {e}")
            raise


# Instancia global
aws_service = AWSService()

