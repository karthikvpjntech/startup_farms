import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.produce_procurement import (
    ProduceAvailabilityItem,
    CustomerProcurementCreateRequest,
    FarmerProcurementConfirmRequest,
    FarmerProcurementRejectRequest,
    ProcurementDeliveryUpdateRequest,
    ProcurementPaymentRequest,
    ProduceProcurementResponse,
    ProduceProcurementListResponse,
    HarvestAlertItem,
    HarvestAlertSubscriptionRequest,
    HarvestAlertSubscriptionResponse,
)
from app.services.produce_procurement_service import ProduceProcurementService

router = APIRouter(prefix="/produce-procurement", tags=["Public Produce Procurement & Farmer Fulfillment"])


@router.get(
    "/available",
    response_model=List[ProduceAvailabilityItem],
    summary="List Available Crop Produce from Verified Farmers"
)
def get_available_produce(
    crop_id: Optional[uuid.UUID] = Query(default=None),
    search: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """Public endpoint to discover crops, available harvest quantities, and farming origins."""
    return ProduceProcurementService.get_available_produce(db=db, crop_id=crop_id, search=search)


@router.get(
    "/harvest-alerts",
    response_model=List[HarvestAlertItem],
    summary="List Real-time Broadcast Harvest Yield Alerts"
)
def get_harvest_alerts(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Public endpoint for live broadcast notifications of newly updated farm yields."""
    return ProduceProcurementService.get_recent_harvest_alerts(db=db, limit=limit)


@router.post(
    "/subscribe-alerts",
    response_model=HarvestAlertSubscriptionResponse,
    summary="Subscribe for Instant SMS and Email Harvest Alerts"
)
def subscribe_harvest_alerts(
    request: HarvestAlertSubscriptionRequest,
    db: Session = Depends(get_db)
):
    """Public endpoint allowing buyers to receive SMS, WhatsApp and email harvest alerts."""
    return ProduceProcurementService.subscribe_harvest_alerts(db=db, request=request)



@router.post(
    "",
    response_model=ProduceProcurementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Public Customer Produce Procurement Request"
)
def create_procurement_request(
    request: CustomerProcurementCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Customer submits a produce procurement requisition for crops (e.g. Paddy / நெல்)."""
    return ProduceProcurementService.create_procurement_request(
        db=db,
        current_user=current_user,
        request=request
    )


@router.get(
    "/my-requests",
    response_model=ProduceProcurementListResponse,
    summary="List Current Customer's Produce Procurement Requests"
)
def list_my_procurements(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return ProduceProcurementService.list_customer_procurements(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        status=status
    )


@router.get(
    "/farmer-requests",
    response_model=ProduceProcurementListResponse,
    summary="List Procurement Requests Received by Farmer"
)
def list_farmer_procurements(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return ProduceProcurementService.list_farmer_procurements(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        status=status
    )


@router.get(
    "/{procurement_id}",
    response_model=ProduceProcurementResponse,
    summary="Get Produce Procurement Detail and Live Tracker"
)
def get_procurement_detail(
    procurement_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return ProduceProcurementService.get_procurement_detail(
        db=db,
        current_user=current_user,
        procurement_id=procurement_id
    )


@router.post(
    "/{procurement_id}/confirm",
    response_model=ProduceProcurementResponse,
    summary="Farmer Confirms Procurement Request"
)
def farmer_confirm_request(
    procurement_id: uuid.UUID,
    request: Optional[FarmerProcurementConfirmRequest] = None,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return ProduceProcurementService.farmer_confirm_request(
        db=db,
        current_user=current_user,
        procurement_id=procurement_id,
        request=request
    )


@router.post(
    "/{procurement_id}/reject",
    response_model=ProduceProcurementResponse,
    summary="Farmer Rejects Procurement Request with Reason"
)
def farmer_reject_request(
    procurement_id: uuid.UUID,
    request: FarmerProcurementRejectRequest,
    current_user: User = Depends(require_roles(RoleEnum.FARMER)),
    db: Session = Depends(get_db)
):
    return ProduceProcurementService.farmer_reject_request(
        db=db,
        current_user=current_user,
        procurement_id=procurement_id,
        request=request
    )


@router.post(
    "/{procurement_id}/pay",
    response_model=ProduceProcurementResponse,
    summary="Customer Settles Payment for Confirmed Procurement"
)
def pay_procurement(
    procurement_id: uuid.UUID,
    request: ProcurementPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return ProduceProcurementService.settle_payment(
        db=db,
        current_user=current_user,
        procurement_id=procurement_id,
        request=request
    )


@router.patch(
    "/{procurement_id}/delivery",
    response_model=ProduceProcurementResponse,
    summary="Advance Order Delivery Progression (Preparing, Ready, Out for Delivery, Delivered)"
)
def update_delivery_status(
    procurement_id: uuid.UUID,
    request: ProcurementDeliveryUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return ProduceProcurementService.update_delivery_status(
        db=db,
        current_user=current_user,
        procurement_id=procurement_id,
        request=request
    )


@router.post(
    "/{procurement_id}/cancel",
    response_model=ProduceProcurementResponse,
    summary="Customer Cancels Pending Procurement Request"
)
def cancel_procurement(
    procurement_id: uuid.UUID,
    reason: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return ProduceProcurementService.cancel_procurement(
        db=db,
        current_user=current_user,
        procurement_id=procurement_id,
        reason=reason
    )
