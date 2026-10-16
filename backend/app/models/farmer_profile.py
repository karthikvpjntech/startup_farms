import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, DateTime, Numeric, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.farm import Farm


class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False
    )
    profile_image_url: Mapped[Optional[str]] = mapped_column(
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
    latitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(9, 6),
        nullable=True
    )
    longitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(9, 6),
        nullable=True
    )
    location_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )

    # Timestamps
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

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="farmer_profile")
    farms: Mapped[List["Farm"]] = relationship(
        "Farm",
        back_populates="farmer_profile",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<FarmerProfile(id={self.id}, user_id={self.user_id}, village='{self.village}', district='{self.district}')>"
