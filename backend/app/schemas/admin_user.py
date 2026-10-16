import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.enums import RoleEnum
from app.core.phone_utils import validate_and_format_phone


class AdminUserCreateRequest(BaseModel):
    """Schema for Super Admin user creation."""
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name of user")
    mobile_number: str = Field(..., min_length=3, max_length=20, description="Unique mobile number")
    email: Optional[str] = Field(default=None, max_length=255, description="Unique email address")
    password: str = Field(..., min_length=8, max_length=128, description="Initial user password")
    roles: List[str] = Field(..., min_length=1, description="List of system roles to assign")

    @field_validator("full_name")
    @classmethod
    def strip_and_validate_full_name(cls, v: str) -> str:
        v_clean = v.strip()
        if not v_clean:
            raise ValueError("Full name cannot be empty or whitespace only")
        return v_clean

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        res = validate_and_format_phone(v)
        if not res:
            raise ValueError("Mobile number is required.")
        return res

    @field_validator("email")
    @classmethod
    def clean_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_clean = v.strip()
            return v_clean if v_clean else None
        return None

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("At least one role must be provided")
        valid_role_names = {r.value for r in RoleEnum}
        cleaned_roles = []
        for r in v:
            r_str = str(r).strip().upper()
            if r_str not in valid_role_names:
                raise ValueError(f"Invalid role: '{r}'. Allowed roles are: {sorted(list(valid_role_names))}")
            if r_str not in cleaned_roles:
                cleaned_roles.append(r_str)
        return cleaned_roles


class AdminUserUpdateRequest(BaseModel):
    """Schema for Super Admin user profile update."""
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    mobile_number: Optional[str] = Field(default=None, min_length=3, max_length=20)
    email: Optional[str] = Field(default=None, max_length=255)

    @field_validator("full_name")
    @classmethod
    def strip_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_clean = v.strip()
            if not v_clean:
                raise ValueError("Full name cannot be empty or whitespace only")
            return v_clean
        return None

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_and_format_phone(v)
        return None

    @field_validator("email")
    @classmethod
    def clean_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_clean = v.strip()
            return v_clean if v_clean else None
        return None


class AdminUserStatusRequest(BaseModel):
    """Schema for Super Admin user status change (activate/deactivate)."""
    is_active: bool = Field(..., description="Target active status")


class AdminRoleAssignRequest(BaseModel):
    """Schema for Super Admin role assignment."""
    roles: List[str] = Field(..., min_length=1, description="List of system roles to assign")

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("At least one role must be provided")
        valid_role_names = {r.value for r in RoleEnum}
        cleaned_roles = []
        for r in v:
            r_str = str(r).strip().upper()
            if r_str not in valid_role_names:
                raise ValueError(f"Invalid role: '{r}'. Allowed roles are: {sorted(list(valid_role_names))}")
            if r_str not in cleaned_roles:
                cleaned_roles.append(r_str)
        return cleaned_roles


class AdminUserResponse(BaseModel):
    """Safe response schema for user detail representation."""
    id: uuid.UUID
    full_name: str
    mobile_number: str
    email: Optional[str] = None
    is_active: bool
    is_deleted: bool
    roles: List[str]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True)


class AdminUserListResponse(BaseModel):
    """Paginated user listing response schema."""
    items: List[AdminUserResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class AdminUserRolesResponse(BaseModel):
    """Response schema for role assignment/removal."""
    user_id: uuid.UUID
    roles: List[str]
