import uuid
import math
import logging
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.enums import RoleEnum
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository
from app.schemas.admin_user import (
    AdminUserCreateRequest,
    AdminUserUpdateRequest,
    AdminUserStatusRequest,
    AdminRoleAssignRequest,
    AdminUserResponse,
    AdminUserListResponse,
    AdminUserRolesResponse,
)

logger = logging.getLogger("agri_smart.admin_user_service")


class AdminUserService:
    """Service handling Super Admin operations on users and role assignments."""

    @staticmethod
    def _to_user_response(user: User) -> AdminUserResponse:
        roles = [ur.role.name for ur in user.user_roles if ur.role and ur.role.is_active]
        return AdminUserResponse(
            id=user.id,
            full_name=user.full_name,
            mobile_number=user.mobile_number,
            email=user.email,
            is_active=user.is_active,
            is_deleted=user.is_deleted,
            roles=roles,
            created_at=user.created_at,
            updated_at=user.updated_at,
            created_by=user.created_by,
            updated_by=user.updated_by,
            deleted_at=user.deleted_at,
            deleted_by=user.deleted_by,
        )

    @staticmethod
    def create_user(
        db: Session,
        request: AdminUserCreateRequest,
        current_admin: User
    ) -> AdminUserResponse:
        """Create a new user with initial assigned roles."""
        # 1. Uniqueness validation
        if UserRepository.get_by_mobile_any(db, request.mobile_number):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this mobile number already exists"
            )

        if request.email and UserRepository.get_by_email_any(db, request.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists"
            )

        # 2. Role validation against DB
        db_roles = RoleRepository.get_by_names(db, request.roles)
        if len(db_roles) != len(request.roles):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more requested roles do not exist in the system"
            )

        # 3. Hash password using Argon2id
        password_hash = get_password_hash(request.password)

        # 4. Create user transactionally with roles
        user = UserRepository.create_with_roles(
            db=db,
            full_name=request.full_name,
            mobile_number=request.mobile_number,
            password_hash=password_hash,
            email=request.email,
            roles=db_roles,
            created_by=current_admin.id,
            is_active=True
        )

        logger.info("Super Admin %s created user %s (%s)", current_admin.id, user.id, user.mobile_number)
        return AdminUserService._to_user_response(user)

    @staticmethod
    def list_users(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_deleted: Optional[bool] = None
    ) -> AdminUserListResponse:
        """List users with pagination, text search, and role/status filters."""
        # Normalize pagination bounds
        safe_page = max(1, page)
        safe_page_size = min(max(1, page_size), 100)
        skip = (safe_page - 1) * safe_page_size

        total = UserRepository.count_users(
            db=db,
            search=search,
            role_name=role,
            is_active=is_active,
            is_deleted=is_deleted
        )

        users = UserRepository.list_users(
            db=db,
            skip=skip,
            limit=safe_page_size,
            search=search,
            role_name=role,
            is_active=is_active,
            is_deleted=is_deleted
        )

        items = [AdminUserService._to_user_response(u) for u in users]
        total_pages = math.ceil(total / safe_page_size) if total > 0 else 0

        return AdminUserListResponse(
            items=items,
            page=safe_page,
            page_size=safe_page_size,
            total=total,
            total_pages=total_pages
        )

    @staticmethod
    def get_user(db: Session, user_id: uuid.UUID) -> AdminUserResponse:
        """Retrieve user details by UUID."""
        user = UserRepository.get_by_id(db, user_id, include_deleted=True)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return AdminUserService._to_user_response(user)

    @staticmethod
    def update_user_profile(
        db: Session,
        user_id: uuid.UUID,
        request: AdminUserUpdateRequest,
        current_admin: User
    ) -> AdminUserResponse:
        """Update basic profile fields (full_name, mobile_number, email)."""
        user = UserRepository.get_by_id(db, user_id, include_deleted=True)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if request.mobile_number and request.mobile_number != user.mobile_number:
            existing = UserRepository.get_by_mobile_any(db, request.mobile_number)
            if existing and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A user with this mobile number already exists"
                )

        if request.email and request.email != user.email:
            existing = UserRepository.get_by_email_any(db, request.email)
            if existing and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A user with this email already exists"
                )

        updated_user = UserRepository.update_profile(
            db=db,
            user=user,
            full_name=request.full_name,
            mobile_number=request.mobile_number,
            email=request.email,
            updated_by=current_admin.id
        )

        logger.info("Super Admin %s updated profile of user %s", current_admin.id, user.id)
        return AdminUserService._to_user_response(updated_user)

    @staticmethod
    def change_user_status(
        db: Session,
        user_id: uuid.UUID,
        request: AdminUserStatusRequest,
        current_admin: User
    ) -> AdminUserResponse:
        """Activate or deactivate user account with safety checks."""
        user = UserRepository.get_by_id(db, user_id, include_deleted=True)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not request.is_active:
            # Self-protection check
            if user.id == current_admin.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot deactivate your own account"
                )

            # Last active Super Admin check
            user_roles = {ur.role.name for ur in user.user_roles if ur.role and ur.role.is_active}
            if RoleEnum.SUPER_ADMIN.value in user_roles and user.is_active and not user.is_deleted:
                active_super_admins = UserRepository.count_active_super_admins(db)
                if active_super_admins <= 1:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="At least one active Super Admin must remain"
                    )

        updated_user = UserRepository.set_active_status(
            db=db,
            user=user,
            is_active=request.is_active,
            updated_by=current_admin.id
        )

        logger.info("Super Admin %s set status of user %s to is_active=%s", current_admin.id, user.id, request.is_active)
        return AdminUserService._to_user_response(updated_user)

    @staticmethod
    def delete_user(
        db: Session,
        user_id: uuid.UUID,
        current_admin: User
    ) -> AdminUserResponse:
        """Soft-delete user account with safety checks."""
        user = UserRepository.get_by_id(db, user_id, include_deleted=True)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Self-protection check
        if user.id == current_admin.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete your own account"
            )

        # Last active Super Admin check
        user_roles = {ur.role.name for ur in user.user_roles if ur.role and ur.role.is_active}
        if RoleEnum.SUPER_ADMIN.value in user_roles and user.is_active and not user.is_deleted:
            active_super_admins = UserRepository.count_active_super_admins(db)
            if active_super_admins <= 1:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="At least one active Super Admin must remain"
                )

        deleted_user = UserRepository.soft_delete(
            db=db,
            user=user,
            deleted_by=current_admin.id
        )

        logger.info("Super Admin %s soft-deleted user %s", current_admin.id, user.id)
        return AdminUserService._to_user_response(deleted_user)

    @staticmethod
    def restore_user(
        db: Session,
        user_id: uuid.UUID,
        current_admin: User
    ) -> AdminUserResponse:
        """Restore a soft-deleted user account (is_active remains unchanged)."""
        user = UserRepository.get_by_id(db, user_id, include_deleted=True)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        restored_user = UserRepository.restore(
            db=db,
            user=user,
            restored_by=current_admin.id
        )

        logger.info("Super Admin %s restored user %s", current_admin.id, user.id)
        return AdminUserService._to_user_response(restored_user)

    @staticmethod
    def assign_roles(
        db: Session,
        user_id: uuid.UUID,
        request: AdminRoleAssignRequest,
        current_admin: User
    ) -> AdminUserRolesResponse:
        """Assign one or more existing system roles to a user without removing existing roles."""
        user = UserRepository.get_by_id(db, user_id, include_deleted=True)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        db_roles = RoleRepository.get_by_names(db, request.roles)
        if len(db_roles) != len(request.roles):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more requested roles do not exist in the system"
            )

        for role in db_roles:
            UserRepository.assign_role(db, user.id, role.id)

        db.expire_all()
        # Refresh user roles
        refreshed_user = UserRepository.get_by_id(db, user.id, include_deleted=True)
        roles = [ur.role.name for ur in refreshed_user.user_roles if ur.role and ur.role.is_active]

        logger.info("Super Admin %s assigned roles %s to user %s", current_admin.id, request.roles, user.id)
        return AdminUserRolesResponse(user_id=user.id, roles=roles)

    @staticmethod
    def remove_role(
        db: Session,
        user_id: uuid.UUID,
        role_name: str,
        current_admin: User
    ) -> AdminUserRolesResponse:
        """Remove a specific role assignment from a user."""
        norm_role_name = role_name.strip().upper()
        user = UserRepository.get_by_id(db, user_id, include_deleted=True)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        role = RoleRepository.get_by_name(db, norm_role_name)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{norm_role_name}' does not exist"
            )

        user_role_names = {ur.role.name for ur in user.user_roles if ur.role}
        if norm_role_name not in user_role_names:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{norm_role_name}' is not assigned to this user"
            )

        # If removing SUPER_ADMIN role, perform safety checks
        if norm_role_name == RoleEnum.SUPER_ADMIN.value:
            # Self-protection
            if user.id == current_admin.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot remove SUPER_ADMIN role from your own account"
                )

            # Last active Super Admin check
            if user.is_active and not user.is_deleted:
                active_super_admins = UserRepository.count_active_super_admins(db)
                if active_super_admins <= 1:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="At least one active Super Admin must remain"
                    )

        UserRepository.remove_role(db, user.id, role.id)

        db.expire_all()
        # Refresh user roles
        refreshed_user = UserRepository.get_by_id(db, user.id, include_deleted=True)
        roles = [ur.role.name for ur in refreshed_user.user_roles if ur.role and ur.role.is_active]

        logger.info("Super Admin %s removed role %s from user %s", current_admin.id, norm_role_name, user.id)
        return AdminUserRolesResponse(user_id=user.id, roles=roles)
