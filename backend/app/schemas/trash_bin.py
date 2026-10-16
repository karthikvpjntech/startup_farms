import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from enum import Enum


class TrashEntityType(str, Enum):
    """Supported entity classifications inside the Super Admin Trash Vault."""
    USER = "USER"
    CROP = "CROP"
    FARM = "FARM"
    FARM_CROP_PLAN = "FARM_CROP_PLAN"
    CULTIVATION = "CULTIVATION"
    STAGE_EXPENSE = "STAGE_EXPENSE"


class TrashBinItemResponse(BaseModel):
    """Representation of an audited soft-deleted entity."""
    id: uuid.UUID
    entity_type: TrashEntityType
    entity_name: str = Field(..., description="Human-readable title or label of the entity")
    entity_code: Optional[str] = Field(default=None, description="System code or reference identifier if any")
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[uuid.UUID] = None
    deleted_by_name: Optional[str] = None
    created_at: Optional[datetime] = None
    details: Dict[str, Any] = Field(default_factory=dict, description="Contextual entity metadata")

    model_config = ConfigDict(from_attributes=True)


class TrashBinListResponse(BaseModel):
    """Paginated collection of soft-deleted items across the ecosystem."""
    items: List[TrashBinItemResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
    stats: Dict[str, int] = Field(default_factory=dict, description="Total soft-deleted count per entity type")


class TrashActionResponse(BaseModel):
    """Result of a restore or physical hard purge operation."""
    success: bool
    message: str
    entity_type: TrashEntityType
    entity_id: uuid.UUID
