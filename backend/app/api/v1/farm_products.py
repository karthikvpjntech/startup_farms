import uuid
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.farm_selling_product import (
    FarmSellingProductResponse,
    FarmSellingProductListResponse,
    FarmProductBuyNowRequest,
)
from app.schemas.marketplace_order import (
    MarketplaceOrderResponse,
)
from app.services.farm_selling_product_service import FarmSellingProductService

router = APIRouter(prefix="/farm-products", tags=["Public Farm Products Marketplace"])


@router.get(
    "",
    response_model=FarmSellingProductListResponse,
    summary="Search & Filter Public Fresh Farm Products Marketplace"
)
def search_farm_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: Optional[str] = Query(default=None, description="Category filter (FRUITS, VEGETABLES, COCONUT, GRAINS_PADDY, OTHER)"),
    search: Optional[str] = Query(default=None, description="Search term for product name, variety, farmer name, or village"),
    variety: Optional[str] = Query(default=None, description="Filter by crop/produce variety (e.g. Panna, Alphonso, Aman Ponni)"),
    min_price: Optional[Decimal] = Query(default=None, ge=0),
    max_price: Optional[Decimal] = Query(default=None, ge=0),
    in_stock_only: bool = Query(default=False, description="Filter only products with available quantity > 0"),
    delivery_type: Optional[str] = Query(default=None, description="DELIVERY or PICKUP"),
    sort_by: Optional[str] = Query(default="newest", description="newest, oldest, price_asc, price_desc, qty_desc"),
    db: Session = Depends(get_db)
):
    """
    Public discovery endpoint for fresh harvest produce listed by local farmers.
    """
    return FarmSellingProductService.search_public_products(
        db=db,
        page=page,
        page_size=page_size,
        category=category,
        search=search,
        variety=variety,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        delivery_type=delivery_type,
        sort_by=sort_by or "newest",
    )


@router.get(
    "/{product_id}",
    response_model=FarmSellingProductResponse,
    summary="Get Public Farm Product Details"
)
def get_public_farm_product_detail(
    product_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieves complete product information, full image gallery, origin farmer location,
    and enabled purchase options (Delivery, COD, Online, Direct Farm Pickup).
    """
    return FarmSellingProductService.get_public_product_detail(
        db=db,
        product_id=product_id
    )


@router.post(
    "/buy-now",
    response_model=MarketplaceOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Direct Buy Now / Farm Pickup Checkout"
)
def buy_now_farm_product(
    request: FarmProductBuyNowRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Direct instant purchase or farm pickup checkout with concurrency-safe stock deduction.
    Supports Online Payment, Cash on Delivery, and Direct Farm Pickup.
    """
    return FarmSellingProductService.buy_now(
        db=db,
        current_user=current_user,
        request=request
    )
