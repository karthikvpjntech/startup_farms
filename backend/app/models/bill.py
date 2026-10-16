import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Date, Numeric, Text, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.farmer_profile import FarmerProfile
    from app.models.farm import Farm
    from app.models.cultivation import CultivationRun, CultivationStage
    from app.models.worker import Worker
    from app.models.supplier import Supplier
    from app.models.payment import Payment


class Bill(Base):
    """
    Unified Farm Operations Bill entity.
    Represents bills for Worker Payments, Machine Costs, Material Purchases, Logistics, or Consolidated Stages.
    """
    __tablename__ = "bills"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    bill_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    farmer_profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farmer_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    farm_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farms.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    cultivation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cultivation_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    stage_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cultivation_stages.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    bill_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="STAGE_CONSOLIDATED"
    )
    recipient_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )
    recipient_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="CONSOLIDATED"
    )
    recipient_worker_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    recipient_supplier_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    bill_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today
    )
    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    pending_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING"
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
    farmer_profile: Mapped["FarmerProfile"] = relationship("FarmerProfile", lazy="joined")
    farm: Mapped["Farm"] = relationship("Farm", lazy="joined")
    cultivation: Mapped[Optional["CultivationRun"]] = relationship("CultivationRun", lazy="joined")
    stage: Mapped[Optional["CultivationStage"]] = relationship("CultivationStage", lazy="joined")
    worker: Mapped[Optional["Worker"]] = relationship("Worker", foreign_keys=[recipient_worker_id], lazy="joined")
    supplier: Mapped[Optional["Supplier"]] = relationship("Supplier", foreign_keys=[recipient_supplier_id], lazy="joined")
    items: Mapped[List["BillItem"]] = relationship("BillItem", back_populates="bill", cascade="all, delete-orphan", lazy="selectin")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="bill", cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Bill(id={self.id}, number='{self.bill_number}', total={self.total_amount}, status='{self.status}')>"


class BillItem(Base):
    """
    Line Item for Farm Operations Bill.
    """
    __tablename__ = "bill_items"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    bill_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("bills.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    item_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="LABOR"
    )
    item_description: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("1.00")
    )
    unit: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="UNIT"
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    total_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    # Relationship
    bill: Mapped["Bill"] = relationship("Bill", back_populates="items")

    def __repr__(self) -> str:
        return f"<BillItem(id={self.id}, desc='{self.item_description}', total={self.total_price})>"
