# services/s3_service.py
import os
import boto3
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'medisupply-dev-visita-uploads')
    
    def upload_file(self, file_content: bytes, file_name: str, content_type: str) -> str:
        """
        Sube un archivo a S3 y retorna la URL pública o presigned URL
        
        Args:
            file_content: Contenido del archivo en bytes
            file_name: Nombre del archivo en S3
            content_type: Tipo MIME del archivo (e.g., 'text/csv', 'application/pdf')
        
        Returns:
            URL del archivo en S3
        """
        try:
            # Generar un path con timestamp para evitar colisiones
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            s3_key = f"reports/{timestamp}_{file_name}"
            
            # Subir el archivo a S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                ContentDisposition=f'attachment; filename="{file_name}"'
            )
            
            # Generar una URL prefirmada válida por 7 días (o usa URL pública si tu bucket es público)
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=604800  # 7 días en segundos
            )
            
            return url
            
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {e}")
            raise Exception(f"Failed to upload file to S3: {str(e)}")
    
    def get_public_url(self, s3_key: str) -> str:
        """
        Genera una URL pública para un objeto en S3 (si el bucket es público)
        """
        return f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"


# Instancia global del servicio
s3_service = S3Service()
