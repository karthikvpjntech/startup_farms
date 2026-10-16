import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.livestock import (
    LivestockCreateRequest,
    LivestockUpdateRequest,
    LivestockResponse,
    LivestockListResponse,
    FarmerLivestockStatsResponse,
)
from app.schemas.marketplace_order import (
    MarketplaceOrderListResponse,
    MarketplaceOrderResponse,
    OrderStatusUpdateRequest,
)
from app.services.livestock_service import LivestockService
from app.services.marketplace_order_service import MarketplaceOrderService

router = APIRouter(prefix="/farmer", tags=["Farmer Livestock Operations"])


@router.get(
    "/livestock/stats",
    response_model=FarmerLivestockStatsResponse,
    summary="Get Farmer Livestock Dashboard Stats"
)
def get_farmer_livestock_stats(
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return LivestockService.get_farmer_dashboard_stats(db=db, current_user=current_user)


@router.post(
    "/livestock",
    response_model=LivestockResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New Livestock"
)
def create_livestock(
    request: LivestockCreateRequest,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return LivestockService.create_livestock(db=db, current_user=current_user, request=request)


@router.get(
    "/livestock",
    response_model=LivestockListResponse,
    summary="List Farmer's Livestock"
)
def list_farmer_livestock(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category_id: Optional[uuid.UUID] = Query(default=None),
    status: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return LivestockService.list_farmer_livestock(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        category_id=category_id,
        status=status,
        search=search
    )


@router.get(
    "/livestock/{livestock_id}",
    response_model=LivestockResponse,
    summary="Get Farmer Livestock Detail"
)
def get_farmer_livestock_detail(
    livestock_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return LivestockService.get_livestock_detail(db=db, livestock_id=livestock_id, current_user=current_user)


@router.put(
    "/livestock/{livestock_id}",
    response_model=LivestockResponse,
    summary="Update Farmer Livestock"
)
def update_farmer_livestock(
    livestock_id: uuid.UUID,
    request: LivestockUpdateRequest,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return LivestockService.update_livestock(
        db=db,
        current_user=current_user,
        livestock_id=livestock_id,
        request=request
    )


@router.post(
    "/livestock/{livestock_id}/publish",
    response_model=LivestockResponse,
    summary="Publish Livestock to Marketplace"
)
def publish_livestock(
    livestock_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return LivestockService.publish_livestock(db=db, current_user=current_user, livestock_id=livestock_id)


@router.post(
    "/livestock/{livestock_id}/unpublish",
    response_model=LivestockResponse,
    summary="Unpublish Livestock from Marketplace"
)
def unpublish_livestock(
    livestock_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return LivestockService.unpublish_livestock(db=db, current_user=current_user, livestock_id=livestock_id)


@router.post(
    "/livestock/{livestock_id}/archive",
    response_model=LivestockResponse,
    summary="Archive Livestock"
)
def archive_livestock(
    livestock_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return LivestockService.archive_livestock(db=db, current_user=current_user, livestock_id=livestock_id)


@router.delete(
    "/livestock/{livestock_id}",
    response_model=LivestockResponse,
    summary="Delete Livestock"
)
def delete_livestock(
    livestock_id: uuid.UUID,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return LivestockService.delete_livestock(db=db, current_user=current_user, livestock_id=livestock_id)


# ============================================================================
# Farmer Order Fulfillment Endpoints
# ============================================================================

@router.get(
    "/orders",
    response_model=MarketplaceOrderListResponse,
    summary="List Orders Received by Farmer"
)
def list_farmer_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
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
    summary="Update Order Fulfillment Status"
)
def update_farmer_order_status(
    order_id: uuid.UUID,
    request: OrderStatusUpdateRequest,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return MarketplaceOrderService.update_farmer_order_status(
        db=db,
        current_user=current_user,
        order_id=order_id,
        new_status=request.status.value,
        notes=request.notes
    )
