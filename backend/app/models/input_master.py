import uuid
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Text, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.procurement_request import ProcurementRequest


class InputMaster(Base):
    __tablename__ = "input_masters"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    input_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    input_name: Mapped[str] = mapped_column(
        String(150),
        index=True,
        nullable=False
    )
    category: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False
    )
    unit: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )
    technical_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True
    )
    brand_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
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
    procurement_requests: Mapped[List["ProcurementRequest"]] = relationship(
        "ProcurementRequest",
        back_populates="input_item",
        cascade="all, delete-orphan"
    )
