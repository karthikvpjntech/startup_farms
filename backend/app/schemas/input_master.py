import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.enums import InputCategory, InputUnit


class InputMasterBase(BaseModel):
    """Base schema defining common agricultural input master fields."""
    input_name: str = Field(..., min_length=1, max_length=150, description="Display name of the input item")
    category: InputCategory = Field(..., description="Agricultural input category (SEED, FERTILIZER, PESTICIDE, etc.)")
    unit: InputUnit = Field(..., description="Standard measurement unit (KG, LITRE, BAG, etc.)")
    technical_name: Optional[str] = Field(default=None, max_length=200, description="Active chemical / biological ingredient")
    brand_name: Optional[str] = Field(default=None, max_length=100, description="Commercial manufacturer brand name")
    description: Optional[str] = Field(default=None, description="Detailed product description / dosage instructions")

    @field_validator("input_name")
    @classmethod
    def clean_input_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Input name cannot be empty or whitespace only")
        return cleaned


class InputMasterCreate(InputMasterBase):
    """Payload for creating a new agricultural input item."""
    input_code: Optional[str] = Field(default=None, max_length=50, description="Optional custom code; generated if omitted")


class InputMasterUpdate(BaseModel):
    """Payload for partially updating an input item."""
    input_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    category: Optional[InputCategory] = None
    unit: Optional[InputUnit] = None
    technical_name: Optional[str] = Field(default=None, max_length=200)
    brand_name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None


class InputMasterStatusUpdate(BaseModel):
    """Payload for updating active status of an input item."""
    is_active: bool = Field(..., description="Active status flag")


class InputMasterResponse(BaseModel):
    """Public response payload for an agricultural input item."""
    id: uuid.UUID
    input_code: str
    input_name: str
    category: str
    unit: str
    technical_name: Optional[str] = None
    brand_name: Optional[str] = None
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


class InputListResponse(BaseModel):
    """Paginated list response schema for agricultural inputs."""
    items: List[InputMasterResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
