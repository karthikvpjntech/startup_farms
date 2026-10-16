import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Date,
    Numeric,
    Integer,
    Text,
    Uuid,
    ForeignKey,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.farmer_profile import FarmerProfile
    from app.models.farm import Farm
    from app.models.cart import CartItem
    from app.models.marketplace_order import MarketplaceOrderItem


class FarmSellingProduct(Base):
    """
    Farmer Selling Farm Product Entity.
    Allows farmers to list and sell fresh farm-harvested produce such as:
    Mango (Panna, etc.), Sapota, Coconut, Lemon, Murungakkai (Drumstick),
    Mathulai (Pomegranate), Guava, Banana, Paddy/Nel (Aman Ponni), and other fruits & vegetables.
    """
    __tablename__ = "farm_selling_products"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    farmer_profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farmer_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    farm_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farms.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Basic Information
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )  # FRUITS, VEGETABLES, COCONUT, GRAINS_PADDY, OTHER
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )  # Mango, Sapota, Lemon, Drumstick, Pomegranate, etc.
    variety: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True
    )  # Panna, Banganapalli, Alphonso, PKM-1, Aman Ponni, etc.
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    primary_image: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    # Pricing & Units
    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )
    price_unit: Mapped[str] = mapped_column(
        String(30),
        default="Kg",
        nullable=False
    )  # Kg, Gram, Quintal, Piece, Dozen, Bundle, Litre, Bag, Other
    unit: Mapped[str] = mapped_column(
        String(30),
        default="Kg",
        nullable=False
    )  # Kg, Gram, Quintal, Piece, Dozen, Bundle, Litre, Bag, Other

    # Inventory Quantities
    available_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    minimum_order_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("1.00"),
        nullable=False
    )

    # Harvest Date & Freshness
    harvest_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )

    # Purchase & Settlement Options
    delivery_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    cod_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    online_payment_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    direct_pickup_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Status: ACTIVE, INACTIVE, OUT_OF_STOCK
    status: Mapped[str] = mapped_column(
        String(30),
        default="ACTIVE",
        index=True,
        nullable=False
    )

    # Soft Delete & Audit
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

    __table_args__ = (
        CheckConstraint("price >= 0", name="chk_farm_selling_product_price_non_negative"),
        CheckConstraint("available_quantity >= 0", name="chk_farm_selling_product_qty_non_negative"),
        CheckConstraint("minimum_order_quantity > 0", name="chk_farm_selling_product_min_order_positive"),
        Index("ix_farm_selling_products_active_lookup", "is_deleted", "status", "category"),
    )

    # Relationships
    farmer_profile: Mapped["FarmerProfile"] = relationship("FarmerProfile", lazy="joined")
    farm: Mapped[Optional["Farm"]] = relationship("Farm", lazy="joined")
    images: Mapped[List["FarmSellingProductImage"]] = relationship(
        "FarmSellingProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="FarmSellingProductImage.display_order",
        lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<FarmSellingProduct(id={self.id}, name='{self.name}', variety='{self.variety}', price={self.price}, status='{self.status}')>"


class FarmSellingProductImage(Base):
    """
    Supporting multi-image gallery record for Farm Selling Products.
    """
    __tablename__ = "farm_selling_product_images"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farm_selling_products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    image_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    product: Mapped["FarmSellingProduct"] = relationship("FarmSellingProduct", back_populates="images")

    def __repr__(self) -> str:
        return f"<FarmSellingProductImage(id={self.id}, product_id={self.product_id}, is_primary={self.is_primary})>"
