import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.input_master import InputListResponse, InputMasterResponse
from app.services.input_service import InputService

router = APIRouter(prefix="/inputs", tags=["Inputs (Agricultural Catalog)"])


@router.get(
    "",
    response_model=InputListResponse,
    summary="List Agricultural Inputs",
    description="Retrieves a paginated list of active agricultural inputs available in the catalog."
)
def list_inputs(
    page: int = Query(default=1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (1-100)"),
    search: Optional[str] = Query(default=None, description="Search term for name, code, active ingredients, brand"),
    category: Optional[str] = Query(default=None, description="Filter by input category (SEED, FERTILIZER, etc.)"),
    is_active: Optional[bool] = Query(default=True, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """
    Returns active inputs from catalog for farmers and agronomic planning.
    """
    return InputService.list_inputs(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        category=category,
        is_active=is_active,
        is_deleted=False
    )


@router.get(
    "/{input_id}",
    response_model=InputMasterResponse,
    summary="Get Agricultural Input Details",
    description="Retrieves full details of a specific agricultural input item by ID."
)
def get_input(
    input_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return InputService.get_input_detail(db=db, input_id=input_id)
