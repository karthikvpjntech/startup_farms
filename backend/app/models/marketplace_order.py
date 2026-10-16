import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Numeric,
    Integer,
    Text,
    Uuid,
    ForeignKey,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.farmer_profile import FarmerProfile
    from app.models.farm import Farm
    from app.models.livestock import Livestock, LivestockReview
    from app.models.farm_selling_product import FarmSellingProduct


class MarketplaceOrder(Base):
    """
    Marketplace Customer Order Entity.
    Groups purchased livestock items from a farmer with financial accounting, delivery, and payment.
    """
    __tablename__ = "marketplace_orders"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    order_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    farmer_profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farmer_profiles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Item count & Financial amounts
    total_items_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )
    subtotal_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )
    delivery_charge: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    # Fulfillment & Settlement Status
    status: Mapped[str] = mapped_column(
        String(30),
        default="PENDING",
        index=True,
        nullable=False
    )  # PENDING, CONFIRMED, FARMER_ACCEPTED, FARMER_REJECTED, PROCESSING, READY_FOR_PICKUP, OUT_FOR_DELIVERY, DELIVERED, CANCELLED, REFUND_REQUESTED, REFUNDED

    payment_status: Mapped[str] = mapped_column(
        String(30),
        default="PENDING",
        index=True,
        nullable=False
    )  # PENDING, PAID, FAILED, REFUNDED

    # Delivery & Contact Details
    delivery_type: Mapped[str] = mapped_column(
        String(30),
        default="FARM_PICKUP",
        nullable=False
    )  # FARM_PICKUP, FARMER_DELIVERY, LOGISTICS_PARTNER

    delivery_contact_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )
    delivery_contact_phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )
    delivery_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    delivery_city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    delivery_pincode: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True
    )

    # Additional metadata
    cancellation_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Soft Delete & Audit
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    deleted_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="chk_marketplace_order_total_non_negative"),
        CheckConstraint("subtotal_amount >= 0", name="chk_marketplace_order_subtotal_non_negative"),
        Index("ix_marketplace_orders_customer_created", "customer_id", "created_at"),
        Index("ix_marketplace_orders_farmer_status", "farmer_profile_id", "status"),
    )

    # Relationships
    customer: Mapped["User"] = relationship("User", foreign_keys=[customer_id], lazy="joined")
    farmer_profile: Mapped["FarmerProfile"] = relationship("FarmerProfile", foreign_keys=[farmer_profile_id], lazy="joined")
    items: Mapped[List["MarketplaceOrderItem"]] = relationship(
        "MarketplaceOrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="joined"
    )
    payment: Mapped[Optional["MarketplacePayment"]] = relationship(
        "MarketplacePayment",
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="joined"
    )
    delivery: Mapped[Optional["MarketplaceDelivery"]] = relationship(
        "MarketplaceDelivery",
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="joined"
    )
    reviews: Mapped[List["LivestockReview"]] = relationship(
        "LivestockReview",
        back_populates="order",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MarketplaceOrder(id={self.id}, number='{self.order_number}', total={self.total_amount}, status='{self.status}')>"


class MarketplaceOrderItem(Base):
    """
    Immutable Price Snapshot Line Item for a purchased livestock or farm produce record.
    """
    __tablename__ = "marketplace_order_items"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("marketplace_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    livestock_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("livestock.id", ondelete="RESTRICT"),
        nullable=True,
        index=True
    )
    farm_product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farm_selling_products.id", ondelete="RESTRICT"),
        nullable=True,
        index=True
    )
    farm_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farms.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Snapshot fields
    product_type: Mapped[str] = mapped_column(
        String(30),
        default="LIVESTOCK",
        nullable=False
    )  # LIVESTOCK, FARM_PRODUCT
    livestock_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    livestock_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    category_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    breed_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    variety_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    unit: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True
    )
    tag_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    selling_model: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True
    )
    image_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )

    # Quantities and Prices
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint("unit_price >= 0", name="chk_order_item_unit_price_non_negative"),
        CheckConstraint("quantity >= 1", name="chk_order_item_qty_positive"),
        CheckConstraint("subtotal >= 0", name="chk_order_item_subtotal_non_negative"),
    )

    # Relationships
    order: Mapped["MarketplaceOrder"] = relationship("MarketplaceOrder", back_populates="items")
    livestock: Mapped[Optional["Livestock"]] = relationship("Livestock", lazy="joined")
    farm_product: Mapped[Optional["FarmSellingProduct"]] = relationship("FarmSellingProduct", lazy="joined")
    farm: Mapped[Optional["Farm"]] = relationship("Farm", lazy="joined")

    def __repr__(self) -> str:
        return f"<MarketplaceOrderItem(id={self.id}, name='{self.livestock_name}', qty={self.quantity}, subtotal={self.subtotal})>"


class MarketplacePayment(Base):
    """
    Payment Settlement Transaction Entity for Marketplace Orders.
    """
    __tablename__ = "marketplace_payments"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    payment_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("marketplace_orders.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )
    payment_method: Mapped[str] = mapped_column(
        String(50),
        default="UPI",
        nullable=False
    )  # UPI, NET_BANKING, CARD, CASH_ON_DELIVERY
    status: Mapped[str] = mapped_column(
        String(30),
        default="PENDING",
        nullable=False
    )  # PENDING, PAID, FAILED, REFUNDED
    transaction_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    payment_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    order: Mapped["MarketplaceOrder"] = relationship("MarketplaceOrder", back_populates="payment")
    customer: Mapped["User"] = relationship("User", foreign_keys=[customer_id], lazy="joined")

    def __repr__(self) -> str:
        return f"<MarketplacePayment(number='{self.payment_number}', amount={self.amount}, status='{self.status}')>"


class MarketplaceDelivery(Base):
    """
    Logistics & Dispatch tracking entity for Marketplace Livestock Deliveries.
    Integrates with the existing DRIVER role & logistics workflow.
    """
    __tablename__ = "marketplace_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    delivery_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("marketplace_orders.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    driver_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    pickup_location: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    drop_location: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    scheduled_pickup: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    vehicle_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    driver_name: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True
    )
    driver_contact: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="PENDING",
        nullable=False
    )  # PENDING, ASSIGNED, PICKED_UP, IN_TRANSIT, DELIVERED, CANCELLED
    tracking_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    order: Mapped["MarketplaceOrder"] = relationship("MarketplaceOrder", back_populates="delivery")
    driver_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[driver_id], lazy="joined")

    def __repr__(self) -> str:
        return f"<MarketplaceDelivery(code='{self.delivery_code}', status='{self.status}')>"
