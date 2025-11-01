"""
Servicio para tracking de tareas de carga masiva en Redis
"""
import redis
import json
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Estados posibles de una tarea"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskService:
    """Servicio para gestionar estado de tareas en Redis"""
    
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://:redis@localhost:6379/1")
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        logger.info(f"✅ TaskService inicializado con Redis")
    
    def _get_key(self, task_id: str) -> str:
        """Genera la key de Redis para una tarea"""
        return f"bulk_upload_task:{task_id}"
    
    async def create_task(
        self,
        task_id: str,
        filename: str,
        proveedor_id: str,
        s3_key: str
    ) -> Dict[str, Any]:
        """
        Crea una nueva tarea en estado PENDING
        
        Args:
            task_id: ID único de la tarea
            filename: Nombre del archivo
            proveedor_id: ID del proveedor
            s3_key: Key del archivo en S3
        
        Returns:
            Información de la tarea creada
        """
        task_data = {
            "task_id": task_id,
            "status": TaskStatus.PENDING.value,
            "filename": filename,
            "proveedor_id": proveedor_id,
            "s3_key": s3_key,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "progress": {
                "total": 0,
                "processed": 0,
                "successful": 0,
                "failed": 0
            },
            "result": None,
            "error": None
        }
        
        key = self._get_key(task_id)
        self.redis_client.setex(
            key,
            86400,  # TTL: 24 horas
            json.dumps(task_data)
        )
        
        logger.info(f"📝 Tarea creada: {task_id}")
        return task_data
    
    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        **kwargs
    ):
        """
        Actualiza el estado de una tarea
        
        Args:
            task_id: ID de la tarea
            status: Nuevo estado
            **kwargs: Campos adicionales a actualizar
        """
        key = self._get_key(task_id)
        task_data_str = self.redis_client.get(key)
        
        if not task_data_str:
            logger.warning(f"⚠️ Tarea no encontrada: {task_id}")
            return
        
        task_data = json.loads(task_data_str)
        task_data["status"] = status.value
        task_data["updated_at"] = datetime.now().isoformat()
        
        # Actualizar campos adicionales
        for key_name, value in kwargs.items():
            task_data[key_name] = value
        
        self.redis_client.setex(
            key,
            86400,  # Renovar TTL
            json.dumps(task_data)
        )
        
        logger.info(f"🔄 Tarea actualizada: {task_id} -> {status.value}")
    
    async def update_progress(
        self,
        task_id: str,
        total: Optional[int] = None,
        processed: Optional[int] = None,
        successful: Optional[int] = None,
        failed: Optional[int] = None
    ):
        """
        Actualiza el progreso de una tarea
        
        Args:
            task_id: ID de la tarea
            total: Total de items a procesar
            processed: Items procesados
            successful: Items exitosos
            failed: Items fallidos
        """
        key = self._get_key(task_id)
        task_data_str = self.redis_client.get(key)
        
        if not task_data_str:
            logger.warning(f"⚠️ Tarea no encontrada: {task_id}")
            return
        
        task_data = json.loads(task_data_str)
        task_data["updated_at"] = datetime.now().isoformat()
        
        if total is not None:
            task_data["progress"]["total"] = total
        if processed is not None:
            task_data["progress"]["processed"] = processed
        if successful is not None:
            task_data["progress"]["successful"] = successful
        if failed is not None:
            task_data["progress"]["failed"] = failed
        
        self.redis_client.setex(
            key,
            86400,
            json.dumps(task_data)
        )
        
        logger.info(f"📊 Progreso actualizado: {task_id} - {processed}/{total}")
    
    async def complete_task(
        self,
        task_id: str,
        result: Dict[str, Any]
    ):
        """
        Marca una tarea como completada con su resultado
        
        Args:
            task_id: ID de la tarea
            result: Resultado final con resumen
        """
        await self.update_task_status(
            task_id,
            TaskStatus.COMPLETED,
            result=result,
            completed_at=datetime.now().isoformat()
        )
        
        logger.info(f"✅ Tarea completada: {task_id}")
    
    async def fail_task(
        self,
        task_id: str,
        error: str
    ):
        """
        Marca una tarea como fallida
        
        Args:
            task_id: ID de la tarea
            error: Mensaje de error
        """
        await self.update_task_status(
            task_id,
            TaskStatus.FAILED,
            error=error,
            failed_at=datetime.now().isoformat()
        )
        
        logger.error(f"❌ Tarea fallida: {task_id} - {error}")
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de una tarea
        
        Args:
            task_id: ID de la tarea
        
        Returns:
            Datos de la tarea o None si no existe
        """
        key = self._get_key(task_id)
        task_data_str = self.redis_client.get(key)
        
        if not task_data_str:
            return None
        
        return json.loads(task_data_str)


# Instancia global
task_service = TaskService()

