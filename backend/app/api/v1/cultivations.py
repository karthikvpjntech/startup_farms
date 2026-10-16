import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.cultivation import (
    CultivationRunCreate,
    CultivationRunStatusUpdate,
    CultivationRunResponse,
    CultivationRunListResponse,
    CultivationStageResponse,
    CultivationStageUpdate,
    CustomStageCreate,
    StageExpenseCreate,
    StageExpenseResponse,
    StageWorkerLogCreate,
    StageWorkerLogResponse,
    StageWorkerPaymentStatusUpdate,
    BulkWorkerLogCreate,
    HarvestYieldUpdate,
    CultivationComparisonResponse,
)
from app.services.cultivation_service import CultivationService

router = APIRouter(prefix="/crops", tags=["Cultivations (Execution & Expenses)"])


@router.post(
    "/cultivations",
    response_model=CultivationRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start Cultivation Run",
    description="Instantiates a live cultivation run from a verified FarmCropPlan and auto-seeds sequential stages. Protected by FARMER role.",
)
def start_cultivation(
    request: CultivationRunCreate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return CultivationService.start_cultivation(db=db, current_user=current_user, request=request)


@router.get(
    "/cultivations",
    response_model=CultivationRunListResponse,
    summary="List Cultivations",
    description="Retrieves paginated cultivation runs for the authenticated farmer. Protected by FARMER role.",
)
def list_cultivations(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
    search: Optional[str] = Query(default=None, description="Search term for farm/crop name"),
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return CultivationService.list_cultivations(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        is_active=is_active,
        search=search,
    )


@router.get(
    "/cultivations/comparison",
    response_model=CultivationComparisonResponse,
    summary="Get Cultivation Comparison Matrix",
    description="Generates side-by-side comparative analysis of Conventional vs Organic cultivation runs including labor, weed, input, yield and profit metrics. Protected by FARMER role.",
)
def get_cultivation_comparison(
    conventional_run_id: Optional[uuid.UUID] = Query(default=None, description="Conventional Run UUID"),
    organic_run_id: Optional[uuid.UUID] = Query(default=None, description="Organic Run UUID"),
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return CultivationService.get_comparison_report(
        db=db,
        current_user=current_user,
        conventional_run_id=conventional_run_id,
        organic_run_id=organic_run_id,
    )


@router.get(
    "/cultivations/{cultivation_id}",
    response_model=CultivationRunResponse,
    summary="Get Cultivation Details",
    description="Retrieves full details of a single cultivation run including stage progress, worker wages, and total logged expenses. Protected by FARMER role.",
)
def get_cultivation(
    cultivation_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return CultivationService.get_cultivation_detail(
        db=db,
        current_user=current_user,
        cultivation_id=cultivation_id,
    )


@router.patch(
    "/cultivations/{cultivation_id}/status",
    response_model=CultivationRunResponse,
    summary="Update Cultivation Status",
    description="Toggles the active status of a cultivation run. Protected by FARMER role.",
)
def update_cultivation_status(
    cultivation_id: uuid.UUID,
    request: CultivationRunStatusUpdate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return CultivationService.update_status(
        db=db,
        current_user=current_user,
        cultivation_id=cultivation_id,
        request=request,
    )


@router.patch(
    "/cultivations/{cultivation_id}/harvest-yield",
    response_model=CultivationRunResponse,
    summary="Record Harvest Yield & Revenue",
    description="Records harvested yield quantity, unit selling price, and calculates total sales gross revenue for profit analysis. Protected by FARMER role.",
)
def update_harvest_yield(
    cultivation_id: uuid.UUID,
    request: HarvestYieldUpdate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return CultivationService.update_harvest_yield(
        db=db,
        current_user=current_user,
        cultivation_id=cultivation_id,
        request=request,
    )


@router.delete(
    "/cultivations/{cultivation_id}",
    response_model=CultivationRunResponse,
    summary="Soft-Delete Cultivation Run",
    description="Soft-deletes a cultivation run. Protected by FARMER role.",
)
def delete_cultivation(
    cultivation_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return CultivationService.delete_cultivation(
        db=db,
        current_user=current_user,
        cultivation_id=cultivation_id,
    )


# ==========================================
# Dynamic Stages Endpoints
# ==========================================

@router.get(
    "/cultivations/{cultivation_id}/stages",
    response_model=List[CultivationStageResponse],
    summary="List Cultivation Stages",
    description="Retrieves the sequential stage progression array with worker wages and itemized expenses. Protected by FARMER role.",
)
def list_stages(
    cultivation_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return CultivationService.list_stages(
        db=db,
        current_user=current_user,
        cultivation_id=cultivation_id,
    )


@router.post(
    "/cultivations/{cultivation_id}/stages",
    response_model=CultivationStageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Custom Dynamic Stage",
    description="Allows farmer to append a custom stage (e.g. 'நில உழவு', 'பில்லு புடுங்குறது', 'மருந்து அடித்தல்') to an active cultivation. Protected by FARMER role.",
)
def create_custom_stage(
    cultivation_id: uuid.UUID,
    request: CustomStageCreate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return CultivationService.create_custom_stage(
        db=db,
        current_user=current_user,
        cultivation_id=cultivation_id,
        request=request,
    )


@router.patch(
    "/stages/{stage_id}",
    response_model=CultivationStageResponse,
    summary="Update Stage Details",
    description="Updates name, status, or dates for a cultivation stage. Protected by FARMER role.",
)
def update_stage(
    stage_id: uuid.UUID,
    request: CultivationStageUpdate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return CultivationService.update_stage(
        db=db,
        current_user=current_user,
        stage_id=stage_id,
        request=request,
    )


@router.delete(
    "/stages/{stage_id}",
    response_model=CultivationStageResponse,
    summary="Delete Stage",
    description="Soft-deletes a custom cultivation stage. Protected by FARMER role.",
)
def delete_stage(
    stage_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return CultivationService.delete_stage(
        db=db,
        current_user=current_user,
        stage_id=stage_id,
    )


@router.post(
    "/stages/{stage_id}/complete-and-next",
    response_model=CultivationRunResponse,
    summary="Complete Stage and Transition to Next",
    description="Marks current stage COMPLETED and shifts the next sequential stage to IN_PROGRESS. Protected by FARMER role.",
)
def complete_and_next_stage(
    stage_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return CultivationService.complete_and_next_stage(
        db=db,
        current_user=current_user,
        stage_id=stage_id,
    )


# ==========================================
# Worker Wages & Attendance Endpoints
# ==========================================

@router.post(
    "/stages/{stage_id}/workers",
    response_model=StageWorkerLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Single Worker Wage Entry",
    description="Records worker days worked, daily wage, auto-computes total wage, and sets payment status (Paid vs Pending). Protected by FARMER role.",
)
def add_worker_log(
    stage_id: uuid.UUID,
    request: StageWorkerLogCreate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return CultivationService.add_worker_log(
        db=db,
        current_user=current_user,
        stage_id=stage_id,
        request=request,
    )


@router.post(
    "/stages/{stage_id}/workers/bulk",
    response_model=List[StageWorkerLogResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk Add Worker Wage Entries",
    description="Records multiple worker wage entries at once for a specific stage. Protected by FARMER role.",
)
def bulk_add_worker_logs(
    stage_id: uuid.UUID,
    request: BulkWorkerLogCreate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return CultivationService.bulk_add_worker_logs(
        db=db,
        current_user=current_user,
        stage_id=stage_id,
        request=request,
    )


@router.get(
    "/stages/{stage_id}/workers",
    response_model=List[StageWorkerLogResponse],
    summary="List Stage Worker Logs",
    description="Retrieves all worker wage and attendance entries for a stage. Protected by FARMER role.",
)
def list_stage_worker_logs(
    stage_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return CultivationService.list_stage_worker_logs(
        db=db,
        current_user=current_user,
        stage_id=stage_id,
    )


@router.patch(
    "/workers/{worker_log_id}/payment-status",
    response_model=StageWorkerLogResponse,
    summary="Update Worker Payment Status",
    description="Toggles worker payment status between PAID and PENDING. Protected by FARMER role.",
)
def update_worker_payment_status(
    worker_log_id: uuid.UUID,
    request: StageWorkerPaymentStatusUpdate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return CultivationService.update_worker_payment_status(
        db=db,
        current_user=current_user,
        worker_log_id=worker_log_id,
        request=request,
    )


@router.delete(
    "/workers/{worker_log_id}",
    response_model=StageWorkerLogResponse,
    summary="Soft-Delete Worker Log",
    description="Soft-deletes a worker attendance and wage record. Protected by FARMER role.",
)
def delete_worker_log(
    worker_log_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return CultivationService.delete_worker_log(
        db=db,
        current_user=current_user,
        worker_log_id=worker_log_id,
    )


# ==========================================
# Stage Expense Endpoints
# ==========================================

@router.post(
    "/stages/{stage_id}/expenses",
    response_model=StageExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Stage Expense",
    description="Logs an itemized expense under a specific cultivation stage. Protected by FARMER role.",
)
def add_expense(
    stage_id: uuid.UUID,
    request: StageExpenseCreate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return CultivationService.add_expense(
        db=db,
        current_user=current_user,
        stage_id=stage_id,
        request=request,
    )


@router.get(
    "/stages/{stage_id}/expenses",
    response_model=List[StageExpenseResponse],
    summary="List Stage Expenses",
    description="Retrieves all line-item expenses for a specific stage. Protected by FARMER role.",
)
def list_stage_expenses(
    stage_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return CultivationService.list_stage_expenses(
        db=db,
        current_user=current_user,
        stage_id=stage_id,
    )


@router.delete(
    "/expenses/{expense_id}",
    response_model=StageExpenseResponse,
    summary="Soft-Delete Expense",
    description="Soft-deletes an itemized stage expense. Protected by FARMER role.",
)
def delete_expense(
    expense_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return CultivationService.delete_expense(
        db=db,
        current_user=current_user,
        expense_id=expense_id,
    )


@router.post(
    "/expenses/{expense_id}/restore",
    response_model=StageExpenseResponse,
    summary="Restore Soft-Deleted Expense",
    description="Restores a previously soft-deleted stage expense (used by 6s undo toast). Protected by FARMER role.",
)
def restore_expense(
    expense_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return CultivationService.restore_expense(
        db=db,
        current_user=current_user,
        expense_id=expense_id,
    )

