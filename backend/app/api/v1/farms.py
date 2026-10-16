import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.farm import (
    FarmCreate,
    FarmUpdate,
    FarmStatusUpdate,
    FarmResponse,
    FarmListResponse,
)
from app.services.farm_service import FarmService

router = APIRouter(prefix="/farms", tags=["Farms (Farmer Management)"])


@router.post(
    "",
    response_model=FarmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Farm",
    description="Creates a new farm for the authenticated Farmer. Protected by FARMER role and requires completed FarmerProfile."
)
def create_farm(
    request: FarmCreate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Creates a new farm record. Automatically links the farm to the caller's FarmerProfile
    and generates a unique sequential farm code (e.g. FARM-000001).
    """
    return FarmService.create_farm(db=db, current_user=current_user, request=request)


@router.get(
    "",
    response_model=FarmListResponse,
    summary="List Farms",
    description="Retrieves a paginated list of non-deleted farms belonging to the authenticated Farmer. Protected by FARMER role."
)
def list_farms(
    page: int = Query(default=1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (1-100)"),
    search: Optional[str] = Query(default=None, description="Search term for farm name, code, village, district, state"),
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Returns paginated farms for the authenticated farmer profile.
    """
    return FarmService.list_farms(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        search=search,
        is_active=is_active
    )


@router.get(
    "/{farm_id}",
    response_model=FarmResponse,
    summary="Get Farm Details",
    description="Retrieves details for a single owned non-deleted farm. Protected by FARMER role."
)
def get_farm(
    farm_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Returns full details of an owned farm. Returns 404 if the farm does not exist or belongs to another farmer.
    """
    return FarmService.get_farm_detail(db=db, current_user=current_user, farm_id=farm_id)


@router.patch(
    "/{farm_id}",
    response_model=FarmResponse,
    summary="Update Farm Details",
    description="Partially updates mutable farm details. Protected by FARMER role."
)
def update_farm(
    farm_id: uuid.UUID,
    request: FarmUpdate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Partially updates mutable fields (name, land area, ownership, location, coordinates).
    Does not allow updating code, ownership identity, or audit fields.
    """
    return FarmService.update_farm(db=db, current_user=current_user, farm_id=farm_id, request=request)


@router.patch(
    "/{farm_id}/status",
    response_model=FarmResponse,
    summary="Update Farm Status",
    description="Toggles the active status of an owned farm. Protected by FARMER role."
)
def update_farm_status(
    farm_id: uuid.UUID,
    request: FarmStatusUpdate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Updates the active/inactive status of an owned farm. Deleted farms cannot change status without restoration.
    """
    return FarmService.update_farm_status(db=db, current_user=current_user, farm_id=farm_id, request=request)


@router.delete(
    "/{farm_id}",
    response_model=FarmResponse,
    summary="Soft Delete Farm",
    description="Soft deletes an owned farm. Protected by FARMER role."
)
def delete_farm(
    farm_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Soft deletes an owned farm. Sets is_deleted=true and records deletion timestamp/user.
    """
    return FarmService.delete_farm(db=db, current_user=current_user, farm_id=farm_id)


@router.post(
    "/{farm_id}/restore",
    response_model=FarmResponse,
    summary="Restore Soft-Deleted Farm",
    description="Restores a previously soft-deleted owned farm. Protected by FARMER role."
)
def restore_farm(
    farm_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Restores a soft-deleted farm. Does not alter the is_active status.
    """
    return FarmService.restore_farm(db=db, current_user=current_user, farm_id=farm_id)
