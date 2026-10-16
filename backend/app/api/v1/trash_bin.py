import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.trash_bin import (
    TrashEntityType,
    TrashBinListResponse,
    TrashActionResponse,
)
from app.services.trash_bin_service import TrashBinService

router = APIRouter(prefix="/admin/trash-bin", tags=["Admin (Trash Bin Vault)"])


@router.get(
    "",
    response_model=TrashBinListResponse,
    summary="List Soft-Deleted Entities",
    description="Super Admin platform audit vault displaying all soft-deleted entities with filtering and stats.",
)
def list_trash_bin(
    entity_type: Optional[TrashEntityType] = Query(default=None, description="Filter by entity type"),
    search: Optional[str] = Query(default=None, description="Search term for name or identifier"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    return TrashBinService.list_trash(
        db=db,
        current_user=current_user,
        entity_type=entity_type,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/{entity_type}/{entity_id}/restore",
    response_model=TrashActionResponse,
    summary="Restore Soft-Deleted Entity",
    description="One-click restoration of any soft-deleted entity from the Trash Vault. Protected by SUPER_ADMIN.",
)
def restore_entity(
    entity_type: TrashEntityType = Path(..., description="Entity classification type"),
    entity_id: uuid.UUID = Path(..., description="Entity unique UUID"),
    current_user: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    return TrashBinService.restore_entity(
        db=db,
        current_user=current_user,
        entity_type=entity_type,
        entity_id=entity_id,
    )


@router.delete(
    "/{entity_type}/{entity_id}/hard-delete",
    response_model=TrashActionResponse,
    summary="Guarded Physical Hard-Deletion",
    description="Permanently purges an entity from the database ledger. Protected by SUPER_ADMIN with strict safety checks.",
)
def hard_delete_entity(
    entity_type: TrashEntityType = Path(..., description="Entity classification type"),
    entity_id: uuid.UUID = Path(..., description="Entity unique UUID"),
    current_user: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    return TrashBinService.hard_delete_entity(
        db=db,
        current_user=current_user,
        entity_type=entity_type,
        entity_id=entity_id,
    )
