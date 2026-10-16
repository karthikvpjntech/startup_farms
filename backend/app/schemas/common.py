from typing import Generic, TypeVar, Optional, Any, List
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standardized API success response wrapper."""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None


class APIErrorResponse(BaseModel):
    """Standardized API error response wrapper."""
    success: bool = False
    message: str = "Something went wrong"
    errors: List[Any] = []


class HealthData(BaseModel):
    """Health check payload schema."""
    status: str = "UP"


class CursorPaginationParams(BaseModel):
    """Keyset / Cursor pagination request query params."""
    cursor: Optional[str] = None
    limit: int = 20
    direction: str = "next"  # "next" or "prev"


class CursorPaginatedResponse(BaseModel, Generic[T]):
    """Keyset / Cursor paginated response wrapper."""
    items: List[T]
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None
    has_more: bool = False
    limit: int = 20


class NumberedPaginatedResponse(BaseModel, Generic[T]):
    """Standardized numbered page response wrapper."""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool = False
    has_prev: bool = False

