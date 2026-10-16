import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.supplier import (
    SupplierCreate,
    SupplierResponse,
    SupplierListResponse,
)
from app.services.supplier_service import SupplierService

router = APIRouter(prefix="/suppliers", tags=["Suppliers (Public / Farmer Catalog)"])


@router.get(
    "",
    response_model=SupplierListResponse,
    summary="List Active Suppliers",
    description="Retrieves active, non-deleted suppliers for vendor dropdowns and sourcing selection."
)
def list_public_suppliers(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(default=None, description="Search term for supplier name, code, district, city"),
    supplier_type: Optional[str] = Query(default=None, description="Filter by supplier business type"),
    db: Session = Depends(get_db)
):
    """
    Returns active suppliers for dropdown selection in procurement requests.
    """
    return SupplierService.list_public_suppliers(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        supplier_type=supplier_type
    )


@router.post(
    "",
    response_model=SupplierResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Supplier Record (Farmer / Public)",
    description="Creates a new agricultural supplier record."
)
def create_supplier_public(
    request: SupplierCreate,
    current_user: User = Depends(require_roles(RoleEnum.SUPER_ADMIN, RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return SupplierService.create_supplier(db=db, request=request, current_admin=current_user)


@router.get(
    "/{supplier_id}",
    response_model=SupplierResponse,
    summary="Get Supplier Details",
    description="Retrieves details of a supplier record by ID."
)
def get_supplier_public(
    supplier_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return SupplierService.get_supplier_detail(db=db, supplier_id=supplier_id)
