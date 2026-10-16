import logging
import uuid
from decimal import Decimal
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.enums import (
    LivestockStatus,
    LivestockSellingModel,
    MarketplaceOrderStatus,
    MarketplacePaymentStatus,
    MarketplaceDeliveryType,
)
from app.models.marketplace_order import MarketplaceOrder
from app.schemas.marketplace_order import (
    OrderCheckoutRequest,
    DirectBuyNowCheckoutRequest,
    MarketplaceOrderResponse,
    MarketplaceOrderListResponse,
    MarketplaceOrderItemResponse,
    MarketplacePaymentResponse,
    MarketplaceDeliveryResponse,
    PaymentVerifyRequest,
    ReviewCreateRequest,
    LivestockReviewResponse,
    AdminMarketplaceMetricsResponse,
    RazorpayOrderCreateResponse,
    RazorpayPaymentVerifyRequest,
)
from app.repositories.marketplace_order_repository import MarketplaceOrderRepository
from app.repositories.cart_repository import CartRepository
from app.repositories.livestock_repository import LivestockRepository
from app.repositories.livestock_review_repository import LivestockReviewRepository
from app.services.notification_service import NotificationService
from app.services.email_service import EmailService
from app.services.razorpay_service import RazorpayService

logger = logging.getLogger("agri_smart.marketplace_order_service")


