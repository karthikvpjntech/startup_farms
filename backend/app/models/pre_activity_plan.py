import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Any, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Numeric, Text, Uuid, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.cultivation import CultivationRun, CultivationStage


class PreActivityPlan(Base):
    """
    Represents a pre-activity plan and requirements checklist created before starting a stage task.
    Enables farmers to specify the purpose (நோக்கம்), machinery needs (டிராக்டர்/மாட்டு உழவு),
    input materials (எரு/உரம்/பூச்சிக்கொல்லி), and labor requirements, with estimated budgets
    and 1-click conversion to actual stage expense ledgers.
    """
    __tablename__ = "pre_activity_plans"

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

    # Activity Identification & Purpose
    activity_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )
    activity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="TILLAGE"  # TILLAGE, SOWING, WEEDING, FERTILIZATION, SPRAYING, HARVESTING, OTHER
    )
    purpose: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # Machinery Configuration & Estimates
    machinery_mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="NONE"  # OWN_TRACTOR, RENTAL_TRACTOR, BULL_CART, MANUAL, NONE
    )
    machinery_details: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict
    )

    # Materials & Manure Needs (list of {item_name, quantity, unit, unit_cost, total_cost})
    materials_details: Mapped[List[Any]] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )

    # Labor / Crew Requirements ({estimated_workers, wage_per_head, total_labor_cost, notes})
    labor_details: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict
    )

    # Financial & Conversion Metrics
    estimated_total_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PLANNED"  # PLANNED, IN_PROGRESS, COMPLETED, CANCELLED
    )
    actual_converted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    converted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Soft-delete & Audit fields
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

    # Relationships
    stage: Mapped["CultivationStage"] = relationship(
        "CultivationStage",
        back_populates="pre_activity_plans"
    )
    cultivation: Mapped["CultivationRun"] = relationship(
        "CultivationRun",
        back_populates="pre_activity_plans"
    )

    def __repr__(self) -> str:
        return f"<PreActivityPlan(id={self.id}, name='{self.activity_name}', purpose='{self.purpose[:30]}', cost={self.estimated_total_cost})>"
