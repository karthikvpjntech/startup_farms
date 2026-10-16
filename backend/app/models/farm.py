import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Numeric, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.farmer_profile import FarmerProfile
    from app.models.farm_crop_plan import FarmCropPlan



class Farm(Base):
    __tablename__ = "farms"

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
    farm_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    farm_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    ownership_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    total_land_area: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False
    )
    land_area_unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    # Location & Survey fields
    survey_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )
    survey_link: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    address_line1: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    address_line2: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    village: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    district: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    state: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    pincode: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True
    )

    # Optional geographic coordinates
    latitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(9, 6),
        nullable=True
    )
    longitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(9, 6),
        nullable=True
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
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True
    )

    # Relationships
    farmer_profile: Mapped["FarmerProfile"] = relationship(
        "FarmerProfile",
        back_populates="farms"
    )
    farm_crop_plans: Mapped[List["FarmCropPlan"]] = relationship(
        "FarmCropPlan",
        back_populates="farm",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Farm(id={self.id}, farm_code='{self.farm_code}', farm_name='{self.farm_name}', farmer_profile_id={self.farmer_profile_id})>"
