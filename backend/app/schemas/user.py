import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from app.schemas.role import RoleResponse
from app.core.phone_utils import validate_and_format_phone


class UserBase(BaseModel):
    full_name: str
    mobile_number: str
    email: Optional[str] = None
    is_active: bool = True

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        res = validate_and_format_phone(v)
        if not res:
            raise ValueError("Mobile number is required.")
        return res


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: uuid.UUID
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
