import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import (
    ShipmentStatus,
    SpecialHandlingType,
    PackageType,
    PickupRequestStatus,
    PickupTimeWindow,
    DeliveryAttemptStatus,
    DeliveryFailureReason,
)


# ==========================================
# 1. Package Schemas
# ==========================================

class ShipmentPackageBase(BaseModel):
    item_description: str = Field(..., min_length=1, max_length=255)
    weight_kg: Decimal = Field(default=Decimal("1.00"), ge=Decimal("0.01"))
    package_type: PackageType = Field(default=PackageType.CORRUGATED_CARTON)


class ShipmentPackageCreate(ShipmentPackageBase):
    pass


class ShipmentPackageResponse(ShipmentPackageBase):
    id: uuid.UUID
    shipment_id: uuid.UUID
    package_number: str
    package_barcode: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 2. Tracking Event Schemas
# ==========================================

class ShipmentTrackingEventResponse(BaseModel):
    id: uuid.UUID
    shipment_id: uuid.UUID
    status: str
    location_hub: Optional[str] = None
    city: Optional[str] = None
    remarks: Optional[str] = None
    updated_by_role: Optional[str] = None
    event_timestamp: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. Delivery Attempt Schemas
# ==========================================

class DeliveryAttemptCreate(BaseModel):
    attempt_status: DeliveryAttemptStatus = Field(default=DeliveryAttemptStatus.SUCCESS)
    failure_reason: Optional[DeliveryFailureReason] = None
    recipient_name: Optional[str] = None
    recipient_signature_note: Optional[str] = None
    driver_notes: Optional[str] = None


class DeliveryAttemptResponse(BaseModel):
    id: uuid.UUID
    shipment_id: uuid.UUID
    attempt_number: int
    attempt_status: str
    failure_reason: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_signature_note: Optional[str] = None
    driver_notes: Optional[str] = None
    attempt_time: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 4. Pickup Request Schemas
# ==========================================

class PickupRequestCreate(BaseModel):
    pickup_address: str = Field(..., min_length=5)
    pickup_contact_name: str = Field(..., min_length=2, max_length=150)
    pickup_contact_phone: str = Field(..., min_length=10, max_length=20)
    scheduled_date: date
    time_window: PickupTimeWindow = Field(default=PickupTimeWindow.MORNING_7_11)
    notes: Optional[str] = None


class PickupRequestAssign(BaseModel):
    driver_id: uuid.UUID
    assigned_vehicle_number: Optional[str] = None
    notes: Optional[str] = None


class PickupRequestResponse(BaseModel):
    id: uuid.UUID
    pickup_code: str
    shipment_id: uuid.UUID
    farmer_profile_id: uuid.UUID
    pickup_address: str
    pickup_contact_name: str
    pickup_contact_phone: str
    scheduled_date: date
    time_window: str
    status: str
    assigned_driver_id: Optional[uuid.UUID] = None
    assigned_vehicle_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 5. Transport Provider Schemas
# ==========================================

class TransportProviderCreate(BaseModel):
    provider_name: str = Field(..., min_length=2, max_length=150)
    provider_code: str = Field(..., min_length=2, max_length=50)
    contact_person: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_number: Optional[str] = None
    service_areas: Optional[str] = None
    is_active: bool = True


class TransportProviderUpdate(BaseModel):
    provider_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_number: Optional[str] = None
    service_areas: Optional[str] = None
    is_active: Optional[bool] = None


class TransportProviderResponse(BaseModel):
    id: uuid.UUID
    provider_name: str
    provider_code: str
    contact_person: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_number: Optional[str] = None
    service_areas: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 6. Shipment Schemas
# ==========================================

class ShipmentCreate(BaseModel):
    order_id: uuid.UUID
    origin_address: str
    origin_city: str
    origin_pincode: str
    destination_address: str
    destination_city: str
    destination_pincode: str
    is_perishable: bool = False
    special_handling: SpecialHandlingType = Field(default=SpecialHandlingType.GENERAL)
    estimated_delivery_date: Optional[date] = None
    packages: List[ShipmentPackageCreate] = Field(default_factory=list)
    # Optional direct pickup request on creation
    request_pickup: bool = True
    pickup_scheduled_date: Optional[date] = None
    pickup_time_window: Optional[PickupTimeWindow] = PickupTimeWindow.MORNING_7_11


class ShipmentStatusUpdate(BaseModel):
    status: ShipmentStatus
    location_hub: Optional[str] = None
    city: Optional[str] = None
    remarks: Optional[str] = None


class ShipmentAssignProvider(BaseModel):
    transport_provider_id: Optional[uuid.UUID] = None
    driver_id: Optional[uuid.UUID] = None
    estimated_delivery_date: Optional[date] = None


class ShipmentResponse(BaseModel):
    id: uuid.UUID
    shipment_number: str
    tracking_number: str
    order_id: uuid.UUID
    farmer_profile_id: uuid.UUID
    customer_id: uuid.UUID
    transport_provider_id: Optional[uuid.UUID] = None
    driver_id: Optional[uuid.UUID] = None
    current_status: str
    current_location: Optional[str] = None
    origin_address: str
    origin_city: str
    origin_pincode: str
    destination_address: str
    destination_city: str
    destination_pincode: str
    total_packages: int
    total_weight_kg: Decimal
    is_perishable: bool
    special_handling: str
    barcode_data: str
    qr_code_data: str
    estimated_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    packages: List[ShipmentPackageResponse] = Field(default_factory=list)
    tracking_events: List[ShipmentTrackingEventResponse] = Field(default_factory=list)
    pickup_requests: List[PickupRequestResponse] = Field(default_factory=list)
    delivery_attempts: List[DeliveryAttemptResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 7. Public & Specialized Responses
# ==========================================

class PublicTrackingResponse(BaseModel):
    """
    Masked public tracking response ensuring customer privacy.
    """
    tracking_number: str
    shipment_number: str
    current_status: str
    current_location: Optional[str] = None
    origin_city: str
    origin_pincode: str
    destination_city: str
    destination_pincode: str
    masked_customer_name: str  # e.g. "K***r M"
    total_packages: int
    total_weight_kg: Decimal
    is_perishable: bool
    special_handling: str
    estimated_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[datetime] = None
    created_at: datetime
    tracking_events: List[ShipmentTrackingEventResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AdminTransportDashboardStats(BaseModel):
    total_shipments: int
    created_count: int
    in_transit_count: int
    out_for_delivery_count: int
    delivered_count: int
    failed_or_returned_count: int
    pending_pickups_count: int
    active_providers_count: int


class DriverPickupTaskResponse(BaseModel):
    pickup_request: PickupRequestResponse
    shipment: ShipmentResponse
