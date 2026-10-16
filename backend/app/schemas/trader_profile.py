import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TraderProfileBase(BaseModel):
    business_name: Optional[str] = Field(default=None, max_length=255, description="Registered enterprise or trading business name")
    business_registration_number: Optional[str] = Field(default=None, max_length=100, description="GSTIN / Mandi license or business registration number")
    address_line1: Optional[str] = Field(default=None, max_length=255, description="Business address / Mandi shop location")
    address_line2: Optional[str] = Field(default=None, max_length=255, description="Secondary business address / Landmark")
    district: Optional[str] = Field(default=None, max_length=100, description="Trading district")
    state: Optional[str] = Field(default=None, max_length=100, description="Trading state")
    pincode: Optional[str] = Field(default=None, max_length=10, description="Postal pincode")


class TraderProfileCreate(TraderProfileBase):
    """Payload for initial trader profile creation."""
    pass


class TraderProfileUpdate(BaseModel):
    """Payload for partial trader profile update."""
    business_name: Optional[str] = Field(default=None, max_length=255)
    business_registration_number: Optional[str] = Field(default=None, max_length=100)
    address_line1: Optional[str] = Field(default=None, max_length=255)
    address_line2: Optional[str] = Field(default=None, max_length=255)
    district: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    pincode: Optional[str] = Field(default=None, max_length=10)


class TraderProfileResponse(TraderProfileBase):
    """Response payload for trader profile representation."""
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
