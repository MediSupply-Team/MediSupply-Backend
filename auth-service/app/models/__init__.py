# app/models/__init__.py
from app.database import Base
from app.models.role import Role, role_permissions
from app.models.permission import Permission
from app.models.user import User

# Exportar todo
__all__ = ["Base", "Role", "Permission", "User", "role_permissions"]