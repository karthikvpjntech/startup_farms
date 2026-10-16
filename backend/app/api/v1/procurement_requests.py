import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.procurement_request import (
    ProcurementRequestCreate,
    ProcurementRequestUpdate,
    ProcurementRequestResponse,
    ProcurementListResponse,
)
from app.services.procurement_service import ProcurementService

router = APIRouter(prefix="/procurement-requests", tags=["Procurement (Farmer Requisitions)"])


@router.post(
    "",
    response_model=ProcurementRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Procurement Request",
    description="Creates a new agricultural input procurement requisition for a farm parcel. Protected by FARMER role."
)
def create_procurement_request(
    request: ProcurementRequestCreate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Submits a procurement request for seeds, fertilizers, or agro-inputs linked to an owned farm parcel.
    """
    return ProcurementService.create_procurement(
        db=db,
        current_user=current_user,
        request=request
    )


@router.get(
    "",
    response_model=ProcurementListResponse,
    summary="List Procurement Requests",
    description="Retrieves a paginated list of procurement requests for the authenticated farmer. Protected by FARMER role."
)
def list_procurement_requests(
    page: int = Query(default=1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (1-100)"),
    status: Optional[str] = Query(default=None, description="Filter by status (PENDING, APPROVED, REJECTED, etc.)"),
    farm_id: Optional[uuid.UUID] = Query(default=None, description="Filter by farm parcel ID"),
    search: Optional[str] = Query(default=None, description="Search term for request code or notes"),
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Returns paginated procurement requests for the calling farmer.
    """
    return ProcurementService.list_farmer_procurements(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        status_filter=status,
        farm_id=farm_id,
        search=search
    )


@router.get(
    "/{request_id}",
    response_model=ProcurementRequestResponse,
    summary="Get Procurement Request Details",
    description="Retrieves full details of an owned procurement request. Protected by FARMER role."
)
def get_procurement_request(
    request_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Returns full details of an owned procurement request.
    """
    return ProcurementService.get_procurement_detail(
        db=db,
        current_user=current_user,
        request_id=request_id
    )


@router.patch(
    "/{request_id}",
    response_model=ProcurementRequestResponse,
    summary="Update Procurement Request",
    description="Partially updates an owned procurement request if in PENDING status. Protected by FARMER role."
)
def update_procurement_request(
    request_id: uuid.UUID,
    request: ProcurementRequestUpdate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Updates mutable fields (quantity, required_date, preferred_supplier_id, notes) of a PENDING request.
    """
    return ProcurementService.update_procurement(
        db=db,
        current_user=current_user,
        request_id=request_id,
        request=request
    )


@router.post(
    "/{request_id}/cancel",
    response_model=ProcurementRequestResponse,
    summary="Cancel Procurement Request",
    description="Cancels an owned procurement request if in PENDING status. Protected by FARMER role."
)
def cancel_procurement_request(
    request_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Cancels a PENDING procurement request.
    """
    return ProcurementService.cancel_procurement(
        db=db,
        current_user=current_user,
        request_id=request_id
    )
