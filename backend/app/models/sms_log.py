import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Text, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.farmer_profile import FarmerProfile


class SMSLog(Base):
    """
    SMS and Notification Log for Farmer CRM.
    Records delivery status (PENDING, SENT, FAILED) for worker wage confirmations, bill notifications, etc.
    """
    __tablename__ = "sms_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    farmer_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farmer_profiles.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    recipient_mobile: Mapped[str] = mapped_column(
        String(20),
        index=True,
        nullable=False
    )
    recipient_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )
    recipient_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="WORKER"
    )
    message_body: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    notification_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="WORK_COMPLETED_PAYMENT"
    )
    related_entity_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    related_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="SENT"
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    gateway_response: Mapped[Optional[str]] = mapped_column(
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
    farmer_profile: Mapped["FarmerProfile"] = relationship("FarmerProfile", lazy="joined")

    def __repr__(self) -> str:
        return f"<SMSLog(id={self.id}, recipient='{self.recipient_name}', status='{self.status}')>"
