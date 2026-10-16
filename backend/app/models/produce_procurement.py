import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Date,
    Numeric,
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
    from app.models.crop import Crop
    from app.models.cultivation import CultivationRun


class ProduceProcurement(Base):
    """
    Public Customer Produce & Crop Procurement Request Entity.
    Manages customer procurement requests for crops/produce (e.g. Paddy / நெல்),
    farmer review & stock confirmation, payment settlements, and delivery progression.
    """
    __tablename__ = "produce_procurements"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    request_code: Mapped[str] = mapped_column(
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
    farm_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farms.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    crop_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("crops.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    cultivation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cultivation_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Product snapshot
    product_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )
    requested_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )
    unit: Mapped[str] = mapped_column(
        String(30),
        default="kg",
        nullable=False
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        nullable=False
    )

    # Schedule & Delivery Address
    required_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )
    delivery_location: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    delivery_city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    delivery_pincode: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True
    )
    contact_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )
    contact_phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Farmer Confirmation & Pickup Location Dispatch
    pickup_location: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    google_maps_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    pickup_instructions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    estimated_pickup_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )

    # Lifecycle Status:
    # PENDING -> FARMER_CONFIRMED (or FARMER_REJECTED) -> CONFIRMED -> PREPARING -> READY_FOR_DELIVERY -> OUT_FOR_DELIVERY -> DELIVERED (or CANCELLED)
    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING",
        index=True,
        nullable=False
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Payment details
    payment_method: Mapped[str] = mapped_column(
        String(50),
        default="CASH_ON_DELIVERY",
        nullable=False
    )  # CASH_ON_DELIVERY, UPI, RAZORPAY, NET_BANKING
    payment_status: Mapped[str] = mapped_column(
        String(30),
        default="PENDING",
        nullable=False
    )  # PENDING, PAID, FAILED
    payment_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    payment_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Logistics & Delivery Dispatch
    driver_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    driver_name: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True
    )
    driver_contact: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    vehicle_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    tracking_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Soft Delete & Auditing
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
        CheckConstraint("requested_quantity > 0", name="chk_produce_procurement_qty_positive"),
        CheckConstraint("unit_price >= 0", name="chk_produce_procurement_unit_price_non_negative"),
        CheckConstraint("total_amount >= 0", name="chk_produce_procurement_total_non_negative"),
        Index("ix_produce_procurements_customer_created", "customer_id", "created_at"),
        Index("ix_produce_procurements_farmer_status", "farmer_profile_id", "status"),
    )

    # Relationships
    customer: Mapped["User"] = relationship("User", foreign_keys=[customer_id], lazy="joined")
    farmer_profile: Mapped["FarmerProfile"] = relationship("FarmerProfile", foreign_keys=[farmer_profile_id], lazy="joined")
    farm: Mapped[Optional["Farm"]] = relationship("Farm", foreign_keys=[farm_id], lazy="joined")
    crop: Mapped["Crop"] = relationship("Crop", foreign_keys=[crop_id], lazy="joined")
    cultivation: Mapped[Optional["CultivationRun"]] = relationship("CultivationRun", foreign_keys=[cultivation_id], lazy="joined")
    driver_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[driver_id], lazy="joined")

    def __repr__(self) -> str:
        return f"<ProduceProcurement(id={self.id}, code='{self.request_code}', product='{self.product_name}', qty={self.requested_quantity} {self.unit}, status='{self.status}')>"
