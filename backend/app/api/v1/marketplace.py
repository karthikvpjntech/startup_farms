import uuid
from decimal import Decimal
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.livestock import (
    LivestockResponse,
    LivestockListResponse,
)
from app.schemas.marketplace_order import (
    LivestockReviewResponse,
)
from app.services.marketplace_service import MarketplaceService

router = APIRouter(prefix="/marketplace", tags=["Public Livestock Marketplace"])


@router.get(
    "/livestock",
    response_model=LivestockListResponse,
    summary="Search & Filter Public Livestock Marketplace"
)
def search_marketplace(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category_code: Optional[str] = Query(default=None, description="Filter by Category Code (e.g., GOAT, CHICKEN)"),
    category_id: Optional[uuid.UUID] = Query(default=None),
    breed_id: Optional[uuid.UUID] = Query(default=None),
    selling_model: Optional[str] = Query(default=None, description="INDIVIDUAL or QUANTITY"),
    gender: Optional[str] = Query(default=None, description="MALE, FEMALE, UNKNOWN"),
    min_price: Optional[Decimal] = Query(default=None, ge=0),
    max_price: Optional[Decimal] = Query(default=None, ge=0),
    min_age: Optional[Decimal] = Query(default=None, ge=0),
    max_age: Optional[Decimal] = Query(default=None, ge=0),
    min_weight: Optional[Decimal] = Query(default=None, ge=0),
    max_weight: Optional[Decimal] = Query(default=None, ge=0),
    search: Optional[str] = Query(default=None, description="Search term for animal name, code, breed, or location (e.g. 'chiken', 'country chicken')"),
    location: Optional[str] = Query(default=None, description="Filter by village, district, or state"),
    latitude: Optional[float] = Query(default=None, description="Buyer GPS Latitude for proximity calculation"),
    longitude: Optional[float] = Query(default=None, description="Buyer GPS Longitude for proximity calculation"),
    max_distance_km: Optional[float] = Query(default=None, description="Max radius in kilometers (e.g. 10.0 for near 10 km)"),
    sort_by: Optional[str] = Query(default="newest", description="newest, oldest, price_asc, price_desc, distance_asc, rating_desc, weight_desc, age_desc"),
    db: Session = Depends(get_db)
):
    return MarketplaceService.search_livestock(
        db=db,
        page=page,
        page_size=page_size,
        category_code=category_code,
        category_id=category_id,
        breed_id=breed_id,
        selling_model=selling_model,
        gender=gender,
        min_price=min_price,
        max_price=max_price,
        min_age=min_age,
        max_age=max_age,
        min_weight=min_weight,
        max_weight=max_weight,
        search=search,
        location=location,
        latitude=latitude,
        longitude=longitude,
        max_distance_km=max_distance_km,
        sort_by=sort_by
    )


@router.get(
    "/livestock/{livestock_id}",
    response_model=LivestockResponse,
    summary="Get Public Livestock Details"
)
def get_public_livestock_detail(
    livestock_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return MarketplaceService.get_public_livestock_detail(db=db, livestock_id=livestock_id)


@router.get(
    "/livestock/{livestock_id}/reviews",
    response_model=List[LivestockReviewResponse],
    summary="Get Reviews for Livestock Listing"
)
def list_livestock_reviews(
    livestock_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    return MarketplaceService.list_reviews(
        db=db,
        livestock_id=livestock_id,
        page=page,
        page_size=page_size
    )
