import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user, security
from app.dependencies.authorization import require_roles
from app.core.jwt import decode_access_token
from app.models.enums import RoleEnum
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.subscription import (
    SubscriptionSettingResponse,
    SubscriptionSettingUpdateRequest,
    UserSubscriptionResponse,
    SubscriptionStatusResponse,
    CreateSubscriptionOrderRequest,
    CreateSubscriptionOrderResponse,
    VerifySubscriptionPaymentRequest,
    AdminGrantSubscriptionRequest,
    AdminToggleSubscriberRequest,
)
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions & Historical Data Gate"])


def get_optional_current_user(
    credentials=Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    if not credentials or not credentials.credentials:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        if payload.get("type") != "access":
            return None
        user_id_str = payload.get("sub")
        if not user_id_str:
            return None
        user_uuid = uuid.UUID(user_id_str)
        user = UserRepository.get_by_id(db, user_uuid)
        if user and not user.is_deleted and user.is_active:
            return user
    except Exception:
        pass
    return None


@router.get(
    "/settings",
    response_model=SubscriptionSettingResponse,
    summary="Get Subscription Settings & Pricing"
)
def get_subscription_settings(db: Session = Depends(get_db)):
    setting = SubscriptionService.get_or_create_settings(db)
    return SubscriptionSettingResponse.model_validate(setting)


@router.get(
    "/my-status",
    response_model=SubscriptionStatusResponse,
    summary="Get Current User Subscription & Historical Data Access Status"
)
def get_my_subscription_status(
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    return SubscriptionService.get_user_subscription_status(db=db, user=current_user)


@router.post(
    "/create-order",
    response_model=CreateSubscriptionOrderResponse,
    summary="Create Razorpay / Instant Payment Order for Historical Data Pass"
)
def create_subscription_order(
    req: CreateSubscriptionOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return SubscriptionService.create_subscription_order(
        db=db, user=current_user, plan_type=req.plan_type
    )


@router.post(
    "/verify-payment",
    response_model=UserSubscriptionResponse,
    summary="Verify Payment and Activate User Subscription"
)
def verify_and_activate_subscription(
    req: VerifySubscriptionPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return SubscriptionService.verify_and_activate_subscription(
        db=db, user=current_user, req=req
    )


# ------------------------------------------------------------------------------
# Super Admin Endpoints
# ------------------------------------------------------------------------------

@router.get(
    "/admin/settings",
    response_model=SubscriptionSettingResponse,
    summary="Admin: Get Global Subscription Configuration"
)
def admin_get_settings(
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    setting = SubscriptionService.get_or_create_settings(db)
    return SubscriptionSettingResponse.model_validate(setting)


@router.put(
    "/admin/settings",
    response_model=SubscriptionSettingResponse,
    summary="Admin: Update Master Toggle (Activate/Deactivate) & Pricing"
)
def admin_update_settings(
    update_data: SubscriptionSettingUpdateRequest,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return SubscriptionService.update_settings(db=db, update_data=update_data)


@router.get(
    "/admin/subscribers",
    response_model=List[UserSubscriptionResponse],
    summary="Admin: List All Active & Past Subscribers"
)
def admin_list_subscribers(
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return SubscriptionService.admin_list_subscribers(db=db)


@router.post(
    "/admin/toggle/{subscription_id}",
    response_model=UserSubscriptionResponse,
    summary="Admin: Toggle Single Subscriber Status (Active / Deactivate)"
)
def admin_toggle_subscriber(
    subscription_id: uuid.UUID,
    req: AdminToggleSubscriberRequest,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return SubscriptionService.admin_toggle_subscriber_status(
        db=db, subscription_id=subscription_id, is_active=req.is_active
    )


@router.post(
    "/admin/grant",
    response_model=UserSubscriptionResponse,
    summary="Admin: Manually Grant Free VIP Subscription to User"
)
def admin_grant_subscription(
    req: AdminGrantSubscriptionRequest,
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return SubscriptionService.admin_grant_subscription(db=db, req=req)
