import uuid
import logging
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.trash_bin_repository import TrashBinRepository
from app.schemas.trash_bin import (
    TrashEntityType,
    TrashBinListResponse,
    TrashActionResponse,
)

logger = logging.getLogger("agri_smart.trash_bin_service")


class TrashBinService:
    """Business service governing the Super Admin Trash-Bin Audit Vault."""

    @staticmethod
    def list_trash(
        db: Session,
        current_user: User,
        entity_type: Optional[TrashEntityType] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> TrashBinListResponse:
        """Lists soft-deleted entities across the entire system."""
        items, total = TrashBinRepository.list_trash_items(
            db=db,
            entity_type=entity_type,
            search=search,
            page=page,
            page_size=page_size,
        )
        stats = TrashBinRepository.get_stats(db)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return TrashBinListResponse(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            stats=stats,
        )

    @staticmethod
    def restore_entity(
        db: Session,
        current_user: User,
        entity_type: TrashEntityType,
        entity_id: uuid.UUID,
    ) -> TrashActionResponse:
        """Restores a soft-deleted entity."""
        success = TrashBinRepository.restore_entity(db=db, entity_type=entity_type, entity_id=entity_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Soft-deleted {entity_type.value} with ID {entity_id} not found",
            )

        logger.info(
            f"Super Admin {current_user.id} restored {entity_type.value} entity {entity_id}"
        )

        return TrashActionResponse(
            success=True,
            message=f"{entity_type.value} successfully restored from Trash Vault",
            entity_type=entity_type,
            entity_id=entity_id,
        )

    @staticmethod
    def hard_delete_entity(
        db: Session,
        current_user: User,
        entity_type: TrashEntityType,
        entity_id: uuid.UUID,
    ) -> TrashActionResponse:
        """Guarded permanent physical hard deletion."""
        if entity_type == TrashEntityType.USER and entity_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Super Admin cannot execute hard-deletion on their own active user account",
            )

        try:
            success = TrashBinRepository.hard_delete_entity(db=db, entity_type=entity_type, entity_id=entity_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{entity_type.value} with ID {entity_id} not found for hard deletion",
                )

            logger.warning(
                f"PERMANENT HARD DELETION: Super Admin {current_user.id} purged {entity_type.value} entity {entity_id}"
            )

            return TrashActionResponse(
                success=True,
                message=f"{entity_type.value} permanently purged from database ledger",
                entity_type=entity_type,
                entity_id=entity_id,
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during hard deletion of {entity_type.value} {entity_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot permanently delete entity due to dependent database records: {str(e)}",
            )
