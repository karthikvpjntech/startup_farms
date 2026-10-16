import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class DiscoveredToolLocationResponse(BaseModel):
    id: uuid.UUID
    tool_interest_id: uuid.UUID
    place_id: Optional[str] = None
    business_name: str
    category: str
    formatted_address: str
    latitude: float
    longitude: float
    phone_number: Optional[str] = None
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = 0
    opening_hours_text: Optional[str] = None
    google_maps_url: Optional[str] = None
    website: Optional[str] = None
    photo_url: Optional[str] = None
    products_available: Optional[str] = None
    distance_meters: Optional[float] = None
    is_verified: bool = True
    last_notified_at: Optional[datetime] = None
    notification_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ToolInterestCreate(BaseModel):
    tool_name: str = Field(..., min_length=2, max_length=100, description="e.g. Urea / Uriya, DAP, Paddy Seeds, Tomato Seeds, Tractor, Power Sprayer, Drip Kit")
    tool_type: str = Field("RENTAL", description="FERTILIZER, SEEDS, PESTICIDE, AGRI_INPUTS, RENTAL, PURCHASE, IRRIGATION_HARDWARE, LIVESTOCK_FEED, TRADER_COMMODITY, SERVICE_REPAIR, OPERATOR_HIRE, OTHER")
    category: Optional[str] = Field(None, description="e.g. FERTILIZERS, SEEDS, PESTICIDES, MACHINERY, IRRIGATION, LIVESTOCK_FEED, TRADERS")
    required_location: str = Field(..., min_length=2, max_length=200, description="e.g. Mysuru, Mandya, Hassan")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    search_radius_km: Optional[float] = Field(25.0, ge=1.0, le=200.0)
    geofence_radius_meters: Optional[float] = Field(500.0, ge=50.0, le=50000.0, description="Radius in meters to trigger proximity notification")
    specifications: Optional[str] = Field(None, max_length=1000, description="e.g. 45kg Neem Coated Urea Bag, Certified Aman Ponni Seeds, 45-55 HP 4WD Tractor")
    max_budget: Optional[Decimal] = Field(None, ge=0)
    auto_discovery_enabled: Optional[bool] = True


class ToolInterestUpdate(BaseModel):
    tool_name: Optional[str] = Field(None, min_length=2, max_length=100)
    tool_type: Optional[str] = None
    category: Optional[str] = None
    required_location: Optional[str] = Field(None, min_length=2, max_length=200)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    search_radius_km: Optional[float] = Field(None, ge=1.0, le=200.0)
    geofence_radius_meters: Optional[float] = Field(None, ge=50.0, le=50000.0)
    specifications: Optional[str] = Field(None, max_length=1000)
    max_budget: Optional[Decimal] = Field(None, ge=0)
    status: Optional[str] = None
    auto_discovery_enabled: Optional[bool] = None


class ToolInterestResponse(BaseModel):
    id: uuid.UUID
    farmer_profile_id: uuid.UUID
    tool_name: str
    tool_type: str
    category: Optional[str] = "MACHINERY"
    required_location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    search_radius_km: float = 25.0
    geofence_radius_meters: float = 500.0
    specifications: Optional[str] = None
    max_budget: Optional[Decimal] = None
    status: str
    auto_discovery_enabled: bool = True
    last_searched_at: Optional[datetime] = None
    discovered_locations_count: int = 0
    discovered_locations: List[DiscoveredToolLocationResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ToolInterestListResponse(BaseModel):
    items: List[ToolInterestResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProximityCheckRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Farmer's current GPS latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Farmer's current GPS longitude")
    proximity_radius_override_meters: Optional[float] = Field(None, ge=50.0, le=50000.0)
    record_notification: Optional[bool] = True


class ProximityAlertItem(BaseModel):
    tool_interest_id: uuid.UUID
    tool_name: str
    tool_type: str
    location_id: uuid.UUID
    business_name: str
    category: str
    formatted_address: str
    latitude: float
    longitude: float
    phone_number: Optional[str] = None
    rating: Optional[float] = None
    opening_hours_text: Optional[str] = None
    photo_url: Optional[str] = None
    distance_meters: float
    geofence_radius_meters: float
    google_maps_url: Optional[str] = None
    notification_title: str
    notification_message: str
    is_new_alert: bool = True


class ProximityCheckResponse(BaseModel):
    current_latitude: float
    current_longitude: float
    nearby_alerts_count: int
    alerts: List[ProximityAlertItem]
    checked_at: datetime


class DiscoveryRefreshResponse(BaseModel):
    tool_interest_id: uuid.UUID
    discovered_count: int
    query_used: str
    locations: List[DiscoveredToolLocationResponse]
    message: str
