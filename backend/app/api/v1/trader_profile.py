from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.trader_profile import (
    TraderProfileCreate,
    TraderProfileUpdate,
    TraderProfileResponse,
)
from app.services.trader_profile_service import TraderProfileService

router = APIRouter(prefix="/traders/profile", tags=["Trader Profile"])


@router.get(
    "",
    response_model=TraderProfileResponse,
    summary="Get Trader Profile",
    description="Retrieves the profile of the currently authenticated Trader. Protected by TRADER role."
)
def get_trader_profile(
    current_user: User = Depends(require_roles(RoleEnum.TRADER)),
    db: Session = Depends(get_db)
):
    return TraderProfileService.get_profile(db=db, current_user=current_user)


@router.post(
    "",
    response_model=TraderProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Trader Profile",
    description="Creates the profile for the currently authenticated Trader. Protected by TRADER role."
)
def create_trader_profile(
    request: TraderProfileCreate,
    current_user: User = Depends(require_roles(RoleEnum.TRADER)),
    db: Session = Depends(get_db)
):
    return TraderProfileService.create_profile(db=db, current_user=current_user, request=request)


@router.patch(
    "",
    response_model=TraderProfileResponse,
    summary="Update Trader Profile",
    description="Partially updates the profile of the currently authenticated Trader. Protected by TRADER role."
)
def update_trader_profile(
    request: TraderProfileUpdate,
    current_user: User = Depends(require_roles(RoleEnum.TRADER)),
    db: Session = Depends(get_db)
):
    return TraderProfileService.update_profile(db=db, current_user=current_user, request=request)
