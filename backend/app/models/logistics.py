import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Numeric, Text, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.farmer_profile import FarmerProfile
    from app.models.farm import Farm
    from app.models.cultivation import CultivationRun
    from app.models.user import User
    from app.models.bill import Bill


class Logistics(Base):
    """
    Harvest Logistics & Transport Dispatch entity.
    Tracks destination, vehicle, driver, load quantity, and shipping costs.
    """
    __tablename__ = "logistics"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    dispatch_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    farmer_profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farmer_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    cultivation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cultivation_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    farm_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farms.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    harvest_location: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    destination: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    pickup_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    delivery_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    vehicle_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    driver_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )
    driver_contact: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )
    driver_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    quantity_transported: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    quantity_unit: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="KG"
    )
    transport_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    loading_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    unloading_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    total_logistics_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PLANNED"
    )
    bill_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("bills.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    attachment_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )

    # Status & Soft-delete fields
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

    # Audit timestamps
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

    # Relationships
    farmer_profile: Mapped["FarmerProfile"] = relationship("FarmerProfile", lazy="joined")
    cultivation: Mapped["CultivationRun"] = relationship("CultivationRun", lazy="joined")
    farm: Mapped["Farm"] = relationship("Farm", lazy="joined")
    driver_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[driver_id], lazy="joined")
    bill: Mapped[Optional["Bill"]] = relationship("Bill", foreign_keys=[bill_id], lazy="joined")

    def __repr__(self) -> str:
        return f"<Logistics(id={self.id}, code='{self.dispatch_code}', dest='{self.destination}', total_cost={self.total_logistics_cost})>"
