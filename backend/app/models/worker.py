import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Numeric, Text, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.farmer_profile import FarmerProfile
    from app.models.user import User


class Worker(Base):
    """
    Worker Master entity for Farmer CRM.
    Enables farmers to register, search, and reuse workers across any farm/crop/stage without duplication.
    """
    __tablename__ = "workers"

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
    worker_code: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False
    )
    full_name: Mapped[str] = mapped_column(
        String(150),
        index=True,
        nullable=False
    )
    mobile_number: Mapped[str] = mapped_column(
        String(20),
        index=True,
        nullable=False
    )
    gender: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="MALE"
    )
    skill: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="GENERAL_LABOR"
    )
    daily_salary: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    village: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    address: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    payment_preference: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="CASH"
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
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
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id], lazy="joined")

    def __repr__(self) -> str:
        return f"<Worker(id={self.id}, code='{self.worker_code}', name='{self.full_name}', skill='{self.skill}')>"
