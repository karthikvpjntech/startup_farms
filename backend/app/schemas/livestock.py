import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import (
    LivestockSellingModel,
    LivestockGender,
    LivestockStatus,
    LivestockHealthStatus,
    LivestockVaccinationStatus,
    LivestockPriceType,
    LivestockAgeUnit,
    LivestockWeightUnit,
    LivestockImageType,
)


# ============================================================================
# Category & Breed Schemas
# ============================================================================

class LivestockCategoryBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50, description="Unique uppercase category code (e.g. GOAT, CHICKEN)")
    name: str = Field(..., min_length=2, max_length=100, description="Category name in English")
    name_ta: Optional[str] = Field(default=None, max_length=150, description="Category name in Tamil (e.g. ஆடு, கோழி)")
    description: Optional[str] = Field(default=None, description="Category overview description")
    icon_slug: Optional[str] = Field(default=None, max_length=50, description="Icon / illustration identifier")
    display_order: int = Field(default=0, ge=0)
    is_active: bool = True


class LivestockCategoryCreateRequest(LivestockCategoryBase):
    pass


class LivestockCategoryUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    name_ta: Optional[str] = Field(default=None, max_length=150)
    description: Optional[str] = None
    icon_slug: Optional[str] = None
    display_order: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class LivestockBreedBase(BaseModel):
    category_id: uuid.UUID
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=100)
    name_ta: Optional[str] = Field(default=None, max_length=150)
    description: Optional[str] = None
    characteristics: Optional[str] = None
    display_order: int = Field(default=0, ge=0)
    is_active: bool = True


class LivestockBreedCreateRequest(LivestockBreedBase):
    pass


class LivestockBreedUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    name_ta: Optional[str] = Field(default=None, max_length=150)
    description: Optional[str] = None
    characteristics: Optional[str] = None
    display_order: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class LivestockBreedResponse(LivestockBreedBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LivestockCategoryResponse(LivestockCategoryBase):
    id: uuid.UUID
    breeds_count: int = 0
    breeds: List[LivestockBreedResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Livestock Image Schemas
# ============================================================================

class LivestockImageCreateRequest(BaseModel):
    image_url: str = Field(..., min_length=5, max_length=500)
    image_type: LivestockImageType = LivestockImageType.MAIN
    display_order: int = Field(default=0, ge=0)
    is_primary: bool = False


class LivestockImageResponse(BaseModel):
    id: uuid.UUID
    livestock_id: uuid.UUID
    image_url: str
    image_type: str
    display_order: int
    is_primary: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Farmer Livestock Management Schemas
# ============================================================================

class LivestockCreateRequest(BaseModel):
    farm_id: uuid.UUID = Field(..., description="Farm holding where the livestock is housed")
    category_id: uuid.UUID = Field(..., description="Category UUID")
    breed_id: Optional[uuid.UUID] = Field(default=None, description="Breed UUID (optional)")
    name: str = Field(..., min_length=2, max_length=255, description="Livestock listing name")
    tag_number: Optional[str] = Field(default=None, max_length=100, description="Animal tag / ear tag number (mandatory for Individual model)")
    selling_model: LivestockSellingModel = Field(default=LivestockSellingModel.INDIVIDUAL, description="INDIVIDUAL (single animal) or QUANTITY (batch/flock)")
    gender: LivestockGender = Field(default=LivestockGender.UNKNOWN)
    date_of_birth: Optional[date] = None
    age: Optional[Decimal] = Field(default=None, ge=0)
    age_unit: Optional[LivestockAgeUnit] = LivestockAgeUnit.MONTHS
    weight: Optional[Decimal] = Field(default=None, ge=0)
    weight_unit: Optional[LivestockWeightUnit] = LivestockWeightUnit.KG
    health_status: LivestockHealthStatus = LivestockHealthStatus.HEALTHY
    vaccination_status: LivestockVaccinationStatus = LivestockVaccinationStatus.UP_TO_DATE
    vaccination_date: Optional[date] = None
    health_certificate_url: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = None
    location_summary: Optional[str] = Field(default=None, max_length=255)
    price: Decimal = Field(..., ge=0, description="Selling price (per unit or total)")
    price_type: LivestockPriceType = LivestockPriceType.PER_UNIT
    available_quantity: int = Field(default=1, ge=0, description="1 for Individual model, N for Quantity model")
    minimum_order_quantity: int = Field(default=1, ge=1)
    maximum_order_quantity: Optional[int] = Field(default=None, ge=1)
    images: List[LivestockImageCreateRequest] = Field(default=[], description="List of livestock photos / document attachments")


class LivestockUpdateRequest(BaseModel):
    farm_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    breed_id: Optional[uuid.UUID] = None
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    tag_number: Optional[str] = Field(default=None, max_length=100)
    selling_model: Optional[LivestockSellingModel] = None
    gender: Optional[LivestockGender] = None
    date_of_birth: Optional[date] = None
    age: Optional[Decimal] = Field(default=None, ge=0)
    age_unit: Optional[LivestockAgeUnit] = None
    weight: Optional[Decimal] = Field(default=None, ge=0)
    weight_unit: Optional[LivestockWeightUnit] = None
    health_status: Optional[LivestockHealthStatus] = None
    vaccination_status: Optional[LivestockVaccinationStatus] = None
    vaccination_date: Optional[date] = None
    health_certificate_url: Optional[str] = None
    description: Optional[str] = None
    location_summary: Optional[str] = None
    price: Optional[Decimal] = Field(default=None, ge=0)
    price_type: Optional[LivestockPriceType] = None
    available_quantity: Optional[int] = Field(default=None, ge=0)
    minimum_order_quantity: Optional[int] = Field(default=None, ge=1)
    maximum_order_quantity: Optional[int] = Field(default=None, ge=1)
    is_active: Optional[bool] = None
    images: Optional[List[LivestockImageCreateRequest]] = None


# ============================================================================
# Response & Marketplace Views
# ============================================================================

class LivestockFarmSummary(BaseModel):
    id: uuid.UUID
    farm_name: str
    farm_code: str
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class LivestockFarmerSummary(BaseModel):
    id: uuid.UUID
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LivestockResponse(BaseModel):
    id: uuid.UUID
    livestock_code: str
    farmer_profile_id: uuid.UUID
    farm_id: uuid.UUID
    category_id: uuid.UUID
    breed_id: Optional[uuid.UUID] = None
    name: str
    tag_number: Optional[str] = None
    selling_model: str
    gender: str
    date_of_birth: Optional[date] = None
    age: Optional[Decimal] = None
    age_unit: Optional[str] = None
    weight: Optional[Decimal] = None
    weight_unit: Optional[str] = None
    health_status: str
    vaccination_status: str
    vaccination_date: Optional[date] = None
    health_certificate_url: Optional[str] = None
    description: Optional[str] = None
    location_summary: Optional[str] = None
    price: Decimal
    price_type: str
    available_quantity: int
    minimum_order_quantity: int
    maximum_order_quantity: Optional[int] = None
    status: str
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    category_name: Optional[str] = None
    category_name_ta: Optional[str] = None
    breed_name: Optional[str] = None
    breed_name_ta: Optional[str] = None
    primary_image_url: Optional[str] = None
    images: List[LivestockImageResponse] = []
    farm: Optional[LivestockFarmSummary] = None
    farmer: Optional[LivestockFarmerSummary] = None
    average_rating: Optional[float] = None
    total_reviews_count: int = 0
    distance_km: Optional[float] = None
    is_near_you: Optional[bool] = None
    is_in_district: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class LivestockListResponse(BaseModel):
    items: List[LivestockResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class FarmerLivestockStatsResponse(BaseModel):
    total_livestock: int = 0
    available_count: int = 0
    reserved_count: int = 0
    sold_count: int = 0
    drafts_count: int = 0
    total_sales_count: int = 0
    sales_count: int = 0
    pending_orders_count: int = 0
    pending_orders: int = 0
    total_revenue: Decimal = Decimal("0.00")
    revenue: Decimal = Decimal("0.00")
