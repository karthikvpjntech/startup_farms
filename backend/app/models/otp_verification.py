import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Integer, Uuid, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class OtpVerification(Base):
    """
    Cryptographically hashed OTP verification entity supporting:
    - 2FA (Two-Factor Authentication) login verification
    - Self-service Password Reset verification
    - Passwordless OTP login & Mobile verification
    """
    __tablename__ = "otp_verifications"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    identifier: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False
    )
    otp_code_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    otp_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="TWO_FACTOR_AUTH"
    )  # TWO_FACTOR_AUTH, PASSWORD_RESET, LOGIN_OTP, SETUP_2FA, PHONE_VERIFY
    session_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    is_used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    max_attempts: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False
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

    __table_args__ = (
        Index("ix_otp_identifier_type_active", "identifier", "otp_type", "is_used"),
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", lazy="joined")

    @property
    def is_expired(self) -> bool:
        now = datetime.now(timezone.utc)
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return now > exp

    @property
    def is_locked(self) -> bool:
        return self.attempts >= self.max_attempts

    def __repr__(self) -> str:
        return f"<OtpVerification(id={self.id}, identifier='{self.identifier}', type='{self.otp_type}', is_used={self.is_used})>"
