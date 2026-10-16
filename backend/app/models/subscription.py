import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Numeric, Integer, Uuid, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class SubscriptionSetting(Base):
    """
    Global historical data access subscription configuration.
    Controlled by Super Admin to activate or deactivate subscription gate.
    """
    __tablename__ = "subscription_settings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    # Master switch: True = Subscription required for older data; False = Free access for all
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    # Number of days where data is free to view (e.g. 30 days = current month is free, older requires subscription)
    free_retention_days: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False
    )
    monthly_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("199.00"),
        nullable=False
    )
    annual_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("999.00"),
        nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        default="INR",
        nullable=False
    )
    title: Mapped[str] = mapped_column(
        String(200),
        default="Agri-Smart Farm Archive & Historical Data Pass",
        nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        default="Unlock unlimited historical farm records, past harvest cycles, multi-year expense analytics, worker logs, and PDF/Excel exports.",
        nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class UserSubscription(Base):
    """
    Individual user subscription pass granting access to historical/older farm data.
    """
    __tablename__ = "user_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    plan_type: Mapped[str] = mapped_column(
        String(50),
        default="MONTHLY",  # MONTHLY, ANNUAL, LIFETIME
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="ACTIVE",  # ACTIVE, EXPIRED, CANCELLED
        index=True,
        nullable=False
    )
    amount_paid: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        default="INR",
        nullable=False
    )
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    payment_method: Mapped[str] = mapped_column(
        String(50),
        default="RAZORPAY",  # RAZORPAY, UPI, CASH, ADMIN_GRANTED
        nullable=False
    )
    payment_reference: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
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

    # Relationship to user
    user: Mapped["User"] = relationship("User", backref="subscriptions")

    @property
    def is_currently_active(self) -> bool:
        now = datetime.now(timezone.utc)
        return self.status == "ACTIVE" and self.end_date >= now
