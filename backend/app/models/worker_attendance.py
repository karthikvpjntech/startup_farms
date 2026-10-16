import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Date, Numeric, Text, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.cultivation import CultivationStage, CultivationRun
    from app.models.worker import Worker
    from app.models.bill import Bill


class WorkerAttendance(Base):
    """
    Worker Attendance and Labor Log for Cultivation Stages.
    Tracks work date, start/end times, working days, daily wage, overtime, calculated total salary, and payment linkage.
    """
    __tablename__ = "worker_attendance"

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
    worker_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    work_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today
    )
    start_time: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    end_time: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    break_hours: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    total_hours: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("8.00")
    )
    working_days: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        default=Decimal("1.00")
    )
    daily_salary: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    overtime_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    calculated_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )
    payment_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING"
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
    worker: Mapped["Worker"] = relationship("Worker", lazy="joined")
    stage: Mapped["CultivationStage"] = relationship("CultivationStage", lazy="joined")
    cultivation: Mapped["CultivationRun"] = relationship("CultivationRun", lazy="joined")
    bill: Mapped[Optional["Bill"]] = relationship("Bill", foreign_keys=[bill_id], lazy="joined")

    def __repr__(self) -> str:
        return f"<WorkerAttendance(id={self.id}, worker_id={self.worker_id}, days={self.working_days}, amount={self.calculated_amount})>"
