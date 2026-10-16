import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.enums import OwnershipTypeEnum, LandAreaUnitEnum


class FarmBase(BaseModel):
    """Base schema defining common farm fields."""
    farm_name: str = Field(..., min_length=1, max_length=255, description="Name of the farm")
    ownership_type: OwnershipTypeEnum = Field(..., description="Ownership model (OWNED, LEASED, SHARED, MANAGED)")
    total_land_area: Decimal = Field(..., gt=0, description="Total land area (must be strictly greater than 0)")
    land_area_unit: LandAreaUnitEnum = Field(..., description="Measurement unit (ACRE, HECTARE, SQUARE_METER)")
    survey_number: Optional[str] = Field(default=None, max_length=100, description="Government Survey / Gat / Khasra / Patta Number")
    survey_link: Optional[str] = Field(default=None, max_length=500, description="URL link to official Land Records portal / GIS survey map / digital RTC")
    address_line1: Optional[str] = Field(default=None, max_length=255, description="Street / Survey No / Area")
    address_line2: Optional[str] = Field(default=None, max_length=255, description="Secondary address / Landmark")
    village: Optional[str] = Field(default=None, max_length=100, description="Village name")
    district: Optional[str] = Field(default=None, max_length=100, description="District name")
    state: Optional[str] = Field(default=None, max_length=100, description="State name")
    pincode: Optional[str] = Field(default=None, max_length=10, description="Postal pincode")
    latitude: Optional[Decimal] = Field(default=None, ge=-90, le=90, description="Geographic latitude (-90 to +90)")
    longitude: Optional[Decimal] = Field(default=None, ge=-180, le=180, description="Geographic longitude (-180 to +180)")

    @field_validator("farm_name")
    @classmethod
    def clean_farm_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Farm name cannot be empty or whitespace only")
        return cleaned


class FarmCreate(FarmBase):
    """Request payload for creating a new farm."""
    pass


class FarmUpdate(BaseModel):
    """Request payload for partially updating farm details."""
    farm_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    ownership_type: Optional[OwnershipTypeEnum] = None
    total_land_area: Optional[Decimal] = Field(default=None, gt=0)
    land_area_unit: Optional[LandAreaUnitEnum] = None
    survey_number: Optional[str] = Field(default=None, max_length=100)
    survey_link: Optional[str] = Field(default=None, max_length=500)
    address_line1: Optional[str] = Field(default=None, max_length=255)
    address_line2: Optional[str] = Field(default=None, max_length=255)
    village: Optional[str] = Field(default=None, max_length=100)
    district: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    pincode: Optional[str] = Field(default=None, max_length=10)
    latitude: Optional[Decimal] = Field(default=None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(default=None, ge=-180, le=180)

    @field_validator("farm_name")
    @classmethod
    def clean_farm_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Farm name cannot be empty or whitespace only")
            return cleaned
        return None


class FarmStatusUpdate(BaseModel):
    """Request payload for updating farm active status."""
    is_active: bool = Field(..., description="Target active status for the farm")


class FarmResponse(BaseModel):
    """Response representation of a farm entity."""
    id: uuid.UUID
    farmer_profile_id: uuid.UUID
    farm_name: str
    farm_code: str
    ownership_type: str
    total_land_area: Decimal
    land_area_unit: str
    survey_number: Optional[str] = None
    survey_link: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    is_active: bool
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True)


class FarmListResponse(BaseModel):
    """Paginated farm listing response."""
    items: List[FarmResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class LandSurveyPortalInfo(BaseModel):
    """Metadata describing an official state land records / survey portal."""
    id: str
    state: str
    portal_name: str
    portal_url: str
    survey_term: str
    document_types: List[str]
    description: str
    sample_survey_format: str


class SurveyPortalsResponse(BaseModel):
    """Response containing official state land record survey portals."""
    portals: List[LandSurveyPortalInfo]
    total: int


class SurveyLinkParseRequest(BaseModel):
    """Request payload to parse and extract metadata from a land records or GIS link."""
    url: str = Field(..., min_length=3, max_length=1000, description="URL of land record, state portal, or GIS map")


class SurveyLinkParseResponse(BaseModel):
    """Extracted metadata and recommendations from survey link."""
    is_valid_url: bool
    recognized_portal: Optional[str] = None
    detected_state: Optional[str] = None
    extracted_survey_number: Optional[str] = None
    extracted_district: Optional[str] = None
    extracted_village: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    clean_url: str
    instructions: Optional[str] = None
