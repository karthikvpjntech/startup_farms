import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ProduceAvailabilityItem(BaseModel):
    """Available produce listing from verified farmer cultivations."""
    crop_id: uuid.UUID
    crop_name: str
    crop_name_local: Optional[str] = None
    local_names: Dict[str, str] = Field(default_factory=dict)
    crop_code: str
    crop_category: str
    image_url: Optional[str] = None
    farmer_profile_id: uuid.UUID
    farmer_name: str
    farmer_mobile: Optional[str] = None
    farm_id: Optional[uuid.UUID] = None
    farm_name: Optional[str] = None
    location: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    cultivation_id: Optional[uuid.UUID] = None
    farming_method: str = "CONVENTIONAL"
    available_quantity: Decimal
    unit: str = "kg"
    unit_price: Decimal = Decimal("0.00")
    harvest_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class CustomerProcurementCreateRequest(BaseModel):
    """Customer creation payload for requesting produce procurement."""
    crop_id: uuid.UUID
    farmer_profile_id: Optional[uuid.UUID] = None
    farm_id: Optional[uuid.UUID] = None
    cultivation_id: Optional[uuid.UUID] = None
    quantity: Decimal = Field(..., gt=0, description="Requested purchase quantity in given unit")
    unit: Optional[str] = Field(default="kg", description="Unit of measurement e.g. kg, bags, tonnes")
    required_date: date
    delivery_location: str = Field(..., min_length=3, description="Detailed street delivery address")
    delivery_city: Optional[str] = Field(default=None, description="City / Town")
    delivery_pincode: Optional[str] = Field(default=None, description="PIN code")
    contact_name: str = Field(..., min_length=2, description="Recipient contact person name")
    contact_phone: str = Field(..., min_length=10, max_length=15, description="Active mobile number for delivery coordination")
    notes: Optional[str] = Field(default=None, description="Special customer instructions or requirements (supports voice input)")


class FarmerProcurementConfirmRequest(BaseModel):
    """Farmer acceptance request payload with pickup location and WhatsApp dispatch."""
    pickup_location: Optional[str] = Field(default=None, description="Farm address / pickup point for customer collection")
    google_maps_url: Optional[str] = Field(default=None, description="Google Maps navigation link for farm holding")
    pickup_instructions: Optional[str] = Field(default=None, description="Specific instructions on farm landmark, timings, packaging")
    estimated_pickup_date: Optional[date] = Field(default=None, description="Estimated date when harvest will be ready for pickup")
    send_whatsapp: bool = Field(default=True, description="Send WhatsApp confirmation with Google Maps location to customer")
    send_sms: bool = Field(default=True, description="Send SMS notification to customer")
    notes: Optional[str] = Field(default=None, description="Optional remarks or harvest packaging instructions")


class FarmerProcurementRejectRequest(BaseModel):
    """Farmer rejection payload with reason."""
    rejection_reason: str = Field(..., min_length=3, description="Reason for inability to fulfill requisition")


class ProcurementDeliveryUpdateRequest(BaseModel):
    """Logistics and delivery progress payload."""
    status: str = Field(..., description="READY_FOR_DELIVERY, OUT_FOR_DELIVERY, DELIVERED, CANCELLED")
    driver_name: Optional[str] = None
    driver_contact: Optional[str] = None
    vehicle_number: Optional[str] = None
    tracking_notes: Optional[str] = None


class ProcurementPaymentRequest(BaseModel):
    """Customer payment settlement payload."""
    payment_method: str = Field(default="UPI", description="UPI, CASH_ON_DELIVERY, RAZORPAY, NET_BANKING")
    payment_reference: Optional[str] = Field(default=None, description="Transaction ID or reference number")
    notes: Optional[str] = None


class ProduceProcurementResponse(BaseModel):
    """Detailed response model for produce procurement requisition."""
    id: uuid.UUID
    request_code: str
    customer_id: uuid.UUID
    customer_name: Optional[str] = None
    customer_mobile: Optional[str] = None
    farmer_profile_id: uuid.UUID
    farmer_name: Optional[str] = None
    farmer_mobile: Optional[str] = None
    farmer_district: Optional[str] = None
    farmer_village: Optional[str] = None
    farm_id: Optional[uuid.UUID] = None
    farm_name: Optional[str] = None
    crop_id: uuid.UUID
    crop_name: str
    crop_name_local: Optional[str] = None
    local_names: Dict[str, str] = Field(default_factory=dict)
    product_name: str
    requested_quantity: Decimal
    unit: str
    unit_price: Decimal
    total_amount: Decimal
    required_date: date
    delivery_location: str
    delivery_city: Optional[str] = None
    delivery_pincode: Optional[str] = None
    contact_name: str
    contact_phone: str
    notes: Optional[str] = None

    # Pickup Location & Navigation
    pickup_location: Optional[str] = None
    google_maps_url: Optional[str] = None
    pickup_instructions: Optional[str] = None
    estimated_pickup_date: Optional[date] = None
    whatsapp_url: Optional[str] = None
    whatsapp_message_preview: Optional[str] = None

    status: str
    rejection_reason: Optional[str] = None
    payment_method: str
    payment_status: str
    payment_reference: Optional[str] = None
    payment_date: Optional[datetime] = None
    driver_id: Optional[uuid.UUID] = None
    driver_name: Optional[str] = None
    driver_contact: Optional[str] = None
    vehicle_number: Optional[str] = None
    tracking_notes: Optional[str] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProduceProcurementListResponse(BaseModel):
    """Paginated list response model for procurements."""
    items: List[ProduceProcurementResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class HarvestAlertItem(BaseModel):
    """Public real-time broadcast alert for newly recorded crop harvests."""
    id: uuid.UUID
    cultivation_id: Optional[uuid.UUID] = None
    crop_id: uuid.UUID
    crop_name: str
    crop_name_local: Optional[str] = None
    local_names: Dict[str, str] = Field(default_factory=dict)
    farmer_name: str
    farmer_mobile: Optional[str] = None
    farm_name: Optional[str] = None
    farm_location: Optional[str] = None
    yield_quantity: Decimal
    yield_unit: str
    selling_price_per_unit: Decimal
    harvest_date: Optional[date] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HarvestAlertSubscriptionRequest(BaseModel):
    """Public subscription for instant SMS and email harvest alerts."""
    name: str = Field(..., min_length=2)
    mobile_number: str = Field(..., min_length=10, max_length=15)
    email: Optional[str] = None
    crops_interested: List[str] = Field(default_factory=list)
    preferred_quantity_type: str = Field(default="ALL", description="RETAIL (small), WHOLESALE (large), ALL")
    district: Optional[str] = None


class HarvestAlertSubscriptionResponse(BaseModel):
    """Confirmation response for harvest alert subscription."""
    success: bool
    message: str
    subscriber_name: str
    subscribed_crops: List[str]
    notification_channels: List[str]

