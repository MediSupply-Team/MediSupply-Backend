"""
Configuración de almacenamiento para archivos (fotos/videos)
Soporta almacenamiento local (desarrollo) y S3 (producción)
"""
import os
from typing import Optional
import boto3
from botocore.exceptions import ClientError

# Configuración
UPLOAD_METHOD = os.getenv("UPLOAD_METHOD", "local")  # "local" o "s3"
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
LOCAL_UPLOAD_DIR = "./uploads"

# Cliente S3 (solo si usamos S3)
s3_client = None
if UPLOAD_METHOD == "s3" and S3_BUCKET_NAME:
    s3_client = boto3.client('s3', region_name=AWS_REGION)


def get_upload_method():
    """Retorna el método de almacenamiento configurado"""
    return UPLOAD_METHOD


def get_storage_path(filename: str) -> str:
    """
    Retorna el path de almacenamiento según el método configurado
    - Local: ./uploads/filename
    - S3: s3://bucket/filename
    """
    if UPLOAD_METHOD == "s3":
        return f"s3://{S3_BUCKET_NAME}/{filename}"
    return f"{LOCAL_UPLOAD_DIR}/{filename}"


async def save_file(file_content: bytes, filename: str) -> str:
    """
    Guarda un archivo según el método de almacenamiento configurado
    
    Args:
        file_content: Contenido del archivo en bytes
        filename: Nombre del archivo
    
    Returns:
        Path donde se guardó el archivo
    """
    if UPLOAD_METHOD == "s3":
        # Subir a S3
        try:
            s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=filename,
                Body=file_content,
                ContentType=_get_content_type(filename)
            )
            return f"s3://{S3_BUCKET_NAME}/{filename}"
        except ClientError as e:
            raise Exception(f"Error subiendo archivo a S3: {str(e)}")
    else:
        # Guardar localmente
        os.makedirs(LOCAL_UPLOAD_DIR, exist_ok=True)
        file_path = f"{LOCAL_UPLOAD_DIR}/{filename}"
        with open(file_path, "wb") as f:
            f.write(file_content)
        return file_path


async def get_file(file_path: str) -> bytes:
    """
    Obtiene un archivo según el método de almacenamiento
    
    Args:
        file_path: Path del archivo (puede ser local o S3)
    
    Returns:
        Contenido del archivo en bytes
    """
    if file_path.startswith("s3://"):
        # Descargar de S3
        bucket, key = _parse_s3_path(file_path)
        try:
            response = s3_client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
        except ClientError as e:
            raise Exception(f"Error descargando archivo de S3: {str(e)}")
    else:
        # Leer archivo local
        with open(file_path, "rb") as f:
            return f.read()


async def delete_file(file_path: str) -> bool:
    """
    Elimina un archivo según el método de almacenamiento
    
    Args:
        file_path: Path del archivo (puede ser local o S3)
    
    Returns:
        True si se eliminó correctamente
    """
    if file_path.startswith("s3://"):
        # Eliminar de S3
        bucket, key = _parse_s3_path(file_path)
        try:
            s3_client.delete_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            print(f"Error eliminando archivo de S3: {str(e)}")
            return False
    else:
        # Eliminar archivo local
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error eliminando archivo local: {str(e)}")
            return False


def _parse_s3_path(s3_path: str) -> tuple:
    """
    Parsea un path S3 (s3://bucket/key) y retorna bucket y key
    """
    parts = s3_path.replace("s3://", "").split("/", 1)
    bucket = parts[0]
    key = parts[1] if len(parts) > 1 else ""
    return bucket, key


def _get_content_type(filename: str) -> str:
    """
    Determina el Content-Type basado en la extensión del archivo
    """
    extension = filename.split(".")[-1].lower()
    content_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "mp4": "video/mp4",
        "avi": "video/x-msvideo",
        "mov": "video/quicktime"
    }
    return content_types.get(extension, "application/octet-stream")


async def file_exists(file_path: str) -> bool:
    """
    Verifica si un archivo existe
    """
    if file_path.startswith("s3://"):
        bucket, key = _parse_s3_path(file_path)
        try:
            s3_client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False
    else:
        return os.path.exists(file_path)
