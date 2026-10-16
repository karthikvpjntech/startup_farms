from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.driver_profile import (
    DriverProfileCreate,
    DriverProfileUpdate,
    DriverProfileResponse,
)
from app.services.driver_profile_service import DriverProfileService

router = APIRouter(prefix="/drivers/profile", tags=["Driver Profile"])


@router.get(
    "",
    response_model=DriverProfileResponse,
    summary="Get Driver Profile",
    description="Retrieves the profile of the currently authenticated Driver. Protected by DRIVER role."
)
def get_driver_profile(
    current_user: User = Depends(require_roles(RoleEnum.DRIVER)),
    db: Session = Depends(get_db)
):
    return DriverProfileService.get_profile(db=db, current_user=current_user)


@router.post(
    "",
    response_model=DriverProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Driver Profile",
    description="Creates the profile for the currently authenticated Driver. Protected by DRIVER role."
)
def create_driver_profile(
    request: DriverProfileCreate,
    current_user: User = Depends(require_roles(RoleEnum.DRIVER)),
    db: Session = Depends(get_db)
):
    return DriverProfileService.create_profile(db=db, current_user=current_user, request=request)


@router.patch(
    "",
    response_model=DriverProfileResponse,
    summary="Update Driver Profile",
    description="Partially updates the profile of the currently authenticated Driver. Protected by DRIVER role."
)
def update_driver_profile(
    request: DriverProfileUpdate,
    current_user: User = Depends(require_roles(RoleEnum.DRIVER)),
    db: Session = Depends(get_db)
):
    return DriverProfileService.update_profile(db=db, current_user=current_user, request=request)
