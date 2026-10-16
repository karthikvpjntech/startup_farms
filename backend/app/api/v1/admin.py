from fastapi import APIRouter, Depends
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["Admin (RBAC Validation)"])


@router.get(
    "/rbac-test",
    summary="Super Admin RBAC Validation Endpoint",
    description="Stage 4 validation endpoint restricted exclusively to authenticated users with SUPER_ADMIN role."
)
def admin_rbac_test(
    current_user: User = Depends(require_roles(RoleEnum.SUPER_ADMIN))
):
    """
    Returns confirmation when the caller possesses the SUPER_ADMIN role.
    """
    return {
        "message": "Super Admin access granted",
        "user_id": str(current_user.id)
    }
