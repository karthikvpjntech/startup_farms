import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.marketplace_order import (
    OrderCheckoutRequest,
    DirectBuyNowCheckoutRequest,
    MarketplaceOrderResponse,
    MarketplaceOrderListResponse,
    PaymentVerifyRequest,
    ReviewCreateRequest,
    LivestockReviewResponse,
    RazorpayOrderCreateResponse,
    RazorpayPaymentVerifyRequest,
)
from app.services.marketplace_order_service import MarketplaceOrderService

router = APIRouter(prefix="/marketplace/orders", tags=["Marketplace Orders & Checkout"])


@router.post(
    "/checkout",
    response_model=List[MarketplaceOrderResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Checkout Cart and Place Order"
)
def checkout_cart(
    request: OrderCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return MarketplaceOrderService.checkout_cart(
        db=db,
        current_user=current_user,
        request=request
    )


@router.post(
    "/buy-now",
    response_model=MarketplaceOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Instant Direct Buy Now Checkout"
)
def buy_now(
    request: DirectBuyNowCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return MarketplaceOrderService.buy_now(
        db=db,
        current_user=current_user,
        request=request
    )


@router.get(
    "",
    response_model=MarketplaceOrderListResponse,
    summary="List Customer's Placed Orders"
)
def list_my_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return MarketplaceOrderService.list_customer_orders(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        status=status
    )


@router.get(
    "/{order_id}",
    response_model=MarketplaceOrderResponse,
    summary="Get Customer Order Details"
)
def get_order_detail(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return MarketplaceOrderService.get_order_detail(
        db=db,
        order_id=order_id,
        current_user=current_user
    )


@router.post(
    "/{order_id}/cancel",
    response_model=MarketplaceOrderResponse,
    summary="Cancel Pending Order"
)
def cancel_order(
    order_id: uuid.UUID,
    reason: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return MarketplaceOrderService.cancel_order(
        db=db,
        order_id=order_id,
        current_user=current_user,
        reason=reason
    )


@router.post(
    "/{order_id}/verify-payment",
    response_model=MarketplaceOrderResponse,
    summary="Verify Payment Settlement for Order"
)
def verify_payment(
    order_id: uuid.UUID,
    request: PaymentVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return MarketplaceOrderService.verify_payment(
        db=db,
        order_id=order_id,
        request=request,
        current_user=current_user
    )


@router.post(
    "/{order_id}/create-razorpay-order",
    response_model=RazorpayOrderCreateResponse,
    summary="Create Razorpay Order for Checkout"
)
def create_razorpay_order(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return MarketplaceOrderService.create_razorpay_order(
        db=db,
        order_id=order_id,
        current_user=current_user
    )


@router.post(
    "/{order_id}/verify-razorpay-payment",
    response_model=MarketplaceOrderResponse,
    summary="Verify Cryptographic Signature and Settle Razorpay Payment"
)
def verify_razorpay_payment(
    order_id: uuid.UUID,
    request: RazorpayPaymentVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return MarketplaceOrderService.verify_razorpay_payment(
        db=db,
        order_id=order_id,
        request=request,
        current_user=current_user
    )


@router.post(
    "/{order_id}/review",
    response_model=LivestockReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Verified Review for Delivered Livestock"
)
def submit_review(
    order_id: uuid.UUID,
    request: ReviewCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return MarketplaceOrderService.submit_review(
        db=db,
        order_id=order_id,
        current_user=current_user,
        request=request
    )
