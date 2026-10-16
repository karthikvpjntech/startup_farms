import logging
import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.supplier import (
    SupplierCreate,
    SupplierUpdate,
    SupplierStatusUpdate,
    SupplierResponse,
    SupplierListResponse,
)

logger = logging.getLogger("agri_smart.supplier_service")


class SupplierService:
    """Service handling Supplier Master administration and public catalog access."""

    @staticmethod
    def create_supplier(
        db: Session,
        request: SupplierCreate,
        current_admin: User
    ) -> SupplierResponse:
        """Creates a new Supplier record with auto-generated code and duplicate check."""
        existing = SupplierRepository.get_active_by_name_or_phone(
            db=db,
            supplier_name=request.supplier_name,
            phone_number=request.phone_number
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An active supplier with this name or phone number already exists"
            )

        supplier_code = request.supplier_code or SupplierRepository.generate_next_supplier_code(db)
        # Verify custom code uniqueness if provided
        if request.supplier_code:
            code_match = SupplierRepository.get_by_code(db, request.supplier_code)
            if code_match:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Supplier code '{request.supplier_code}' already exists"
                )

        supplier = SupplierRepository.create(
            db=db,
            supplier_code=supplier_code,
            supplier_data=request.model_dump(),
            created_by=current_admin.id
        )
        logger.info("Supplier created: code=%s name='%s' id=%s", supplier.supplier_code, supplier.supplier_name, supplier.id)
        return SupplierResponse.model_validate(supplier)

    @staticmethod
    def list_admin_suppliers(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        supplier_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_deleted: Optional[bool] = None
    ) -> SupplierListResponse:
        """Retrieves paginated supplier records for Super Admin with search and filters."""
        skip = (page - 1) * page_size
        suppliers = SupplierRepository.list_suppliers(
            db=db,
            skip=skip,
            limit=page_size,
            search=search,
            supplier_type=supplier_type,
            is_active=is_active,
            include_deleted=(is_deleted is True or is_deleted is None)
        )
        total = SupplierRepository.count_suppliers(
            db=db,
            search=search,
            supplier_type=supplier_type,
            is_active=is_active,
            include_deleted=(is_deleted is True or is_deleted is None)
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return SupplierListResponse(
            items=[SupplierResponse.model_validate(s) for s in suppliers],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages
        )

    @staticmethod
    def list_public_suppliers(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        supplier_type: Optional[str] = None
    ) -> SupplierListResponse:
        """Retrieves active, non-deleted suppliers for public/farmer selection in dropdowns."""
        skip = (page - 1) * page_size
        suppliers = SupplierRepository.list_suppliers(
            db=db,
            skip=skip,
            limit=page_size,
            search=search,
            supplier_type=supplier_type,
            is_active=True,
            include_deleted=False
        )
        total = SupplierRepository.count_suppliers(
            db=db,
            search=search,
            supplier_type=supplier_type,
            is_active=True,
            include_deleted=False
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return SupplierListResponse(
            items=[SupplierResponse.model_validate(s) for s in suppliers],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages
        )

    @staticmethod
    def get_supplier_detail(
        db: Session,
        supplier_id: uuid.UUID
    ) -> SupplierResponse:
        """Retrieves full details of a supplier record by ID."""
        supplier = SupplierRepository.get_by_id(db, supplier_id=supplier_id, include_deleted=True)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found"
            )
        return SupplierResponse.model_validate(supplier)

    @staticmethod
    def update_supplier(
        db: Session,
        supplier_id: uuid.UUID,
        request: SupplierUpdate,
        current_admin: User
    ) -> SupplierResponse:
        """Updates mutable fields of a supplier record."""
        supplier = SupplierRepository.get_by_id(db, supplier_id=supplier_id, include_deleted=False)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found"
            )

        update_dict = request.model_dump(exclude_unset=True)
        new_name = update_dict.get("supplier_name", supplier.supplier_name)
        new_phone = update_dict.get("phone_number", supplier.phone_number)
        if new_name != supplier.supplier_name or new_phone != supplier.phone_number:
            existing = SupplierRepository.get_active_by_name_or_phone(
                db=db,
                supplier_name=new_name,
                phone_number=new_phone,
                exclude_id=supplier.id
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Another active supplier with this name or phone number already exists"
                )

        updated_supplier = SupplierRepository.update(
            db=db,
            supplier=supplier,
            update_data=update_dict,
            updated_by=current_admin.id
        )
        logger.info("Supplier %s updated by admin %s", supplier_id, current_admin.id)
        return SupplierResponse.model_validate(updated_supplier)

    @staticmethod
    def update_supplier_status(
        db: Session,
        supplier_id: uuid.UUID,
        request: SupplierStatusUpdate,
        current_admin: User
    ) -> SupplierResponse:
        """Toggles the active/inactive status of a supplier."""
        supplier = SupplierRepository.get_by_id(db, supplier_id=supplier_id, include_deleted=True)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found"
            )
        if supplier.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update status of a deleted supplier. Restore the supplier first."
            )

        supplier.is_active = request.is_active
        supplier.updated_by = current_admin.id
        db.commit()
        db.refresh(supplier)
        logger.info("Supplier %s status changed to is_active=%s by admin %s", supplier_id, request.is_active, current_admin.id)
        return SupplierResponse.model_validate(supplier)

    @staticmethod
    def delete_supplier(
        db: Session,
        supplier_id: uuid.UUID,
        current_admin: User
    ) -> SupplierResponse:
        """Soft-deletes a supplier record."""
        supplier = SupplierRepository.get_by_id(db, supplier_id=supplier_id, include_deleted=False)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found"
            )

        deleted_supplier = SupplierRepository.soft_delete(
            db=db,
            supplier=supplier,
            deleted_by=current_admin.id
        )
        logger.info("Supplier %s soft-deleted by admin %s", supplier_id, current_admin.id)
        return SupplierResponse.model_validate(deleted_supplier)

    @staticmethod
    def restore_supplier(
        db: Session,
        supplier_id: uuid.UUID,
        current_admin: User
    ) -> SupplierResponse:
        """Restores a soft-deleted supplier record."""
        supplier = SupplierRepository.get_by_id(db, supplier_id=supplier_id, include_deleted=True)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found"
            )
        if not supplier.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supplier is not deleted"
            )

        existing = SupplierRepository.get_active_by_name_or_phone(
            db=db,
            supplier_name=supplier.supplier_name,
            phone_number=supplier.phone_number,
            exclude_id=supplier.id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Another active supplier with this name or phone already exists"
            )

        restored_supplier = SupplierRepository.restore(
            db=db,
            supplier=supplier,
            restored_by=current_admin.id
        )
        logger.info("Supplier %s restored by admin %s", supplier_id, current_admin.id)
        return SupplierResponse.model_validate(restored_supplier)
