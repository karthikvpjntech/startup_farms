import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.admin_user import (
    AdminUserCreateRequest,
    AdminUserUpdateRequest,
    AdminUserStatusRequest,
    AdminRoleAssignRequest,
    AdminUserResponse,
    AdminUserListResponse,
    AdminUserRolesResponse,
)
from app.services.admin_user_service import AdminUserService

router = APIRouter(prefix="/admin/users", tags=["Admin (User Management)"])


@router.post(
    "",
    response_model=AdminUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create User",
    description="Creates a new user account with initial assigned system roles. Protected by SUPER_ADMIN role."
)
def create_user(
    request: AdminUserCreateRequest,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Super Admin endpoint to create a user and assign one or more predefined roles.
    """
    return AdminUserService.create_user(db=db, request=request, current_admin=current_admin)


@router.get(
    "",
    response_model=AdminUserListResponse,
    summary="List Users",
    description="Retrieves a paginated list of users with optional search and filters. Protected by SUPER_ADMIN role."
)
def list_users(
    page: int = Query(default=1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (1-100)"),
    search: Optional[str] = Query(default=None, description="Search term for full_name, email, or mobile_number"),
    role: Optional[str] = Query(default=None, description="Filter users possessing this role"),
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
    is_deleted: Optional[bool] = Query(default=None, description="Filter by soft-deleted status"),
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Super Admin endpoint to list all users with pagination and search/filtering.
    """
    return AdminUserService.list_users(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        role=role,
        is_active=is_active,
        is_deleted=is_deleted
    )


@router.get(
    "/{user_id}",
    response_model=AdminUserResponse,
    summary="Get User Detail",
    description="Retrieves comprehensive details for a specific user by UUID. Protected by SUPER_ADMIN role."
)
def get_user_detail(
    user_id: uuid.UUID,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Super Admin endpoint to retrieve single user details.
    """
    return AdminUserService.get_user(db=db, user_id=user_id)


@router.patch(
    "/{user_id}",
    response_model=AdminUserResponse,
    summary="Update User Profile",
    description="Updates user identity fields (full_name, mobile_number, email). Protected by SUPER_ADMIN role."
)
def update_user_profile(
    user_id: uuid.UUID,
    request: AdminUserUpdateRequest,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Super Admin endpoint to update profile fields for a user.
    """
    return AdminUserService.update_user_profile(
        db=db,
        user_id=user_id,
        request=request,
        current_admin=current_admin
    )


@router.patch(
    "/{user_id}/status",
    response_model=AdminUserResponse,
    summary="Change User Active Status",
    description="Activates or deactivates a user account. Enforces self-lockout and last Super Admin protections."
)
def change_user_status(
    user_id: uuid.UUID,
    request: AdminUserStatusRequest,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Super Admin endpoint to activate or deactivate a user account.
    """
    return AdminUserService.change_user_status(
        db=db,
        user_id=user_id,
        request=request,
        current_admin=current_admin
    )


@router.delete(
    "/{user_id}",
    response_model=AdminUserResponse,
    summary="Soft Delete User",
    description="Soft-deletes a user account. Sets is_deleted=true and records audit info. Enforces safety rules."
)
def soft_delete_user(
    user_id: uuid.UUID,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Super Admin endpoint to soft-delete a user.
    """
    return AdminUserService.delete_user(
        db=db,
        user_id=user_id,
        current_admin=current_admin
    )


@router.post(
    "/{user_id}/restore",
    response_model=AdminUserResponse,
    summary="Restore User",
    description="Restores a previously soft-deleted user. is_active is preserved as-is. Protected by SUPER_ADMIN role."
)
def restore_user(
    user_id: uuid.UUID,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Super Admin endpoint to restore a soft-deleted user.
    """
    return AdminUserService.restore_user(
        db=db,
        user_id=user_id,
        current_admin=current_admin
    )


@router.post(
    "/{user_id}/roles",
    response_model=AdminUserRolesResponse,
    summary="Assign Roles to User",
    description="Assigns one or more existing system roles to a user without removing existing roles."
)
def assign_roles(
    user_id: uuid.UUID,
    request: AdminRoleAssignRequest,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Super Admin endpoint to assign roles to a user.
    """
    return AdminUserService.assign_roles(
        db=db,
        user_id=user_id,
        request=request,
        current_admin=current_admin
    )


@router.delete(
    "/{user_id}/roles/{role_name}",
    response_model=AdminUserRolesResponse,
    summary="Remove Role from User",
    description="Removes a specific role assignment from a user. Enforces self-lockout and last Super Admin protections."
)
def remove_role(
    user_id: uuid.UUID,
    role_name: str,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Super Admin endpoint to remove a role from a user.
    """
    return AdminUserService.remove_role(
        db=db,
        user_id=user_id,
        role_name=role_name,
        current_admin=current_admin
    )
