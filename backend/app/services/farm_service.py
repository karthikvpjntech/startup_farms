import logging
import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import RoleEnum
from app.models.user import User
from app.models.farmer_profile import FarmerProfile
from app.repositories.farmer_profile_repository import FarmerProfileRepository
from app.repositories.farm_repository import FarmRepository
from app.schemas.farm import (
    FarmCreate,
    FarmUpdate,
    FarmStatusUpdate,
    FarmResponse,
    FarmListResponse,
)

logger = logging.getLogger("agri_smart.farm_service")


class FarmService:
    """Service handling Farm business logic, ownership enforcement, and validation."""

    @staticmethod
    def _resolve_farmer_profile(db: Session, current_user: User) -> FarmerProfile:
        """
        Validates that the authenticated user possesses the FARMER role and has completed their FarmerProfile.
        Raises HTTP 403 if missing role, or HTTP 409 if profile has not been created yet.
        """
        user_roles = {ur.role.name for ur in current_user.user_roles if ur.role and ur.role.is_active}
        if RoleEnum.FARMER.value not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have the FARMER role"
            )

        profile = FarmerProfileRepository.get_by_user_id(db, current_user.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Farmer profile must be completed before managing farms"
            )
        return profile

    @staticmethod
    def create_farm(
        db: Session,
        current_user: User,
        request: FarmCreate
    ) -> FarmResponse:
        """Creates a new farm for the authenticated farmer with unique auto-generated farm code."""
        farmer_profile = FarmService._resolve_farmer_profile(db, current_user)

        # Check duplicate active farm name under the same farmer profile
        existing_farm = FarmRepository.get_active_by_name(db, farmer_profile.id, request.farm_name)
        if existing_farm:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A farm with this name already exists for your profile"
            )

        farm_code = FarmRepository.generate_next_farm_code(db)
        farm = FarmRepository.create(
            db=db,
            farmer_profile_id=farmer_profile.id,
            farm_code=farm_code,
            farm_data=request.model_dump(),
            created_by=current_user.id
        )
        logger.info("Farm created: code=%s id=%s farmer_profile_id=%s", farm.farm_code, farm.id, farmer_profile.id)
        return FarmResponse.model_validate(farm)

    @staticmethod
    def list_farms(
        db: Session,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> FarmListResponse:
        """Retrieves paginated non-deleted farms belonging exclusively to the authenticated farmer."""
        farmer_profile = FarmService._resolve_farmer_profile(db, current_user)
        skip = (page - 1) * page_size
        farms = FarmRepository.list_by_farmer_profile(
            db=db,
            farmer_profile_id=farmer_profile.id,
            skip=skip,
            limit=page_size,
            search=search,
            is_active=is_active,
            include_deleted=False
        )
        total = FarmRepository.count_by_farmer_profile(
            db=db,
            farmer_profile_id=farmer_profile.id,
            search=search,
            is_active=is_active,
            include_deleted=False
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return FarmListResponse(
            items=[FarmResponse.model_validate(f) for f in farms],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages
        )

    @staticmethod
    def get_farm_detail(
        db: Session,
        current_user: User,
        farm_id: uuid.UUID
    ) -> FarmResponse:
        """Retrieves details of an owned non-deleted farm. Returns 404 if not found or owned by another farmer."""
        farmer_profile = FarmService._resolve_farmer_profile(db, current_user)
        farm = FarmRepository.get_by_id(
            db=db,
            farm_id=farm_id,
            farmer_profile_id=farmer_profile.id,
            include_deleted=False
        )
        if not farm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm not found"
            )
        return FarmResponse.model_validate(farm)

    @staticmethod
    def update_farm(
        db: Session,
        current_user: User,
        farm_id: uuid.UUID,
        request: FarmUpdate
    ) -> FarmResponse:
        """Partially updates mutable farm details for the owned farm."""
        farmer_profile = FarmService._resolve_farmer_profile(db, current_user)
        farm = FarmRepository.get_by_id(
            db=db,
            farm_id=farm_id,
            farmer_profile_id=farmer_profile.id,
            include_deleted=False
        )
        if not farm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm not found"
            )

        update_dict = request.model_dump(exclude_unset=True)
        new_name = update_dict.get("farm_name")
        if new_name and new_name.strip().lower() != farm.farm_name.strip().lower():
            existing = FarmRepository.get_active_by_name(
                db=db,
                farmer_profile_id=farmer_profile.id,
                farm_name=new_name,
                exclude_farm_id=farm.id
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A farm with this name already exists for your profile"
                )

        updated_farm = FarmRepository.update(
            db=db,
            farm=farm,
            update_data=update_dict,
            updated_by=current_user.id
        )
        logger.info("Farm %s updated by user %s", farm_id, current_user.id)
        return FarmResponse.model_validate(updated_farm)

    @staticmethod
    def update_farm_status(
        db: Session,
        current_user: User,
        farm_id: uuid.UUID,
        request: FarmStatusUpdate
    ) -> FarmResponse:
        """Updates active status of an owned non-deleted farm."""
        farmer_profile = FarmService._resolve_farmer_profile(db, current_user)
        farm = FarmRepository.get_by_id(
            db=db,
            farm_id=farm_id,
            farmer_profile_id=farmer_profile.id,
            include_deleted=True
        )
        if not farm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm not found"
            )
        if farm.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update status of a deleted farm. Restore the farm first."
            )

        updated_farm = FarmRepository.update_status(
            db=db,
            farm=farm,
            is_active=request.is_active,
            updated_by=current_user.id
        )
        logger.info("Farm %s status changed to is_active=%s", farm_id, request.is_active)
        return FarmResponse.model_validate(updated_farm)

    @staticmethod
    def delete_farm(
        db: Session,
        current_user: User,
        farm_id: uuid.UUID
    ) -> FarmResponse:
        """Soft-deletes an owned farm."""
        farmer_profile = FarmService._resolve_farmer_profile(db, current_user)
        farm = FarmRepository.get_by_id(
            db=db,
            farm_id=farm_id,
            farmer_profile_id=farmer_profile.id,
            include_deleted=False
        )
        if not farm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm not found"
            )

        deleted_farm = FarmRepository.soft_delete(
            db=db,
            farm=farm,
            deleted_by=current_user.id
        )
        logger.info("Farm %s soft-deleted by user %s", farm_id, current_user.id)
        return FarmResponse.model_validate(deleted_farm)

    @staticmethod
    def restore_farm(
        db: Session,
        current_user: User,
        farm_id: uuid.UUID
    ) -> FarmResponse:
        """Restores a soft-deleted owned farm without modifying is_active status."""
        farmer_profile = FarmService._resolve_farmer_profile(db, current_user)
        farm = FarmRepository.get_by_id(
            db=db,
            farm_id=farm_id,
            farmer_profile_id=farmer_profile.id,
            include_deleted=True
        )
        if not farm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm not found"
            )
        if not farm.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Farm is not deleted"
            )

        # Check duplicate name with active farms
        existing = FarmRepository.get_active_by_name(
            db=db,
            farmer_profile_id=farmer_profile.id,
            farm_name=farm.farm_name,
            exclude_farm_id=farm.id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An active farm with this name already exists. Rename or adjust existing farm first."
            )

        restored_farm = FarmRepository.restore(
            db=db,
            farm=farm,
            updated_by=current_user.id
        )
        logger.info("Farm %s restored by user %s", farm_id, current_user.id)
        return FarmResponse.model_validate(restored_farm)
