import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class WorkerProfileBase(BaseModel):
    address_line1: Optional[str] = Field(default=None, max_length=255, description="Residential / native village address")
    district: Optional[str] = Field(default=None, max_length=100, description="District name")
    state: Optional[str] = Field(default=None, max_length=100, description="State name")
    pincode: Optional[str] = Field(default=None, max_length=10, description="Postal pincode")


class WorkerProfileCreate(WorkerProfileBase):
    """Payload for initial worker profile creation."""
    pass


class WorkerProfileUpdate(BaseModel):
    """Payload for partial worker profile update."""
    address_line1: Optional[str] = Field(default=None, max_length=255)
    district: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    pincode: Optional[str] = Field(default=None, max_length=10)


class WorkerProfileResponse(WorkerProfileBase):
    """Response payload for worker profile representation."""
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
