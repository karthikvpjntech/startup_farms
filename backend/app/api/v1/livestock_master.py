import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.livestock import (
    LivestockCategoryResponse,
    LivestockCategoryCreateRequest,
    LivestockCategoryUpdateRequest,
    LivestockBreedResponse,
    LivestockBreedCreateRequest,
    LivestockBreedUpdateRequest,
)
from app.services.livestock_service import LivestockService

router = APIRouter(tags=["Livestock Master Data"])


# ============================================================================
# Public Read Endpoints
# ============================================================================

@router.get(
    "/livestock/categories",
    response_model=List[LivestockCategoryResponse],
    summary="List Active Livestock Categories"
)
def list_categories(
    is_active: bool = Query(default=True),
    db: Session = Depends(get_db)
):
    return LivestockService.list_categories(db=db, is_active_only=is_active)


@router.get(
    "/livestock/breeds",
    response_model=List[LivestockBreedResponse],
    summary="List Livestock Breeds"
)
def list_breeds(
    category_id: Optional[uuid.UUID] = Query(default=None, description="Filter breeds by category UUID"),
    is_active: bool = Query(default=True),
    db: Session = Depends(get_db)
):
    return LivestockService.list_breeds(db=db, category_id=category_id, is_active_only=is_active)


# ============================================================================
# Super Admin Endpoints
# ============================================================================

@router.post(
    "/admin/livestock/categories",
    response_model=LivestockCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Livestock Category"
)
def create_category(
    request: LivestockCategoryCreateRequest,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return LivestockService.create_category(db=db, request=request)


@router.patch(
    "/admin/livestock/categories/{category_id}",
    response_model=LivestockCategoryResponse,
    summary="Update Livestock Category"
)
def update_category(
    category_id: uuid.UUID,
    request: LivestockCategoryUpdateRequest,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return LivestockService.update_category(db=db, category_id=category_id, request=request)


@router.post(
    "/admin/livestock/breeds",
    response_model=LivestockBreedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Livestock Breed"
)
def create_breed(
    request: LivestockBreedCreateRequest,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return LivestockService.create_breed(db=db, request=request)


@router.patch(
    "/admin/livestock/breeds/{breed_id}",
    response_model=LivestockBreedResponse,
    summary="Update Livestock Breed"
)
def update_breed(
    breed_id: uuid.UUID,
    request: LivestockBreedUpdateRequest,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return LivestockService.update_breed(db=db, breed_id=breed_id, request=request)
