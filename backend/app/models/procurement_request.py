import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Date, Numeric, Text, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.farmer_profile import FarmerProfile
    from app.models.farm import Farm
    from app.models.input_master import InputMaster
    from app.models.supplier import Supplier


class ProcurementRequest(Base):
    __tablename__ = "procurement_requests"

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
    farmer_profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farmer_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    farm_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farms.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    input_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("input_masters.id", ondelete="RESTRICT"),
        index=True,
        nullable=False
    )
    preferred_supplier_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )
    unit: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )
    required_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="PENDING",
        index=True,
        nullable=False
    )

    # Soft-delete fields
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
    farm: Mapped["Farm"] = relationship("Farm", lazy="joined")
    input_item: Mapped["InputMaster"] = relationship("InputMaster", back_populates="procurement_requests", lazy="joined")
    preferred_supplier: Mapped[Optional["Supplier"]] = relationship("Supplier", back_populates="procurement_requests", lazy="joined")
