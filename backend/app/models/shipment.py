import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Date,
    Numeric,
    Integer,
    Text,
    Uuid,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.farmer_profile import FarmerProfile
    from app.models.marketplace_order import MarketplaceOrder
    from app.models.transport_provider import TransportProvider
    from app.models.pickup_request import PickupRequest


class Shipment(Base):
    """
    Central fulfillment and logistics aggregate entity.
    Tracks packages from farm packing through hub milestones to customer doorstep.
    """
    __tablename__ = "shipments"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    shipment_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )  # e.g., SHP-20261002-00045
    tracking_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )  # e.g., AGRI2026100200045

    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("marketplace_orders.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    farmer_profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farmer_profiles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    transport_provider_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("transport_providers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    driver_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Progression Status & Current Location
    current_status: Mapped[str] = mapped_column(
        String(40),
        default="CREATED",
        index=True,
        nullable=False
    )  # CREATED, READY_FOR_PICKUP, PICKUP_ASSIGNED, PICKED_UP, AT_ORIGIN_HUB, IN_TRANSIT, AT_DESTINATION_HUB, OUT_FOR_DELIVERY, DELIVERED, DELIVERY_FAILED, RETURN_INITIATED, RETURN_IN_TRANSIT, RETURNED, CANCELLED
    current_location: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    # Origin & Pickup Details
    origin_address: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    origin_city: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    origin_pincode: Mapped[str] = mapped_column(
        String(10),
        nullable=False
    )

    # Destination & Customer Details
    destination_address: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    destination_city: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    destination_pincode: Mapped[str] = mapped_column(
        String(10),
        nullable=False
    )

    # Parcel & Handling Attributes
    total_packages: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )
    total_weight_kg: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("1.00"),
        nullable=False
    )
    is_perishable: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    special_handling: Mapped[str] = mapped_column(
        String(50),
        default="GENERAL",
        nullable=False
    )  # GENERAL, KEEP_COOL, KEEP_DRY, FRAGILE, PERISHABLE, LIVE_PLANT, DIRECT_FARM

    # Barcode & QR Code payload
    barcode_data: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    qr_code_data: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # Timeline Dates
    estimated_delivery_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )
    actual_delivery_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Audit Timestamps
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
    order: Mapped["MarketplaceOrder"] = relationship(
        "MarketplaceOrder",
        foreign_keys=[order_id],
        lazy="selectin"
    )
    farmer_profile: Mapped["FarmerProfile"] = relationship(
        "FarmerProfile",
        foreign_keys=[farmer_profile_id],
        lazy="selectin"
    )
    customer: Mapped["User"] = relationship(
        "User",
        foreign_keys=[customer_id],
        lazy="selectin"
    )
    transport_provider: Mapped[Optional["TransportProvider"]] = relationship(
        "TransportProvider",
        back_populates="shipments",
        lazy="selectin"
    )
    driver: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[driver_id],
        lazy="selectin"
    )

    packages: Mapped[List["ShipmentPackage"]] = relationship(
        "ShipmentPackage",
        back_populates="shipment",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ShipmentPackage.created_at"
    )
    tracking_events: Mapped[List["ShipmentTrackingEvent"]] = relationship(
        "ShipmentTrackingEvent",
        back_populates="shipment",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ShipmentTrackingEvent.event_timestamp"
    )
    pickup_requests: Mapped[List["PickupRequest"]] = relationship(
        "PickupRequest",
        back_populates="shipment",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    delivery_attempts: Mapped[List["DeliveryAttempt"]] = relationship(
        "DeliveryAttempt",
        back_populates="shipment",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="DeliveryAttempt.attempt_time"
    )

    def __repr__(self) -> str:
        return f"<Shipment(num='{self.shipment_number}', track='{self.tracking_number}', status='{self.current_status}')>"


class ShipmentPackage(Base):
    """
    Individual packaged item / parcel within a shipment.
    Supports multi-box or multi-crate shipments.
    """
    __tablename__ = "shipment_packages"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    shipment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("shipments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    package_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )  # e.g., PKG-20261002-00045-1
    package_barcode: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    item_description: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    weight_kg: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        default=Decimal("1.00"),
        nullable=False
    )
    package_type: Mapped[str] = mapped_column(
        String(50),
        default="CORRUGATED_CARTON",
        nullable=False
    )  # JUTE_BAG, PLASTIC_CRATE, WOODEN_BOX, CORRUGATED_CARTON, SACK, CAN, BUNDLE, OTHER

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    shipment: Mapped["Shipment"] = relationship(
        "Shipment",
        back_populates="packages"
    )

    def __repr__(self) -> str:
        return f"<ShipmentPackage(pkg='{self.package_number}', type='{self.package_type}', weight={self.weight_kg})>"


class ShipmentTrackingEvent(Base):
    """
    Immutable, append-only event ledger for all shipment milestone and status changes.
    """
    __tablename__ = "shipment_tracking_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    shipment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("shipments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        index=True
    )
    location_hub: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )  # e.g. "Agri-Smart Hub — Coimbatore South", "Salem Sorting Center"
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    updated_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    updated_by_role: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    event_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    shipment: Mapped["Shipment"] = relationship(
        "Shipment",
        back_populates="tracking_events"
    )
    updated_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[updated_by_user_id],
        lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<ShipmentTrackingEvent(status='{self.status}', location='{self.location_hub}', time='{self.event_timestamp}')>"


class DeliveryAttempt(Base):
    """
    Log of doorstep delivery tries, customer handoffs, or retry notes.
    """
    __tablename__ = "delivery_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    shipment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("shipments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    attempt_number: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )
    attempt_status: Mapped[str] = mapped_column(
        String(30),
        default="SUCCESS",
        nullable=False
    )  # SUCCESS, FAILED, RESCHEDULED
    failure_reason: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )  # CUSTOMER_UNAVAILABLE, INCORRECT_ADDRESS, CUSTOMER_REJECTED, PACKAGE_DAMAGED, TRANSPORT_ISSUE, WEATHER_DELAY, OTHER
    recipient_name: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True
    )
    recipient_signature_note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    driver_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    attempt_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    shipment: Mapped["Shipment"] = relationship(
        "Shipment",
        back_populates="delivery_attempts"
    )

    def __repr__(self) -> str:
        return f"<DeliveryAttempt(num={self.attempt_number}, status='{self.attempt_status}')>"
