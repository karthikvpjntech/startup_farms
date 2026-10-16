import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User

from app.schemas.farmer_crm import (
    WorkerCreate,
    WorkerUpdate,
    WorkerResponse,
    WorkerListResponse,
    MachineCreate,
    MachineUpdate,
    MachineResponse,
    MachineListResponse,
    WorkerAttendanceCreate,
    WorkerAttendanceResponse,
    BulkWorkerAttendanceCreate,
    MachineUsageCreate,
    MachineUsageResponse,
    MaterialPurchaseCreate,
    MaterialPurchaseResponse,
    MaterialPurchaseListResponse,
    CultivationScheduleBulkCreate,
    CultivationScheduleResponse,
    BillCreate,
    BillResponse,
    BillListResponse,
    StageBillGenerateRequest,
    PaymentCreate,
    PaymentResponse,
    PaymentListResponse,
    LogisticsCreate,
    LogisticsStatusUpdate,
    LogisticsResponse,
    LogisticsListResponse,
    SMSSendRequest,
    SMSLogResponse,
    SMSLogListResponse,
    CRMDashboardSummaryResponse,
    CRMCultivationDetailResponse,
    CropCostSummaryResponse,
    CropCostReportItem,
    WorkerPaymentReportItem,
    SupplierPurchaseReportItem,
    FarmExpenseReportItem,
)
from app.services.farmer_crm_service import FarmerCRMService

router = APIRouter(prefix="/farmer/crm", tags=["Farmer CRM Operations & Management"])


# ==========================================
# Dashboard & Summary Analytics
# ==========================================

