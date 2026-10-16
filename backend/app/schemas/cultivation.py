import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import StageStatus, ExpenseCategory, PaymentMode, MachineryOwnership, FarmingMethod, WorkerPaymentStatus


# ==========================================
# Worker Wage & Attendance Schemas
# ==========================================

class StageWorkerLogBase(BaseModel):
    worker_name: str = Field(..., min_length=1, max_length=150, description="Worker name (e.g., 'மாரியம்மாள்', 'கந்தசாமி')")
    worker_id: Optional[uuid.UUID] = Field(default=None, description="Registered User UUID if assigned")
    days_worked: Decimal = Field(..., gt=0, le=365, description="Days worked (e.g., 4.0 or 2.5)")
    daily_wage: Decimal = Field(..., ge=0, description="Daily wage in INR (e.g., 350.00)")
    payment_status: WorkerPaymentStatus = Field(default=WorkerPaymentStatus.PENDING, description="PAID or PENDING")
    notes: Optional[str] = Field(default=None, max_length=500)


class StageWorkerLogCreate(StageWorkerLogBase):
    pass


class BulkWorkerLogCreate(BaseModel):
    workers: List[StageWorkerLogCreate] = Field(..., min_length=1)


class StageWorkerLogUpdate(BaseModel):
    worker_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    days_worked: Optional[Decimal] = Field(default=None, gt=0, le=365)
    daily_wage: Optional[Decimal] = Field(default=None, ge=0)
    payment_status: Optional[WorkerPaymentStatus] = None
    notes: Optional[str] = None


class StageWorkerPaymentStatusUpdate(BaseModel):
    payment_status: WorkerPaymentStatus


class StageWorkerLogResponse(BaseModel):
    id: uuid.UUID
    stage_id: uuid.UUID
    cultivation_id: uuid.UUID
    worker_name: str
    worker_id: Optional[uuid.UUID] = None
    days_worked: Decimal
    daily_wage: Decimal
    total_wage: Decimal
    payment_status: str
    notes: Optional[str] = None
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Stage Expense Schemas
# ==========================================

class StageExpenseBase(BaseModel):
    expense_category: ExpenseCategory
    title: str = Field(..., min_length=1, max_length=255)
    amount: Decimal = Field(..., gt=0)
    payment_mode: PaymentMode = Field(default=PaymentMode.CASH)
    worker_count: Optional[int] = Field(default=None, ge=1)
    per_head_wage: Optional[Decimal] = Field(default=None, ge=0)
    quantity_desc: Optional[str] = Field(default=None, max_length=200)
    machinery_type: Optional[MachineryOwnership] = None
    bill_image_url: Optional[str] = Field(default=None, max_length=500)
    notes: Optional[str] = None


class StageExpenseCreate(StageExpenseBase):
    pass


class StageExpenseResponse(BaseModel):
    id: uuid.UUID
    stage_id: uuid.UUID
    cultivation_id: uuid.UUID
    expense_category: str
    title: str
    amount: Decimal
    payment_mode: str
    worker_count: Optional[int] = None
    per_head_wage: Optional[Decimal] = None
    quantity_desc: Optional[str] = None
    machinery_type: Optional[str] = None
    bill_image_url: Optional[str] = None
    notes: Optional[str] = None
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Dynamic Stage Schemas
# ==========================================

class CustomStageCreate(BaseModel):
    stage_name: str = Field(..., min_length=1, max_length=200, description="Custom stage name in Tamil/English")
    stage_order: Optional[int] = Field(default=None, ge=1, description="Optional custom position; if omitted, appended at end")
    farming_type: Optional[FarmingMethod] = Field(default=FarmingMethod.CONVENTIONAL)
    status: Optional[StageStatus] = Field(default=StageStatus.PENDING)


class CultivationStageUpdate(BaseModel):
    stage_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    status: Optional[StageStatus] = None
    farming_type: Optional[FarmingMethod] = None
    start_date: Optional[date] = None
    completed_date: Optional[date] = None


class CultivationStageResponse(BaseModel):
    id: uuid.UUID
    cultivation_id: uuid.UUID
    stage_order: int
    stage_name: str
    farming_type: str = "CONVENTIONAL"
    status: str
    start_date: Optional[date] = None
    completed_date: Optional[date] = None
    expenses: List[StageExpenseResponse] = []
    worker_logs: List[StageWorkerLogResponse] = []
    total_labor_wages: Decimal = Decimal("0.00")
    total_expenses: Decimal = Decimal("0.00")

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Cultivation Run Schemas
# ==========================================

