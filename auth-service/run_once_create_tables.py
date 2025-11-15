# auth-service/run_once_create_tables.py
import asyncio
from app.database import engine, Base
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tablas creadas exitosamente")

if __name__ == "__main__":
    asyncio.run(main())