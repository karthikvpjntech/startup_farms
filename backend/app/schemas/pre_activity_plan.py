import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class MaterialItemDetail(BaseModel):
    item_name: str
    quantity: Decimal = Decimal("1.0")
    unit: str = "Unit"
    unit_cost: Decimal = Decimal("0.00")
    total_cost: Decimal = Decimal("0.00")
    notes: Optional[str] = None


class MachineryDetail(BaseModel):
    machinery_type: Optional[str] = "Tractor"
    diesel_liters: Optional[Decimal] = None
    diesel_rate_per_liter: Optional[Decimal] = None
    rental_hours: Optional[Decimal] = None
    rental_rate_per_hour: Optional[Decimal] = None
    driver_wage_included: Optional[bool] = True
    total_machinery_cost: Decimal = Decimal("0.00")
    notes: Optional[str] = None


class LaborCrewDetail(BaseModel):
    estimated_workers: int = 0
    wage_per_head: Decimal = Decimal("0.00")
    worker_names: Optional[List[str]] = None
    total_labor_cost: Decimal = Decimal("0.00")
    notes: Optional[str] = None


class PreActivityPlanBase(BaseModel):
    activity_name: str = Field(..., max_length=200, description="Name of the activity (e.g. முதல் சால் உழவு)")
    activity_type: str = Field(default="TILLAGE", description="Type: TILLAGE, SOWING, WEEDING, FERTILIZATION, SPRAYING, HARVESTING, OTHER")
    purpose: str = Field(..., description="Objective / நோக்கம் of this farm activity")
    machinery_mode: str = Field(default="NONE", description="OWN_TRACTOR, RENTAL_TRACTOR, BULL_CART, MANUAL, NONE")
    machinery_details: Dict[str, Any] = Field(default_factory=dict)
    materials_details: List[Dict[str, Any]] = Field(default_factory=list)
    labor_details: Dict[str, Any] = Field(default_factory=dict)
    estimated_total_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    status: str = Field(default="PLANNED", description="PLANNED, IN_PROGRESS, COMPLETED, CANCELLED")


class PreActivityPlanCreate(PreActivityPlanBase):
    pass


class PreActivityPlanUpdate(BaseModel):
    activity_name: Optional[str] = None
    activity_type: Optional[str] = None
    purpose: Optional[str] = None
    machinery_mode: Optional[str] = None
    machinery_details: Optional[Dict[str, Any]] = None
    materials_details: Optional[List[Dict[str, Any]]] = None
    labor_details: Optional[Dict[str, Any]] = None
    estimated_total_cost: Optional[Decimal] = None
    status: Optional[str] = None


class PreActivityPlanResponse(BaseModel):
    id: uuid.UUID
    stage_id: uuid.UUID
    cultivation_id: uuid.UUID
    activity_name: str
    activity_type: str
    purpose: str
    machinery_mode: str
    machinery_details: Dict[str, Any]
    materials_details: List[Dict[str, Any]]
    labor_details: Dict[str, Any]
    estimated_total_cost: Decimal
    status: str
    actual_converted: bool
    converted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PreActivityConvertRequest(BaseModel):
    payment_mode: str = Field(default="CASH", description="CASH, UPI, BANK_TRANSFER")
    override_actual_cost: Optional[Decimal] = None
    worker_names: Optional[List[str]] = None
    notes: Optional[str] = None


class PreActivityConvertResponse(BaseModel):
    plan_id: uuid.UUID
    stage_id: uuid.UUID
    cultivation_id: uuid.UUID
    expenses_created: int
    worker_logs_created: int
    total_logged_amount: Decimal
    message: str
