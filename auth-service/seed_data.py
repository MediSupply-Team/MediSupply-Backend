# auth-service/seed_data.py
"""Inserta datos iniciales: roles, permisos y usuarios de ejemplo"""
import asyncio
from sqlalchemy import select, func, insert
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.user import User
from app.models.role import Role, role_permissions
from app.models.permission import Permission
from app.services.password_service import password_service
from app.config import settings
import sys

def get_async_url(url: str) -> str:
    """Convierte postgresql:// a postgresql+asyncpg://"""
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    return url

async def seed():
    try:
        engine = create_async_engine(get_async_url(settings.DATABASE_URL))
        SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
        
        async with SessionLocal() as db:
            # Verificar si ya hay datos
            result = await db.execute(select(func.count()).select_from(Role))
            count = result.scalar()
            
            if count > 0:
                print("ℹ️  Ya existen datos en la base de datos")
                await engine.dispose()
                return
            
            print("🌱 Insertando roles...")
            roles_data = [
                {"id": 1, "name": "ADMIN", "description": "Administrador del sistema"},
                {"id": 2, "name": "HOSPITAL_ADMIN", "description": "Administrador de hospital"},
                {"id": 3, "name": "WAREHOUSE_STAFF", "description": "Personal de almacén"},
                {"id": 4, "name": "DRIVER", "description": "Conductor de entregas"},
                {"id": 5, "name": "SELLER", "description": "Proveedor/Vendedor"},
                {"id": 6, "name": "CUSTOMER", "description": "Cliente/Comprador"},
            ]
            
            for role_data in roles_data:
                role = Role(**role_data)
                db.add(role)
            
            await db.commit()
            print(f"✅ {len(roles_data)} roles insertados")
            
            print("🌱 Insertando permisos...")
            permissions_data = [
                {"name": "orders:create", "resource": "orders", "action": "create"},
                {"name": "orders:read", "resource": "orders", "action": "read"},
                {"name": "orders:update", "resource": "orders", "action": "update"},
                {"name": "orders:delete", "resource": "orders", "action": "delete"},
                {"name": "catalog:read", "resource": "catalog", "action": "read"},
                {"name": "catalog:manage", "resource": "catalog", "action": "manage"},
                {"name": "routes:view", "resource": "routes", "action": "read"},
                {"name": "routes:optimize", "resource": "routes", "action": "optimize"},
                {"name": "users:manage", "resource": "users", "action": "manage"},
            ]
            
            perm_map = {}
            for perm_data in permissions_data:
                permission = Permission(**perm_data)
                db.add(permission)
                await db.flush()
                perm_map[perm_data["name"]] = permission.id
            
            await db.commit()
            print(f"✅ {len(permissions_data)} permisos insertados")
            
            print("🌱 Asignando permisos a roles...")
            
            # ADMIN - todos los permisos (role_id=1)
            for perm_id in perm_map.values():
                await db.execute(
                    insert(role_permissions).values(role_id=1, permission_id=perm_id)
                )
            
            # HOSPITAL_ADMIN (role_id=2)
            hospital_perms = ["orders:create", "orders:read", "catalog:read"]
            for perm_name in hospital_perms:
                await db.execute(
                    insert(role_permissions).values(role_id=2, permission_id=perm_map[perm_name])
                )
            
            # WAREHOUSE_STAFF (role_id=3)
            warehouse_perms = ["catalog:manage", "catalog:read", "orders:read"]
            for perm_name in warehouse_perms:
                await db.execute(
                    insert(role_permissions).values(role_id=3, permission_id=perm_map[perm_name])
                )
            
            # DRIVER (role_id=4)
            driver_perms = ["routes:view", "orders:read"]
            for perm_name in driver_perms:
                await db.execute(
                    insert(role_permissions).values(role_id=4, permission_id=perm_map[perm_name])
                )
            
            # SELLER (role_id=5)
            vendor_perms = ["orders:read", "catalog:read"]
            for perm_name in vendor_perms:
                await db.execute(
                    insert(role_permissions).values(role_id=5, permission_id=perm_map[perm_name])
                )
            
            # CUSTOMER (role_id=6)
            customer_perms = ["orders:create", "orders:read", "catalog:read"]
            for perm_name in customer_perms:
                await db.execute(
                    insert(role_permissions).values(role_id=6, permission_id=perm_map[perm_name])
                )
            
            await db.commit()
            print("✅ Permisos asignados a roles")
            
            print("🌱 Creando usuarios de ejemplo...")
            
            # Usuario Admin
            admin_user = User(
                email="admin@medisupply.com",
                password_hash=password_service.hash_password("admin123"),
                name="Admin MediSupply",
                role_id=1,
                is_active=True
            )
            db.add(admin_user)
            
            # Usuario Hospital Admin
            hospital_admin = User(
                email="hospital@medisupply.com",
                password_hash=password_service.hash_password("hospital123"),
                name="Hospital San José",
                role_id=2,
                is_active=True
            )
            db.add(hospital_admin)
            
            # Usuario Warehouse Staff
            warehouse_user = User(
                email="warehouse@medisupply.com",
                password_hash=password_service.hash_password("warehouse123"),
                name="Juan Pérez - Almacén",
                role_id=3,
                is_active=True
            )
            db.add(warehouse_user)
            
            # Usuario Driver
            driver_user = User(
                email="driver@medisupply.com",
                password_hash=password_service.hash_password("driver123"),
                name="Carlos Rodríguez - Conductor",
                role_id=4,
                is_active=True
            )
            db.add(driver_user)
            
            # Usuario Seller
            seller_user = User(
                email="seller@medisupply.com",
                password_hash=password_service.hash_password("seller123"),
                name="Farmacia Central - Vendedor",
                role_id=5,
                is_active=True
            )
            db.add(seller_user)
            
            # Usuario Customer
            customer_user = User(
                email="customer@medisupply.com",
                password_hash=password_service.hash_password("customer123"),
                name="Hospital General - Cliente",
                role_id=6,
                is_active=True
            )
            db.add(customer_user)
            
            await db.commit()
            
            print("\n✅ Usuarios creados exitosamente:")
            print("  👤 admin@medisupply.com / admin123 (ADMIN)")
            print("  👤 hospital@medisupply.com / hospital123 (HOSPITAL_ADMIN)")
            print("  👤 warehouse@medisupply.com / warehouse123 (WAREHOUSE_STAFF)")
            print("  👤 driver@medisupply.com / driver123 (DRIVER)")
            print("  👤 seller@medisupply.com / seller123 (SELLER)")
            print("  👤 customer@medisupply.com / customer123 (CUSTOMER)")
            print("\n✅ Seed completado exitosamente!")
        
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Error en seed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(seed())