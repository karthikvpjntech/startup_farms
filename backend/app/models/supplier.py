import uuid
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Text, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.procurement_request import ProcurementRequest


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    supplier_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    supplier_name: Mapped[str] = mapped_column(
        String(150),
        index=True,
        nullable=False
    )
    contact_person: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    phone_number: Mapped[str] = mapped_column(
        String(20),
        index=True,
        nullable=False
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    address_line1: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    address_line2: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    village_city: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    district: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False
    )
    state: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False
    )
    pincode: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )
    gstin: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True
    )
    supplier_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="DISTRIBUTOR"
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
        back_populates="preferred_supplier"
    )
