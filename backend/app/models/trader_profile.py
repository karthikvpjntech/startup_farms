import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class TraderProfile(Base):
    __tablename__ = "trader_profiles"

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
    business_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    business_registration_number: Mapped[Optional[str]] = mapped_column(
        String(100),
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
    user: Mapped["User"] = relationship("User", back_populates="trader_profile")

    def __repr__(self) -> str:
        return f"<TraderProfile(id={self.id}, user_id={self.user_id}, business_name='{self.business_name}')>"
