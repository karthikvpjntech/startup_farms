import uuid
import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.subscription import SubscriptionSetting, UserSubscription
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionSettingResponse,
    SubscriptionSettingUpdateRequest,
    UserSubscriptionResponse,
    SubscriptionStatusResponse,
    CreateSubscriptionOrderResponse,
    VerifySubscriptionPaymentRequest,
    AdminGrantSubscriptionRequest,
)
from app.services.razorpay_service import RazorpayService

logger = logging.getLogger("agri_smart.subscription_service")


class SubscriptionService:
    @staticmethod
    def get_or_create_settings(db: Session) -> SubscriptionSetting:
        stmt = select(SubscriptionSetting).order_by(SubscriptionSetting.id.asc()).limit(1)
        setting = db.execute(stmt).scalar_one_or_none()
        if not setting:
            setting = SubscriptionSetting(
                id=1,
                is_enabled=True,
                free_retention_days=30,
                monthly_price=Decimal("199.00"),
                annual_price=Decimal("999.00"),
                currency="INR",
                title="Agri-Smart Farm Archive & Historical Data Pass",
                description="Unlock unlimited historical farm records, past harvest cycles, multi-year expense analytics, worker logs, and PDF/Excel exports."
            )
            db.add(setting)
            db.commit()
            db.refresh(setting)
        return setting

    @classmethod
    def update_settings(
        cls, db: Session, update_data: SubscriptionSettingUpdateRequest
    ) -> SubscriptionSettingResponse:
        setting = cls.get_or_create_settings(db)

        if update_data.is_enabled is not None:
            setting.is_enabled = update_data.is_enabled
        if update_data.free_retention_days is not None:
            setting.free_retention_days = update_data.free_retention_days
        if update_data.monthly_price is not None:
            setting.monthly_price = update_data.monthly_price
        if update_data.annual_price is not None:
            setting.annual_price = update_data.annual_price
        if update_data.currency is not None:
            setting.currency = update_data.currency
        if update_data.title is not None:
            setting.title = update_data.title
        if update_data.description is not None:
            setting.description = update_data.description

        setting.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(setting)
        return SubscriptionSettingResponse.model_validate(setting)

    @classmethod
    def get_active_subscription_for_user(
        cls, db: Session, user_id: uuid.UUID
    ) -> Optional[UserSubscription]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(UserSubscription)
            .where(
                UserSubscription.user_id == user_id,
                UserSubscription.status == "ACTIVE",
                UserSubscription.end_date >= now
            )
            .order_by(desc(UserSubscription.end_date))
            .limit(1)
        )
        return db.execute(stmt).scalar_one_or_none()

    @classmethod
    def get_user_subscription_status(
        cls, db: Session, user: Optional[User]
    ) -> SubscriptionStatusResponse:
        setting = cls.get_or_create_settings(db)

        # If master switch is deactivated, all users have unlocked historical access
        if not setting.is_enabled:
            return SubscriptionStatusResponse(
                is_subscription_required=False,
                has_active_subscription=False,
                is_unlocked=True,
                free_retention_days=setting.free_retention_days,
                monthly_price=setting.monthly_price,
                annual_price=setting.annual_price,
                currency=setting.currency,
                active_subscription=None
            )

        if not user:
            return SubscriptionStatusResponse(
                is_subscription_required=True,
                has_active_subscription=False,
                is_unlocked=False,
                free_retention_days=setting.free_retention_days,
                monthly_price=setting.monthly_price,
                annual_price=setting.annual_price,
                currency=setting.currency,
                active_subscription=None
            )

        # Super Admin role always has free unlocked access
        is_admin = any(
            ur.role and getattr(ur.role, "name", None) == "SUPER_ADMIN"
            for ur in getattr(user, "user_roles", [])
        )
        if is_admin:
            return SubscriptionStatusResponse(
                is_subscription_required=True,
                has_active_subscription=True,
                is_unlocked=True,
                free_retention_days=setting.free_retention_days,
                monthly_price=setting.monthly_price,
                annual_price=setting.annual_price,
                currency=setting.currency,
                active_subscription=None
            )

        sub = cls.get_active_subscription_for_user(db, user.id)
        sub_resp = None
        if sub:
            sub_resp = UserSubscriptionResponse(
                id=sub.id,
                user_id=sub.user_id,
                user_name=user.full_name if user else None,
                user_mobile=user.mobile_number if user else None,
                user_email=user.email if user else None,
                plan_type=sub.plan_type,
                status=sub.status,
                amount_paid=sub.amount_paid,
                currency=sub.currency,
                start_date=sub.start_date,
                end_date=sub.end_date,
                payment_method=sub.payment_method,
                payment_reference=sub.payment_reference,
                notes=sub.notes,
                created_at=sub.created_at,
                is_active=sub.is_currently_active
            )

        has_sub = sub is not None
        return SubscriptionStatusResponse(
            is_subscription_required=True,
            has_active_subscription=has_sub,
            is_unlocked=has_sub,
            free_retention_days=setting.free_retention_days,
            monthly_price=setting.monthly_price,
            annual_price=setting.annual_price,
            currency=setting.currency,
            active_subscription=sub_resp
        )

    @classmethod
    def create_subscription_order(
        cls, db: Session, user: User, plan_type: str
    ) -> CreateSubscriptionOrderResponse:
        setting = cls.get_or_create_settings(db)
        amount = setting.annual_price if plan_type == "ANNUAL" else setting.monthly_price

        receipt = f"sub_{plan_type.lower()}_{uuid.uuid4().hex[:8]}"
        rzp_order = RazorpayService.create_razorpay_order(
            amount_in_rupees=amount,
            receipt=receipt,
            notes={
                "user_id": str(user.id),
                "plan_type": plan_type,
                "purpose": "historical_data_subscription",
            }
        )

        return CreateSubscriptionOrderResponse(
            order_id=rzp_order.get("razorpay_order_id"),
            amount=amount,
            currency=setting.currency,
            key_id=rzp_order.get("key_id"),
            plan_type=plan_type,
            description=f"{setting.title} ({plan_type.capitalize()} Plan)"
        )

    @classmethod
    def verify_and_activate_subscription(
        cls, db: Session, user: User, req: VerifySubscriptionPaymentRequest
    ) -> UserSubscriptionResponse:
        setting = cls.get_or_create_settings(db)
        plan_type = req.plan_type.upper()
        if plan_type not in ["MONTHLY", "ANNUAL", "LIFETIME"]:
            plan_type = "MONTHLY"

        amount = setting.annual_price if plan_type == "ANNUAL" else setting.monthly_price
        if plan_type == "LIFETIME":
            amount = Decimal("2999.00")

        # Verify signature if Razorpay keys provided
        if req.payment_method == "RAZORPAY" and req.razorpay_order_id and req.razorpay_payment_id and req.razorpay_signature:
            is_valid = RazorpayService.verify_payment_signature(
                req.razorpay_order_id,
                req.razorpay_payment_id,
                req.razorpay_signature
            )
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cryptographic payment signature verification failed."
                )

        now = datetime.now(timezone.utc)
        if plan_type == "MONTHLY":
            end_date = now + timedelta(days=30)
        elif plan_type == "ANNUAL":
            end_date = now + timedelta(days=365)
        else:  # LIFETIME
            end_date = now + timedelta(days=36500)

        # Check existing active subscription to extend if desired
        existing = cls.get_active_subscription_for_user(db, user.id)
        if existing and existing.end_date > now:
            start_date = existing.end_date
            if plan_type == "MONTHLY":
                end_date = start_date + timedelta(days=30)
            elif plan_type == "ANNUAL":
                end_date = start_date + timedelta(days=365)

        payment_ref = req.razorpay_payment_id or req.razorpay_order_id or f"pay_{uuid.uuid4().hex[:12]}"
        subscription = UserSubscription(
            user_id=user.id,
            plan_type=plan_type,
            status="ACTIVE",
            amount_paid=amount,
            currency=setting.currency,
            start_date=now,
            end_date=end_date,
            payment_method=req.payment_method,
            payment_reference=payment_ref,
            notes=f"Subscribed via {req.payment_method} on {now.strftime('%Y-%m-%d %H:%M')}"
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)

        return UserSubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            user_name=user.full_name,
            user_mobile=user.mobile_number,
            user_email=user.email,
            plan_type=subscription.plan_type,
            status=subscription.status,
            amount_paid=subscription.amount_paid,
            currency=subscription.currency,
            start_date=subscription.start_date,
            end_date=subscription.end_date,
            payment_method=subscription.payment_method,
            payment_reference=subscription.payment_reference,
            notes=subscription.notes,
            created_at=subscription.created_at,
            is_active=subscription.is_currently_active
        )

    @classmethod
    def admin_list_subscribers(cls, db: Session) -> List[UserSubscriptionResponse]:
        stmt = (
            select(UserSubscription, User)
            .join(User, UserSubscription.user_id == User.id, isouter=True)
            .order_by(desc(UserSubscription.created_at))
        )
        results = db.execute(stmt).all()

        output = []
        for sub, user in results:
            output.append(
                UserSubscriptionResponse(
                    id=sub.id,
                    user_id=sub.user_id,
                    user_name=user.full_name if user else "Unknown",
                    user_mobile=user.mobile_number if user else None,
                    user_email=user.email if user else None,
                    plan_type=sub.plan_type,
                    status=sub.status,
                    amount_paid=sub.amount_paid,
                    currency=sub.currency,
                    start_date=sub.start_date,
                    end_date=sub.end_date,
                    payment_method=sub.payment_method,
                    payment_reference=sub.payment_reference,
                    notes=sub.notes,
                    created_at=sub.created_at,
                    is_active=sub.is_currently_active
                )
            )
        return output

    @classmethod
    def admin_toggle_subscriber_status(
        cls, db: Session, subscription_id: uuid.UUID, is_active: bool
    ) -> UserSubscriptionResponse:
        sub = db.get(UserSubscription, subscription_id)
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription record not found."
            )

        sub.status = "ACTIVE" if is_active else "CANCELLED"
        sub.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(sub)

        user = db.get(User, sub.user_id)
        return UserSubscriptionResponse(
            id=sub.id,
            user_id=sub.user_id,
            user_name=user.full_name if user else "Unknown",
            user_mobile=user.mobile_number if user else None,
            user_email=user.email if user else None,
            plan_type=sub.plan_type,
            status=sub.status,
            amount_paid=sub.amount_paid,
            currency=sub.currency,
            start_date=sub.start_date,
            end_date=sub.end_date,
            payment_method=sub.payment_method,
            payment_reference=sub.payment_reference,
            notes=sub.notes,
            created_at=sub.created_at,
            is_active=sub.is_currently_active
        )

    @classmethod
    def admin_grant_subscription(
        cls, db: Session, req: AdminGrantSubscriptionRequest
    ) -> UserSubscriptionResponse:
        user = db.get(User, req.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found."
            )

        now = datetime.now(timezone.utc)
        end_date = now + timedelta(days=req.duration_days)

        subscription = UserSubscription(
            user_id=user.id,
            plan_type=req.plan_type,
            status="ACTIVE",
            amount_paid=Decimal("0.00"),
            currency="INR",
            start_date=now,
            end_date=end_date,
            payment_method="ADMIN_GRANTED",
            payment_reference=f"vip_admin_{uuid.uuid4().hex[:8]}",
            notes=req.notes or "Super Admin VIP Access"
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)

        return UserSubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            user_name=user.full_name,
            user_mobile=user.mobile_number,
            user_email=user.email,
            plan_type=subscription.plan_type,
            status=subscription.status,
            amount_paid=subscription.amount_paid,
            currency=subscription.currency,
            start_date=subscription.start_date,
            end_date=subscription.end_date,
            payment_method=subscription.payment_method,
            payment_reference=subscription.payment_reference,
            notes=subscription.notes,
            created_at=subscription.created_at,
            is_active=subscription.is_currently_active
        )
