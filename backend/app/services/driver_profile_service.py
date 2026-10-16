import logging
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import RoleEnum
from app.models.user import User
from app.models.driver_profile import DriverProfile
from app.schemas.driver_profile import (
    DriverProfileCreate,
    DriverProfileUpdate,
    DriverProfileResponse,
)
from app.repositories.driver_profile_repository import DriverProfileRepository

logger = logging.getLogger("agri_smart.driver_profile_service")


class DriverProfileService:
    """Service handling Driver Profile business logic and validation."""

    @staticmethod
    def _verify_driver_role(current_user: User) -> None:
        user_roles = {ur.role.name for ur in current_user.user_roles if ur.role and ur.role.is_active}
        if RoleEnum.DRIVER.value not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have the DRIVER role"
            )

    @staticmethod
    def get_profile(db: Session, current_user: User) -> DriverProfileResponse:
        DriverProfileService._verify_driver_role(current_user)
        profile = DriverProfileRepository.get_by_user_id(db, current_user.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        return DriverProfileResponse.model_validate(profile)

    @staticmethod
    def create_profile(
        db: Session,
        current_user: User,
        request: DriverProfileCreate
    ) -> DriverProfileResponse:
        DriverProfileService._verify_driver_role(current_user)
        existing = DriverProfileRepository.get_by_user_id(db, current_user.id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Profile already exists"
            )

        profile = DriverProfileRepository.create(
            db=db,
            user_id=current_user.id,
            profile_data=request.model_dump(exclude_unset=True)
        )
        logger.info("Driver profile created for user %s", current_user.id)
        return DriverProfileResponse.model_validate(profile)

    @staticmethod
    def update_profile(
        db: Session,
        current_user: User,
        request: DriverProfileUpdate
    ) -> DriverProfileResponse:
        DriverProfileService._verify_driver_role(current_user)
        profile = DriverProfileRepository.get_by_user_id(db, current_user.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )

        updated_profile = DriverProfileRepository.update(
            db=db,
            profile=profile,
            update_data=request.model_dump(exclude_unset=True)
        )
        logger.info("Driver profile updated for user %s", current_user.id)
        return DriverProfileResponse.model_validate(updated_profile)
