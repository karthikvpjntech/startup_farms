import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import ProcurementStatus
from app.schemas.farm import FarmResponse
from app.schemas.input_master import InputMasterResponse
from app.schemas.supplier import SupplierResponse


class ProcurementRequestCreate(BaseModel):
    """Payload for creating a new agricultural procurement request."""
    farm_id: uuid.UUID = Field(..., description="Target farm parcel ID")
    input_id: uuid.UUID = Field(..., description="Target agricultural input item ID from catalog")
    preferred_supplier_id: Optional[uuid.UUID] = Field(default=None, description="Optional preferred supplier ID")
    quantity: Decimal = Field(..., gt=0, description="Quantity required (must be > 0)")
    unit: str = Field(..., min_length=1, max_length=30, description="Measurement unit matching input item")
    required_date: date = Field(..., description="Required delivery date")
    notes: Optional[str] = Field(default=None, description="Additional notes or specifications for delivery")


class ProcurementRequestUpdate(BaseModel):
    """Payload for updating an existing procurement request in PENDING status."""
    preferred_supplier_id: Optional[uuid.UUID] = None
    quantity: Optional[Decimal] = Field(default=None, gt=0)
    required_date: Optional[date] = None
    notes: Optional[str] = None


class ProcurementRequestStatusUpdate(BaseModel):
    """Payload for admin / approver changing status of procurement request."""
    status: ProcurementStatus = Field(..., description="New procurement status (APPROVED, REJECTED, FULFILLED, CANCELLED)")


class ProcurementRequestResponse(BaseModel):
    """Safe response payload representing a procurement request."""
    id: uuid.UUID
    request_code: str
    farmer_profile_id: uuid.UUID
    farm_id: uuid.UUID
    input_id: uuid.UUID
    preferred_supplier_id: Optional[uuid.UUID] = None
    quantity: Decimal
    unit: str
    required_date: date
    notes: Optional[str] = None
    status: str
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None

    farm: Optional[FarmResponse] = None
    input_item: Optional[InputMasterResponse] = None
    preferred_supplier: Optional[SupplierResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ProcurementListResponse(BaseModel):
    """Paginated list response for procurement requests."""
    items: List[ProcurementRequestResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
