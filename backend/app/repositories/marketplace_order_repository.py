import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from app.models.marketplace_order import (
    MarketplaceOrder,
    MarketplaceOrderItem,
    MarketplacePayment,
    MarketplaceDelivery,
)
from app.models.enums import MarketplaceOrderStatus, MarketplacePaymentStatus


class MarketplaceOrderRepository:
    """Repository handling Marketplace Orders, OrderItems, Payments, and Deliveries."""

    @staticmethod
    def generate_next_order_number(db: Session) -> str:
        current_year = datetime.now(timezone.utc).year
        prefix = f"ORD-LS-{current_year}-"
        pattern = re.compile(rf"^ORD-LS-{current_year}-(\d+)$")

        codes = db.scalars(
            select(MarketplaceOrder.order_number).where(
                MarketplaceOrder.order_number.like(f"{prefix}%")
            )
        ).all()

        max_num = 0
        for code in codes:
            match = pattern.match(code)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num

        next_num = max_num + 1
        return f"{prefix}{next_num:06d}"

    @staticmethod
    def generate_next_payment_number(db: Session) -> str:
        current_year = datetime.now(timezone.utc).year
        prefix = f"PAY-LS-{current_year}-"
        pattern = re.compile(rf"^PAY-LS-{current_year}-(\d+)$")

        codes = db.scalars(
            select(MarketplacePayment.payment_number).where(
                MarketplacePayment.payment_number.like(f"{prefix}%")
            )
        ).all()

        max_num = 0
        for code in codes:
            match = pattern.match(code)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num

        next_num = max_num + 1
        return f"{prefix}{next_num:06d}"

    @staticmethod
    def generate_next_delivery_code(db: Session) -> str:
        current_year = datetime.now(timezone.utc).year
        prefix = f"DEL-LS-{current_year}-"
        pattern = re.compile(rf"^DEL-LS-{current_year}-(\d+)$")

        codes = db.scalars(
            select(MarketplaceDelivery.delivery_code).where(
                MarketplaceDelivery.delivery_code.like(f"{prefix}%")
            )
        ).all()

        max_num = 0
        for code in codes:
            match = pattern.match(code)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num

        next_num = max_num + 1
        return f"{prefix}{next_num:06d}"

    @staticmethod
    def create_order_with_items_and_delivery(
        db: Session,
        order_number: str,
        customer_id: uuid.UUID,
        farmer_profile_id: uuid.UUID,
        order_data: Dict[str, Any],
        items_data: List[Dict[str, Any]],
        payment_data: Dict[str, Any],
        delivery_data: Dict[str, Any],
        created_by: Optional[uuid.UUID] = None
    ) -> MarketplaceOrder:
        now = datetime.now(timezone.utc)

        delivery_type_val = order_data.get("delivery_type", "FARM_PICKUP")
        if hasattr(delivery_type_val, "value"):
            delivery_type_val = delivery_type_val.value

        payment_method_val = payment_data.get("payment_method", "UPI")
        if hasattr(payment_method_val, "value"):
            payment_method_val = payment_method_val.value

        initial_order_status = (
            MarketplaceOrderStatus.CONFIRMED.value
            if payment_method_val == "CASH_ON_DELIVERY"
            else MarketplaceOrderStatus.PENDING.value
        )

        order = MarketplaceOrder(
            id=uuid.uuid4(),
            order_number=order_number,
            customer_id=customer_id,
            farmer_profile_id=farmer_profile_id,
            total_items_count=order_data["total_items_count"],
            subtotal_amount=Decimal(str(order_data["subtotal_amount"])),
            delivery_charge=Decimal(str(order_data.get("delivery_charge", 0))),
            tax_amount=Decimal(str(order_data.get("tax_amount", 0))),
            discount_amount=Decimal(str(order_data.get("discount_amount", 0))),
            total_amount=Decimal(str(order_data["total_amount"])),
            status=initial_order_status,
            payment_status=MarketplacePaymentStatus.PENDING.value,
            delivery_type=delivery_type_val,
            delivery_contact_name=order_data["delivery_contact_name"],
            delivery_contact_phone=order_data["delivery_contact_phone"],
            delivery_address=order_data.get("delivery_address"),
            delivery_city=order_data.get("delivery_city"),
            delivery_pincode=order_data.get("delivery_pincode"),
            notes=order_data.get("notes"),
            is_deleted=False,
            created_at=now,
            updated_at=now,
            created_by=created_by,
            updated_by=created_by
        )
        db.add(order)
        db.flush()

        # Add Order Items (Immutable Price Snapshot)
        for item_d in items_data:
            order_item = MarketplaceOrderItem(
                id=uuid.uuid4(),
                order_id=order.id,
                livestock_id=item_d["livestock_id"],
                farm_id=item_d["farm_id"],
                livestock_name=item_d["livestock_name"],
                livestock_code=item_d["livestock_code"],
                category_name=item_d["category_name"],
                breed_name=item_d.get("breed_name"),
                tag_number=item_d.get("tag_number"),
                selling_model=item_d["selling_model"],
                image_url=item_d.get("image_url"),
                unit_price=Decimal(str(item_d["unit_price"])),
                quantity=int(item_d["quantity"]),
                subtotal=Decimal(str(item_d["subtotal"])),
                created_at=now
            )
            db.add(order_item)

        # Create Payment Record
        payment = MarketplacePayment(
            id=uuid.uuid4(),
            payment_number=payment_data["payment_number"],
            order_id=order.id,
            customer_id=customer_id,
            amount=Decimal(str(order_data["total_amount"])),
            payment_method=payment_method_val,
            status=MarketplacePaymentStatus.PENDING.value,
            created_at=now,
            updated_at=now
        )
        db.add(payment)

        # Create Delivery Record
        delivery = MarketplaceDelivery(
            id=uuid.uuid4(),
            delivery_code=delivery_data["delivery_code"],
            order_id=order.id,
            pickup_location=delivery_data["pickup_location"],
            drop_location=delivery_data["drop_location"],
            driver_name=delivery_data.get("driver_name"),
            driver_contact=delivery_data.get("driver_contact"),
            status="PENDING",
            created_at=now,
            updated_at=now
        )
        db.add(delivery)

        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def get_by_id(
        db: Session,
        order_id: uuid.UUID,
        customer_id: Optional[uuid.UUID] = None,
        farmer_profile_id: Optional[uuid.UUID] = None
    ) -> Optional[MarketplaceOrder]:
        stmt = select(MarketplaceOrder).where(
            MarketplaceOrder.id == order_id,
            MarketplaceOrder.is_deleted == False
        )
        if customer_id is not None:
            stmt = stmt.where(MarketplaceOrder.customer_id == customer_id)
        if farmer_profile_id is not None:
            stmt = stmt.where(MarketplaceOrder.farmer_profile_id == farmer_profile_id)
        return db.scalar(stmt)

    @staticmethod
    def get_by_id_internal(db: Session, order_id: uuid.UUID) -> Optional[MarketplaceOrder]:
        stmt = select(MarketplaceOrder).where(
            MarketplaceOrder.id == order_id,
            MarketplaceOrder.is_deleted == False
        )
        return db.scalar(stmt)

    @staticmethod
    def list_customer_orders(
        db: Session,
        customer_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None
    ) -> Tuple[List[MarketplaceOrder], int]:
        stmt = select(MarketplaceOrder).where(
            MarketplaceOrder.customer_id == customer_id,
            MarketplaceOrder.is_deleted == False
        )
        if status:
            stmt = stmt.where(MarketplaceOrder.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        stmt = stmt.order_by(MarketplaceOrder.created_at.desc()).offset(skip).limit(limit)
        items = list(db.scalars(stmt).unique().all())
        return items, total

    @staticmethod
    def list_farmer_orders(
        db: Session,
        farmer_profile_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None
    ) -> Tuple[List[MarketplaceOrder], int]:
        stmt = select(MarketplaceOrder).where(
            MarketplaceOrder.farmer_profile_id == farmer_profile_id,
            MarketplaceOrder.is_deleted == False
        )
        if status:
            stmt = stmt.where(MarketplaceOrder.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        stmt = stmt.order_by(MarketplaceOrder.created_at.desc()).offset(skip).limit(limit)
        items = list(db.scalars(stmt).unique().all())
        return items, total

    @staticmethod
    def list_all_admin_orders(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[MarketplaceOrder], int]:
        stmt = select(MarketplaceOrder).where(MarketplaceOrder.is_deleted == False)
        if status:
            stmt = stmt.where(MarketplaceOrder.status == status)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    MarketplaceOrder.order_number.ilike(pattern),
                    MarketplaceOrder.delivery_contact_name.ilike(pattern),
                    MarketplaceOrder.delivery_contact_phone.ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        stmt = stmt.order_by(MarketplaceOrder.created_at.desc()).offset(skip).limit(limit)
        items = list(db.scalars(stmt).unique().all())
        return items, total

    @staticmethod
    def update_order_status(
        db: Session,
        order: MarketplaceOrder,
        new_status: str,
        cancellation_reason: Optional[str] = None,
        notes: Optional[str] = None,
        updated_by: Optional[uuid.UUID] = None
    ) -> MarketplaceOrder:
        order.status = new_status
        if cancellation_reason:
            order.cancellation_reason = cancellation_reason
        if notes:
            order.notes = notes
        order.updated_by = updated_by
        order.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def mark_payment_paid(
        db: Session,
        payment: MarketplacePayment,
        transaction_reference: str,
        notes: Optional[str] = None
    ) -> MarketplacePayment:
        now = datetime.now(timezone.utc)
        payment.status = MarketplacePaymentStatus.PAID.value
        payment.transaction_reference = transaction_reference
        payment.payment_date = now
        if notes:
            payment.notes = notes
        payment.updated_at = now

        # Update order payment status
        order = payment.order
        if order:
            order.payment_status = MarketplacePaymentStatus.PAID.value
            if order.status == MarketplaceOrderStatus.PENDING.value:
                order.status = MarketplaceOrderStatus.CONFIRMED.value
            order.updated_at = now

        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def get_admin_metrics(db: Session) -> Dict[str, Any]:
        """Real-time super admin marketplace KPIs aggregated directly from PostgreSQL."""
        from app.models.livestock import Livestock

        total_listings = db.scalar(select(func.count(Livestock.id)).where(Livestock.is_deleted == False)) or 0
        active_listings = db.scalar(
            select(func.count(Livestock.id)).where(
                Livestock.is_deleted == False,
                Livestock.status == "PUBLISHED",
                Livestock.is_active == True,
                Livestock.available_quantity > 0
            )
        ) or 0

        orders = list(db.scalars(select(MarketplaceOrder).where(MarketplaceOrder.is_deleted == False)).unique().all())
        total_orders = len(orders)
        pending_orders = sum(1 for o in orders if o.status in {"PENDING", "CONFIRMED", "PROCESSING"})
        completed_orders = sum(1 for o in orders if o.status == "DELIVERED")
        cancelled_orders = sum(1 for o in orders if o.status in {"CANCELLED", "REFUNDED"})

        total_gmv = sum(o.total_amount for o in orders if o.status != "CANCELLED")
        platform_fee = total_gmv * Decimal("0.05")  # 5% platform service rate
        farmer_payouts = total_gmv - platform_fee

        return {
            "total_listings": total_listings,
            "active_listings": active_listings,
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "completed_orders": completed_orders,
            "cancelled_orders": cancelled_orders,
            "total_sales_volume": total_gmv,
            "total_marketplace_revenue": platform_fee,
            "total_farmer_payouts": farmer_payouts,
            "total_gmv": total_gmv,
            "platform_fee": platform_fee,
            "farmer_payouts": farmer_payouts,
        }