class MarketplaceOrderService:
    """
    Business service executing checkout with concurrency protection,
    server-side price snapshots, payment verification, and order state machine.
    """

    @staticmethod
    def _map_order_to_response(order: MarketplaceOrder) -> MarketplaceOrderResponse:
        items_resp = [
            MarketplaceOrderItemResponse(
                id=item.id,
                order_id=item.order_id,
                livestock_id=item.livestock_id,
                farm_id=item.farm_id,
                livestock_name=item.livestock_name,
                livestock_code=item.livestock_code,
                category_name=item.category_name,
                breed_name=item.breed_name,
                tag_number=item.tag_number,
                selling_model=item.selling_model,
                image_url=item.image_url,
                unit_price=item.unit_price,
                quantity=item.quantity,
                subtotal=item.subtotal,
                created_at=item.created_at,
            )
            for item in order.items
        ]

        pay_resp = None
        if order.payment:
            pay_resp = MarketplacePaymentResponse(
                id=order.payment.id,
                payment_number=order.payment.payment_number,
                order_id=order.payment.order_id,
                customer_id=order.payment.customer_id,
                amount=order.payment.amount,
                payment_method=order.payment.payment_method,
                status=order.payment.status,
                transaction_reference=order.payment.transaction_reference,
                payment_date=order.payment.payment_date,
                notes=order.payment.notes,
                created_at=order.payment.created_at,
            )

        del_resp = None
        if order.delivery:
            del_resp = MarketplaceDeliveryResponse(
                id=order.delivery.id,
                delivery_code=order.delivery.delivery_code,
                order_id=order.delivery.order_id,
                driver_id=order.delivery.driver_id,
                driver_name=order.delivery.driver_name,
                driver_contact=order.delivery.driver_contact,
                vehicle_number=order.delivery.vehicle_number,
                pickup_location=order.delivery.pickup_location,
                drop_location=order.delivery.drop_location,
                scheduled_pickup=order.delivery.scheduled_pickup,
                delivered_at=order.delivery.delivered_at,
                status=order.delivery.status,
                tracking_notes=order.delivery.tracking_notes,
                created_at=order.delivery.created_at,
            )

        return MarketplaceOrderResponse(
            id=order.id,
            order_number=order.order_number,
            customer_id=order.customer_id,
            customer_name=order.customer.full_name if order.customer else None,
            customer_mobile=order.customer.mobile_number if order.customer else None,
            farmer_profile_id=order.farmer_profile_id,
            farmer_name=order.farmer_profile.user.full_name if order.farmer_profile and order.farmer_profile.user else None,
            farmer_mobile=order.farmer_profile.user.mobile_number if order.farmer_profile and order.farmer_profile.user else None,
            total_items_count=order.total_items_count,
            subtotal_amount=order.subtotal_amount,
            delivery_charge=order.delivery_charge,
            tax_amount=order.tax_amount,
            discount_amount=order.discount_amount,
            total_amount=order.total_amount,
            status=order.status,
            payment_status=order.payment_status,
            delivery_type=order.delivery_type,
            delivery_contact_name=order.delivery_contact_name,
            delivery_contact_phone=order.delivery_contact_phone,
            delivery_address=order.delivery_address,
            delivery_city=order.delivery_city,
            delivery_pincode=order.delivery_pincode,
            cancellation_reason=order.cancellation_reason,
            notes=order.notes,
            created_at=order.created_at,
            updated_at=order.updated_at,
            items=items_resp,
            payment=pay_resp,
            delivery=del_resp,
        )

    # ========================================================================
    # Checkout Workflow (Cart & Buy Now)
    # ========================================================================

    @staticmethod
    def checkout_cart(
        db: Session,
        current_user: User,
        request: OrderCheckoutRequest
    ) -> List[MarketplaceOrderResponse]:
        cart = CartRepository.get_cart_by_user_id(db, current_user.id)
        if not cart or not cart.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your shopping cart is empty."
            )

        # Group cart items by Farmer Profile
        items_by_farmer: Dict[uuid.UUID, List[Dict[str, Any]]] = {}

        # 1. Lock and validate all items inside a single database transaction
        for cart_item in cart.items:
            livestock = LivestockRepository.get_by_id_for_update(db, cart_item.livestock_id)
            if not livestock or livestock.is_deleted or not livestock.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or more livestock items in your cart are no longer available."
                )

            if livestock.status != LivestockStatus.PUBLISHED.value:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"'{livestock.name}' is currently {livestock.status.lower()} and cannot be ordered."
                )

            if livestock.available_quantity < cart_item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Insufficient quantity for '{livestock.name}'. Only {livestock.available_quantity} available in stock."
                )

            # Deduct inventory atomically
            livestock.available_quantity -= cart_item.quantity
            if livestock.selling_model == LivestockSellingModel.INDIVIDUAL.value or livestock.available_quantity == 0:
                livestock.status = LivestockStatus.SOLD.value

            db.flush()

            primary_img = next((img.image_url for img in livestock.images if img.is_primary), None)
            if not primary_img and livestock.images:
                primary_img = livestock.images[0].image_url

            unit_price = livestock.price
            item_subtotal = unit_price * cart_item.quantity

            item_snapshot = {
                "livestock_id": livestock.id,
                "farm_id": livestock.farm_id,
                "livestock_name": livestock.name,
                "livestock_code": livestock.livestock_code,
                "category_name": livestock.category.name if livestock.category else "",
                "breed_name": livestock.breed.name if livestock.breed else None,
                "tag_number": livestock.tag_number,
                "selling_model": livestock.selling_model,
                "image_url": primary_img,
                "unit_price": unit_price,
                "quantity": cart_item.quantity,
                "subtotal": item_subtotal,
                "farm_location": f"{livestock.farm.village}, {livestock.farm.district}" if livestock.farm else "Farm Location"
            }

            f_id = livestock.farmer_profile_id
            if f_id not in items_by_farmer:
                items_by_farmer[f_id] = []
            items_by_farmer[f_id].append(item_snapshot)

        # 2. Create one order per farmer
        created_orders = []
        for farmer_profile_id, farmer_items in items_by_farmer.items():
            order_number = MarketplaceOrderRepository.generate_next_order_number(db)
            payment_number = MarketplaceOrderRepository.generate_next_payment_number(db)
            delivery_code = MarketplaceOrderRepository.generate_next_delivery_code(db)

            subtotal = sum(Decimal(str(it["subtotal"])) for it in farmer_items)
            total_items_count = sum(int(it["quantity"]) for it in farmer_items)
            delivery_charge = Decimal("0.00") if request.delivery_type == MarketplaceDeliveryType.FARM_PICKUP else Decimal("200.00")
            tax_amount = Decimal("0.00")
            total_amount = subtotal + delivery_charge + tax_amount

            pickup_loc = farmer_items[0]["farm_location"]
            drop_loc = f"{request.delivery_address or ''}, {request.delivery_city or ''} - {request.delivery_pincode or ''}".strip(" ,-") or "Customer Address"

            order_data = {
                "total_items_count": total_items_count,
                "subtotal_amount": subtotal,
                "delivery_charge": delivery_charge,
                "tax_amount": tax_amount,
                "discount_amount": Decimal("0.00"),
                "total_amount": total_amount,
                "delivery_type": request.delivery_type,
                "delivery_contact_name": request.delivery_contact_name,
                "delivery_contact_phone": request.delivery_contact_phone,
                "delivery_address": request.delivery_address,
                "delivery_city": request.delivery_city,
                "delivery_pincode": request.delivery_pincode,
                "notes": request.notes,
            }

            payment_data = {
                "payment_number": payment_number,
                "payment_method": request.payment_method,
            }

            delivery_data = {
                "delivery_code": delivery_code,
                "pickup_location": pickup_loc,
                "drop_location": drop_loc,
            }

            order = MarketplaceOrderRepository.create_order_with_items_and_delivery(
                db=db,
                order_number=order_number,
                customer_id=current_user.id,
                farmer_profile_id=farmer_profile_id,
                order_data=order_data,
                items_data=farmer_items,
                payment_data=payment_data,
                delivery_data=delivery_data,
                created_by=current_user.id
            )
            created_orders.append(order)

            # Send Email & SMS notifications (non-blocking)
            try:
                if current_user.email:
                    EmailService.send_order_confirmation_email(
                        to_email=current_user.email,
                        customer_name=current_user.full_name,
                        order_number=order_number,
                        total_amount=str(total_amount),
                        items=[{"name": item["livestock_name"], "quantity": item["quantity"], "subtotal": str(item["subtotal"])} for item in farmer_items],
                        delivery_address=request.delivery_address or "Farm Gate Pickup",
                    )
                NotificationService.send_order_placed_sms(
                    db=db,
                    farmer_profile_id=farmer_profile_id,
                    customer_mobile=current_user.mobile_number,
                    customer_name=current_user.full_name,
                    order_number=order_number,
                    total_amount=str(total_amount),
                    order_id=order.id
                )
            except Exception as e:
                logger.warning("Failed to dispatch order notification: %s", e)

        # 3. Clear cart after successful checkout
        CartRepository.clear_cart(db, cart.id)

        logger.info("User %s successfully placed %d marketplace order(s)", current_user.id, len(created_orders))
        return [MarketplaceOrderService._map_order_to_response(o) for o in created_orders]

    @staticmethod
    def buy_now(
        db: Session,
        current_user: User,
        request: DirectBuyNowCheckoutRequest
    ) -> MarketplaceOrderResponse:
        # Atomic lock
        livestock = LivestockRepository.get_by_id_for_update(db, request.livestock_id)
        if not livestock or livestock.is_deleted or not livestock.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livestock not found.")

        if livestock.status != LivestockStatus.PUBLISHED.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"'{livestock.name}' is currently {livestock.status.lower()} and cannot be ordered."
            )

        if livestock.selling_model == LivestockSellingModel.INDIVIDUAL.value and request.quantity != 1:
            request.quantity = 1

        if livestock.available_quantity < request.quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Insufficient inventory. Only {livestock.available_quantity} available."
            )

        # Deduct inventory atomically
        livestock.available_quantity -= request.quantity
        if livestock.selling_model == LivestockSellingModel.INDIVIDUAL.value or livestock.available_quantity == 0:
            livestock.status = LivestockStatus.SOLD.value
        db.flush()

        primary_img = next((img.image_url for img in livestock.images if img.is_primary), None)
        if not primary_img and livestock.images:
            primary_img = livestock.images[0].image_url

        unit_price = livestock.price
        subtotal = unit_price * request.quantity
        delivery_charge = Decimal("0.00") if request.delivery_type == MarketplaceDeliveryType.FARM_PICKUP else Decimal("200.00")
        tax_amount = Decimal("0.00")
        total_amount = subtotal + delivery_charge + tax_amount

        order_number = MarketplaceOrderRepository.generate_next_order_number(db)
        payment_number = MarketplaceOrderRepository.generate_next_payment_number(db)
        delivery_code = MarketplaceOrderRepository.generate_next_delivery_code(db)

        pickup_loc = f"{livestock.farm.village}, {livestock.farm.district}" if livestock.farm else "Farm Location"
        drop_loc = f"{request.delivery_address or ''}, {request.delivery_city or ''} - {request.delivery_pincode or ''}".strip(" ,-") or "Customer Address"

        item_snapshot = {
            "livestock_id": livestock.id,
            "farm_id": livestock.farm_id,
            "livestock_name": livestock.name,
            "livestock_code": livestock.livestock_code,
            "category_name": livestock.category.name if livestock.category else "",
            "breed_name": livestock.breed.name if livestock.breed else None,
            "tag_number": livestock.tag_number,
            "selling_model": livestock.selling_model,
            "image_url": primary_img,
            "unit_price": unit_price,
            "quantity": request.quantity,
            "subtotal": subtotal,
        }

        order_data = {
            "total_items_count": request.quantity,
            "subtotal_amount": subtotal,
            "delivery_charge": delivery_charge,
            "tax_amount": tax_amount,
            "discount_amount": Decimal("0.00"),
            "total_amount": total_amount,
            "delivery_type": request.delivery_type,
            "delivery_contact_name": request.delivery_contact_name,
            "delivery_contact_phone": request.delivery_contact_phone,
            "delivery_address": request.delivery_address,
            "delivery_city": request.delivery_city,
            "delivery_pincode": request.delivery_pincode,
            "notes": request.notes,
        }

        payment_data = {
            "payment_number": payment_number,
            "payment_method": request.payment_method,
        }

        delivery_data = {
            "delivery_code": delivery_code,
            "pickup_location": pickup_loc,
            "drop_location": drop_loc,
        }

        order = MarketplaceOrderRepository.create_order_with_items_and_delivery(
            db=db,
            order_number=order_number,
            customer_id=current_user.id,
            farmer_profile_id=livestock.farmer_profile_id,
            order_data=order_data,
            items_data=[item_snapshot],
            payment_data=payment_data,
            delivery_data=delivery_data,
            created_by=current_user.id
        )

        try:
            if current_user.email:
                EmailService.send_order_confirmation_email(
                    to_email=current_user.email,
                    customer_name=current_user.full_name,
                    order_number=order_number,
                    total_amount=str(total_amount),
                    items=[{"name": item_snapshot["livestock_name"], "quantity": item_snapshot["quantity"], "subtotal": str(item_snapshot["subtotal"])}],
                    delivery_address=request.delivery_address or "Farm Gate Pickup",
                )
            NotificationService.send_order_placed_sms(
                db=db,
                farmer_profile_id=livestock.farmer_profile_id,
                customer_mobile=current_user.mobile_number,
                customer_name=current_user.full_name,
                order_number=order_number,
                total_amount=str(total_amount),
                order_id=order.id
            )
        except Exception as e:
            logger.warning("Failed to dispatch order notification: %s", e)

        return MarketplaceOrderService._map_order_to_response(order)

    # ========================================================================
    # Payment Verification & Razorpay Gateway Integration
    # ========================================================================

    @staticmethod
    def verify_payment(
        db: Session,
        order_id: uuid.UUID,
        request: PaymentVerifyRequest,
        current_user: User
    ) -> MarketplaceOrderResponse:
        order = MarketplaceOrderRepository.get_by_id(db, order_id, customer_id=current_user.id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

        if not order.payment:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order payment record missing.")

        payment = MarketplaceOrderRepository.mark_payment_paid(
            db=db,
            payment=order.payment,
            transaction_reference=request.transaction_reference,
            notes=request.notes
        )
        logger.info("Payment %s verified for Order %s", payment.payment_number, order.order_number)

        # Trigger digital payment receipt notifications
        try:
            if current_user.email:
                EmailService.send_payment_receipt_email(
                    to_email=current_user.email,
                    customer_name=current_user.full_name,
                    order_number=order.order_number,
                    payment_number=payment.payment_number,
                    amount=str(payment.amount),
                    payment_method=payment.payment_method,
                    transaction_ref=request.transaction_reference
                )
            NotificationService.send_payment_received_sms(
                db=db,
                farmer_profile_id=order.farmer_profile_id,
                customer_mobile=current_user.mobile_number,
                customer_name=current_user.full_name,
                order_number=order.order_number,
                amount=str(payment.amount),
                order_id=order.id
            )
        except Exception as e:
            logger.warning("Failed to dispatch payment receipt notification: %s", e)

        return MarketplaceOrderService._map_order_to_response(order)

    @staticmethod
    def create_razorpay_order(
        db: Session,
        order_id: uuid.UUID,
        current_user: User
    ) -> RazorpayOrderCreateResponse:
        """
        Creates a Razorpay Test / Live order for checkout payment modal.
        """
        order = MarketplaceOrderRepository.get_by_id(db, order_id, customer_id=current_user.id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

        rzp_data = RazorpayService.create_razorpay_order(
            amount_in_rupees=order.total_amount,
            receipt=order.order_number,
            notes={
                "order_id": str(order.id),
                "order_number": order.order_number,
                "customer_id": str(current_user.id),
            }
        )

        return RazorpayOrderCreateResponse(
            order_id=order.id,
            order_number=order.order_number,
            razorpay_order_id=rzp_data["razorpay_order_id"],
            amount=rzp_data["amount"],
            currency=rzp_data["currency"],
            key_id=rzp_data["key_id"],
            is_simulated=rzp_data.get("is_simulated", False),
        )

    @staticmethod
    def verify_razorpay_payment(
        db: Session,
        order_id: uuid.UUID,
        request: RazorpayPaymentVerifyRequest,
        current_user: User
    ) -> MarketplaceOrderResponse:
        """
        Cryptographically validates Razorpay HMAC-SHA256 signature and settles the order.
        """
        order = MarketplaceOrderRepository.get_by_id(db, order_id, customer_id=current_user.id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

        if not order.payment:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order payment record missing.")

        is_valid = RazorpayService.verify_payment_signature(
            razorpay_order_id=request.razorpay_order_id,
            razorpay_payment_id=request.razorpay_payment_id,
            razorpay_signature=request.razorpay_signature,
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Razorpay cryptographic payment signature. Verification failed."
            )

        payment = MarketplaceOrderRepository.mark_payment_paid(
            db=db,
            payment=order.payment,
            transaction_reference=request.razorpay_payment_id,
            notes=f"Razorpay Order: {request.razorpay_order_id} | Signature Verified"
        )
        logger.info("Razorpay Payment %s verified for Order %s", payment.payment_number, order.order_number)

        # Trigger digital payment receipt notifications
        try:
            if current_user.email:
                EmailService.send_payment_receipt_email(
                    to_email=current_user.email,
                    customer_name=current_user.full_name,
                    order_number=order.order_number,
                    payment_number=payment.payment_number,
                    amount=str(payment.amount),
                    payment_method="RAZORPAY",
                    transaction_ref=request.razorpay_payment_id
                )
            NotificationService.send_payment_received_sms(
                db=db,
                farmer_profile_id=order.farmer_profile_id,
                customer_mobile=current_user.mobile_number,
                customer_name=current_user.full_name,
                order_number=order.order_number,
                amount=str(payment.amount),
                order_id=order.id
            )
        except Exception as e:
            logger.warning("Failed to dispatch Razorpay payment receipt notifications: %s", e)

        return MarketplaceOrderService._map_order_to_response(order)

    # ========================================================================
    # Customer Order Queries & Cancellation
    # ========================================================================

    @staticmethod
    def list_customer_orders(
        db: Session,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None
    ) -> MarketplaceOrderListResponse:
        skip = (page - 1) * page_size
        items, total = MarketplaceOrderRepository.list_customer_orders(
            db=db,
            customer_id=current_user.id,
            skip=skip,
            limit=page_size,
            status=status
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        responses = [MarketplaceOrderService._map_order_to_response(o) for o in items]
        return MarketplaceOrderListResponse(
            items=responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    @staticmethod
    def get_order_detail(
        db: Session,
        order_id: uuid.UUID,
        current_user: User
    ) -> MarketplaceOrderResponse:
        # If user is super admin or the customer or the farmer
        order = MarketplaceOrderRepository.get_by_id(db, order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

        is_admin = any(ur.role.name == "SUPER_ADMIN" for ur in current_user.user_roles if ur.role)
        is_customer = order.customer_id == current_user.id
        is_farmer = current_user.farmer_profile and order.farmer_profile_id == current_user.farmer_profile.id

        if not (is_admin or is_customer or is_farmer):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this order.")

        return MarketplaceOrderService._map_order_to_response(order)

    @staticmethod
    def cancel_order(
        db: Session,
        order_id: uuid.UUID,
        current_user: User,
        reason: Optional[str] = None
    ) -> MarketplaceOrderResponse:
        order = MarketplaceOrderRepository.get_by_id(db, order_id, customer_id=current_user.id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

        # Eligible statuses for customer cancellation
        if order.status not in {MarketplaceOrderStatus.PENDING.value, MarketplaceOrderStatus.CONFIRMED.value}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order in '{order.status}' status cannot be cancelled directly. Please contact the farmer."
            )

        # Restore inventory
        for item in order.items:
            livestock = LivestockRepository.get_by_id_for_update(db, item.livestock_id)
            if livestock:
                livestock.available_quantity += item.quantity
                if livestock.status == LivestockStatus.SOLD.value and livestock.available_quantity > 0:
                    livestock.status = LivestockStatus.PUBLISHED.value
                db.flush()

        updated = MarketplaceOrderRepository.update_order_status(
            db=db,
            order=order,
            new_status=MarketplaceOrderStatus.CANCELLED.value,
            cancellation_reason=reason or "Cancelled by customer",
            updated_by=current_user.id
        )
        logger.info("Order %s cancelled by customer %s", order.order_number, current_user.id)
        return MarketplaceOrderService._map_order_to_response(updated)

    # ========================================================================
    # Farmer Order Management
    # ========================================================================

    @staticmethod
    def list_farmer_orders(
        db: Session,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None
    ) -> MarketplaceOrderListResponse:
        farmer_profile = current_user.farmer_profile
        if not farmer_profile:
            return MarketplaceOrderListResponse(items=[], total=0, page=page, page_size=page_size, total_pages=0)

        skip = (page - 1) * page_size
        items, total = MarketplaceOrderRepository.list_farmer_orders(
            db=db,
            farmer_profile_id=farmer_profile.id,
            skip=skip,
            limit=page_size,
            status=status
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        responses = [MarketplaceOrderService._map_order_to_response(o) for o in items]
        return MarketplaceOrderListResponse(
            items=responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    @staticmethod
    def update_farmer_order_status(
        db: Session,
        current_user: User,
        order_id: uuid.UUID,
        new_status: str,
        notes: Optional[str] = None
    ) -> MarketplaceOrderResponse:
        farmer_profile = current_user.farmer_profile
        if not farmer_profile:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Farmer profile required.")

        order = MarketplaceOrderRepository.get_by_id(db, order_id, farmer_profile_id=farmer_profile.id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

        # If rejected, restore inventory
        if new_status == MarketplaceOrderStatus.FARMER_REJECTED.value:
            for item in order.items:
                livestock = LivestockRepository.get_by_id_for_update(db, item.livestock_id)
                if livestock:
                    livestock.available_quantity += item.quantity
                    if livestock.status == LivestockStatus.SOLD.value and livestock.available_quantity > 0:
                        livestock.status = LivestockStatus.PUBLISHED.value
                    db.flush()

        updated = MarketplaceOrderRepository.update_order_status(
            db=db,
            order=order,
            new_status=new_status,
            notes=notes,
            updated_by=current_user.id
        )
        logger.info("Farmer %s updated Order %s status to %s", current_user.id, order.order_number, new_status)
        return MarketplaceOrderService._map_order_to_response(updated)

    # ========================================================================
    # Verified Reviews Submission
    # ========================================================================

    @staticmethod
    def submit_review(
        db: Session,
        order_id: uuid.UUID,
        current_user: User,
        request: ReviewCreateRequest
    ) -> LivestockReviewResponse:
        order = MarketplaceOrderRepository.get_by_id(db, order_id, customer_id=current_user.id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

        if order.status != MarketplaceOrderStatus.DELIVERED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reviews can only be submitted after the order has been delivered."
            )

        # Verify order contains this livestock
        contains_item = any(item.livestock_id == request.livestock_id for item in order.items)
        if not contains_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This order does not contain the specified livestock item."
            )

        # Check existing review
        existing = LivestockReviewRepository.get_existing_review(
            db=db,
            order_id=order_id,
            livestock_id=request.livestock_id,
            customer_id=current_user.id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already submitted a review for this purchase."
            )

        review = LivestockReviewRepository.create_review(
            db=db,
            order_id=order_id,
            livestock_id=request.livestock_id,
            customer_id=current_user.id,
            rating=request.rating,
            review_text=request.review_text
        )
        logger.info("Customer %s reviewed livestock %s with rating %d", current_user.id, request.livestock_id, request.rating)
        return LivestockReviewResponse(
            id=review.id,
            livestock_id=review.livestock_id,
            order_id=review.order_id,
            customer_id=review.customer_id,
            customer_name=current_user.full_name,
            rating=review.rating,
            review_text=review.review_text,
            is_verified_purchase=review.is_verified_purchase,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )

    # ========================================================================
    # Super Admin Dashboard & Moderation
    # ========================================================================

    @staticmethod
    def get_admin_metrics(db: Session) -> AdminMarketplaceMetricsResponse:
        metrics = MarketplaceOrderRepository.get_admin_metrics(db)
        return AdminMarketplaceMetricsResponse(**metrics)

    @staticmethod
    def list_all_admin_orders(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> MarketplaceOrderListResponse:
        skip = (page - 1) * page_size
        items, total = MarketplaceOrderRepository.list_all_admin_orders(
            db=db,
            skip=skip,
            limit=page_size,
            status=status,
            search=search
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        responses = [MarketplaceOrderService._map_order_to_response(o) for o in items]
        return MarketplaceOrderListResponse(
            items=responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
