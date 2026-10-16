import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class RoleCreate(RoleBase):
    pass


class RoleResponse(RoleBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
