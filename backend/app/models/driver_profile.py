import uuid
from datetime import datetime, date, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Date, DateTime, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class DriverProfile(Base):
    __tablename__ = "driver_profiles"

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
    license_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    license_expiry_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )
    address_line1: Mapped[Optional[str]] = mapped_column(
        String(255),
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

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="driver_profile")

    def __repr__(self) -> str:
        return f"<DriverProfile(id={self.id}, user_id={self.user_id}, license_number='{self.license_number}')>"
