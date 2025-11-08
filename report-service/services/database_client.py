"""
Cliente de base de datos para acceder directamente a la BD de Orders
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncpg
import json


class DatabaseClient:
    """Cliente para consultar la base de datos de Orders directamente"""
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Establece el pool de conexiones a la base de datos"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
    
    async def disconnect(self):
        """Cierra el pool de conexiones"""
        if self.pool:
            await self.pool.close()
            self.pool = None
    
    async def get_orders(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Obtiene órdenes de la base de datos con filtros opcionales
        
        Args:
            start_date: Fecha de inicio para filtrar
            end_date: Fecha de fin para filtrar
            status: Estado de la orden para filtrar
            limit: Límite de resultados
            offset: Offset para paginación
            
        Returns:
            Lista de órdenes
        """
        if not self.pool:
            await self.connect()
        
        query = """
            SELECT 
                id,
                customer_id,
                items,
                status,
                created_by_role,
                source,
                user_name,
                address,
                validated_at,
                confirmed_at,
                released_at,
                delivered_at,
                completed_at,
                created_at,
                updated_at,
                notes,
                cancellation_reason
            FROM orders
            WHERE 1=1
        """
        
        params = []
        param_count = 1
        
        if start_date:
            query += f" AND created_at >= ${param_count}"
            params.append(start_date)
            param_count += 1
        
        if end_date:
            query += f" AND created_at <= ${param_count}"
            params.append(end_date)
            param_count += 1
        
        if status:
            query += f" AND status = ${param_count}"
            params.append(status)
            param_count += 1
        
        query += f" ORDER BY created_at DESC LIMIT ${param_count} OFFSET ${param_count + 1}"
        params.extend([limit, offset])
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
            orders = []
            for row in rows:
                order = dict(row)
                # Convertir UUID a string
                order['id'] = str(order['id'])
                # Convertir JSON a dict si es necesario
                if isinstance(order.get('items'), str):
                    order['items'] = json.loads(order['items'])
                if isinstance(order.get('address'), str):
                    order['address'] = json.loads(order['address'])
                # Convertir datetime a ISO format
                for date_field in ['validated_at', 'confirmed_at', 'released_at', 
                                  'delivered_at', 'completed_at', 'created_at', 'updated_at']:
                    if order.get(date_field):
                        order[date_field] = order[date_field].isoformat()
                
                orders.append(order)
            
            return orders
    
    async def get_order_count(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> int:
        """
        Obtiene el conteo total de órdenes con filtros opcionales
        
        Args:
            start_date: Fecha de inicio para filtrar
            end_date: Fecha de fin para filtrar
            status: Estado de la orden para filtrar
            
        Returns:
            Número total de órdenes
        """
        if not self.pool:
            await self.connect()
        
        query = "SELECT COUNT(*) FROM orders WHERE 1=1"
        params = []
        param_count = 1
        
        if start_date:
            query += f" AND created_at >= ${param_count}"
            params.append(start_date)
            param_count += 1
        
        if end_date:
            query += f" AND created_at <= ${param_count}"
            params.append(end_date)
            param_count += 1
        
        if status:
            query += f" AND status = ${param_count}"
            params.append(status)
            param_count += 1
        
        async with self.pool.acquire() as conn:
            count = await conn.fetchval(query, *params)
            return count
    
    async def get_orders_by_status(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, int]:
        """
        Obtiene el conteo de órdenes agrupadas por estado
        
        Args:
            start_date: Fecha de inicio para filtrar
            end_date: Fecha de fin para filtrar
            
        Returns:
            Diccionario con el conteo por estado
        """
        if not self.pool:
            await self.connect()
        
        query = """
            SELECT status, COUNT(*) as count
            FROM orders
            WHERE 1=1
        """
        
        params = []
        param_count = 1
        
        if start_date:
            query += f" AND created_at >= ${param_count}"
            params.append(start_date)
            param_count += 1
        
        if end_date:
            query += f" AND created_at <= ${param_count}"
            params.append(end_date)
            param_count += 1
        
        query += " GROUP BY status"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return {row['status']: row['count'] for row in rows}
    
    async def get_top_products(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtiene los productos más vendidos
        
        Args:
            start_date: Fecha de inicio para filtrar
            end_date: Fecha de fin para filtrar
            limit: Límite de resultados
            
        Returns:
            Lista de productos con su cantidad vendida
        """
        if not self.pool:
            await self.connect()
        
        query = """
            WITH order_items AS (
                SELECT 
                    jsonb_array_elements(items::jsonb) as item,
                    created_at
                FROM orders
                WHERE status NOT IN ('CANCELLED', 'FAILED')
        """
        
        params = []
        param_count = 1
        
        if start_date:
            query += f" AND created_at >= ${param_count}"
            params.append(start_date)
            param_count += 1
        
        if end_date:
            query += f" AND created_at <= ${param_count}"
            params.append(end_date)
            param_count += 1
        
        query += f"""
            )
            SELECT 
                item->>'product_id' as product_id,
                item->>'name' as product_name,
                SUM((item->>'quantity')::integer) as total_quantity,
                COUNT(*) as order_count
            FROM order_items
            GROUP BY item->>'product_id', item->>'name'
            ORDER BY total_quantity DESC
            LIMIT ${param_count}
        """
        params.append(limit)
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [
                {
                    'product_id': row['product_id'],
                    'product_name': row['product_name'],
                    'total_quantity': row['total_quantity'],
                    'order_count': row['order_count']
                }
                for row in rows
            ]
    
    async def get_sales_by_customer(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtiene las ventas agrupadas por cliente
        
        Args:
            start_date: Fecha de inicio para filtrar
            end_date: Fecha de fin para filtrar
            limit: Límite de resultados
            
        Returns:
            Lista de clientes con sus métricas de ventas
        """
        if not self.pool:
            await self.connect()
        
        query = """
            SELECT 
                customer_id,
                user_name,
                COUNT(*) as order_count,
                COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) as completed_orders,
                COUNT(CASE WHEN status = 'CANCELLED' THEN 1 END) as cancelled_orders
            FROM orders
            WHERE 1=1
        """
        
        params = []
        param_count = 1
        
        if start_date:
            query += f" AND created_at >= ${param_count}"
            params.append(start_date)
            param_count += 1
        
        if end_date:
            query += f" AND created_at <= ${param_count}"
            params.append(end_date)
            param_count += 1
        
        query += f"""
            GROUP BY customer_id, user_name
            ORDER BY order_count DESC
            LIMIT ${param_count}
        """
        params.append(limit)
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]


# Instancia global del cliente
db_client = DatabaseClient()
