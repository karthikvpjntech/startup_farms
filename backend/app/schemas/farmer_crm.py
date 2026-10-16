import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator
from app.models.enums import (
    WorkerGender,
    WorkerSkill,
    MachineType,
    BillType,
    BillStatus,
    PaymentMethod,
    PaymentStatus,
    LogisticsStatus,
    NotificationStatus,
    NotificationType,
)
from app.core.phone_utils import validate_and_format_phone


# ==========================================
# Worker Master Schemas
# ==========================================

class WorkerBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150, description="Worker full name")
    mobile_number: str = Field(..., min_length=7, max_length=20, description="Primary contact number")
    gender: WorkerGender = Field(default=WorkerGender.MALE, description="Gender classification")
    skill: WorkerSkill = Field(default=WorkerSkill.GENERAL_LABOR, description="Skill specialization")
    daily_salary: Decimal = Field(default=Decimal("0.00"), ge=0, description="Daily salary rate in INR")
    village: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=255)
    payment_preference: PaymentMethod = Field(default=PaymentMethod.CASH, description="Preferred payment mode")
    is_active: bool = Field(default=True)

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        res = validate_and_format_phone(v)
        if not res:
            raise ValueError("Mobile number is required.")
        return res


class WorkerCreate(WorkerBase):
    worker_code: Optional[str] = Field(default=None, max_length=50, description="Auto-generated if omitted")
    user_id: Optional[uuid.UUID] = None


class WorkerUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    mobile_number: Optional[str] = Field(default=None, min_length=7, max_length=20)
    gender: Optional[WorkerGender] = None
    skill: Optional[WorkerSkill] = None
    daily_salary: Optional[Decimal] = Field(default=None, ge=0)
    village: Optional[str] = None
    address: Optional[str] = None
    payment_preference: Optional[PaymentMethod] = None
    is_active: Optional[bool] = None

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_and_format_phone(v)
        return None


