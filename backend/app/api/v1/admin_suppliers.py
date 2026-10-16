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
    SupplierUpdate,
    SupplierStatusUpdate,
    SupplierResponse,
    SupplierListResponse,
)
from app.services.supplier_service import SupplierService

router = APIRouter(prefix="/admin/suppliers", tags=["Admin (Suppliers Master)"])


@router.post(
    "",
    response_model=SupplierResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Supplier Record",
    description="Creates a new agricultural supplier master record. Protected by SUPER_ADMIN and FARMER roles."
)
def create_supplier(
    request: SupplierCreate,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN, RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return SupplierService.create_supplier(db=db, request=request, current_admin=current_admin)


@router.get(
    "",
    response_model=SupplierListResponse,
    summary="List Supplier Master Records (Admin)",
    description="Retrieves a paginated list of suppliers with search and filters. Protected by SUPER_ADMIN and FARMER roles."
)
def list_admin_suppliers(
    page: int = Query(default=1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (1-100)"),
    search: Optional[str] = Query(default=None, description="Search by name, code, phone, district"),
    supplier_type: Optional[str] = Query(default=None, description="Filter by supplier classification"),
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
    is_deleted: Optional[bool] = Query(default=None, description="Filter by deleted status"),
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN, RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return SupplierService.list_admin_suppliers(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        supplier_type=supplier_type,
        is_active=is_active,
        is_deleted=is_deleted
    )


@router.get(
    "/{supplier_id}",
    response_model=SupplierResponse,
    summary="Get Supplier Details",
    description="Retrieves full details of a supplier master record by ID. Protected by SUPER_ADMIN and FARMER roles."
)
def get_supplier(
    supplier_id: uuid.UUID,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN, RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return SupplierService.get_supplier_detail(db=db, supplier_id=supplier_id)


@router.patch(
    "/{supplier_id}",
    response_model=SupplierResponse,
    summary="Update Supplier Record",
    description="Partially updates a supplier master record. Protected by SUPER_ADMIN and FARMER roles."
)
def update_supplier(
    supplier_id: uuid.UUID,
    request: SupplierUpdate,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN, RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return SupplierService.update_supplier(db=db, supplier_id=supplier_id, request=request, current_admin=current_admin)


@router.patch(
    "/{supplier_id}/status",
    response_model=SupplierResponse,
    summary="Update Supplier Status",
    description="Toggles the active status of a supplier master record. Protected by SUPER_ADMIN and FARMER roles."
)
def update_supplier_status(
    supplier_id: uuid.UUID,
    request: SupplierStatusUpdate,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN, RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return SupplierService.update_supplier_status(db=db, supplier_id=supplier_id, request=request, current_admin=current_admin)


@router.delete(
    "/{supplier_id}",
    response_model=SupplierResponse,
    summary="Soft Delete Supplier Record",
    description="Soft-deletes a supplier master record. Protected by SUPER_ADMIN and FARMER roles."
)
def delete_supplier(
    supplier_id: uuid.UUID,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN, RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return SupplierService.delete_supplier(db=db, supplier_id=supplier_id, current_admin=current_admin)


@router.post(
    "/{supplier_id}/restore",
    response_model=SupplierResponse,
    summary="Restore Soft-Deleted Supplier Record",
    description="Restores a previously soft-deleted supplier master record. Protected by SUPER_ADMIN and FARMER roles."
)
def restore_supplier(
    supplier_id: uuid.UUID,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN, RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return SupplierService.restore_supplier(db=db, supplier_id=supplier_id, current_admin=current_admin)
