import logging
import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.crop import Crop
from app.repositories.crop_repository import CropRepository
from app.schemas.crop import (
    CropCreate,
    CropUpdate,
    CropStatusUpdate,
    CropResponse,
    CropListResponse,
)

logger = logging.getLogger("agri_smart.crop_service")


class CropService:
    """Service handling Crop Master administration and farmer catalog access."""

    @staticmethod
    def create_crop(
        db: Session,
        request: CropCreate,
        current_admin: User
    ) -> CropResponse:
        """Creates a new Crop Master record with auto-generated code and duplicate name check."""
        existing = CropRepository.get_active_by_name(db, request.crop_name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An active crop with this name already exists"
            )

        crop_code = CropRepository.generate_next_crop_code(db)
        crop = CropRepository.create(
            db=db,
            crop_code=crop_code,
            crop_data=request.model_dump(),
            created_by=current_admin.id
        )
        logger.info("Crop created: code=%s name='%s' id=%s", crop.crop_code, crop.crop_name, crop.id)
        return CropResponse.model_validate(crop)

    @staticmethod
    def list_admin_crops(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_deleted: Optional[bool] = None
    ) -> CropListResponse:
        """Retrieves paginated crop records for Super Admin with search and status filters."""
        skip = (page - 1) * page_size
        crops = CropRepository.list_crops(
            db=db,
            skip=skip,
            limit=page_size,
            search=search,
            category=category,
            is_active=is_active,
            include_deleted=(is_deleted is True or is_deleted is None)
        )
        total = CropRepository.count_crops(
            db=db,
            search=search,
            category=category,
            is_active=is_active,
            include_deleted=(is_deleted is True or is_deleted is None)
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return CropListResponse(
            items=[CropResponse.model_validate(c) for c in crops],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages
        )

    @staticmethod
    def list_farmer_crops(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        category: Optional[str] = None
    ) -> CropListResponse:
        """Retrieves active, non-deleted crop records available for farmer crop planning."""
        skip = (page - 1) * page_size
        crops = CropRepository.list_crops(
            db=db,
            skip=skip,
            limit=page_size,
            search=search,
            category=category,
            is_active=True,
            include_deleted=False
        )
        total = CropRepository.count_crops(
            db=db,
            search=search,
            category=category,
            is_active=True,
            include_deleted=False
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return CropListResponse(
            items=[CropResponse.model_validate(c) for c in crops],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages
        )

    @staticmethod
    def get_crop_detail(
        db: Session,
        crop_id: uuid.UUID
    ) -> CropResponse:
        """Retrieves details of a crop master record by ID."""
        crop = CropRepository.get_by_id(db, crop_id=crop_id, include_deleted=True)
        if not crop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crop not found"
            )
        return CropResponse.model_validate(crop)

    @staticmethod
    def update_crop(
        db: Session,
        crop_id: uuid.UUID,
        request: CropUpdate,
        current_admin: User
    ) -> CropResponse:
        """Updates mutable fields of a crop master record."""
        crop = CropRepository.get_by_id(db, crop_id=crop_id, include_deleted=False)
        if not crop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crop not found"
            )

        update_dict = request.model_dump(exclude_unset=True)
        new_name = update_dict.get("crop_name")
        if new_name and new_name.strip().lower() != crop.crop_name.strip().lower():
            existing = CropRepository.get_active_by_name(db, new_name, exclude_crop_id=crop.id)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An active crop with this name already exists"
                )

        updated_crop = CropRepository.update(
            db=db,
            crop=crop,
            update_data=update_dict,
            updated_by=current_admin.id
        )
        logger.info("Crop %s updated by admin %s", crop_id, current_admin.id)
        return CropResponse.model_validate(updated_crop)

    @staticmethod
    def update_crop_status(
        db: Session,
        crop_id: uuid.UUID,
        request: CropStatusUpdate,
        current_admin: User
    ) -> CropResponse:
        """Toggles the active/inactive status of a crop."""
        crop = CropRepository.get_by_id(db, crop_id=crop_id, include_deleted=True)
        if not crop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crop not found"
            )
        if crop.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update status of a deleted crop. Restore the crop first."
            )

        updated_crop = CropRepository.update_status(
            db=db,
            crop=crop,
            is_active=request.is_active,
            updated_by=current_admin.id
        )
        logger.info("Crop %s status changed to is_active=%s by admin %s", crop_id, request.is_active, current_admin.id)
        return CropResponse.model_validate(updated_crop)

    @staticmethod
    def delete_crop(
        db: Session,
        crop_id: uuid.UUID,
        current_admin: User
    ) -> CropResponse:
        """Soft-deletes a crop master record."""
        crop = CropRepository.get_by_id(db, crop_id=crop_id, include_deleted=False)
        if not crop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crop not found"
            )

        deleted_crop = CropRepository.soft_delete(
            db=db,
            crop=crop,
            deleted_by=current_admin.id
        )
        logger.info("Crop %s soft-deleted by admin %s", crop_id, current_admin.id)
        return CropResponse.model_validate(deleted_crop)

    @staticmethod
    def restore_crop(
        db: Session,
        crop_id: uuid.UUID,
        current_admin: User
    ) -> CropResponse:
        """Restores a soft-deleted crop master record."""
        crop = CropRepository.get_by_id(db, crop_id=crop_id, include_deleted=True)
        if not crop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crop not found"
            )
        if not crop.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Crop is not deleted"
            )

        existing = CropRepository.get_active_by_name(db, crop.crop_name, exclude_crop_id=crop.id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An active crop with this name already exists. Adjust existing crop first."
            )

        restored_crop = CropRepository.restore(
            db=db,
            crop=crop,
            updated_by=current_admin.id
        )
        logger.info("Crop %s restored by admin %s", crop_id, current_admin.id)
        return CropResponse.model_validate(restored_crop)