@router.get(
    "/dashboard-summary",
    response_model=CRMDashboardSummaryResponse,
    summary="Get Farmer CRM Dashboard Summary",
    description="Retrieves live aggregated KPI numbers for total farms, active crops, today's work, workers/machines assigned, and pending payments.",
)
def get_dashboard_summary(
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.get_dashboard_summary(db=db, current_user=current_user)


@router.get(
    "/cultivations/{cultivation_id}/crm-detail",
    response_model=CRMCultivationDetailResponse,
    summary="Get Cultivation CRM Detail Record",
    description="Retrieves full CRM detail for a cultivation including chronological timeline events, stage breakdowns, and financials.",
)
def get_cultivation_crm_detail(
    cultivation_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.get_cultivation_crm_detail(
        db=db, current_user=current_user, cultivation_id=cultivation_id
    )


@router.get(
    "/cultivations/{cultivation_id}/cost-summary",
    response_model=CropCostSummaryResponse,
    summary="Get Cultivation Cost Breakdown",
    description="Returns stage-wise itemized labor, machine, material, and logistics cost totals.",
)
def get_crop_cost_summary(
    cultivation_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.get_crop_cost_summary(
        db=db, current_user=current_user, cultivation_id=cultivation_id
    )


# ==========================================
# Worker Master Endpoints
# ==========================================

@router.post(
    "/workers",
    response_model=WorkerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New Worker into Master",
    description="Registers a new worker into the farmer's Worker Master. If worker already exists with same mobile, reuses existing record.",
)
def create_worker(
    request: WorkerCreate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.create_worker(db=db, current_user=current_user, request=request)


@router.get(
    "/workers",
    response_model=WorkerListResponse,
    summary="Search & List Workers in Master",
    description="Searches reusable workers with filters by skill, gender, mobile number, name, and active status.",
)
def list_workers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    skill: Optional[str] = Query(default=None),
    gender: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.list_workers(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        search=search,
        skill=skill,
        gender=gender,
        is_active=is_active,
    )


@router.get(
    "/workers/{worker_id}",
    response_model=WorkerResponse,
    summary="Get Worker Master Details",
)
def get_worker(
    worker_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.get_worker(db=db, current_user=current_user, worker_id=worker_id)


@router.put(
    "/workers/{worker_id}",
    response_model=WorkerResponse,
    summary="Update Worker Details",
)
def update_worker(
    worker_id: uuid.UUID,
    request: WorkerUpdate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.update_worker(
        db=db, current_user=current_user, worker_id=worker_id, request=request
    )


@router.delete(
    "/workers/{worker_id}",
    response_model=WorkerResponse,
    summary="Soft-Delete Worker",
)
def delete_worker(
    worker_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.delete_worker(db=db, current_user=current_user, worker_id=worker_id)


# ==========================================
# Worker Attendance & Activity Endpoints
# ==========================================

@router.post(
    "/stages/{stage_id}/attendance",
    response_model=WorkerAttendanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log Worker Stage Attendance & Wages",
    description="Logs daily worker attendance, start/end time, working days, and automatically computes wage amount.",
)
def add_worker_attendance(
    stage_id: uuid.UUID,
    request: WorkerAttendanceCreate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.add_worker_attendance(
        db=db, current_user=current_user, stage_id=stage_id, request=request
    )


@router.post(
    "/stages/{stage_id}/attendance/bulk",
    response_model=List[WorkerAttendanceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk Log Worker Attendance",
)
def bulk_add_worker_attendance(
    stage_id: uuid.UUID,
    request: BulkWorkerAttendanceCreate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.bulk_add_worker_attendance(
        db=db, current_user=current_user, stage_id=stage_id, request=request
    )


@router.get(
    "/stages/{stage_id}/attendance",
    response_model=List[WorkerAttendanceResponse],
    summary="List Worker Attendance for Stage",
)
def list_stage_attendances(
    stage_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.list_stage_attendances(
        db=db, current_user=current_user, stage_id=stage_id
    )


@router.delete(
    "/attendance/{attendance_id}",
    response_model=WorkerAttendanceResponse,
    summary="Soft-Delete Worker Attendance Record",
)
def delete_attendance(
    attendance_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.delete_attendance(
        db=db, current_user=current_user, attendance_id=attendance_id
    )


# ==========================================
# Machine Master & Usage Endpoints
# ==========================================

@router.post(
    "/machines",
    response_model=MachineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Machine into Master",
)
def create_machine(
    request: MachineCreate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.create_machine(db=db, current_user=current_user, request=request)


@router.get(
    "/machines",
    response_model=MachineListResponse,
    summary="Search & List Machines",
)
def list_machines(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    machine_type: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.list_machines(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        search=search,
        machine_type=machine_type,
        is_active=is_active,
    )


@router.put(
    "/machines/{machine_id}",
    response_model=MachineResponse,
    summary="Update Machine Details",
)
def update_machine(
    machine_id: uuid.UUID,
    request: MachineUpdate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.update_machine(
        db=db, current_user=current_user, machine_id=machine_id, request=request
    )


@router.delete(
    "/machines/{machine_id}",
    response_model=MachineResponse,
    summary="Soft-Delete Machine",
)
def delete_machine(
    machine_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.delete_machine(
        db=db, current_user=current_user, machine_id=machine_id
    )


@router.post(
    "/stages/{stage_id}/machines",
    response_model=MachineUsageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log Machine Usage in Stage",
)
def add_machine_usage(
    stage_id: uuid.UUID,
    request: MachineUsageCreate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.add_machine_usage(
        db=db, current_user=current_user, stage_id=stage_id, request=request
    )


@router.get(
    "/stages/{stage_id}/machines",
    response_model=List[MachineUsageResponse],
    summary="List Machine Usages for Stage",
)
def list_stage_machine_usages(
    stage_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.list_stage_machine_usages(
        db=db, current_user=current_user, stage_id=stage_id
    )


@router.delete(
    "/machine-usage/{usage_id}",
    response_model=MachineUsageResponse,
    summary="Soft-Delete Machine Usage",
)
def delete_machine_usage(
    usage_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.delete_machine_usage(
        db=db, current_user=current_user, usage_id=usage_id
    )


# ==========================================
# Material Purchases Endpoints
# ==========================================

@router.post(
    "/purchases",
    response_model=MaterialPurchaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Material Purchase",
)
def create_material_purchase(
    request: MaterialPurchaseCreate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.create_material_purchase(
        db=db, current_user=current_user, request=request
    )


@router.get(
    "/purchases",
    response_model=MaterialPurchaseListResponse,
    summary="List Material Purchases",
)
def list_purchases(
    cultivation_id: Optional[uuid.UUID] = Query(default=None),
    stage_id: Optional[uuid.UUID] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.list_purchases(
        db=db,
        current_user=current_user,
        cultivation_id=cultivation_id,
        stage_id=stage_id,
        page=page,
        page_size=page_size,
    )


# ==========================================
# Cultivation Schedules Endpoints
# ==========================================

@router.post(
    "/cultivations/{cultivation_id}/schedules",
    response_model=List[CultivationScheduleResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Save Cultivation Stage Schedules",
)
def create_or_update_schedules(
    cultivation_id: uuid.UUID,
    request: CultivationScheduleBulkCreate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.create_or_update_schedules(
        db=db,
        current_user=current_user,
        cultivation_id=cultivation_id,
        request=request,
    )


@router.get(
    "/cultivations/{cultivation_id}/schedules",
    response_model=List[CultivationScheduleResponse],
    summary="Get Cultivation Stage Schedules",
)
def get_schedules(
    cultivation_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.get_schedules(
        db=db, current_user=current_user, cultivation_id=cultivation_id
    )


# ==========================================
# Billing & Payments Endpoints
# ==========================================

@router.post(
    "/bills/generate-stage-bill",
    response_model=BillResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Consolidated Stage Bill",
    description="Compiles all unbilled labor attendance, machine usages, and expenses for a stage into an individual bill.",
)
def generate_stage_bill(
    request: StageBillGenerateRequest,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.generate_stage_bill(
        db=db, current_user=current_user, request=request
    )


@router.post(
    "/bills",
    response_model=BillResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Custom Bill",
)
def create_custom_bill(
    request: BillCreate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.create_custom_bill(
        db=db, current_user=current_user, request=request
    )


@router.get(
    "/bills",
    response_model=BillListResponse,
    summary="List Bills & Invoices",
)
def list_bills(
    cultivation_id: Optional[uuid.UUID] = Query(default=None),
    stage_id: Optional[uuid.UUID] = Query(default=None),
    status: Optional[str] = Query(default=None),
    bill_type: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.list_bills(
        db=db,
        current_user=current_user,
        cultivation_id=cultivation_id,
        stage_id=stage_id,
        status_val=status,
        bill_type=bill_type,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/bills/{bill_id}",
    response_model=BillResponse,
    summary="Get Bill by ID",
)
def get_bill(
    bill_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.get_bill(db=db, current_user=current_user, bill_id=bill_id)


@router.post(
    "/payments",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Process Payment Checkout (UPI / Net Banking / Cash)",
    description="Settles bill balance, records transaction reference metadata safely, and triggers worker/supplier SMS notification.",
)
def record_payment(
    request: PaymentCreate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.record_payment(
        db=db, current_user=current_user, request=request
    )


@router.get(
    "/payments",
    response_model=PaymentListResponse,
    summary="List Payment Settlements",
)
def list_payments(
    bill_id: Optional[uuid.UUID] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.list_payments(
        db=db,
        current_user=current_user,
        bill_id=bill_id,
        page=page,
        page_size=page_size,
    )


# ==========================================
# Logistics Endpoints
# ==========================================

@router.post(
    "/logistics",
    response_model=LogisticsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Harvest Logistics Dispatch",
)
def create_logistics(
    request: LogisticsCreate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.create_logistics(
        db=db, current_user=current_user, request=request
    )


@router.get(
    "/logistics",
    response_model=LogisticsListResponse,
    summary="List Logistics Dispatches",
)
def list_logistics(
    cultivation_id: Optional[uuid.UUID] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.list_logistics(
        db=db,
        current_user=current_user,
        cultivation_id=cultivation_id,
        page=page,
        page_size=page_size,
    )


@router.patch(
    "/logistics/{logistics_id}/status",
    response_model=LogisticsResponse,
    summary="Update Logistics Status",
)
def update_logistics_status(
    logistics_id: uuid.UUID,
    request: LogisticsStatusUpdate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.update_logistics_status(
        db=db,
        current_user=current_user,
        logistics_id=logistics_id,
        request=request,
    )


# ==========================================
# SMS & Notifications Endpoints
# ==========================================

@router.post(
    "/notifications/send-sms",
    response_model=SMSLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send SMS Notification",
)
def send_manual_sms(
    request: SMSSendRequest,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.send_manual_sms(
        db=db, current_user=current_user, request=request
    )


@router.get(
    "/notifications",
    response_model=SMSLogListResponse,
    summary="List SMS & Notification Delivery Logs (Supports Keyset Cursor and Numbered Pages)",
)
def list_sms_logs(
    cursor: Optional[str] = Query(default=None, description="Keyset cursor token (created_at_id)"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.list_sms_logs(
        db=db, current_user=current_user, cursor=cursor, page=page, page_size=page_size
    )


# ==========================================
# Reports Endpoints
# ==========================================

@router.get(
    "/reports/crop-cost",
    response_model=List[CropCostReportItem],
    summary="Get Crop Cost Summary Report",
)
def get_crop_cost_report(
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.get_crop_cost_report(db=db, current_user=current_user)


@router.get(
    "/reports/worker-payments",
    response_model=List[WorkerPaymentReportItem],
    summary="Get Worker Earnings & Settlement Report",
)
def get_worker_payment_report(
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.get_worker_payment_report(db=db, current_user=current_user)


@router.get(
    "/reports/supplier-purchases",
    response_model=List[SupplierPurchaseReportItem],
    summary="Get Supplier Purchases & Payments Report",
)
def get_supplier_purchase_report(
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.get_supplier_purchase_report(db=db, current_user=current_user)


@router.get(
    "/reports/farm-expenses",
    response_model=List[FarmExpenseReportItem],
    summary="Get Farm Expenses Category Breakdown",
)
def get_farm_expense_report(
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db),
):
    return FarmerCRMService.get_farm_expense_report(db=db, current_user=current_user)
