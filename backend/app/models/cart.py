import uuid
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import (
    DateTime,
    Integer,
    Uuid,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.livestock import Livestock
    from app.models.farm_selling_product import FarmSellingProduct


class Cart(Base):
    """
    Customer Shopping Cart Entity.
    Tied 1-to-1 to a User account.
    """
    __tablename__ = "carts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
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

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="joined")
    items: Mapped[List["CartItem"]] = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan",
        order_by="CartItem.created_at"
    )

    def __repr__(self) -> str:
        return f"<Cart(id={self.id}, user_id={self.user_id})>"


class CartItem(Base):
    """
    Item inside a customer's shopping cart referencing a live livestock record or farm produce record.
    """
    __tablename__ = "cart_items"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    cart_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    livestock_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("livestock.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    farm_product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farm_selling_products.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
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
        CheckConstraint("quantity >= 1", name="chk_cart_item_quantity_positive"),
        CheckConstraint(
            "(livestock_id IS NOT NULL AND farm_product_id IS NULL) OR (livestock_id IS NULL AND farm_product_id IS NOT NULL)",
            name="chk_cart_item_product_reference"
        ),
    )

    # Relationships
    cart: Mapped["Cart"] = relationship("Cart", back_populates="items")
    livestock: Mapped[Optional["Livestock"]] = relationship("Livestock", lazy="joined")
    farm_product: Mapped[Optional["FarmSellingProduct"]] = relationship("FarmSellingProduct", lazy="joined")

    def __repr__(self) -> str:
        return f"<CartItem(id={self.id}, cart_id={self.cart_id}, livestock_id={self.livestock_id}, farm_product_id={self.farm_product_id}, qty={self.quantity})>"

