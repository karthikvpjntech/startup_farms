import uuid
from datetime import datetime, timezone
from typing import Optional, List, Any, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Integer, Text, Uuid, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.crop import Crop


class CropCultivationStage(Base):
    """
    Represents an admin-configured master cultivation process stage for a specific crop.
    Used to dynamically drive 3D/interactive visualizations, timelines, and farming instructions.
    """
    __tablename__ = "crop_cultivation_stages"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    crop_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("crops.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    stage_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    stage_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )
    stage_name_local: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    duration_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=15
    )

    # Real media & visual archetype configuration
    image_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    thumbnail_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    visual_asset_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="VEGETATIVE"
    )
    visual_theme_color: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="#10b981"
    )

    # Recommendations & Task Guidance (JSON list of strings or activity objects)
    recommended_activities: Mapped[List[Any]] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )
    recommended_inputs: Mapped[List[Any]] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )

    # Status & Soft-delete
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

    # Timestamps & Audit
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
    crop: Mapped["Crop"] = relationship(
        "Crop",
        back_populates="cultivation_process_stages"
    )

    def __repr__(self) -> str:
        return f"<CropCultivationStage(id={self.id}, crop_id={self.crop_id}, order={self.stage_order}, name='{self.stage_name}')>"
