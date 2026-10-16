import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Date, Numeric, Text, Integer, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.cultivation import CultivationRun


class CultivationSchedule(Base):
    """
    Cultivation Schedule entity for Farmer CRM.
    Enables farmers to plan stage timeline schedules before and during work execution.
    """
    __tablename__ = "cultivation_schedules"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    cultivation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cultivation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    stage_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    stage_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )
    planned_start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )
    planned_end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )
    estimated_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PLANNED"
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
    cultivation: Mapped["CultivationRun"] = relationship("CultivationRun", lazy="joined")

    def __repr__(self) -> str:
        return f"<CultivationSchedule(id={self.id}, stage='{self.stage_name}', start={self.planned_start_date}, end={self.planned_end_date})>"
