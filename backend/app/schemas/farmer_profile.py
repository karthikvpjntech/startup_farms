import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class FarmerProfileBase(BaseModel):
    profile_image_url: Optional[str] = Field(default=None, max_length=500, description="URL to farmer avatar/photo")
    address_line1: Optional[str] = Field(default=None, max_length=255, description="Street / Door / Area address")
    address_line2: Optional[str] = Field(default=None, max_length=255, description="Secondary address / Landmark")
    village: Optional[str] = Field(default=None, max_length=100, description="Village name")
    district: Optional[str] = Field(default=None, max_length=100, description="District name")
    state: Optional[str] = Field(default=None, max_length=100, description="State name")
    pincode: Optional[str] = Field(default=None, max_length=10, description="Postal pincode")
    latitude: Optional[Decimal] = Field(default=None, description="GPS Latitude (-90 to 90)")
    longitude: Optional[Decimal] = Field(default=None, description="GPS Longitude (-180 to 180)")
    location_url: Optional[str] = Field(default=None, max_length=500, description="Google Maps pin or GPS link")


class FarmerProfileCreate(FarmerProfileBase):
    """Payload for initial farmer profile creation."""
    pass


class FarmerProfileUpdate(BaseModel):
    """Payload for partial farmer profile update."""
    profile_image_url: Optional[str] = Field(default=None, max_length=500)
    address_line1: Optional[str] = Field(default=None, max_length=255)
    address_line2: Optional[str] = Field(default=None, max_length=255)
    village: Optional[str] = Field(default=None, max_length=100)
    district: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    pincode: Optional[str] = Field(default=None, max_length=10)
    latitude: Optional[Decimal] = Field(default=None)
    longitude: Optional[Decimal] = Field(default=None)
    location_url: Optional[str] = Field(default=None, max_length=500)


class FarmerProfileResponse(FarmerProfileBase):
    """Response payload for farmer profile representation."""
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
