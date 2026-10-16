import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User
from app.models.cultivation import CultivationStage, CultivationRun
from app.models.farmer_profile import FarmerProfile
from app.repositories.farmer_profile_repository import FarmerProfileRepository
from app.repositories.pre_activity_repository import PreActivityRepository
from app.schemas.pre_activity_plan import (
    PreActivityPlanCreate,
    PreActivityPlanUpdate,
    PreActivityPlanResponse,
    PreActivityConvertRequest,
    PreActivityConvertResponse,
)

router = APIRouter(tags=["Pre-Activity Planning & Requirements"])


def _verify_farmer_access(db: Session, current_user: User) -> FarmerProfile:
    profile = FarmerProfileRepository.get_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Farmer profile required to manage pre-activity plans"
        )
    return profile


@router.post(
    "/stages/{stage_id}/pre-activities",
    response_model=PreActivityPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Pre-Activity Plan & Requirements",
    description="Logs purpose, machinery, materials, and labor requirements with budget estimation before starting a field task.",
)
def create_pre_activity_plan(
    stage_id: uuid.UUID,
    request: PreActivityPlanCreate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    farmer_profile = _verify_farmer_access(db, current_user)
    
    stage = db.query(CultivationStage).filter(
        CultivationStage.id == stage_id,
        CultivationStage.is_deleted == False
    ).first()
    if not stage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cultivation stage not found")

    run = db.query(CultivationRun).filter(
        CultivationRun.id == stage.cultivation_id,
        CultivationRun.farmer_profile_id == farmer_profile.id,
        CultivationRun.is_deleted == False
    ).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this cultivation run")

    plan = PreActivityRepository.create_plan(
        db=db,
        stage=stage,
        data=request,
        created_by=current_user.id
    )
    return plan


@router.get(
    "/stages/{stage_id}/pre-activities",
    response_model=List[PreActivityPlanResponse],
    summary="List Pre-Activity Plans for Stage",
    description="Retrieves all pre-activity plans and checklists for a specific cultivation stage.",
)
def list_stage_pre_activities(
    stage_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    _verify_farmer_access(db, current_user)
    return PreActivityRepository.list_by_stage(db, stage_id)


@router.get(
    "/cultivations/{cultivation_id}/pre-activities",
    response_model=List[PreActivityPlanResponse],
    summary="List All Pre-Activity Plans for Cultivation",
    description="Retrieves all pre-activity plans across all stages for a cultivation run.",
)
def list_cultivation_pre_activities(
    cultivation_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    _verify_farmer_access(db, current_user)
    return PreActivityRepository.list_by_cultivation(db, cultivation_id)


@router.get(
    "/pre-activities/{plan_id}",
    response_model=PreActivityPlanResponse,
    summary="Get Pre-Activity Plan Details",
)
def get_pre_activity_plan(
    plan_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    _verify_farmer_access(db, current_user)
    plan = PreActivityRepository.get_by_id(db, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pre-activity plan not found")
    return plan


@router.patch(
    "/pre-activities/{plan_id}",
    response_model=PreActivityPlanResponse,
    summary="Update Pre-Activity Plan",
)
def update_pre_activity_plan(
    plan_id: uuid.UUID,
    request: PreActivityPlanUpdate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    _verify_farmer_access(db, current_user)
    plan = PreActivityRepository.get_by_id(db, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pre-activity plan not found")
    return PreActivityRepository.update_plan(db, plan, request, current_user.id)


@router.delete(
    "/pre-activities/{plan_id}",
    response_model=PreActivityPlanResponse,
    summary="Delete Pre-Activity Plan",
)
def delete_pre_activity_plan(
    plan_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    _verify_farmer_access(db, current_user)
    plan = PreActivityRepository.get_by_id(db, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pre-activity plan not found")
    return PreActivityRepository.delete_plan(db, plan, current_user.id)


@router.post(
    "/pre-activities/{plan_id}/convert-to-expenses",
    response_model=PreActivityConvertResponse,
    summary="Convert Pre-Task Plan to Actual Expenses & Wages",
    description="Seamlessly translates planned machinery, inputs, and labor into actual stage ledger expenses and worker logs without double entry.",
)
def convert_to_actual_expenses(
    plan_id: uuid.UUID,
    request: PreActivityConvertRequest,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    _verify_farmer_access(db, current_user)
    plan = PreActivityRepository.get_by_id(db, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pre-activity plan not found")
    
    if plan.actual_converted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This pre-task plan has already been converted to actual expenses"
        )

    expenses_count, workers_count, total_amount = PreActivityRepository.convert_to_actual_ledger(
        db=db,
        plan=plan,
        request=request,
        user_id=current_user.id
    )

    return PreActivityConvertResponse(
        plan_id=plan.id,
        stage_id=plan.stage_id,
        cultivation_id=plan.cultivation_id,
        expenses_created=expenses_count,
        worker_logs_created=workers_count,
        total_logged_amount=total_amount,
        message=f"Successfully converted pre-task to {expenses_count} expense items and {workers_count} worker wage entries (Total: ₹{total_amount:,.2f})",
    )