class CultivationRunCreate(BaseModel):
    farm_crop_plan_id: uuid.UUID
    sowing_date: Optional[date] = None
    maturity_days: Optional[int] = Field(default=90, ge=1, le=365)
    farming_method: Optional[FarmingMethod] = Field(default=FarmingMethod.CONVENTIONAL)
    season_year: Optional[str] = Field(default=None, max_length=50)
    land_area: Optional[Decimal] = Field(default=None, gt=0)
    land_area_unit: Optional[str] = Field(default="ACRE", max_length=20)
    custom_stages: Optional[List[str]] = Field(default=None, description="Optional custom initial stage list")


class CultivationRunStatusUpdate(BaseModel):
    is_active: bool


class HarvestYieldUpdate(BaseModel):
    yield_quantity: Decimal = Field(..., ge=0, description="Harvested crop quantity")
    yield_unit: Optional[str] = Field(default="Bags / மூட்டை", max_length=50)
    selling_price_per_unit: Decimal = Field(..., ge=0, description="Market selling price per unit in INR")
    gross_revenue: Optional[Decimal] = Field(default=None, ge=0, description="Total sales gross income; auto-calculated if None")


class CultivationRunResponse(BaseModel):
    id: uuid.UUID
    farm_crop_plan_id: uuid.UUID
    farm_id: uuid.UUID
    crop_id: uuid.UUID
    crop_name: str
    farm_name: str
    farm_code: str
    sowing_date: date
    maturity_days: int
    target_harvest_date: date
    current_stage_order: int
    farming_method: str = "CONVENTIONAL"
    season_year: Optional[str] = None
    land_area: Optional[Decimal] = None
    land_area_unit: str = "ACRE"
    yield_quantity: Optional[Decimal] = None
    yield_unit: Optional[str] = "Bags / மூட்டை"
    selling_price_per_unit: Optional[Decimal] = None
    gross_revenue: Optional[Decimal] = None
    is_active: bool
    is_deleted: bool
    stages: List[CultivationStageResponse] = []
    total_expenses: Decimal = Decimal("0.00")
    total_labor_wages: Decimal = Decimal("0.00")
    total_material_expenses: Decimal = Decimal("0.00")
    total_machinery_expenses: Decimal = Decimal("0.00")
    total_pending_wages: Decimal = Decimal("0.00")
    net_profit: Optional[Decimal] = None
    net_result: Optional[Decimal] = None
    net_result_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CultivationRunListResponse(BaseModel):
    items: List[CultivationRunResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


# ==========================================
# Comparison Schemas (Organic vs Conventional / Year-Over-Year)
# ==========================================

class ComparisonBreakdownMetric(BaseModel):
    category_key: str
    title_en: str
    title_ta: str
    conventional_val: Decimal
    organic_val: Decimal
    diff_val: Decimal  # positive means organic spent more; negative means savings
    unit: str = "₹"
    notes_conventional: Optional[str] = None
    notes_organic: Optional[str] = None


class CultivationComparisonResponse(BaseModel):
    conventional_run: Optional[CultivationRunResponse] = None
    organic_run: Optional[CultivationRunResponse] = None
    breakdown_metrics: List[ComparisonBreakdownMetric] = []
    total_conventional_expense: Decimal = Decimal("0.00")
    total_organic_expense: Decimal = Decimal("0.00")
    expense_savings: Decimal = Decimal("0.00")  # (conv - org)
    conventional_gross_revenue: Decimal = Decimal("0.00")
    organic_gross_revenue: Decimal = Decimal("0.00")
    conventional_net_profit: Decimal = Decimal("0.00")
    organic_net_profit: Decimal = Decimal("0.00")
    net_profit_gain: Decimal = Decimal("0.00")  # (org_net - conv_net)
    has_previous_data: bool = True
    message: Optional[str] = None


class MediaUploadProofRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(default="image/jpeg", max_length=100)
    file_size_bytes: Optional[int] = None


class MediaUploadProofResponse(BaseModel):
    upload_url: str
    public_url: str
    file_key: str
    expires_in_seconds: int = 3600

