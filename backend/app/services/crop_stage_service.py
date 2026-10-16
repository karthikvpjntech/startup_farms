import os
import uuid
import shutil
import logging
from typing import Optional
from pathlib import Path
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.crop import Crop
from app.repositories.crop_repository import CropRepository
from app.repositories.crop_stage_repository import CropStageRepository
from app.schemas.crop_stage import (
    CropStageCreate,
    CropStageUpdate,
    CropStageReorderRequest,
    CropStageResponse,
    CropStageListResponse,
    CropStageImageUploadResponse,
)

logger = logging.getLogger("agri_smart.crop_stage_service")

# Static upload directory configuration
UPLOAD_BASE_DIR = Path("uploads/stages")
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class CropStageService:
    """Service providing cultivation process stage administration and media handling."""

    @staticmethod
    def _verify_crop_exists(db: Session, crop_id: uuid.UUID) -> Crop:
        crop = CropRepository.get_by_id(db, crop_id=crop_id, include_deleted=False)
        if not crop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Crop with ID {crop_id} not found"
            )
        return crop

    @staticmethod
    def list_stages_admin(db: Session, crop_id: uuid.UUID) -> CropStageListResponse:
        """Retrieves all stages (active & inactive) for Super Admin management."""
        CropStageService._verify_crop_exists(db, crop_id)
        stages = CropStageRepository.list_by_crop_id(db, crop_id, include_inactive=True, include_deleted=False)
        total_duration = sum(s.duration_days for s in stages)
        return CropStageListResponse(
            items=[CropStageResponse.model_validate(s) for s in stages],
            total=len(stages),
            total_duration_days=total_duration
        )

    @staticmethod
    def list_stages_public(db: Session, crop_id: uuid.UUID) -> CropStageListResponse:
        """Retrieves active stages for farmers and interactive visualization players."""
        CropStageService._verify_crop_exists(db, crop_id)
        stages = CropStageRepository.list_by_crop_id(db, crop_id, include_inactive=False, include_deleted=False)
        total_duration = sum(s.duration_days for s in stages)
        return CropStageListResponse(
            items=[CropStageResponse.model_validate(s) for s in stages],
            total=len(stages),
            total_duration_days=total_duration
        )

    @staticmethod
    def get_stage_detail(db: Session, crop_id: uuid.UUID, stage_id: uuid.UUID) -> CropStageResponse:
        """Retrieves single stage details."""
        CropStageService._verify_crop_exists(db, crop_id)
        stage = CropStageRepository.get_by_id(db, stage_id=stage_id, include_deleted=False)
        if not stage or stage.crop_id != crop_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cultivation stage not found"
            )
        return CropStageResponse.model_validate(stage)

    @staticmethod
    def create_stage(
        db: Session,
        crop_id: uuid.UUID,
        request: CropStageCreate,
        current_admin: User
    ) -> CropStageResponse:
        """Creates a new cultivation process stage under the specified crop."""
        CropStageService._verify_crop_exists(db, crop_id)
        stage_data = request.model_dump(exclude_unset=True)
        
        stage = CropStageRepository.create(
            db=db,
            crop_id=crop_id,
            stage_data=stage_data,
            created_by=current_admin.id,
            explicit_order=request.stage_order
        )
        logger.info("Admin %s created stage '%s' (#%d) for crop %s", current_admin.id, stage.stage_name, stage.stage_order, crop_id)
        return CropStageResponse.model_validate(stage)

    @staticmethod
    def update_stage(
        db: Session,
        crop_id: uuid.UUID,
        stage_id: uuid.UUID,
        request: CropStageUpdate,
        current_admin: User
    ) -> CropStageResponse:
        """Updates editable fields of a cultivation process stage."""
        CropStageService._verify_crop_exists(db, crop_id)
        stage = CropStageRepository.get_by_id(db, stage_id=stage_id, include_deleted=False)
        if not stage or stage.crop_id != crop_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cultivation stage not found"
            )

        update_dict = request.model_dump(exclude_unset=True)
        updated_stage = CropStageRepository.update(
            db=db,
            stage=stage,
            update_data=update_dict,
            updated_by=current_admin.id
        )
        logger.info("Admin %s updated stage %s for crop %s", current_admin.id, stage_id, crop_id)
        return CropStageResponse.model_validate(updated_stage)

    @staticmethod
    def reorder_stages(
        db: Session,
        crop_id: uuid.UUID,
        request: CropStageReorderRequest,
        current_admin: User
    ) -> CropStageListResponse:
        """Updates sequence numbers for a crop's cultivation stages."""
        CropStageService._verify_crop_exists(db, crop_id)
        mappings = [{"stage_id": item.stage_id, "stage_order": item.stage_order} for item in request.stages]
        
        reordered = CropStageRepository.reorder_stages(
            db=db,
            crop_id=crop_id,
            order_mappings=mappings,
            updated_by=current_admin.id
        )
        total_duration = sum(s.duration_days for s in reordered)
        logger.info("Admin %s reordered %d stages for crop %s", current_admin.id, len(mappings), crop_id)
        return CropStageListResponse(
            items=[CropStageResponse.model_validate(s) for s in reordered],
            total=len(reordered),
            total_duration_days=total_duration
        )

    @staticmethod
    def delete_stage(
        db: Session,
        crop_id: uuid.UUID,
        stage_id: uuid.UUID,
        current_admin: User
    ) -> CropStageResponse:
        """Soft deletes a cultivation stage."""
        CropStageService._verify_crop_exists(db, crop_id)
        stage = CropStageRepository.get_by_id(db, stage_id=stage_id, include_deleted=False)
        if not stage or stage.crop_id != crop_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cultivation stage not found"
            )

        deleted = CropStageRepository.soft_delete(db, stage=stage, deleted_by=current_admin.id)
        logger.info("Admin %s deleted stage %s for crop %s", current_admin.id, stage_id, crop_id)
        return CropStageResponse.model_validate(deleted)

    @staticmethod
    async def upload_stage_image(
        db: Session,
        crop_id: uuid.UUID,
        stage_id: uuid.UUID,
        file: UploadFile,
        current_admin: User
    ) -> CropStageImageUploadResponse:
        """Validates and persists a real crop stage image, updating the stage record."""
        CropStageService._verify_crop_exists(db, crop_id)
        stage = CropStageRepository.get_by_id(db, stage_id=stage_id, include_deleted=False)
        if not stage or stage.crop_id != crop_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cultivation stage not found"
            )

        # 1. Validate file extension
        ext = Path(file.filename or "").suffix.lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image format '{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}"
            )

        # 2. Ensure target upload directory exists
        UPLOAD_BASE_DIR.mkdir(parents=True, exist_ok=True)

        # 3. Create sanitized unique file name
        unique_filename = f"{crop_id}_{stage_id}_{uuid.uuid4().hex[:8]}{ext}"
        destination_path = UPLOAD_BASE_DIR / unique_filename

        # 4. Stream and write file with size limit check
        file_size = 0
        try:
            with open(destination_path, "wb") as buffer:
                while chunk := await file.read(1024 * 1024):  # 1MB chunks
                    file_size += len(chunk)
                    if file_size > MAX_FILE_SIZE_BYTES:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="File size exceeds maximum allowed limit of 10MB"
                        )
                    buffer.write(chunk)
        except Exception as e:
            if destination_path.exists():
                destination_path.unlink()
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save uploaded image"
            )

        # 5. Set image URL in database (relative path served by static mount)
        image_url = f"/uploads/stages/{unique_filename}"
        stage.image_url = image_url
        stage.thumbnail_url = image_url
        stage.updated_by = current_admin.id
        db.commit()
        db.refresh(stage)

        logger.info("Admin %s uploaded photo for stage %s: %s", current_admin.id, stage_id, image_url)
        return CropStageImageUploadResponse(
            stage_id=stage.id,
            image_url=image_url,
            message="Stage image uploaded and linked successfully"
        )
