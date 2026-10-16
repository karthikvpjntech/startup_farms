import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.cart import (
    CartResponse,
    CartItemAddRequest,
    CartItemUpdateRequest,
)
from app.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["Customer Shopping Cart"])


@router.get(
    "",
    response_model=CartResponse,
    summary="Get Current User's Cart"
)
def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return CartService.get_cart_response(db=db, current_user=current_user)


@router.post(
    "/items",
    response_model=CartResponse,
    status_code=status.HTTP_200_OK,
    summary="Add Livestock Item to Cart"
)
def add_item_to_cart(
    request: CartItemAddRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return CartService.add_to_cart(db=db, current_user=current_user, request=request)


@router.put(
    "/items/{item_id}",
    response_model=CartResponse,
    summary="Update Cart Item Quantity"
)
def update_cart_item(
    item_id: uuid.UUID,
    request: CartItemUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return CartService.update_cart_item(
        db=db,
        current_user=current_user,
        item_id=item_id,
        request=request
    )


@router.delete(
    "/items/{item_id}",
    response_model=CartResponse,
    summary="Remove Item from Cart"
)
def remove_cart_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return CartService.remove_cart_item(
        db=db,
        current_user=current_user,
        item_id=item_id
    )


@router.delete(
    "",
    response_model=CartResponse,
    summary="Clear Cart"
)
def clear_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return CartService.clear_cart(db=db, current_user=current_user)
