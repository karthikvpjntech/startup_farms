import uuid
from datetime import datetime, date, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, Date, Text, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.farmer_profile import FarmerProfile
    from app.models.shipment import Shipment


class PickupRequest(Base):
    """
    Farmer dispatch & logistics pickup scheduling entity.
    Coordinates driver arrival at farm parcel with scheduled time window.
    """
    __tablename__ = "pickup_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    pickup_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )  # e.g., PKP-20261002-00012

    shipment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("shipments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    farmer_profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farmer_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    pickup_address: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    pickup_contact_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )
    pickup_contact_phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    scheduled_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )
    time_window: Mapped[str] = mapped_column(
        String(50),
        default="MORNING_7_11",
        nullable=False
    )  # MORNING_7_11, AFTERNOON_12_4, EVENING_4_8, ANYTIME

    status: Mapped[str] = mapped_column(
        String(30),
        default="PENDING",
        index=True,
        nullable=False
    )  # PENDING, ASSIGNED, COMPLETED, CANCELLED

    assigned_driver_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    assigned_vehicle_number: Mapped[Optional[str]] = mapped_column(
        String(50),
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
    shipment: Mapped["Shipment"] = relationship(
        "Shipment",
        back_populates="pickup_requests"
    )
    farmer_profile: Mapped["FarmerProfile"] = relationship(
        "FarmerProfile",
        foreign_keys=[farmer_profile_id],
        lazy="joined"
    )
    assigned_driver: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assigned_driver_id],
        lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<PickupRequest(code='{self.pickup_code}', status='{self.status}', date={self.scheduled_date})>"
