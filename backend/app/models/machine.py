import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Numeric, Text, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.farmer_profile import FarmerProfile


class Machine(Base):
    """
    Machine Master entity for Farmer CRM.
    Enables farmers to manage and assign owned or rented machinery (Tractor, Pump, Seeder, Harvester).
    """
    __tablename__ = "machines"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    farmer_profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farmer_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    machine_code: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False
    )
    machine_name: Mapped[str] = mapped_column(
        String(150),
        index=True,
        nullable=False
    )
    machine_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="TRACTOR"
    )
    ownership_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="OWNED"
    )
    owner_name: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True
    )
    owner_contact: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    rate_per_hour: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )
    rate_per_day: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )
    operator_included: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Status & Soft-delete fields
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
        nullable=False
    )
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

    def __repr__(self) -> str:
        return f"<Machine(id={self.id}, code='{self.machine_code}', name='{self.machine_name}', type='{self.machine_type}')>"
