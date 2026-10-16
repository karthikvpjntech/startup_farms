import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.shipment import (
    ShipmentResponse,
    AdminTransportDashboardStats,
    TransportProviderCreate,
    TransportProviderUpdate,
    TransportProviderResponse,
    ShipmentAssignProvider,
)
from app.services.shipment_service import ShipmentService

router = APIRouter(prefix="/admin/transport", tags=["Super Admin — Transport & Logistics Hub"])


@router.get(
    "/dashboard",
    response_model=AdminTransportDashboardStats,
    summary="Get Transport Operations Metrics Dashboard",
)
def get_transport_dashboard_stats(
    current_user: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    service = ShipmentService(db)
    stats = service.get_admin_dashboard_stats()
    return AdminTransportDashboardStats(**stats)


@router.get(
    "/shipments",
    summary="Master Logistics Directory — All Shipments",
)
def list_all_shipments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    transport_provider_id: Optional[uuid.UUID] = Query(default=None),
    current_user: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    service = ShipmentService(db)
    items, total = service.list_admin_shipments(
        page=page,
        page_size=page_size,
        status=status,
        search=search,
        transport_provider_id=transport_provider_id,
    )
    return {
        "items": [ShipmentResponse.model_validate(s) for s in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 1,
    }


@router.get(
    "/providers",
    response_model=List[TransportProviderResponse],
    summary="List Transport Carrier Partners",
)
def list_transport_providers(
    active_only: bool = Query(default=False),
    current_user: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    service = ShipmentService(db)
    providers = service.list_transport_providers(active_only=active_only)
    return [TransportProviderResponse.model_validate(p) for p in providers]


@router.post(
    "/providers",
    response_model=TransportProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Transport Carrier Partner",
)
def create_transport_provider(
    data: TransportProviderCreate,
    current_user: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    service = ShipmentService(db)
    return service.create_transport_provider(data)


@router.patch(
    "/providers/{provider_id}",
    response_model=TransportProviderResponse,
    summary="Update Transport Carrier Partner",
)
def update_transport_provider(
    provider_id: uuid.UUID,
    data: TransportProviderUpdate,
    current_user: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    service = ShipmentService(db)
    return service.update_transport_provider(provider_id, data)


@router.post(
    "/shipments/{shipment_id}/assign-provider",
    response_model=ShipmentResponse,
    summary="Assign Transport Carrier & Driver to Shipment",
)
def assign_shipment_carrier(
    shipment_id: uuid.UUID,
    data: ShipmentAssignProvider,
    current_user: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    service = ShipmentService(db)
    return service.assign_shipment_provider(
        shipment_id=shipment_id,
        user_id=current_user.id,
        data=data,
    )
