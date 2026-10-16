import logging
import uuid
from decimal import Decimal
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.enums import LivestockSellingModel, LivestockStatus
from app.schemas.cart import (
    CartResponse,
    CartItemResponse,
    CartItemAddRequest,
    CartItemUpdateRequest,
)
from app.repositories.cart_repository import CartRepository
from app.repositories.livestock_repository import LivestockRepository
from app.repositories.farm_selling_product_repository import FarmSellingProductRepository

logger = logging.getLogger("agri_smart.cart_service")


class CartService:
    """Business service handling customer shopping cart calculations and live inventory validation."""

    @staticmethod
    def get_cart_response(db: Session, current_user: User) -> CartResponse:
        cart = CartRepository.get_or_create_cart(db, current_user.id)

        item_responses: List[CartItemResponse] = []
        subtotal = Decimal("0.00")
        total_items_count = 0
        has_unavailable = False

        for item in cart.items:
            if item.farm_product_id:
                # Farm selling produce product
                prod = FarmSellingProductRepository.get_by_id(db, item.farm_product_id)
                if not prod or prod.is_deleted:
                    is_avail = False
                    unit_price = Decimal("0.00")
                    item_total = Decimal("0.00")
                    has_unavailable = True
                    name = "Unavailable Product"
                    cat_name = "N/A"
                    primary_img = None
                    avail_qty = Decimal("0.00")
                    f_id = uuid.uuid4()
                    farm_id = None
                    farm_name = "N/A"
                    loc = None
                    item_status = "UNAVAILABLE"
                    unit = "Kg"
                    variety = None
                else:
                    is_avail = (
                        prod.status == "ACTIVE" and
                        prod.available_quantity >= item.quantity
                    )
                    if not is_avail:
                        has_unavailable = True

                    unit_price = prod.price
                    item_total = unit_price * item.quantity
                    subtotal += item_total
                    total_items_count += item.quantity

                    name = prod.name
                    cat_name = prod.category
                    variety = prod.variety
                    unit = prod.unit
                    primary_img = prod.primary_image
                    avail_qty = prod.available_quantity
                    f_id = prod.farmer_profile_id
                    farm_id = prod.farm_id
                    farm_name = prod.farm.farm_name if prod.farm else ""
                    if prod.farmer_profile:
                        loc = f"{prod.farmer_profile.village or ''}, {prod.farmer_profile.district or ''}".strip(", ")
                    else:
                        loc = None
                    item_status = prod.status

                item_resp = CartItemResponse(
                    id=item.id,
                    cart_id=cart.id,
                    product_type="FARM_PRODUCT",
                    farm_product_id=item.farm_product_id,
                    livestock_id=None,
                    quantity=item.quantity,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                    product_name=name,
                    category_name=cat_name,
                    variety_name=variety,
                    unit=unit,
                    unit_price=unit_price,
                    item_total=item_total,
                    primary_image_url=primary_img,
                    available_quantity=avail_qty,
                    is_available=is_avail,
                    status=item_status,
                    farmer_profile_id=f_id,
                    farm_id=farm_id,
                    farm_name=farm_name,
                    location_summary=loc
                )
                item_responses.append(item_resp)

            else:
                # Livestock item
                livestock = LivestockRepository.get_by_id(db, item.livestock_id)
                if not livestock or livestock.is_deleted or not livestock.is_active:
                    is_avail = False
                    unit_price = Decimal("0.00")
                    item_total = Decimal("0.00")
                    has_unavailable = True
                    name = "Unavailable Livestock"
                    code = "N/A"
                    cat_name = "N/A"
                    breed_name = None
                    tag_num = None
                    selling_model = "UNKNOWN"
                    primary_img = None
                    avail_qty = Decimal("0.00")
                    f_id = uuid.uuid4()
                    farm_id = uuid.uuid4()
                    farm_name = "N/A"
                    loc = None
                    item_status = "UNAVAILABLE"
                else:
                    is_avail = (
                        livestock.status == LivestockStatus.PUBLISHED.value and
                        livestock.available_quantity >= item.quantity
                    )
                    if not is_avail:
                        has_unavailable = True

                    unit_price = livestock.price
                    item_total = unit_price * item.quantity
                    subtotal += item_total
                    total_items_count += item.quantity

                    name = livestock.name
                    code = livestock.livestock_code
                    cat_name = livestock.category.name if livestock.category else ""
                    breed_name = livestock.breed.name if livestock.breed else None
                    tag_num = livestock.tag_number
                    selling_model = livestock.selling_model
                    primary_img = next((img.image_url for img in livestock.images if img.is_primary), None)
                    if not primary_img and livestock.images:
                        primary_img = livestock.images[0].image_url
                    avail_qty = Decimal(str(livestock.available_quantity))
                    f_id = livestock.farmer_profile_id
                    farm_id = livestock.farm_id
                    farm_name = livestock.farm.farm_name if livestock.farm else ""
                    loc = livestock.location_summary or (f"{livestock.farm.village}, {livestock.farm.district}" if livestock.farm else None)
                    item_status = livestock.status

                item_resp = CartItemResponse(
                    id=item.id,
                    cart_id=cart.id,
                    product_type="LIVESTOCK",
                    livestock_id=item.livestock_id,
                    farm_product_id=None,
                    quantity=item.quantity,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                    product_name=name,
                    livestock_code=code if 'code' in locals() else None,
                    livestock_name=name,
                    category_name=cat_name,
                    breed_name=breed_name if 'breed_name' in locals() else None,
                    tag_number=tag_num if 'tag_num' in locals() else None,
                    selling_model=selling_model if 'selling_model' in locals() else None,
                    unit_price=unit_price,
                    item_total=item_total,
                    primary_image_url=primary_img,
                    available_quantity=avail_qty,
                    is_available=is_avail,
                    status=item_status,
                    farmer_profile_id=f_id,
                    farm_id=farm_id,
                    farm_name=farm_name,
                    location_summary=loc
                )
                item_responses.append(item_resp)

        delivery_est = Decimal("0.00")
        tax_est = Decimal("0.00")
        total_est = subtotal + delivery_est + tax_est

        return CartResponse(
            id=cart.id,
            user_id=cart.user_id,
            items=item_responses,
            total_items_count=total_items_count,
            subtotal_amount=subtotal,
            estimated_delivery_charge=delivery_est,
            estimated_tax_amount=tax_est,
            estimated_total_amount=total_est,
            has_unavailable_items=has_unavailable,
            updated_at=cart.updated_at,
        )

    @staticmethod
    def add_to_cart(db: Session, current_user: User, request: CartItemAddRequest) -> CartResponse:
        cart = CartRepository.get_or_create_cart(db, current_user.id)

        if request.farm_product_id:
            prod = FarmSellingProductRepository.get_by_id(db, request.farm_product_id)
            if not prod or prod.is_deleted:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm product not found.")

            if prod.status != "ACTIVE":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Product is currently out of stock or inactive."
                )

            if prod.available_quantity < request.quantity:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Only {prod.available_quantity} {prod.unit} available in stock."
                )

            CartRepository.add_or_update_item(
                db=db,
                cart_id=cart.id,
                quantity=request.quantity,
                farm_product_id=prod.id
            )
            logger.info("User %s added farm product %s (%s) to cart", current_user.id, prod.name, prod.id)
            return CartService.get_cart_response(db, current_user)

        elif request.livestock_id:
            livestock = LivestockRepository.get_by_id(db, request.livestock_id)
            if not livestock or livestock.is_deleted or not livestock.is_active:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livestock not found.")

            if livestock.status != LivestockStatus.PUBLISHED.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Livestock is not currently published for sale."
                )

            if livestock.selling_model == LivestockSellingModel.INDIVIDUAL.value:
                if request.quantity != 1:
                    request.quantity = 1

            if livestock.available_quantity < request.quantity:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Only {livestock.available_quantity} available in stock."
                )

            CartRepository.add_or_update_item(
                db=db,
                cart_id=cart.id,
                quantity=request.quantity,
                livestock_id=livestock.id
            )
            logger.info("User %s added livestock %s to cart", current_user.id, livestock.livestock_code)
            return CartService.get_cart_response(db, current_user)

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either farm_product_id or livestock_id must be provided."
            )

    @staticmethod
    def update_cart_item(db: Session, current_user: User, item_id: uuid.UUID, request: CartItemUpdateRequest) -> CartResponse:
        cart = CartRepository.get_cart_by_user_id(db, current_user.id)
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found.")

        item = CartRepository.get_cart_item(db, cart.id, item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found.")

        if item.farm_product_id:
            prod = FarmSellingProductRepository.get_by_id(db, item.farm_product_id)
            if prod:
                if prod.available_quantity < request.quantity:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Only {prod.available_quantity} {prod.unit} available in stock."
                    )
        elif item.livestock_id:
            livestock = LivestockRepository.get_by_id(db, item.livestock_id)
            if livestock:
                if livestock.selling_model == LivestockSellingModel.INDIVIDUAL.value and request.quantity > 1:
                    request.quantity = 1
                if livestock.available_quantity < request.quantity:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Only {livestock.available_quantity} available in stock."
                    )

        CartRepository.update_item_quantity(db, item, request.quantity)
        return CartService.get_cart_response(db, current_user)

    @staticmethod
    def remove_cart_item(db: Session, current_user: User, item_id: uuid.UUID) -> CartResponse:
        cart = CartRepository.get_cart_by_user_id(db, current_user.id)
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found.")

        item = CartRepository.get_cart_item(db, cart.id, item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found.")

        CartRepository.remove_item(db, item)
        return CartService.get_cart_response(db, current_user)

    @staticmethod
    def clear_cart(db: Session, current_user: User) -> CartResponse:
        cart = CartRepository.get_cart_by_user_id(db, current_user.id)
        if cart:
            CartRepository.clear_cart(db, cart.id)
        return CartService.get_cart_response(db, current_user)
