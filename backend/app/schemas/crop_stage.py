import uuid
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CropStageBase(BaseModel):
    """Base schema for crop cultivation process stage."""
    stage_name: str = Field(..., min_length=1, max_length=200, description="Stage name (e.g., Bulb Formation)")
    stage_name_local: Optional[str] = Field(default=None, max_length=200, description="Local language name (e.g., Tamil)")
    description: Optional[str] = Field(default=None, description="Detailed agronomic guidance and stage indicators")
    duration_days: int = Field(default=15, ge=1, le=365, description="Estimated duration in days")
    image_url: Optional[str] = Field(default=None, max_length=500, description="Real uploaded photo URL")
    thumbnail_url: Optional[str] = Field(default=None, max_length=500, description="Thumbnail photo URL")
    visual_asset_type: str = Field(
        default="VEGETATIVE",
        max_length=50,
        description="3D / Visual asset archetype (SEED, SOIL_PREP, NURSERY, TRANSPLANT, VEGETATIVE, BULB_FORMATION, FLOWERING, FRUITING, HARVEST, YIELD_STORAGE)"
    )
    visual_theme_color: str = Field(default="#10b981", max_length=20, description="Hex color theme for stage")
    recommended_activities: List[Any] = Field(default_factory=list, description="Recommended field activities")
    recommended_inputs: List[Any] = Field(default_factory=list, description="Recommended fertilizers/pesticides/inputs")
    is_active: bool = Field(default=True, description="Whether stage is enabled in visualizations")

    @field_validator("stage_name")
    @classmethod
    def clean_stage_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Stage name cannot be empty")
        return cleaned

    @field_validator("stage_name_local", "description", "image_url", "thumbnail_url")
    @classmethod
    def clean_optional_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            return cleaned if cleaned else None
        return None


class CropStageCreate(CropStageBase):
    """Payload for creating a new cultivation process stage."""
    stage_order: Optional[int] = Field(default=None, ge=1, description="Explicit stage order sequence (auto-assigned if omitted)")


class CropStageUpdate(BaseModel):
    """Payload for partially updating a cultivation process stage."""
    stage_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    stage_name_local: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None)
    duration_days: Optional[int] = Field(default=None, ge=1, le=365)
    image_url: Optional[str] = Field(default=None, max_length=500)
    thumbnail_url: Optional[str] = Field(default=None, max_length=500)
    visual_asset_type: Optional[str] = Field(default=None, max_length=50)
    visual_theme_color: Optional[str] = Field(default=None, max_length=20)
    recommended_activities: Optional[List[Any]] = None
    recommended_inputs: Optional[List[Any]] = None
    is_active: Optional[bool] = None

    @field_validator("stage_name")
    @classmethod
    def clean_stage_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Stage name cannot be empty")
            return cleaned
        return None


class StageOrderItem(BaseModel):
    """Individual stage order mapping."""
    stage_id: uuid.UUID = Field(..., description="ID of the stage")
    stage_order: int = Field(..., ge=1, description="New 1-indexed order")


class CropStageReorderRequest(BaseModel):
    """Payload for reordering stages of a crop."""
    stages: List[StageOrderItem] = Field(..., min_length=1, description="Ordered list of stages")


class CropStageResponse(BaseModel):
    """Safe response payload representing a cultivation stage."""
    id: uuid.UUID
    crop_id: uuid.UUID
    stage_order: int
    stage_name: str
    stage_name_local: Optional[str] = None
    description: Optional[str] = None
    duration_days: int
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    visual_asset_type: str
    visual_theme_color: str
    recommended_activities: List[Any]
    recommended_inputs: List[Any]
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CropStageListResponse(BaseModel):
    """List response for cultivation process stages."""
    items: List[CropStageResponse]
    total: int
    total_duration_days: int


class CropStageImageUploadResponse(BaseModel):
    """Response payload after successful photo upload."""
    stage_id: uuid.UUID
    image_url: str
    message: str
