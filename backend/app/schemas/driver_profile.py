import uuid
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DriverProfileBase(BaseModel):
    license_number: Optional[str] = Field(default=None, max_length=100, description="Commercial / heavy driving license number")
    license_expiry_date: Optional[date] = Field(default=None, description="Driving license expiration date (YYYY-MM-DD)")
    address_line1: Optional[str] = Field(default=None, max_length=255, description="Residential / operational base address")
    district: Optional[str] = Field(default=None, max_length=100, description="Base district")
    state: Optional[str] = Field(default=None, max_length=100, description="Base state")
    pincode: Optional[str] = Field(default=None, max_length=10, description="Postal pincode")


class DriverProfileCreate(DriverProfileBase):
    """Payload for initial driver profile creation."""
    pass


class DriverProfileUpdate(BaseModel):
    """Payload for partial driver profile update."""
    license_number: Optional[str] = Field(default=None, max_length=100)
    license_expiry_date: Optional[date] = Field(default=None)
    address_line1: Optional[str] = Field(default=None, max_length=255)
    district: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    pincode: Optional[str] = Field(default=None, max_length=10)


class DriverProfileResponse(DriverProfileBase):
    """Response payload for driver profile representation."""
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
