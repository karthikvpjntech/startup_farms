import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.authorization import require_roles
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.tool_interest import (
    ToolInterestCreate,
    ToolInterestUpdate,
    ToolInterestResponse,
    ToolInterestListResponse,
    DiscoveryRefreshResponse,
    ProximityCheckRequest,
    ProximityCheckResponse,
)
from app.services.tool_discovery_service import ToolDiscoveryService

router = APIRouter(prefix="/farmer/tool-interests", tags=["Farmer Tool Demand & Geofenced Discovery"])


@router.post(
    "",
    response_model=APIResponse[ToolInterestResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register Tool Requirement & Auto-Discover Local Vendors",
)
def create_tool_interest(
    payload: ToolInterestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.FARMER, RoleEnum.SUPER_ADMIN])),
):
    """
    Registers a new machinery / tool demand (e.g. Tractor rental in Mysuru)
    and automatically executes Google Places discovery to find and store matching
    equipment dealers, custom hiring centers, and tractor rental businesses.
    """
    ti = ToolDiscoveryService.create_tool_interest(db, current_user, payload)
    res = ToolDiscoveryService.get_tool_interest(db, ti.id, current_user)
    return APIResponse[ToolInterestResponse](
        success=True,
        message=f"Tool requirement registered. Found {res.discovered_locations_count} matching providers in {res.required_location}.",
        data=res,
    )


@router.get(
    "",
    response_model=APIResponse[ToolInterestListResponse],
    summary="List Farmer Tool Requirements",
)
def list_tool_interests(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: ACTIVE, FULFILLED, PAUSED, ARCHIVED"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.FARMER, RoleEnum.SUPER_ADMIN])),
):
    """
    Lists all saved tool requirements for the authenticated farmer with count of discovered vendors.
    """
    data = ToolDiscoveryService.list_tool_interests(
        db, current_user, status_filter=status_filter, page=page, page_size=page_size
    )
    return APIResponse[ToolInterestListResponse](
        success=True,
        message="Tool requirements retrieved successfully",
        data=data,
    )


@router.get(
    "/{tool_interest_id}",
    response_model=APIResponse[ToolInterestResponse],
    summary="Get Tool Requirement Details & Discovered Places",
)
def get_tool_interest(
    tool_interest_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.FARMER, RoleEnum.SUPER_ADMIN])),
):
    """
    Retrieves full details of a specific tool demand including all discovered Google Places vendor locations.
    """
    data = ToolDiscoveryService.get_tool_interest(db, tool_interest_id, current_user)
    return APIResponse[ToolInterestResponse](
        success=True,
        message="Tool requirement retrieved successfully",
        data=data,
    )


@router.put(
    "/{tool_interest_id}",
    response_model=APIResponse[ToolInterestResponse],
    summary="Update Tool Requirement",
)
def update_tool_interest(
    tool_interest_id: uuid.UUID,
    payload: ToolInterestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.FARMER, RoleEnum.SUPER_ADMIN])),
):
    """
    Updates tool requirement specifications, status, or search radius.
    """
    data = ToolDiscoveryService.update_tool_interest(db, tool_interest_id, current_user, payload)
    return APIResponse[ToolInterestResponse](
        success=True,
        message="Tool requirement updated successfully",
        data=data,
    )


@router.delete(
    "/{tool_interest_id}",
    response_model=APIResponse[dict],
    summary="Remove Tool Requirement",
)
def delete_tool_interest(
    tool_interest_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.FARMER, RoleEnum.SUPER_ADMIN])),
):
    """
    Soft-deletes a tool requirement and archives associated discovered locations.
    """
    res = ToolDiscoveryService.delete_tool_interest(db, tool_interest_id, current_user)
    return APIResponse[dict](
        success=True,
        message=res["message"],
        data=res,
    )


@router.post(
    "/{tool_interest_id}/refresh-discovery",
    response_model=APIResponse[DiscoveryRefreshResponse],
    summary="Refresh Google Places Discovery",
)
def refresh_discovery(
    tool_interest_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.FARMER, RoleEnum.SUPER_ADMIN])),
):
    """
    Re-runs Google Places search for the specified tool demand to find freshly listed vendors.
    """
    data = ToolDiscoveryService.refresh_discovery(db, tool_interest_id, current_user)
    return APIResponse[DiscoveryRefreshResponse](
        success=True,
        message=data.message,
        data=data,
    )


@router.post(
    "/check-proximity",
    response_model=APIResponse[ProximityCheckResponse],
    summary="Check Farmer GPS Proximity & Trigger Geofenced Alerts",
)
def check_proximity(
    payload: ProximityCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.FARMER, RoleEnum.SUPER_ADMIN])),
):
    """
    Receives the farmer's current GPS coordinates (lat, lng), calculates Haversine distances
    to all active discovered machinery vendor locations, and generates real-time proximity alerts
    when the farmer is within the configured geofence radius (e.g. 500m).
    """
    data = ToolDiscoveryService.check_proximity(db, current_user, payload)
    return APIResponse[ProximityCheckResponse](
        success=True,
        message=f"Proximity check completed. {data.nearby_alerts_count} machinery services nearby.",
        data=data,
    )
