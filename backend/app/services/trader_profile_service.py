import logging
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import RoleEnum
from app.models.user import User
from app.models.trader_profile import TraderProfile
from app.schemas.trader_profile import (
    TraderProfileCreate,
    TraderProfileUpdate,
    TraderProfileResponse,
)
from app.repositories.trader_profile_repository import TraderProfileRepository

logger = logging.getLogger("agri_smart.trader_profile_service")


class TraderProfileService:
    """Service handling Trader Profile business logic and validation."""

    @staticmethod
    def _verify_trader_role(current_user: User) -> None:
        user_roles = {ur.role.name for ur in current_user.user_roles if ur.role and ur.role.is_active}
        if RoleEnum.TRADER.value not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have the TRADER role"
            )

    @staticmethod
    def get_profile(db: Session, current_user: User) -> TraderProfileResponse:
        TraderProfileService._verify_trader_role(current_user)
        profile = TraderProfileRepository.get_by_user_id(db, current_user.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        return TraderProfileResponse.model_validate(profile)

    @staticmethod
    def create_profile(
        db: Session,
        current_user: User,
        request: TraderProfileCreate
    ) -> TraderProfileResponse:
        TraderProfileService._verify_trader_role(current_user)
        existing = TraderProfileRepository.get_by_user_id(db, current_user.id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Profile already exists"
            )

        profile = TraderProfileRepository.create(
            db=db,
            user_id=current_user.id,
            profile_data=request.model_dump(exclude_unset=True)
        )
        logger.info("Trader profile created for user %s", current_user.id)
        return TraderProfileResponse.model_validate(profile)

    @staticmethod
    def update_profile(
        db: Session,
        current_user: User,
        request: TraderProfileUpdate
    ) -> TraderProfileResponse:
        TraderProfileService._verify_trader_role(current_user)
        profile = TraderProfileRepository.get_by_user_id(db, current_user.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )

        updated_profile = TraderProfileRepository.update(
            db=db,
            profile=profile,
            update_data=request.model_dump(exclude_unset=True)
        )
        logger.info("Trader profile updated for user %s", current_user.id)
        return TraderProfileResponse.model_validate(updated_profile)
