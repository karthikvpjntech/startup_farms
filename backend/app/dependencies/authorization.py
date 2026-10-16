from typing import Union, Callable, Set
from fastapi import Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.models.enums import RoleEnum
from app.models.user import User


def require_roles(*allowed_roles: Union[RoleEnum, str]) -> Callable:
    """
    Role-Based Access Control (RBAC) dependency factory.

    Enforces that the authenticated user possesses at least one of the specified allowed roles
    (ANY-role match) based on their current active roles loaded from PostgreSQL.

    Raises:
        HTTPException (403 Forbidden): If the user does not possess any of the allowed roles.
        HTTPException (401 Unauthorized): If authentication fails or account is inactive/deleted.

    Returns:
        The authenticated User model instance.
    """
    # Normalize required role names to uppercase strings (flattening lists/tuples if passed)
    flat_roles = []
    for r in allowed_roles:
        if isinstance(r, (list, tuple, set)):
            flat_roles.extend(r)
        else:
            flat_roles.append(r)

    required_role_names: Set[str] = {
        r.value.upper() if isinstance(r, RoleEnum) else str(r).upper()
        for r in flat_roles
    }

    def role_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        # Resolve active database roles assigned to the user
        user_active_role_names: Set[str] = {
            ur.role.name.upper()
            for ur in current_user.user_roles
            if ur.role and ur.role.is_active
        }

        # Check if user possesses at least one required role (ANY-match logic)
        if not required_role_names.intersection(user_active_role_names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )

        return current_user

    return role_checker


def require_role(allowed_role: Union[RoleEnum, str]) -> Callable:
    """
    Convenience alias for single-role protection.
    """
    return require_roles(allowed_role)
