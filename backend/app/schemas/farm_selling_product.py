import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class FarmSellingProductImageResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    image_url: str
    is_primary: bool
    display_order: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FarmSellingProductCreateRequest(BaseModel):
    farm_id: Optional[uuid.UUID] = Field(default=None, description="Optional Farm UUID where product was harvested")
    category: str = Field(..., description="Product Category (FRUITS, VEGETABLES, COCONUT, GRAINS_PADDY, OTHER)")
    name: str = Field(..., min_length=1, max_length=255, description="Product Name (e.g., Mango, Sapota, Lemon, Murungakkai, Aman Ponni Nel)")
    variety: Optional[str] = Field(default=None, max_length=255, description="Produce Variety (e.g., Panna, Banganapalli, Alphonso, PKM-1, Amulya-155)")
    description: Optional[str] = Field(default=None, description="Detailed product description and freshness guarantees")
    primary_image: str = Field(..., min_length=1, description="Primary high-resolution image URL")
    price: Decimal = Field(..., ge=0, description="Selling price per unit in INR (₹)")
    price_unit: str = Field(default="Kg", max_length=30, description="Price measurement unit (e.g. Kg, Piece, Quintal, Bag)")
    unit: str = Field(default="Kg", max_length=30, description="Supported measurement unit (Kg, Gram, Quintal, Piece, Dozen, Bundle, Litre, Bag, Other)")
    available_quantity: Decimal = Field(default=Decimal("0.00"), ge=0, description="Real inventory quantity available for sale")
    minimum_order_quantity: Decimal = Field(default=Decimal("1.00"), gt=0, description="Minimum order quantity threshold")
    harvest_date: Optional[date] = Field(default=None, description="Harvest date of the produce")
    delivery_available: bool = Field(default=True, description="Enable customer home delivery")
    cod_available: bool = Field(default=True, description="Enable Cash on Delivery (COD)")
    online_payment_available: bool = Field(default=True, description="Enable Online Payment (UPI / Card / Net Banking)")
    direct_pickup_available: bool = Field(default=True, description="Enable Direct Farm Pickup / Visit Farm")
    status: str = Field(default="ACTIVE", description="ACTIVE, INACTIVE, OUT_OF_STOCK")
    additional_images: Optional[List[str]] = Field(default=[], description="List of additional image URLs for gallery")


class FarmSellingProductUpdateRequest(BaseModel):
    farm_id: Optional[uuid.UUID] = None
    category: Optional[str] = None
    name: Optional[str] = None
    variety: Optional[str] = None
    description: Optional[str] = None
    primary_image: Optional[str] = None
    price: Optional[Decimal] = Field(default=None, ge=0)
    price_unit: Optional[str] = None
    unit: Optional[str] = None
    available_quantity: Optional[Decimal] = Field(default=None, ge=0)
    minimum_order_quantity: Optional[Decimal] = Field(default=None, gt=0)
    harvest_date: Optional[date] = None
    delivery_available: Optional[bool] = None
    cod_available: Optional[bool] = None
    online_payment_available: Optional[bool] = None
    direct_pickup_available: Optional[bool] = None
    status: Optional[str] = None
    additional_images: Optional[List[str]] = None


class FarmSellingProductStockUpdateRequest(BaseModel):
    available_quantity: Decimal = Field(..., ge=0, description="Updated available inventory quantity")
    status: Optional[str] = Field(default=None, description="Optional new status (ACTIVE, INACTIVE, OUT_OF_STOCK)")


class FarmSellingProductResponse(BaseModel):
    id: uuid.UUID
    farmer_profile_id: uuid.UUID
    farmer_name: Optional[str] = None
    farmer_mobile: Optional[str] = None
    farmer_profile_image: Optional[str] = None
    farm_id: Optional[uuid.UUID] = None
    farm_name: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    location_summary: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    category: str
    name: str
    variety: Optional[str] = None
    description: Optional[str] = None
    primary_image: str
    price: Decimal
    price_unit: str
    unit: str
    available_quantity: Decimal
    minimum_order_quantity: Decimal
    harvest_date: Optional[date] = None
    delivery_available: bool
    cod_available: bool
    online_payment_available: bool
    direct_pickup_available: bool
    status: str
    is_out_of_stock: bool = False
    images: List[FarmSellingProductImageResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FarmSellingProductListResponse(BaseModel):
    items: List[FarmSellingProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class FarmerSellingProductStatsResponse(BaseModel):
    total_products: int = 0
    active_products: int = 0
    out_of_stock_products: int = 0
    total_orders: int = 0
    total_revenue: Decimal = Decimal("0.00")

    model_config = ConfigDict(from_attributes=True)


class FarmProductBuyNowRequest(BaseModel):
    product_id: uuid.UUID = Field(..., description="Target Farm Selling Product UUID")
    quantity: Decimal = Field(default=Decimal("1.00"), gt=0, description="Purchase quantity")
    fulfillment_type: str = Field(default="FARMER_DELIVERY", description="FARMER_DELIVERY, LOGISTICS_PARTNER, FARM_PICKUP")
    payment_method: str = Field(default="CASH_ON_DELIVERY", description="UPI, NET_BANKING, CARD, CASH_ON_DELIVERY")
    delivery_contact_name: str = Field(..., min_length=1, max_length=150)
    delivery_contact_phone: str = Field(..., min_length=5, max_length=20)
    delivery_address: Optional[str] = Field(default=None, description="Required if fulfillment_type is delivery")
    delivery_city: Optional[str] = None
    delivery_pincode: Optional[str] = None
    notes: Optional[str] = None
