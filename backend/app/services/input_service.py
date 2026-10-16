import logging
import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.input_master_repository import InputMasterRepository
from app.schemas.input_master import (
    InputMasterCreate,
    InputMasterUpdate,
    InputMasterStatusUpdate,
    InputMasterResponse,
    InputListResponse,
)

logger = logging.getLogger("agri_smart.input_service")


class InputService:
    """Service handling Agricultural Input Master catalog operations."""

    @staticmethod
    def create_input(
        db: Session,
        request: InputMasterCreate,
        current_admin: User
    ) -> InputMasterResponse:
        """Creates a new Input Master record with auto-generated code and duplicate check."""
        existing = InputMasterRepository.get_active_by_name(db, request.input_name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An active input item with this name already exists"
            )

        input_code = request.input_code or InputMasterRepository.generate_next_input_code(db)
        if request.input_code:
            code_match = InputMasterRepository.get_by_code(db, request.input_code)
            if code_match:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Input code '{request.input_code}' already exists"
                )

        input_item = InputMasterRepository.create(
            db=db,
            input_code=input_code,
            input_data=request.model_dump(),
            created_by=current_admin.id
        )
        logger.info("Input created: code=%s name='%s' id=%s", input_item.input_code, input_item.input_name, input_item.id)
        return InputMasterResponse.model_validate(input_item)

    @staticmethod
    def list_inputs(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_deleted: Optional[bool] = None
    ) -> InputListResponse:
        """Retrieves paginated input catalog items."""
        skip = (page - 1) * page_size
        items = InputMasterRepository.list_inputs(
            db=db,
            skip=skip,
            limit=page_size,
            search=search,
            category=category,
            is_active=is_active,
            include_deleted=(is_deleted is True or is_deleted is None)
        )
        total = InputMasterRepository.count_inputs(
            db=db,
            search=search,
            category=category,
            is_active=is_active,
            include_deleted=(is_deleted is True or is_deleted is None)
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return InputListResponse(
            items=[InputMasterResponse.model_validate(i) for i in items],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages
        )

    @staticmethod
    def get_input_detail(
        db: Session,
        input_id: uuid.UUID
    ) -> InputMasterResponse:
        """Retrieves details of an input catalog item by ID."""
        input_item = InputMasterRepository.get_by_id(db, input_id=input_id, include_deleted=True)
        if not input_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agricultural input item not found"
            )
        return InputMasterResponse.model_validate(input_item)

    @staticmethod
    def update_input(
        db: Session,
        input_id: uuid.UUID,
        request: InputMasterUpdate,
        current_admin: User
    ) -> InputMasterResponse:
        """Updates mutable fields of an input item."""
        input_item = InputMasterRepository.get_by_id(db, input_id=input_id, include_deleted=False)
        if not input_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agricultural input item not found"
            )

        update_dict = request.model_dump(exclude_unset=True)
        new_name = update_dict.get("input_name")
        if new_name and new_name.strip().lower() != input_item.input_name.strip().lower():
            existing = InputMasterRepository.get_active_by_name(db, new_name, exclude_id=input_item.id)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Another active input item with this name already exists"
                )

        updated_item = InputMasterRepository.update(
            db=db,
            input_item=input_item,
            update_data=update_dict,
            updated_by=current_admin.id
        )
        logger.info("Input %s updated by admin %s", input_id, current_admin.id)
        return InputMasterResponse.model_validate(updated_item)

    @staticmethod
    def update_input_status(
        db: Session,
        input_id: uuid.UUID,
        request: InputMasterStatusUpdate,
        current_admin: User
    ) -> InputMasterResponse:
        """Toggles the active/inactive status of an input item."""
        input_item = InputMasterRepository.get_by_id(db, input_id=input_id, include_deleted=True)
        if not input_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agricultural input item not found"
            )
        if input_item.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update status of a deleted input item. Restore it first."
            )

        input_item.is_active = request.is_active
        input_item.updated_by = current_admin.id
        db.commit()
        db.refresh(input_item)
        logger.info("Input %s status changed to is_active=%s by admin %s", input_id, request.is_active, current_admin.id)
        return InputMasterResponse.model_validate(input_item)

    @staticmethod
    def delete_input(
        db: Session,
        input_id: uuid.UUID,
        current_admin: User
    ) -> InputMasterResponse:
        """Soft-deletes an input item."""
        input_item = InputMasterRepository.get_by_id(db, input_id=input_id, include_deleted=False)
        if not input_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agricultural input item not found"
            )

        deleted_item = InputMasterRepository.soft_delete(
            db=db,
            input_item=input_item,
            deleted_by=current_admin.id
        )
        logger.info("Input %s soft-deleted by admin %s", input_id, current_admin.id)
        return InputMasterResponse.model_validate(deleted_item)