class WorkerResponse(WorkerBase):
    id: uuid.UUID
    farmer_profile_id: uuid.UUID
    worker_code: str
    user_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkerListResponse(BaseModel):
    items: List[WorkerResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


# ==========================================
# Machine Master Schemas
# ==========================================

class MachineBase(BaseModel):
    machine_name: str = Field(..., min_length=2, max_length=150, description="Name/Model of machine")
    machine_type: MachineType = Field(default=MachineType.TRACTOR)
    ownership_type: str = Field(default="OWNED", description="OWNED or RENTAL")
    owner_name: Optional[str] = Field(default=None, max_length=150)
    owner_contact: Optional[str] = Field(default=None, max_length=20)
    rate_per_hour: Optional[Decimal] = Field(default=None, ge=0)
    rate_per_day: Optional[Decimal] = Field(default=None, ge=0)
    operator_included: bool = Field(default=False)
    is_active: bool = Field(default=True)


class MachineCreate(MachineBase):
    machine_code: Optional[str] = Field(default=None, max_length=50, description="Auto-generated if omitted")


class MachineUpdate(BaseModel):
    machine_name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    machine_type: Optional[MachineType] = None
    ownership_type: Optional[str] = None
    owner_name: Optional[str] = None
    owner_contact: Optional[str] = None
    rate_per_hour: Optional[Decimal] = Field(default=None, ge=0)
    rate_per_day: Optional[Decimal] = Field(default=None, ge=0)
    operator_included: Optional[bool] = None
    is_active: Optional[bool] = None


class MachineResponse(MachineBase):
    id: uuid.UUID
    farmer_profile_id: uuid.UUID
    machine_code: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MachineListResponse(BaseModel):
    items: List[MachineResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


# ==========================================
# Worker Attendance & Attendance Schemas
# ==========================================

class WorkerAttendanceCreate(BaseModel):
    worker_id: uuid.UUID = Field(..., description="Worker UUID from Worker Master")
    work_date: date = Field(default_factory=date.today)
    start_time: Optional[str] = Field(default="08:00 AM", max_length=20)
    end_time: Optional[str] = Field(default="05:00 PM", max_length=20)
    break_hours: Decimal = Field(default=Decimal("1.00"), ge=0)
    total_hours: Decimal = Field(default=Decimal("8.00"), gt=0)
    working_days: Decimal = Field(default=Decimal("1.00"), gt=0)
    daily_salary: Optional[Decimal] = Field(default=None, ge=0, description="Overrides worker master salary if provided")
    overtime_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    notes: Optional[str] = None

    @field_validator("work_date")
    @classmethod
    def validate_work_date_not_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Attendance date cannot be in the future")
        return v


class BulkWorkerAttendanceCreate(BaseModel):
    attendances: List[WorkerAttendanceCreate]


class WorkerAttendanceResponse(BaseModel):
    id: uuid.UUID
    stage_id: uuid.UUID
    cultivation_id: uuid.UUID
    worker_id: uuid.UUID
    worker_name: str
    worker_code: str
    gender: str
    skill: str
    mobile_number: str
    work_date: date
    start_time: Optional[str]
    end_time: Optional[str]
    break_hours: Decimal
    total_hours: Decimal
    working_days: Decimal
    daily_salary: Decimal
    overtime_amount: Decimal
    calculated_amount: Decimal
    payment_status: str
    bill_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Machine Usage Schemas
# ==========================================

class MachineUsageCreate(BaseModel):
    machine_id: uuid.UUID = Field(..., description="Machine UUID from Machine Master")
    usage_date: date = Field(default_factory=date.today)
    hours_used: Decimal = Field(default=Decimal("0.00"), ge=0)
    days_used: Decimal = Field(default=Decimal("0.00"), ge=0)
    rate_applied: Optional[Decimal] = Field(default=None, ge=0)
    fuel_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    operator_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    notes: Optional[str] = None


class MachineUsageResponse(BaseModel):
    id: uuid.UUID
    stage_id: uuid.UUID
    cultivation_id: uuid.UUID
    machine_id: uuid.UUID
    machine_name: str
    machine_code: str
    machine_type: str
    usage_date: date
    hours_used: Decimal
    days_used: Decimal
    rate_applied: Decimal
    fuel_cost: Decimal
    operator_cost: Decimal
    total_cost: Decimal
    bill_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Material Purchase Schemas
# ==========================================

class MaterialPurchaseCreate(BaseModel):
    supplier_id: uuid.UUID = Field(..., description="Supplier UUID from Supplier Master")
    cultivation_id: Optional[uuid.UUID] = None
    stage_id: Optional[uuid.UUID] = None
    material_category: str = Field(default="SEED")
    material_name: str = Field(..., min_length=2, max_length=150)
    quantity: Decimal = Field(..., gt=0)
    unit: str = Field(default="KG", max_length=30)
    unit_rate: Decimal = Field(..., ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    purchase_date: date = Field(default_factory=date.today)
    notes: Optional[str] = None


class MaterialPurchaseResponse(BaseModel):
    id: uuid.UUID
    purchase_code: str
    farmer_profile_id: uuid.UUID
    cultivation_id: Optional[uuid.UUID]
    stage_id: Optional[uuid.UUID]
    supplier_id: uuid.UUID
    supplier_name: str
    supplier_contact: str
    material_category: str
    material_name: str
    quantity: Decimal
    unit: str
    unit_rate: Decimal
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    purchase_date: date
    payment_status: str
    bill_id: Optional[uuid.UUID]
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MaterialPurchaseListResponse(BaseModel):
    items: List[MaterialPurchaseResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


# ==========================================
# Cultivation Schedule Schemas
# ==========================================

class CultivationScheduleItem(BaseModel):
    stage_order: int
    stage_name: str
    planned_start_date: date
    planned_end_date: date
    estimated_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    status: str = Field(default="PLANNED")


class CultivationScheduleBulkCreate(BaseModel):
    schedules: List[CultivationScheduleItem]


class CultivationScheduleResponse(CultivationScheduleItem):
    id: uuid.UUID
    cultivation_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Billing & Invoice Schemas
# ==========================================

class BillItemCreate(BaseModel):
    item_type: str = Field(default="LABOR")
    item_description: str
    quantity: Decimal = Field(default=Decimal("1.00"), gt=0)
    unit: str = Field(default="UNIT")
    unit_price: Decimal = Field(..., ge=0)
    total_price: Decimal = Field(..., ge=0)


class BillItemResponse(BillItemCreate):
    id: uuid.UUID
    bill_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class BillCreate(BaseModel):
    farm_id: uuid.UUID
    cultivation_id: Optional[uuid.UUID] = None
    stage_id: Optional[uuid.UUID] = None
    bill_type: BillType = Field(default=BillType.STAGE_CONSOLIDATED)
    recipient_name: str = Field(..., max_length=150)
    recipient_type: str = Field(default="CONSOLIDATED")
    recipient_worker_id: Optional[uuid.UUID] = None
    recipient_supplier_id: Optional[uuid.UUID] = None
    bill_date: date = Field(default_factory=date.today)
    due_date: Optional[date] = None
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    items: List[BillItemCreate] = []
    notes: Optional[str] = None


class StageBillGenerateRequest(BaseModel):
    stage_id: uuid.UUID
    include_workers: bool = True
    include_machines: bool = True
    include_materials: bool = True
    include_other: bool = True
    notes: Optional[str] = None


class BillResponse(BaseModel):
    id: uuid.UUID
    bill_number: str
    farmer_profile_id: uuid.UUID
    farm_id: uuid.UUID
    farm_name: str
    cultivation_id: Optional[uuid.UUID]
    crop_name: Optional[str]
    stage_id: Optional[uuid.UUID]
    stage_name: Optional[str]
    bill_type: str
    recipient_name: str
    recipient_type: str
    recipient_worker_id: Optional[uuid.UUID]
    recipient_supplier_id: Optional[uuid.UUID]
    bill_date: date
    due_date: Optional[date]
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    pending_amount: Decimal
    status: str
    notes: Optional[str]
    items: List[BillItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BillListResponse(BaseModel):
    items: List[BillResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


# ==========================================
# Payment Checkout Schemas
# ==========================================

class PaymentCreate(BaseModel):
    bill_id: uuid.UUID
    amount: Decimal = Field(..., gt=0, description="Amount to pay in INR")
    payment_method: PaymentMethod = Field(default=PaymentMethod.CASH)
    transaction_reference: Optional[str] = Field(default=None, max_length=100, description="UPI/Bank reference ID (NO PINs or sensitive credentials)")
    payment_date: Optional[datetime] = Field(default_factory=datetime.now)
    send_sms_notification: bool = Field(default=True, description="Trigger SMS notification to recipient")
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    id: uuid.UUID
    payment_number: str
    bill_id: uuid.UUID
    bill_number: str
    farmer_profile_id: uuid.UUID
    amount: Decimal
    payment_method: str
    payment_date: datetime
    status: str
    transaction_reference: Optional[str]
    recipient_name: str
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentListResponse(BaseModel):
    items: List[PaymentResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


# ==========================================
# Logistics Schemas
# ==========================================

class LogisticsCreate(BaseModel):
    cultivation_id: uuid.UUID
    farm_id: uuid.UUID
    harvest_location: str = Field(..., min_length=2, max_length=255)
    destination: str = Field(..., min_length=2, max_length=255)
    pickup_date: datetime = Field(default_factory=datetime.now)
    delivery_date: Optional[datetime] = None
    vehicle_number: str = Field(..., min_length=2, max_length=50)
    driver_name: str = Field(..., min_length=2, max_length=150)
    driver_contact: str = Field(..., min_length=10, max_length=20)
    driver_id: Optional[uuid.UUID] = None
    quantity_transported: Decimal = Field(..., gt=0)
    quantity_unit: str = Field(default="KG", max_length=30)
    transport_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    loading_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    unloading_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    notes: Optional[str] = None


class LogisticsStatusUpdate(BaseModel):
    status: LogisticsStatus
    delivery_date: Optional[datetime] = None
    notes: Optional[str] = None


class LogisticsResponse(BaseModel):
    id: uuid.UUID
    dispatch_code: str
    farmer_profile_id: uuid.UUID
    cultivation_id: uuid.UUID
    crop_name: str
    farm_id: uuid.UUID
    farm_name: str
    harvest_location: str
    destination: str
    pickup_date: datetime
    delivery_date: Optional[datetime]
    vehicle_number: str
    driver_name: str
    driver_contact: str
    driver_id: Optional[uuid.UUID]
    quantity_transported: Decimal
    quantity_unit: str
    transport_cost: Decimal
    loading_cost: Decimal
    unloading_cost: Decimal
    total_logistics_cost: Decimal
    status: str
    bill_id: Optional[uuid.UUID]
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LogisticsListResponse(BaseModel):
    items: List[LogisticsResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


# ==========================================
# SMS / Notifications Schemas
# ==========================================

class SMSSendRequest(BaseModel):
    recipient_mobile: str = Field(..., min_length=5, max_length=20)
    recipient_name: str = Field(default="Recipient", max_length=150)
    recipient_type: str = Field(default="WORKER")
    message_body: str = Field(..., min_length=1)
    notification_type: NotificationType = Field(default=NotificationType.WORK_COMPLETED_PAYMENT)
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[uuid.UUID] = None

    @field_validator("recipient_mobile")
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        res = validate_and_format_phone(v)
        if not res:
            raise ValueError("Recipient mobile number is required.")
        return res

    @model_validator(mode="before")
    @classmethod
    def normalize_sms_payload(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Normalize recipient_mobile from phone_number / mobile / phone
            if not data.get("recipient_mobile"):
                data["recipient_mobile"] = (
                    data.get("phone_number")
                    or data.get("mobile")
                    or data.get("phone")
                    or ""
                )
            # Normalize message_body from message / content / text
            if not data.get("message_body"):
                data["message_body"] = (
                    data.get("message")
                    or data.get("content")
                    or data.get("text")
                    or ""
                )
            # Normalize recipient_name
            if not data.get("recipient_name"):
                data["recipient_name"] = data.get("name") or "Recipient"
        return data


class SMSLogResponse(BaseModel):
    id: uuid.UUID
    farmer_profile_id: uuid.UUID
    recipient_mobile: str
    recipient_name: str
    recipient_type: str
    message_body: str
    notification_type: str
    related_entity_type: Optional[str]
    related_entity_id: Optional[uuid.UUID]
    status: str
    sent_at: Optional[datetime]
    gateway_response: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SMSLogListResponse(BaseModel):
    items: List[SMSLogResponse]
    page: int = 1
    page_size: int = 50
    total: int = 0
    total_pages: int = 0
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None
    has_more: bool = False


# ==========================================
# CRM Dashboard Summary & Analytics Schemas
# ==========================================

class CRMTodayActivityItem(BaseModel):
    id: uuid.UUID
    cultivation_id: uuid.UUID
    farm_name: str
    crop_name: str
    stage_name: str
    stage_order: int
    workers_assigned: int
    machines_assigned: int
    status: str


class CRMDashboardSummaryResponse(BaseModel):
    total_farms: int
    active_crop_plans: int
    active_cultivations: int
    today_work_count: int
    workers_currently_assigned: int
    machines_currently_assigned: int
    material_purchases_count: int
    total_cultivation_cost: Decimal
    pending_payments_amount: Decimal
    completed_payments_amount: Decimal
    current_crop_stage: Optional[str] = None
    current_crop_progress_pct: int = 0
    active_cultivation_farm: Optional[str] = None
    active_cultivation_crop: Optional[str] = None
    active_cultivation_season: Optional[str] = None
    today_activities: List[CRMTodayActivityItem] = []


class StageCostBreakdown(BaseModel):
    stage_order: int
    stage_name: str
    status: str
    labor_cost: Decimal
    machine_cost: Decimal
    material_cost: Decimal
    other_cost: Decimal
    total_stage_cost: Decimal
    paid_amount: Decimal
    pending_amount: Decimal


class CropCostSummaryResponse(BaseModel):
    cultivation_id: uuid.UUID
    farm_name: str
    crop_name: str
    season: str
    land_area: Decimal
    land_area_unit: str
    stages: List[StageCostBreakdown]
    total_labor_cost: Decimal
    total_machine_cost: Decimal
    total_material_cost: Decimal
    total_logistics_cost: Decimal
    total_other_cost: Decimal
    total_cultivation_cost: Decimal
    cost_per_area_unit: Decimal
    total_paid_amount: Decimal
    total_pending_amount: Decimal
    gross_revenue: Optional[Decimal] = None
    net_profit_or_loss: Optional[Decimal] = None


# ==========================================
# CRM Record Detailed View Schemas
# ==========================================

class CRMTimelineEvent(BaseModel):
    date: date
    title: str
    stage_name: str
    event_type: str  # STAGE_STARTED, WORKER_LOGGED, PURCHASE_MADE, BILL_GENERATED, PAYMENT_PAID, LOGISTICS_DISPATCHED
    description: str
    cost: Optional[Decimal] = None
    payment_status: Optional[str] = None
    metadata: Optional[dict] = None


class CRMCultivationDetailResponse(BaseModel):
    cultivation_id: uuid.UUID
    farm_id: uuid.UUID
    farm_name: str
    crop_id: uuid.UUID
    crop_name: str
    season: str
    land_area: Decimal
    land_area_unit: str
    sowing_date: Optional[date] = None
    target_harvest_date: Optional[date] = None
    current_stage_order: int
    current_stage_name: str
    overall_progress_pct: int
    status: str
    total_cost: Decimal
    total_paid: Decimal
    total_pending: Decimal
    worker_count: int
    machine_count: int
    purchase_count: int
    logistics_count: int
    stages: List[StageCostBreakdown]
    timeline_events: List[CRMTimelineEvent]


# ==========================================
# CRM Reports Schemas
# ==========================================

class CropCostReportItem(BaseModel):
    cultivation_id: uuid.UUID
    farm_name: str
    crop_name: str
    season: str
    land_area: Decimal
    land_area_unit: str
    labor_cost: Decimal
    machine_cost: Decimal
    material_cost: Decimal
    logistics_cost: Decimal
    other_cost: Decimal
    total_cost: Decimal
    cost_per_acre: Decimal
    paid_amount: Decimal
    pending_amount: Decimal


class WorkerPaymentReportItem(BaseModel):
    worker_id: uuid.UUID
    worker_code: str
    worker_name: str
    mobile_number: str
    gender: str
    skill: str
    total_working_days: Decimal
    total_salary: Decimal
    paid_amount: Decimal
    pending_amount: Decimal


class SupplierPurchaseReportItem(BaseModel):
    supplier_id: uuid.UUID
    supplier_code: str
    supplier_name: str
    phone_number: str
    total_purchases_count: int
    total_purchase_amount: Decimal
    paid_amount: Decimal
    pending_amount: Decimal


class FarmExpenseReportItem(BaseModel):
    category: str
    total_amount: Decimal
    paid_amount: Decimal
    pending_amount: Decimal
    percentage: Decimal
