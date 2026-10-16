import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Date, Numeric, Text, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.farmer_profile import FarmerProfile
    from app.models.cultivation import CultivationStage, CultivationRun
    from app.models.supplier import Supplier
    from app.models.bill import Bill


class MaterialPurchase(Base):
    """
    Material Purchase entity for Farmer CRM.
    Enables purchasing seeds, fertilizers, pesticides, and inputs directly from reusable suppliers with auto bill creation.
    """
    __tablename__ = "material_purchases"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    purchase_code: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False
    )
    farmer_profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farmer_profiles.id", ondelete="CASCADE"),
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
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    material_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="SEED"
    )
    material_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    unit: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="KG"
    )
    unit_rate: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )
    purchase_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today
    )
    payment_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING"
    )
    bill_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("bills.id", ondelete="SET NULL"),
        nullable=True,
        index=True
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
    supplier: Mapped["Supplier"] = relationship("Supplier", lazy="joined")
    cultivation: Mapped[Optional["CultivationRun"]] = relationship("CultivationRun", lazy="joined")
    stage: Mapped[Optional["CultivationStage"]] = relationship("CultivationStage", lazy="joined")
    bill: Mapped[Optional["Bill"]] = relationship("Bill", foreign_keys=[bill_id], lazy="joined")

    def __repr__(self) -> str:
        return f"<MaterialPurchase(id={self.id}, code='{self.purchase_code}', item='{self.material_name}', total={self.total_amount})>"
