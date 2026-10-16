from fastapi import APIRouter, Depends
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User

router = APIRouter(prefix="/rbac", tags=["RBAC Validation"])


@router.get(
    "/multi-role-test",
    summary="Multi-Role RBAC Validation Endpoint",
    description="Stage 4 validation endpoint accessible to authenticated users with either SUPER_ADMIN or FARMER role."
)
def multi_role_test(
    current_user: User = Depends(require_roles(RoleEnum.SUPER_ADMIN, RoleEnum.FARMER))
):
    """
    Returns confirmation when the caller possesses at least one of the allowed roles (SUPER_ADMIN or FARMER).
    """
    active_roles = [
        ur.role.name for ur in current_user.user_roles if ur.role and ur.role.is_active
    ]
    return {
        "message": "Multi-role access granted",
        "user_id": str(current_user.id),
        "roles": active_roles
    }
