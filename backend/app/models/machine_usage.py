import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Date, Numeric, Text, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.cultivation import CultivationStage, CultivationRun
    from app.models.machine import Machine
    from app.models.bill import Bill


class MachineUsage(Base):
    """
    Machine Usage Log for Cultivation Stages.
    Tracks machine usage duration (hours/days), rates, fuel/operator costs, and payment linkage.
    """
    __tablename__ = "machine_usages"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    stage_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cultivation_stages.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    cultivation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cultivation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    machine_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("machines.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    usage_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today
    )
    hours_used: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    days_used: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    rate_applied: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    fuel_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    operator_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
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
    machine: Mapped["Machine"] = relationship("Machine", lazy="joined")
    stage: Mapped["CultivationStage"] = relationship("CultivationStage", lazy="joined")
    cultivation: Mapped["CultivationRun"] = relationship("CultivationRun", lazy="joined")
    bill: Mapped[Optional["Bill"]] = relationship("Bill", foreign_keys=[bill_id], lazy="joined")

    def __repr__(self) -> str:
        return f"<MachineUsage(id={self.id}, machine_id={self.machine_id}, total_cost={self.total_cost})>"
