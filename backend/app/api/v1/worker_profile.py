from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.worker_profile import (
    WorkerProfileCreate,
    WorkerProfileUpdate,
    WorkerProfileResponse,
)
from app.services.worker_profile_service import WorkerProfileService

router = APIRouter(prefix="/workers/profile", tags=["Worker Profile"])


@router.get(
    "",
    response_model=WorkerProfileResponse,
    summary="Get Worker Profile",
    description="Retrieves the profile of the currently authenticated Worker. Protected by WORKER role."
)
def get_worker_profile(
    current_user: User = Depends(require_roles(RoleEnum.WORKER)),
    db: Session = Depends(get_db)
):
    return WorkerProfileService.get_profile(db=db, current_user=current_user)


@router.post(
    "",
    response_model=WorkerProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Worker Profile",
    description="Creates the profile for the currently authenticated Worker. Protected by WORKER role."
)
def create_worker_profile(
    request: WorkerProfileCreate,
    current_user: User = Depends(require_roles(RoleEnum.WORKER)),
    db: Session = Depends(get_db)
):
    return WorkerProfileService.create_profile(db=db, current_user=current_user, request=request)


@router.patch(
    "",
    response_model=WorkerProfileResponse,
    summary="Update Worker Profile",
    description="Partially updates the profile of the currently authenticated Worker. Protected by WORKER role."
)
def update_worker_profile(
    request: WorkerProfileUpdate,
    current_user: User = Depends(require_roles(RoleEnum.WORKER)),
    db: Session = Depends(get_db)
):
    return WorkerProfileService.update_profile(db=db, current_user=current_user, request=request)
