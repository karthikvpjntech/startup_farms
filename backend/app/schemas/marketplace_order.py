import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.enums import (
    MarketplaceOrderStatus,
    MarketplacePaymentStatus,
    MarketplacePaymentMethod,
    MarketplaceDeliveryType,
    MarketplaceDeliveryStatus,
)
from app.core.phone_utils import validate_and_format_phone


# ============================================================================
# Checkout & Order Requests
# ============================================================================

class OrderCheckoutRequest(BaseModel):
    delivery_type: MarketplaceDeliveryType = Field(
        default=MarketplaceDeliveryType.FARM_PICKUP,
        description="FARM_PICKUP, FARMER_DELIVERY, or LOGISTICS_PARTNER"
    )
    delivery_contact_name: str = Field(..., min_length=2, max_length=150, description="Recipient full name")
    delivery_contact_phone: str = Field(..., min_length=7, max_length=20, description="Recipient contact phone")
    delivery_address: Optional[str] = Field(default=None, description="Full delivery street address")
    delivery_city: Optional[str] = Field(default=None, max_length=100)
    delivery_pincode: Optional[str] = Field(default=None, max_length=10)
    payment_method: MarketplacePaymentMethod = Field(
        default=MarketplacePaymentMethod.UPI,
        description="UPI, NET_BANKING, CARD, or CASH_ON_DELIVERY"
    )
    notes: Optional[str] = Field(default=None, description="Special instructions or delivery notes")

    @field_validator("delivery_contact_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        res = validate_and_format_phone(v)
        if not res:
            raise ValueError("Recipient contact phone is required.")
        return res


class DirectBuyNowCheckoutRequest(OrderCheckoutRequest):
    livestock_id: uuid.UUID = Field(..., description="Target livestock UUID to purchase immediately")
    quantity: int = Field(default=1, ge=1, description="Quantity to purchase")


class OrderStatusUpdateRequest(BaseModel):
    status: MarketplaceOrderStatus
    cancellation_reason: Optional[str] = None
    notes: Optional[str] = None


class PaymentVerifyRequest(BaseModel):
    transaction_reference: str = Field(..., min_length=3, max_length=100, description="Bank / UPI reference number / UTR")
    notes: Optional[str] = None


class ReviewCreateRequest(BaseModel):
    livestock_id: uuid.UUID
    rating: int = Field(..., ge=1, le=5, description="Rating between 1 and 5 stars")
    review_text: Optional[str] = Field(default=None, description="Detailed customer review comments")


# ============================================================================
# Order & Fulfillment Responses
# ============================================================================

class MarketplaceOrderItemResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    product_type: str = "LIVESTOCK"
    livestock_id: Optional[uuid.UUID] = None
    farm_product_id: Optional[uuid.UUID] = None
    farm_id: Optional[uuid.UUID] = None
    product_name: Optional[str] = None
    livestock_name: Optional[str] = None
    livestock_code: Optional[str] = None
    category_name: str
    breed_name: Optional[str] = None
    variety_name: Optional[str] = None
    unit: Optional[str] = None
    tag_number: Optional[str] = None
    selling_model: Optional[str] = None
    image_url: Optional[str] = None
    unit_price: Decimal
    quantity: int
    subtotal: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)



class MarketplacePaymentResponse(BaseModel):
    id: uuid.UUID
    payment_number: str
    order_id: uuid.UUID
    customer_id: uuid.UUID
    amount: Decimal
    payment_method: str
    status: str
    transaction_reference: Optional[str] = None
    payment_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MarketplaceDeliveryResponse(BaseModel):
    id: uuid.UUID
    delivery_code: str
    order_id: uuid.UUID
    driver_id: Optional[uuid.UUID] = None
    driver_name: Optional[str] = None
    driver_contact: Optional[str] = None
    vehicle_number: Optional[str] = None
    pickup_location: str
    drop_location: str
    scheduled_pickup: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    status: str
    tracking_notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LivestockReviewResponse(BaseModel):
    id: uuid.UUID
    livestock_id: uuid.UUID
    order_id: uuid.UUID
    customer_id: uuid.UUID
    customer_name: Optional[str] = None
    rating: int
    review_text: Optional[str] = None
    is_verified_purchase: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MarketplaceOrderResponse(BaseModel):
    id: uuid.UUID
    order_number: str
    customer_id: uuid.UUID
    customer_name: Optional[str] = None
    customer_mobile: Optional[str] = None
    farmer_profile_id: uuid.UUID
    farmer_name: Optional[str] = None
    farmer_mobile: Optional[str] = None
    total_items_count: int
    subtotal_amount: Decimal
    delivery_charge: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    status: str
    payment_status: str
    delivery_type: str
    delivery_contact_name: str
    delivery_contact_phone: str
    delivery_address: Optional[str] = None
    delivery_city: Optional[str] = None
    delivery_pincode: Optional[str] = None
    cancellation_reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    items: List[MarketplaceOrderItemResponse] = []
    payment: Optional[MarketplacePaymentResponse] = None
    delivery: Optional[MarketplaceDeliveryResponse] = None

    model_config = ConfigDict(from_attributes=True)


class MarketplaceOrderListResponse(BaseModel):
    items: List[MarketplaceOrderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminMarketplaceMetricsResponse(BaseModel):
    total_listings: int = 0
    active_listings: int = 0
    total_orders: int = 0
    pending_orders: int = 0
    completed_orders: int = 0
    cancelled_orders: int = 0
    total_sales_volume: Decimal = Decimal("0.00")
    total_marketplace_revenue: Decimal = Decimal("0.00")
    total_farmer_payouts: Decimal = Decimal("0.00")
    total_gmv: Decimal = Decimal("0.00")
    platform_fee: Decimal = Decimal("0.00")
    farmer_payouts: Decimal = Decimal("0.00")


# ============================================================================
# Razorpay Integration Schemas
# ============================================================================

class RazorpayOrderCreateResponse(BaseModel):
    order_id: uuid.UUID
    order_number: str
    razorpay_order_id: str
    amount: int  # in paise
    currency: str
    key_id: str
    is_simulated: bool = False


class RazorpayPaymentVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    notes: Optional[str] = None
