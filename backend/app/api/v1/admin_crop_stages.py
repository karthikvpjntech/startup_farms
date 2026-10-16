import uuid
from fastapi import APIRouter, Depends, status, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.crop_stage import (
    CropStageCreate,
    CropStageUpdate,
    CropStageReorderRequest,
    CropStageResponse,
    CropStageListResponse,
    CropStageImageUploadResponse,
)
from app.services.crop_stage_service import CropStageService

router = APIRouter(prefix="/admin/crops/{crop_id}/stages", tags=["Admin (Crop Stages & Visuals)"])


@router.get(
    "",
    response_model=CropStageListResponse,
    summary="List Cultivation Stages for Crop (Admin)",
    description="Retrieves all stages (active & inactive) configured for a crop, sorted by sequence order. Protected by SUPER_ADMIN role."
)
def list_crop_stages_admin(
    crop_id: uuid.UUID,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return CropStageService.list_stages_admin(db=db, crop_id=crop_id)


@router.post(
    "",
    response_model=CropStageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Cultivation Process Stage",
    description="Adds a new stage to the crop cultivation process. Protected by SUPER_ADMIN role."
)
def create_crop_stage(
    crop_id: uuid.UUID,
    request: CropStageCreate,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return CropStageService.create_stage(
        db=db,
        crop_id=crop_id,
        request=request,
        current_admin=current_admin
    )


@router.get(
    "/{stage_id}",
    response_model=CropStageResponse,
    summary="Get Cultivation Stage Details",
    description="Retrieves full details of a specific cultivation stage. Protected by SUPER_ADMIN role."
)
def get_crop_stage(
    crop_id: uuid.UUID,
    stage_id: uuid.UUID,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return CropStageService.get_stage_detail(db=db, crop_id=crop_id, stage_id=stage_id)


@router.patch(
    "/{stage_id}",
    response_model=CropStageResponse,
    summary="Update Cultivation Stage Details",
    description="Partially updates stage attributes (name, duration, description, 3D asset type, activities). Protected by SUPER_ADMIN role."
)
def update_crop_stage(
    crop_id: uuid.UUID,
    stage_id: uuid.UUID,
    request: CropStageUpdate,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return CropStageService.update_stage(
        db=db,
        crop_id=crop_id,
        stage_id=stage_id,
        request=request,
        current_admin=current_admin
    )


@router.put(
    "/reorder",
    response_model=CropStageListResponse,
    summary="Batch Reorder Cultivation Stages",
    description="Updates the numerical sequence order of stages for a crop. Protected by SUPER_ADMIN role."
)
def reorder_crop_stages(
    crop_id: uuid.UUID,
    request: CropStageReorderRequest,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return CropStageService.reorder_stages(
        db=db,
        crop_id=crop_id,
        request=request,
        current_admin=current_admin
    )


@router.post(
    "/{stage_id}/image",
    response_model=CropStageImageUploadResponse,
    summary="Upload Real Stage Photo",
    description="Uploads and associates a real photographic asset with a cultivation stage. Protected by SUPER_ADMIN role."
)
async def upload_stage_image(
    crop_id: uuid.UUID,
    stage_id: uuid.UUID,
    file: UploadFile = File(..., description="Image file (JPG, PNG, WebP up to 10MB)"),
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return await CropStageService.upload_stage_image(
        db=db,
        crop_id=crop_id,
        stage_id=stage_id,
        file=file,
        current_admin=current_admin
    )


@router.delete(
    "/{stage_id}",
    response_model=CropStageResponse,
    summary="Delete Cultivation Stage",
    description="Soft-deletes a cultivation process stage. Protected by SUPER_ADMIN role."
)
def delete_crop_stage(
    crop_id: uuid.UUID,
    stage_id: uuid.UUID,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return CropStageService.delete_stage(
        db=db,
        crop_id=crop_id,
        stage_id=stage_id,
        current_admin=current_admin
    )
