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
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.farmer_profile import FarmerProfile
    from app.models.farm import Farm
    from app.models.user import User
    from app.models.marketplace_order import MarketplaceOrder, MarketplaceOrderItem


class LivestockCategory(Base):
    """
    Master Livestock Category (e.g., Chicken, Goat, Cow, Buffalo, Sheep, Duck, Turkey, Rabbit, Other).
    Supports Tamil & English naming and taxonomy hierarchy.
    """
    __tablename__ = "livestock_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    name_ta: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    icon_slug: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
        nullable=False
    )

    # Timestamps
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

    # Relationships
    breeds: Mapped[List["LivestockBreed"]] = relationship(
        "LivestockBreed",
        back_populates="category",
        cascade="all, delete-orphan",
        order_by="LivestockBreed.display_order"
    )
    livestock_items: Mapped[List["Livestock"]] = relationship(
        "Livestock",
        back_populates="category"
    )

    def __repr__(self) -> str:
        return f"<LivestockCategory(code='{self.code}', name='{self.name}')>"


class LivestockBreed(Base):
    """
    Master Livestock Breed classified under a Category (e.g., Boer, Kanni Adu, Kadaknath, Kangayam).
    """
    __tablename__ = "livestock_breeds"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("livestock_categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    code: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    name_ta: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    characteristics: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
        nullable=False
    )

    # Timestamps
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
        UniqueConstraint("category_id", "name", name="uq_livestock_breed_category_name"),
    )

    # Relationships
    category: Mapped["LivestockCategory"] = relationship(
        "LivestockCategory",
        back_populates="breeds"
    )
    livestock_items: Mapped[List["Livestock"]] = relationship(
        "Livestock",
        back_populates="breed"
    )

    def __repr__(self) -> str:
        return f"<LivestockBreed(id={self.id}, name='{self.name}', category_id={self.category_id})>"


class Livestock(Base):
    """
    Primary Livestock Entity.
    Supports Model A (Individual Animal) and Model B (Quantity-Based Batch/Flock).
    """
    __tablename__ = "livestock"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    livestock_code: Mapped[str] = mapped_column(
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
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("livestock_categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    breed_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("livestock_breeds.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    tag_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )
    selling_model: Mapped[str] = mapped_column(
        String(30),
        default="INDIVIDUAL",
        nullable=False
    )  # INDIVIDUAL or QUANTITY
    gender: Mapped[str] = mapped_column(
        String(30),
        default="UNKNOWN",
        nullable=False
    )
    date_of_birth: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )
    age: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(6, 2),
        nullable=True
    )
    age_unit: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    weight: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(8, 2),
        nullable=True
    )
    weight_unit: Mapped[Optional[str]] = mapped_column(
        String(20),
        default="KG",
        nullable=True
    )

    # Health & Vaccination
    health_status: Mapped[str] = mapped_column(
        String(50),
        default="HEALTHY",
        nullable=False
    )
    vaccination_status: Mapped[str] = mapped_column(
        String(50),
        default="UP_TO_DATE",
        nullable=False
    )
    vaccination_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )
    health_certificate_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )

    # Description & Custom Location
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    location_summary: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    # Pricing & Inventory
    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )
    price_type: Mapped[str] = mapped_column(
        String(30),
        default="PER_UNIT",
        nullable=False
    )
    available_quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )
    minimum_order_quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )
    maximum_order_quantity: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )

    # Lifecycle Status
    status: Mapped[str] = mapped_column(
        String(30),
        default="DRAFT",
        index=True,
        nullable=False
    )  # DRAFT, PUBLISHED, RESERVED, SOLD, UNAVAILABLE, ARCHIVED

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
        nullable=False
    )

    # Soft Delete
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

    # Audit Timestamps
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
        CheckConstraint("available_quantity >= 0", name="chk_livestock_avail_qty_non_negative"),
        CheckConstraint("price >= 0", name="chk_livestock_price_non_negative"),
        CheckConstraint("minimum_order_quantity >= 1", name="chk_livestock_min_order_qty_positive"),
        Index("ix_livestock_status_active_deleted", "status", "is_active", "is_deleted"),
        Index("ix_livestock_category_price", "category_id", "price"),
    )

    # Relationships
    farmer_profile: Mapped["FarmerProfile"] = relationship("FarmerProfile", lazy="joined")
    farm: Mapped["Farm"] = relationship("Farm", lazy="joined")
    category: Mapped["LivestockCategory"] = relationship("LivestockCategory", back_populates="livestock_items", lazy="joined")
    breed: Mapped[Optional["LivestockBreed"]] = relationship("LivestockBreed", back_populates="livestock_items", lazy="joined")
    images: Mapped[List["LivestockImage"]] = relationship(
        "LivestockImage",
        back_populates="livestock",
        cascade="all, delete-orphan",
        order_by="LivestockImage.display_order",
        lazy="joined"
    )
    reviews: Mapped[List["LivestockReview"]] = relationship(
        "LivestockReview",
        back_populates="livestock",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Livestock(id={self.id}, code='{self.livestock_code}', name='{self.name}', status='{self.status}', qty={self.available_quantity})>"


class LivestockImage(Base):
    """
    Multiple images per livestock listing (e.g. Main, Front, Side, Back, Face, Health Document).
    """
    __tablename__ = "livestock_images"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    livestock_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("livestock.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    image_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    image_type: Mapped[str] = mapped_column(
        String(30),
        default="MAIN",
        nullable=False
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    livestock: Mapped["Livestock"] = relationship("Livestock", back_populates="images")

    def __repr__(self) -> str:
        return f"<LivestockImage(id={self.id}, type='{self.image_type}', primary={self.is_primary})>"


class LivestockReview(Base):
    """
    Customer Review and Rating submitted for a completed, verified purchase.
    """
    __tablename__ = "livestock_reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    livestock_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("livestock.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("marketplace_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    review_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    is_verified_purchase: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
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
        CheckConstraint("rating >= 1 AND rating <= 5", name="chk_livestock_review_rating_1_to_5"),
        UniqueConstraint("order_id", "livestock_id", "customer_id", name="uq_livestock_review_order_item_customer"),
    )

    livestock: Mapped["Livestock"] = relationship("Livestock", back_populates="reviews")
    customer: Mapped["User"] = relationship("User", foreign_keys=[customer_id], lazy="joined")
    order: Mapped["MarketplaceOrder"] = relationship("MarketplaceOrder", back_populates="reviews")

    def __repr__(self) -> str:
        return f"<LivestockReview(id={self.id}, rating={self.rating}, customer_id={self.customer_id})>"
