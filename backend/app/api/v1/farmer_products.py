import uuid
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.farm_selling_product import (
    FarmSellingProductCreateRequest,
    FarmSellingProductUpdateRequest,
    FarmSellingProductStockUpdateRequest,
    FarmSellingProductResponse,
    FarmSellingProductListResponse,
    FarmerSellingProductStatsResponse,
)
from app.schemas.marketplace_order import (
    MarketplaceOrderListResponse,
    MarketplaceOrderResponse,
    OrderStatusUpdateRequest,
)
from app.services.farm_selling_product_service import FarmSellingProductService
from app.services.marketplace_order_service import MarketplaceOrderService

router = APIRouter(prefix="/farmer/products", tags=["Farmer Selling Products"])


@router.get(
    "/stats",
    response_model=FarmerSellingProductStatsResponse,
    summary="Get Farmer Selling Products Dashboard Statistics"
)
def get_farmer_product_stats(
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Returns dashboard metrics for farmer selling products:
    total products, active products, out of stock count, orders received, and total revenue.
    """
    return FarmSellingProductService.get_farmer_stats(db=db, current_user=current_user)


@router.post(
    "",
    response_model=FarmSellingProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create New Selling Farm Product"
)
def create_farmer_product(
    request: FarmSellingProductCreateRequest,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Allows an authenticated farmer to register a fresh farm product listing
    with primary and secondary images, pricing, available inventory, and fulfillment options.
    """
    return FarmSellingProductService.create_product(
        db=db,
        current_user=current_user,
        request=request
    )


@router.get(
    "",
    response_model=FarmSellingProductListResponse,
    summary="List Farmer's Selling Products"
)
def list_farmer_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: Optional[str] = Query(default=None, description="FRUITS, VEGETABLES, COCONUT, GRAINS_PADDY, OTHER"),
    status: Optional[str] = Query(default=None, description="ACTIVE, INACTIVE, OUT_OF_STOCK"),
    search: Optional[str] = Query(default=None, description="Search product name or variety"),
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Returns paginated list of selling products owned by the authenticated farmer.
    """
    return FarmSellingProductService.list_farmer_products(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        category=category,
        status_filter=status,
        search=search,
    )


@router.get(
    "/{product_id}",
    response_model=FarmSellingProductResponse,
    summary="Get Farmer Product Details"
)
def get_farmer_product_detail(
    product_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Fetches full product details for farmer editing.
    """
    return FarmSellingProductService.get_product_detail(
        db=db,
        current_user=current_user,
        product_id=product_id
    )


@router.put(
    "/{product_id}",
    response_model=FarmSellingProductResponse,
    summary="Update Farmer Selling Product"
)
def update_farmer_product(
    product_id: uuid.UUID,
    request: FarmSellingProductUpdateRequest,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Updates product specifications, pricing, inventory, delivery options, or gallery images.
    """
    return FarmSellingProductService.update_product(
        db=db,
        current_user=current_user,
        product_id=product_id,
        request=request
    )


@router.patch(
    "/{product_id}/stock",
    response_model=FarmSellingProductResponse,
    summary="Quick Update Available Stock"
)
def update_product_stock(
    product_id: uuid.UUID,
    request: FarmSellingProductStockUpdateRequest,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Quick adjustment of available inventory quantity (e.g. after a new harvest).
    Automatically flips status to OUT_OF_STOCK if 0, or ACTIVE if > 0.
    """
    return FarmSellingProductService.update_stock(
        db=db,
        current_user=current_user,
        product_id=product_id,
        request=request
    )


@router.delete(
    "/{product_id}",
    response_model=FarmSellingProductResponse,
    summary="Soft Delete Selling Product"
)
def delete_farmer_product(
    product_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Soft-deletes a product listing without deleting historical customer orders.
    """
    return FarmSellingProductService.delete_product(
        db=db,
        current_user=current_user,
        product_id=product_id
    )


# ============================================================================
# Farmer Order Fulfillment Endpoints for Farm Products
# ============================================================================

@router.get(
    "/orders/received",
    response_model=MarketplaceOrderListResponse,
    summary="List Farm Product Orders Received by Farmer"
)
def list_farmer_product_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Lists customer orders for farm produce received by the authenticated farmer.
    """
    return MarketplaceOrderService.list_farmer_orders(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        status=status
    )


@router.patch(
    "/orders/{order_id}/status",
    response_model=MarketplaceOrderResponse,
    summary="Update Fulfillment Status for Farm Product Order"
)
def update_farmer_order_status(
    order_id: uuid.UUID,
    request: OrderStatusUpdateRequest,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    """
    Allows farmer to accept, prepare, mark ready for pickup, dispatch, or complete orders.
    """
    return MarketplaceOrderService.update_farmer_order_status(
        db=db,
        current_user=current_user,
        order_id=order_id,
        new_status=request.status.value,
        notes=request.notes
    )
