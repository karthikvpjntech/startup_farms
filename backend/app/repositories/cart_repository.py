import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.cart import Cart, CartItem


class CartRepository:
    """Repository handling customer shopping cart persistence."""

    @staticmethod
    def get_or_create_cart(db: Session, user_id: uuid.UUID) -> Cart:
        cart = db.scalar(select(Cart).where(Cart.user_id == user_id))
        if not cart:
            cart = Cart(
                id=uuid.uuid4(),
                user_id=user_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(cart)
            db.commit()
            db.refresh(cart)
        return cart

    @staticmethod
    def get_cart_by_user_id(db: Session, user_id: uuid.UUID) -> Optional[Cart]:
        return db.scalar(select(Cart).where(Cart.user_id == user_id))

    @staticmethod
    def get_cart_item(db: Session, cart_id: uuid.UUID, item_id: uuid.UUID) -> Optional[CartItem]:
        return db.scalar(
            select(CartItem).where(
                CartItem.id == item_id,
                CartItem.cart_id == cart_id
            )
        )

    @staticmethod
    def get_cart_item_by_livestock_id(db: Session, cart_id: uuid.UUID, livestock_id: uuid.UUID) -> Optional[CartItem]:
        return db.scalar(
            select(CartItem).where(
                CartItem.cart_id == cart_id,
                CartItem.livestock_id == livestock_id
            )
        )

    @staticmethod
    def get_cart_item_by_farm_product_id(db: Session, cart_id: uuid.UUID, farm_product_id: uuid.UUID) -> Optional[CartItem]:
        return db.scalar(
            select(CartItem).where(
                CartItem.cart_id == cart_id,
                CartItem.farm_product_id == farm_product_id
            )
        )

    @staticmethod
    def add_or_update_item(
        db: Session,
        cart_id: uuid.UUID,
        quantity: int,
        livestock_id: Optional[uuid.UUID] = None,
        farm_product_id: Optional[uuid.UUID] = None,
    ) -> CartItem:
        if farm_product_id:
            item = CartRepository.get_cart_item_by_farm_product_id(db, cart_id, farm_product_id)
        else:
            item = CartRepository.get_cart_item_by_livestock_id(db, cart_id, livestock_id)

        now = datetime.now(timezone.utc)
        if item:
            item.quantity = quantity
            item.updated_at = now
        else:
            item = CartItem(
                id=uuid.uuid4(),
                cart_id=cart_id,
                livestock_id=livestock_id,
                farm_product_id=farm_product_id,
                quantity=quantity,
                created_at=now,
                updated_at=now
            )
            db.add(item)

        # Touch cart updated_at
        cart = db.scalar(select(Cart).where(Cart.id == cart_id))
        if cart:
            cart.updated_at = now

        db.commit()
        db.refresh(item)
        return item


    @staticmethod
    def update_item_quantity(db: Session, item: CartItem, quantity: int) -> CartItem:
        now = datetime.now(timezone.utc)
        item.quantity = quantity
        item.updated_at = now
        cart = db.scalar(select(Cart).where(Cart.id == item.cart_id))
        if cart:
            cart.updated_at = now
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def remove_item(db: Session, item: CartItem) -> None:
        cart_id = item.cart_id
        db.delete(item)
        now = datetime.now(timezone.utc)
        cart = db.scalar(select(Cart).where(Cart.id == cart_id))
        if cart:
            cart.updated_at = now
        db.commit()

    @staticmethod
    def clear_cart(db: Session, cart_id: uuid.UUID) -> None:
        db.query(CartItem).filter(CartItem.cart_id == cart_id).delete()
        now = datetime.now(timezone.utc)
        cart = db.scalar(select(Cart).where(Cart.id == cart_id))
        if cart:
            cart.updated_at = now
        db.commit()
