import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.crop import (
    CropCreate,
    CropUpdate,
    CropStatusUpdate,
    CropResponse,
    CropListResponse,
)
from app.services.crop_service import CropService

router = APIRouter(prefix="/admin/crops", tags=["Admin (Crop Master)"])


@router.post(
    "",
    response_model=CropResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Crop Master Record",
    description="Creates a new crop master record. Protected by SUPER_ADMIN role."
)
def create_crop(
    request: CropCreate,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return CropService.create_crop(db=db, request=request, current_admin=current_admin)


@router.get(
    "",
    response_model=CropListResponse,
    summary="List Crop Master Records (Admin)",
    description="Retrieves a paginated list of crops with search and status filters. Protected by SUPER_ADMIN role."
)
def list_admin_crops(
    page: int = Query(default=1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (1-100)"),
    search: Optional[str] = Query(default=None, description="Search by crop name, code, or scientific name"),
    category: Optional[str] = Query(default=None, description="Filter by crop category"),
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
    is_deleted: Optional[bool] = Query(default=None, description="Filter by deleted status"),
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return CropService.list_admin_crops(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        category=category,
        is_active=is_active,
        is_deleted=is_deleted
    )


@router.get(
    "/{crop_id}",
    response_model=CropResponse,
    summary="Get Crop Master Details",
    description="Retrieves full details of a crop master record by ID. Protected by SUPER_ADMIN role."
)
def get_crop(
    crop_id: uuid.UUID,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return CropService.get_crop_detail(db=db, crop_id=crop_id)


@router.patch(
    "/{crop_id}",
    response_model=CropResponse,
    summary="Update Crop Master Record",
    description="Partially updates a crop master record. Protected by SUPER_ADMIN role."
)
def update_crop(
    crop_id: uuid.UUID,
    request: CropUpdate,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return CropService.update_crop(db=db, crop_id=crop_id, request=request, current_admin=current_admin)


@router.patch(
    "/{crop_id}/status",
    response_model=CropResponse,
    summary="Update Crop Status",
    description="Toggles the active status of a crop master record. Protected by SUPER_ADMIN role."
)
def update_crop_status(
    crop_id: uuid.UUID,
    request: CropStatusUpdate,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return CropService.update_crop_status(db=db, crop_id=crop_id, request=request, current_admin=current_admin)


@router.delete(
    "/{crop_id}",
    response_model=CropResponse,
    summary="Soft Delete Crop Master Record",
    description="Soft-deletes a crop master record. Protected by SUPER_ADMIN role."
)
def delete_crop(
    crop_id: uuid.UUID,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return CropService.delete_crop(db=db, crop_id=crop_id, current_admin=current_admin)


@router.post(
    "/{crop_id}/restore",
    response_model=CropResponse,
    summary="Restore Soft-Deleted Crop Record",
    description="Restores a previously soft-deleted crop master record. Protected by SUPER_ADMIN role."
)
def restore_crop(
    crop_id: uuid.UUID,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return CropService.restore_crop(db=db, crop_id=crop_id, current_admin=current_admin)
