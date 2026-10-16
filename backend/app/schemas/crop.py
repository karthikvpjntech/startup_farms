import uuid
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.enums import CropCategory, CropCategoryEnum


class CropBase(BaseModel):
    """Base schema defining core crop master fields."""
    crop_name: str = Field(..., min_length=1, max_length=100, description="Common name of the crop (e.g. Rice, Tomato)")
    crop_name_local: Optional[str] = Field(default=None, max_length=200, description="Local language name (e.g. வெங்காயம்)")
    local_names: Optional[Dict[str, str]] = Field(default_factory=dict, description="Multilingual name dictionary {'ta': '...', 'hi': '...', 'kn': '...', 'te': '...'}")
    image_url: Optional[str] = Field(default=None, max_length=500, description="Visual media or crop illustration URL")
    scientific_name: Optional[str] = Field(default=None, max_length=150, description="Botanical / scientific name")
    crop_category: CropCategory = Field(..., description="Crop category classification")
    description: Optional[str] = Field(default=None, description="Brief agronomic description")

    @field_validator("crop_name")
    @classmethod
    def clean_crop_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Crop name cannot be empty or whitespace only")
        return cleaned

    @field_validator("scientific_name", "description", "crop_name_local", "image_url")
    @classmethod
    def clean_optional_text(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            return cleaned if cleaned else None
        return None


class CropCreate(CropBase):
    """Payload for creating a new crop master record."""
    pass


class CropUpdate(BaseModel):
    """Payload for partially updating a crop master record."""
    crop_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    crop_name_local: Optional[str] = Field(default=None, max_length=200)
    local_names: Optional[Dict[str, str]] = None
    image_url: Optional[str] = Field(default=None, max_length=500)
    scientific_name: Optional[str] = Field(default=None, max_length=150)
    crop_category: Optional[CropCategory] = None
    description: Optional[str] = Field(default=None)

    @field_validator("crop_name")
    @classmethod
    def clean_crop_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Crop name cannot be empty or whitespace only")
            return cleaned
        return None

    @field_validator("scientific_name", "description", "crop_name_local", "image_url")
    @classmethod
    def clean_optional_text(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            return cleaned if cleaned else None
        return None


class CropStatusUpdate(BaseModel):
    """Payload for changing active status of a crop."""
    is_active: bool = Field(..., description="Target active status")


class CropResponse(BaseModel):
    """Safe response payload for Crop Master representation."""
    id: uuid.UUID
    crop_code: str
    crop_name: str
    crop_name_local: Optional[str] = None
    local_names: Optional[Dict[str, str]] = None
    image_url: Optional[str] = None
    scientific_name: Optional[str] = None
    crop_category: str
    description: Optional[str] = None
    is_active: bool
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True)


class CropListResponse(BaseModel):
    """Paginated list response schema for Crop Master records."""
    items: List[CropResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
