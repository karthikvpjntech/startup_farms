from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.marketplace_order import (
    AdminMarketplaceMetricsResponse,
    MarketplaceOrderListResponse,
)
from app.services.marketplace_order_service import MarketplaceOrderService

router = APIRouter(prefix="/admin/marketplace", tags=["Admin (Marketplace Management)"])


@router.get(
    "/metrics",
    response_model=AdminMarketplaceMetricsResponse,
    summary="Get Marketplace Key Performance Metrics"
)
def get_marketplace_metrics(
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return MarketplaceOrderService.get_admin_metrics(db=db)


@router.get(
    "/orders",
    response_model=MarketplaceOrderListResponse,
    summary="List All Orders in System for Admin"
)
def list_all_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    current_admin: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    return MarketplaceOrderService.list_all_admin_orders(
        db=db,
        page=page,
        page_size=page_size,
        status=status,
        search=search
    )
