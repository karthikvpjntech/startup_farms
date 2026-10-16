"""FastAPI dependency injection utilities."""
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.authorization import require_roles, require_role

__all__ = [
    "get_db",
    "get_current_user",
    "require_roles",
    "require_role",
]
