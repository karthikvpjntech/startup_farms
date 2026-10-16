import uuid
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user_role import UserRole
    from app.models.farmer_profile import FarmerProfile
    from app.models.trader_profile import TraderProfile
    from app.models.driver_profile import DriverProfile
    from app.models.worker_profile import WorkerProfile


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    mobile_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=True
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
        nullable=False
    )
    # Two-Factor Authentication (2FA OTP)
    is_two_factor_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    two_factor_method: Mapped[str] = mapped_column(
        String(20),
        default="EMAIL",
        nullable=False
    )

    # Soft delete foundation
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
        nullable=True
    )

    # Audit foundation
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
        nullable=True
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True
    )

    # Relationships
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    farmer_profile: Mapped[Optional["FarmerProfile"]] = relationship(
        "FarmerProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    trader_profile: Mapped[Optional["TraderProfile"]] = relationship(
        "TraderProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    driver_profile: Mapped[Optional["DriverProfile"]] = relationship(
        "DriverProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    worker_profile: Mapped[Optional["WorkerProfile"]] = relationship(
        "WorkerProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, mobile_number='{self.mobile_number}', full_name='{self.full_name}')>"
