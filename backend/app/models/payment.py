import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Numeric, Text, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.farmer_profile import FarmerProfile
    from app.models.bill import Bill


class Payment(Base):
    """
    Payment Settlement entity for Farm Bills.
    Supports UPI, NET_BANKING, and CASH settlement with safe metadata logging.
    """
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    payment_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    bill_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("bills.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    farmer_profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farmer_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )
    payment_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="CASH"
    )
    payment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PAID"
    )
    transaction_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    attachment_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )

    # Status & Soft-delete fields
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
    bill: Mapped["Bill"] = relationship("Bill", back_populates="payments")
    farmer_profile: Mapped["FarmerProfile"] = relationship("FarmerProfile", lazy="joined")

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, number='{self.payment_number}', amount={self.amount}, method='{self.payment_method}')>"
