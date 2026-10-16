import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Text, Uuid, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class PaymentWebhookLog(Base):
    """
    Audit log entity for inbound payment gateway webhooks (Razorpay, etc.).
    Guarantees webhook event idempotency, historical event traceability,
    and automatic recovery from client-side network dropouts.
    """
    __tablename__ = "payment_webhook_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    event_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False
    )
    event_type: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False
    )  # payment.captured, payment.failed, order.paid, refund.processed, subscription.charged
    signature: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    payload: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="PROCESSED",
        index=True,
        nullable=False
    )  # PROCESSED, FAILED, IGNORED, DUPLICATE, INVALID_SIGNATURE
    related_entity_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )  # MARKETPLACE_ORDER, SUBSCRIPTION, BILL, GENERAL
    related_entity_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        Index("ix_webhook_type_status_created", "event_type", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<PaymentWebhookLog(id={self.id}, event='{self.event_type}', status='{self.status}')>"
