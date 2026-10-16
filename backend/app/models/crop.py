import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Text, Uuid, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.farm_crop_plan import FarmCropPlan
    from app.models.crop_stage import CropCultivationStage


class Crop(Base):
    __tablename__ = "crops"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    crop_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    crop_name_local: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True
    )
    local_names: Mapped[Dict[str, str]] = mapped_column(
        JSON,
        nullable=False,
        default=dict
    )
    image_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    crop_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    scientific_name: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True
    )
    crop_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
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
    farm_crop_plans: Mapped[List["FarmCropPlan"]] = relationship(
        "FarmCropPlan",
        back_populates="crop"
    )
    cultivation_process_stages: Mapped[List["CropCultivationStage"]] = relationship(
        "CropCultivationStage",
        back_populates="crop",
        cascade="all, delete-orphan",
        order_by="CropCultivationStage.stage_order"
    )

    def __repr__(self) -> str:
        return f"<Crop(id={self.id}, crop_code='{self.crop_code}', crop_name='{self.crop_name}', crop_category='{self.crop_category}')>"
