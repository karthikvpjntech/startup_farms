from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.crop import CropListResponse
from app.services.crop_service import CropService

router = APIRouter(prefix="/crops", tags=["Crops (Farmer Catalog)"])


@router.get(
    "",
    response_model=CropListResponse,
    summary="List Active Crops (Farmer)",
    description="Retrieves a paginated list of active, non-deleted crops available for crop planning. Protected by FARMER role."
)
def list_farmer_crops(
    page: int = Query(default=1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (1-100)"),
    search: Optional[str] = Query(default=None, description="Search term for crop name, code, or scientific name"),
    category: Optional[str] = Query(default=None, description="Filter by crop category"),
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Returns active, non-deleted crops for farmers to select in crop planning.
    """
    return CropService.list_farmer_crops(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        category=category
    )
