import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Date, Numeric, Text, Uuid, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.farm import Farm
    from app.models.crop import Crop


class FarmCropPlan(Base):
    __tablename__ = "farm_crop_plans"
    __table_args__ = (
        CheckConstraint("planned_area > 0", name="chk_farm_crop_plans_planned_area"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    farm_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farms.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    crop_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("crops.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    season: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    planned_start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )
    planned_end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )
    planned_area: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    land_area_unit: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Seed Specifications & Per-Acre Rate Options
    seed_variety: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    seed_rate_per_acre: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )
    seed_rate_unit: Mapped[Optional[str]] = mapped_column(
        String(30),
        default="kg/acre",
        nullable=True
    )
    total_seed_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )
    sowing_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        default="DIRECT_SEEDING",
        nullable=True
    )
    seed_brand_or_source: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True
    )
    remind_next_year: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
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

    # Audit & Timestamps
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
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    farm: Mapped["Farm"] = relationship(
        "Farm",
        back_populates="farm_crop_plans"
    )
    crop: Mapped["Crop"] = relationship(
        "Crop",
        back_populates="farm_crop_plans"
    )

    def __repr__(self) -> str:
        return f"<FarmCropPlan(id={self.id}, farm_id={self.farm_id}, crop_id={self.crop_id}, season='{self.season}')>"
