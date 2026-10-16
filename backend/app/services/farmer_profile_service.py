import logging
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import RoleEnum
from app.models.user import User
from app.models.farmer_profile import FarmerProfile
from app.schemas.farmer_profile import (
    FarmerProfileCreate,
    FarmerProfileUpdate,
    FarmerProfileResponse,
)
from app.repositories.farmer_profile_repository import FarmerProfileRepository

logger = logging.getLogger("agri_smart.farmer_profile_service")


class FarmerProfileService:
    """Service handling Farmer Profile business logic and validation."""

    @staticmethod
    def _verify_farmer_role(current_user: User) -> None:
        user_roles = {ur.role.name for ur in current_user.user_roles if ur.role and ur.role.is_active}
        if RoleEnum.FARMER.value not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have the FARMER role"
            )

    @staticmethod
    def get_profile(db: Session, current_user: User) -> FarmerProfileResponse:
        FarmerProfileService._verify_farmer_role(current_user)
        profile = FarmerProfileRepository.get_by_user_id(db, current_user.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        return FarmerProfileResponse.model_validate(profile)

    @staticmethod
    def _sanitize_data(data: dict) -> dict:
        """If user passed a Google Maps URL into profile_image_url, move it to location_url."""
        img_url = data.get("profile_image_url")
        if img_url and ("maps.app.goo.gl" in img_url or "google.com/maps" in img_url or "goo.gl/maps" in img_url):
            if not data.get("location_url"):
                data["location_url"] = img_url
            data["profile_image_url"] = None
        return data

    @staticmethod
    def create_profile(
        db: Session,
        current_user: User,
        request: FarmerProfileCreate
    ) -> FarmerProfileResponse:
        FarmerProfileService._verify_farmer_role(current_user)
        existing = FarmerProfileRepository.get_by_user_id(db, current_user.id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Profile already exists"
            )

        data = FarmerProfileService._sanitize_data(request.model_dump(exclude_unset=True))
        profile = FarmerProfileRepository.create(
            db=db,
            user_id=current_user.id,
            profile_data=data
        )
        logger.info("Farmer profile created for user %s", current_user.id)
        return FarmerProfileResponse.model_validate(profile)

    @staticmethod
    def update_profile(
        db: Session,
        current_user: User,
        request: FarmerProfileUpdate
    ) -> FarmerProfileResponse:
        FarmerProfileService._verify_farmer_role(current_user)
        profile = FarmerProfileRepository.get_by_user_id(db, current_user.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )

        data = FarmerProfileService._sanitize_data(request.model_dump(exclude_unset=True))
        updated_profile = FarmerProfileRepository.update(
            db=db,
            profile=profile,
            update_data=data
        )
        logger.info("Farmer profile updated for user %s", current_user.id)
        return FarmerProfileResponse.model_validate(updated_profile)
