import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.farm_crop_plan import (
    FarmCropPlanCreate,
    FarmCropPlanUpdate,
    FarmCropPlanStatusUpdate,
    FarmCropPlanResponse,
    FarmCropPlanListResponse,
    CropSeedRecommendationResponse,
    HistoricalSeedUsageItem,
)
from app.services.farm_crop_plan_service import FarmCropPlanService

router = APIRouter(prefix="/farm-crop-plans", tags=["Farm Crop Plans"])


@router.get(
    "/seed-recommendations",
    response_model=List[CropSeedRecommendationResponse],
    summary="Get Seed Variety & Per-Acre Rate Recommendations",
    description="Provides agronomic recommendations for seed rates per acre and certified varieties for crops."
)
def get_seed_recommendations(
    crop_id: Optional[uuid.UUID] = Query(default=None, description="Optional crop ID filter"),
    db: Session = Depends(get_db)
):
    """
    Returns agronomic recommendations for seed varieties, per-acre rates, and sowing methods.
    """
    return FarmCropPlanService.get_seed_recommendations(db=db, crop_id=crop_id)


@router.get(
    "/seed-history",
    response_model=List[HistoricalSeedUsageItem],
    summary="Get Historical Seed Usage Memory",
    description="Retrieves past seasons' seed varieties, rates used, and harvest yields for farmer parcels."
)
def get_historical_seed_usage(
    farm_id: Optional[uuid.UUID] = Query(default=None, description="Filter by owned farm ID"),
    crop_id: Optional[uuid.UUID] = Query(default=None, description="Filter by crop ID"),
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Returns historical seed memory with previous rates, varieties, and yield outputs.
    """
    return FarmCropPlanService.get_historical_seed_usage(
        db=db,
        current_user=current_user,
        farm_id=farm_id,
        crop_id=crop_id
    )


@router.post(
    "",
    response_model=FarmCropPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Farm Crop Plan",
    description="Creates a new crop plan for an owned farm. Protected by FARMER role."
)
def create_farm_crop_plan(
    request: FarmCropPlanCreate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Creates a new crop plan. Validates farm ownership, crop availability, area constraints, and season uniqueness.
    """
    return FarmCropPlanService.create_plan(db=db, current_user=current_user, request=request)


@router.get(
    "",
    response_model=FarmCropPlanListResponse,
    summary="List Farm Crop Plans",
    description="Retrieves paginated crop plans belonging to farms owned by the authenticated farmer. Protected by FARMER role."
)
def list_farm_crop_plans(
    page: int = Query(default=1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (1-100)"),
    farm_id: Optional[uuid.UUID] = Query(default=None, description="Filter by owned farm ID"),
    crop_id: Optional[uuid.UUID] = Query(default=None, description="Filter by crop ID"),
    season: Optional[str] = Query(default=None, description="Filter by season"),
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
    search: Optional[str] = Query(default=None, description="Search by crop name, code, farm name, or notes"),
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Returns paginated crop plans for the authenticated farmer profile.
    """
    return FarmCropPlanService.list_plans(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        farm_id=farm_id,
        crop_id=crop_id,
        season=season,
        is_active=is_active,
        search=search
    )


@router.get(
    "/{plan_id}",
    response_model=FarmCropPlanResponse,
    summary="Get Farm Crop Plan Details",
    description="Retrieves details for a single owned non-deleted farm crop plan. Protected by FARMER role."
)
def get_farm_crop_plan(
    plan_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Returns details of an owned crop plan. Returns 404 if not found or owned by another farmer.
    """
    return FarmCropPlanService.get_plan_detail(db=db, current_user=current_user, plan_id=plan_id)


@router.patch(
    "/{plan_id}",
    response_model=FarmCropPlanResponse,
    summary="Update Farm Crop Plan",
    description="Partially updates an owned farm crop plan. Protected by FARMER role."
)
def update_farm_crop_plan(
    plan_id: uuid.UUID,
    request: FarmCropPlanUpdate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Partially updates mutable plan details. Revalidates duplicate rules and area limits if changed.
    """
    return FarmCropPlanService.update_plan(db=db, current_user=current_user, plan_id=plan_id, request=request)


@router.patch(
    "/{plan_id}/status",
    response_model=FarmCropPlanResponse,
    summary="Update Farm Crop Plan Status",
    description="Toggles the active status of an owned crop plan. Protected by FARMER role."
)
def update_farm_crop_plan_status(
    plan_id: uuid.UUID,
    request: FarmCropPlanStatusUpdate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Updates the active/inactive status of an owned crop plan. Deleted plans cannot change status without restoration.
    """
    return FarmCropPlanService.update_plan_status(db=db, current_user=current_user, plan_id=plan_id, request=request)


@router.delete(
    "/{plan_id}",
    response_model=FarmCropPlanResponse,
    summary="Soft Delete Farm Crop Plan",
    description="Soft deletes an owned farm crop plan. Protected by FARMER role."
)
def delete_farm_crop_plan(
    plan_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Soft deletes an owned crop plan.
    """
    return FarmCropPlanService.delete_plan(db=db, current_user=current_user, plan_id=plan_id)


@router.post(
    "/{plan_id}/restore",
    response_model=FarmCropPlanResponse,
    summary="Restore Soft-Deleted Farm Crop Plan",
    description="Restores a previously soft-deleted owned farm crop plan. Protected by FARMER role."
)
def restore_farm_crop_plan(
    plan_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Restores a soft-deleted crop plan without altering is_active status.
    """
    return FarmCropPlanService.restore_plan(db=db, current_user=current_user, plan_id=plan_id)


@router.post(
    "/{plan_id}/remind-seed-usage",
    summary="Trigger Seasonal Seed Usage Notification",
    description="Dispatches SMS and In-App notification reminding the farmer of last year's seed variety, rate, and yield for this parcel. Protected by FARMER role."
)
def remind_seed_usage(
    plan_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Dispatches next-year/seasonal seed usage reminder to the farmer.
    """
    return FarmCropPlanService.send_seasonal_seed_reminder(
        db=db,
        current_user=current_user,
        plan_id=plan_id
    )
