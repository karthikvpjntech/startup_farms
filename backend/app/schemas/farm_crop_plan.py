import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.enums import CropSeason, CropSeasonEnum, LandAreaUnitEnum


class FarmCropPlanCreate(BaseModel):
    """Payload for creating a new farm crop plan with seed rate options."""
    farm_id: uuid.UUID = Field(..., description="UUID of the owned farm")
    crop_id: uuid.UUID = Field(..., description="UUID of the selected active crop")
    season: CropSeason = Field(..., description="Target cultivation season (e.g. KHARIF, RABI)")
    planned_start_date: date = Field(..., description="Planned season starting date")
    planned_end_date: Optional[date] = Field(default=None, description="Planned season concluding date")
    planned_area: Decimal = Field(..., gt=0, description="Planned cultivation area (must be > 0)")
    land_area_unit: LandAreaUnitEnum = Field(..., description="Unit of measurement matching the farm land unit")
    notes: Optional[str] = Field(default=None, description="Optional planning remarks or notes")

    # Seed Specifications & Per-Acre Options
    seed_variety: Optional[str] = Field(default=None, description="Selected seed variety (e.g., CO-51, ADT-37, Co-Onion-5, TMV-7)")
    seed_rate_per_acre: Optional[Decimal] = Field(default=None, ge=0, description="Quantity of seed required per acre")
    seed_rate_unit: Optional[str] = Field(default="kg/acre", description="Unit for seed rate (e.g. kg/acre, grams/acre, bags/acre)")
    total_seed_quantity: Optional[Decimal] = Field(default=None, ge=0, description="Calculated total seed quantity needed")
    sowing_method: Optional[str] = Field(default="DIRECT_SEEDING", description="DIRECT_SEEDING, NURSERY_TRANSPLANTING, BROADCASTING, DRIP_BED")
    seed_brand_or_source: Optional[str] = Field(default=None, description="Supplier / seed certification source")
    remind_next_year: bool = Field(default=True, description="Enable automatic next-year memory notification before the season")

    @model_validator(mode="after")
    def validate_dates(self) -> "FarmCropPlanCreate":
        if self.planned_start_date and self.planned_end_date:
            if self.planned_end_date < self.planned_start_date:
                raise ValueError("planned_end_date must be on or after planned_start_date")
        return self


class FarmCropPlanUpdate(BaseModel):
    """Payload for partially updating a farm crop plan."""
    crop_id: Optional[uuid.UUID] = None
    season: Optional[CropSeason] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    planned_area: Optional[Decimal] = Field(default=None, gt=0)
    land_area_unit: Optional[LandAreaUnitEnum] = None
    notes: Optional[str] = Field(default=None)

    seed_variety: Optional[str] = None
    seed_rate_per_acre: Optional[Decimal] = Field(default=None, ge=0)
    seed_rate_unit: Optional[str] = None
    total_seed_quantity: Optional[Decimal] = Field(default=None, ge=0)
    sowing_method: Optional[str] = None
    seed_brand_or_source: Optional[str] = None
    remind_next_year: Optional[bool] = None

    @model_validator(mode="after")
    def validate_dates(self) -> "FarmCropPlanUpdate":
        if self.planned_start_date and self.planned_end_date:
            if self.planned_end_date < self.planned_start_date:
                raise ValueError("planned_end_date must be on or after planned_start_date")
        return self


class FarmCropPlanStatusUpdate(BaseModel):
    """Payload for updating active status of a farm crop plan."""
    is_active: bool = Field(..., description="Target active status for the crop plan")


class FarmCropPlanResponse(BaseModel):
    """Response payload for Farm Crop Plan representation."""
    id: uuid.UUID
    farm_id: uuid.UUID
    crop_id: uuid.UUID
    season: str
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    planned_area: Decimal
    land_area_unit: str
    notes: Optional[str] = None

    seed_variety: Optional[str] = None
    seed_rate_per_acre: Optional[Decimal] = None
    seed_rate_unit: Optional[str] = "kg/acre"
    total_seed_quantity: Optional[Decimal] = None
    sowing_method: Optional[str] = "DIRECT_SEEDING"
    seed_brand_or_source: Optional[str] = None
    remind_next_year: bool = True

    is_active: bool
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True)


class FarmCropPlanListResponse(BaseModel):
    """Paginated list response for Farm Crop Plans."""
    items: List[FarmCropPlanResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class SeedVarietyOption(BaseModel):
    """Individual certified seed variety with agronomic seed rate per acre."""
    variety_name: str
    variety_name_local: Optional[str] = None
    recommended_seed_rate: Decimal
    seed_rate_unit: str = "kg/acre"
    duration_days: int
    description: Optional[str] = None


class CropSeedRecommendationResponse(BaseModel):
    """Agronomic recommendation payload for seed varieties and per-acre rates."""
    crop_id: Optional[uuid.UUID] = None
    crop_name: str
    crop_name_local: Optional[str] = None
    default_seed_rate_per_acre: Decimal
    seed_rate_unit: str = "kg/acre"
    varieties: List[SeedVarietyOption]
    sowing_methods: List[str]
    agronomic_advisory: str


class HistoricalSeedUsageItem(BaseModel):
    """Previous year / past season seed usage memory record for a farm parcel."""
    plan_id: uuid.UUID
    farm_id: uuid.UUID
    farm_name: str
    crop_id: uuid.UUID
    crop_name: str
    crop_name_local: Optional[str] = None
    season: str
    planned_start_date: Optional[date] = None
    planned_area: Decimal
    land_area_unit: str
    seed_variety: Optional[str] = None
    seed_rate_per_acre: Optional[Decimal] = None
    seed_rate_unit: Optional[str] = "kg/acre"
    total_seed_quantity: Optional[Decimal] = None
    sowing_method: Optional[str] = None
    seed_brand_or_source: Optional[str] = None
    achieved_yield_quantity: Optional[Decimal] = None
    yield_unit: Optional[str] = None
    yield_per_acre: Optional[Decimal] = None
    created_at: datetime

