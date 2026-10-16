from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.farmer_profile import (
    FarmerProfileCreate,
    FarmerProfileUpdate,
    FarmerProfileResponse,
)
from app.services.farmer_profile_service import FarmerProfileService

router = APIRouter(prefix="/farmers/profile", tags=["Farmer Profile"])


@router.get(
    "",
    response_model=FarmerProfileResponse,
    summary="Get Farmer Profile",
    description="Retrieves the profile of the currently authenticated Farmer. Protected by FARMER role."
)
def get_farmer_profile(
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return FarmerProfileService.get_profile(db=db, current_user=current_user)


@router.post(
    "",
    response_model=FarmerProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Farmer Profile",
    description="Creates the profile for the currently authenticated Farmer. Protected by FARMER role."
)
def create_farmer_profile(
    request: FarmerProfileCreate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return FarmerProfileService.create_profile(db=db, current_user=current_user, request=request)


@router.patch(
    "",
    response_model=FarmerProfileResponse,
    summary="Update Farmer Profile",
    description="Partially updates the profile of the currently authenticated Farmer. Protected by FARMER role."
)
def update_farmer_profile(
    request: FarmerProfileUpdate,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return FarmerProfileService.update_profile(db=db, current_user=current_user, request=request)
