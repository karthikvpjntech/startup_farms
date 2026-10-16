import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CartItemAddRequest(BaseModel):
    livestock_id: Optional[uuid.UUID] = Field(default=None, description="Target livestock UUID to add to cart")
    farm_product_id: Optional[uuid.UUID] = Field(default=None, description="Target farm product UUID to add to cart")
    quantity: int = Field(default=1, ge=1, description="Quantity to purchase")


class CartItemUpdateRequest(BaseModel):
    quantity: int = Field(..., ge=1, description="New quantity for this cart item")


class CartItemResponse(BaseModel):
    id: uuid.UUID
    cart_id: uuid.UUID
    product_type: str = "LIVESTOCK"  # LIVESTOCK, FARM_PRODUCT
    livestock_id: Optional[uuid.UUID] = None
    farm_product_id: Optional[uuid.UUID] = None
    quantity: int
    created_at: datetime
    updated_at: datetime

    # Live listing metadata snapshots & validation
    product_name: str
    livestock_name: Optional[str] = None
    livestock_code: Optional[str] = None
    category_name: str
    breed_name: Optional[str] = None
    variety_name: Optional[str] = None
    unit: Optional[str] = None
    tag_number: Optional[str] = None
    selling_model: Optional[str] = None
    unit_price: Decimal
    item_total: Decimal
    primary_image_url: Optional[str] = None
    available_quantity: Decimal
    is_available: bool
    status: str
    farmer_profile_id: uuid.UUID
    farm_id: Optional[uuid.UUID] = None
    farm_name: Optional[str] = None
    location_summary: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    items: List[CartItemResponse] = []
    total_items_count: int = 0
    subtotal_amount: Decimal = Decimal("0.00")
    estimated_delivery_charge: Decimal = Decimal("0.00")
    estimated_tax_amount: Decimal = Decimal("0.00")
    estimated_total_amount: Decimal = Decimal("0.00")
    has_unavailable_items: bool = False
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

