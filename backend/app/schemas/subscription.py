import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class SubscriptionSettingResponse(BaseModel):
    id: int
    is_enabled: bool
    free_retention_days: int
    monthly_price: Decimal
    annual_price: Decimal
    currency: str
    title: str
    description: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubscriptionSettingUpdateRequest(BaseModel):
    is_enabled: Optional[bool] = None
    free_retention_days: Optional[int] = Field(None, ge=0, le=3650)
    monthly_price: Optional[Decimal] = Field(None, ge=0)
    annual_price: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None


class UserSubscriptionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user_name: Optional[str] = None
    user_mobile: Optional[str] = None
    user_email: Optional[str] = None
    plan_type: str
    status: str
    amount_paid: Decimal
    currency: str
    start_date: datetime
    end_date: datetime
    payment_method: str
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class SubscriptionStatusResponse(BaseModel):
    is_subscription_required: bool
    has_active_subscription: bool
    is_unlocked: bool
    free_retention_days: int
    monthly_price: Decimal
    annual_price: Decimal
    currency: str
    active_subscription: Optional[UserSubscriptionResponse] = None


class CreateSubscriptionOrderRequest(BaseModel):
    plan_type: str = Field(..., pattern="^(MONTHLY|ANNUAL|LIFETIME)$")


class CreateSubscriptionOrderResponse(BaseModel):
    order_id: Optional[str] = None
    amount: Decimal
    currency: str
    key_id: Optional[str] = None
    plan_type: str
    description: str


class VerifySubscriptionPaymentRequest(BaseModel):
    plan_type: str
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
    payment_method: str = "RAZORPAY"  # RAZORPAY, UPI, CASH


class AdminGrantSubscriptionRequest(BaseModel):
    user_id: uuid.UUID
    plan_type: str = "ANNUAL"  # MONTHLY, ANNUAL, LIFETIME
    duration_days: int = 365
    notes: Optional[str] = "Admin VIP pass granted"


class AdminToggleSubscriberRequest(BaseModel):
    is_active: bool
