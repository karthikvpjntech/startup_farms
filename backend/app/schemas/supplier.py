import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.enums import SupplierType
from app.core.phone_utils import validate_and_format_phone


class SupplierBase(BaseModel):
    """Base schema defining common agricultural supplier fields."""
    supplier_name: str = Field(..., min_length=1, max_length=150, description="Business or individual supplier name")
    contact_person: Optional[str] = Field(default=None, max_length=100, description="Primary contact person name")
    phone_number: str = Field(..., min_length=5, max_length=20, description="Phone / mobile number")
    email: Optional[str] = Field(default=None, max_length=255, description="Email address")
    address_line1: str = Field(..., min_length=1, max_length=255, description="Street / Shop address")
    address_line2: Optional[str] = Field(default=None, max_length=255, description="Secondary address / Landmark")
    village_city: str = Field(..., min_length=1, max_length=100, description="City / Village")
    district: str = Field(..., min_length=1, max_length=100, description="District")
    state: str = Field(..., min_length=1, max_length=100, description="State")
    pincode: str = Field(..., min_length=1, max_length=20, description="Postal / Zip code")
    gstin: Optional[str] = Field(default=None, max_length=30, description="GST / Tax Identification Number")
    supplier_type: SupplierType = Field(default=SupplierType.DISTRIBUTOR, description="Supplier business classification")

    @field_validator("supplier_name", "address_line1", "village_city", "district", "state", "pincode")
    @classmethod
    def clean_required_strings(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Required string field cannot be empty or whitespace only")
        return cleaned

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        res = validate_and_format_phone(v)
        if not res:
            raise ValueError("Phone number is required.")
        return res


class SupplierCreate(SupplierBase):
    """Payload for registering a new supplier."""
    supplier_code: Optional[str] = Field(default=None, max_length=50, description="Optional custom code; generated if omitted")


class SupplierUpdate(BaseModel):
    """Payload for partially updating supplier details."""
    supplier_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    contact_person: Optional[str] = Field(default=None, max_length=100)
    phone_number: Optional[str] = Field(default=None, min_length=5, max_length=20)
    email: Optional[str] = Field(default=None, max_length=255)
    address_line1: Optional[str] = Field(default=None, max_length=255)
    address_line2: Optional[str] = Field(default=None, max_length=255)
    village_city: Optional[str] = Field(default=None, max_length=100)
    district: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    pincode: Optional[str] = Field(default=None, max_length=20)
    gstin: Optional[str] = Field(default=None, max_length=30)
    supplier_type: Optional[SupplierType] = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_and_format_phone(v)
        return None


class SupplierStatusUpdate(BaseModel):
    """Payload for toggling active status of a supplier."""
    is_active: bool = Field(..., description="Target active status flag")


class SupplierResponse(BaseModel):
    """Safe response payload representing a supplier record."""
    id: uuid.UUID
    supplier_code: str
    supplier_name: str
    contact_person: Optional[str] = None
    phone_number: str
    email: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    village_city: str
    district: str
    state: str
    pincode: str
    gstin: Optional[str] = None
    supplier_type: str
    is_active: bool
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True)


class SupplierListResponse(BaseModel):
    """Paginated list response for suppliers."""
    items: List[SupplierResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
