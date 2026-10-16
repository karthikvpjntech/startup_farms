import logging
import uuid
from decimal import Decimal
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.livestock import (
    LivestockResponse,
    LivestockListResponse,
)
from app.schemas.marketplace_order import (
    LivestockReviewResponse,
)
from app.repositories.livestock_repository import LivestockRepository
from app.repositories.livestock_review_repository import LivestockReviewRepository
from app.services.livestock_service import LivestockService

logger = logging.getLogger("agri_smart.marketplace_service")


class MarketplaceService:
    """Public Marketplace Search & Detail Service."""

    @staticmethod
    def search_livestock(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        category_code: Optional[str] = None,
        category_id: Optional[uuid.UUID] = None,
        breed_id: Optional[uuid.UUID] = None,
        selling_model: Optional[str] = None,
        gender: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        min_age: Optional[Decimal] = None,
        max_age: Optional[Decimal] = None,
        min_weight: Optional[Decimal] = None,
        max_weight: Optional[Decimal] = None,
        search: Optional[str] = None,
        location: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        max_distance_km: Optional[float] = None,
        sort_by: Optional[str] = "newest"
    ) -> LivestockListResponse:
        skip = (page - 1) * page_size
        items, total = LivestockRepository.search_marketplace(
            db=db,
            skip=skip,
            limit=page_size,
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
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        responses = [
            LivestockService._map_to_response(
                db=db,
                item=item,
                distance_km=dist,
                is_near_you=is_near
            )
            for item, dist, is_near in items
        ]
        return LivestockListResponse(
            items=responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    @staticmethod
    def get_public_livestock_detail(db: Session, livestock_id: uuid.UUID) -> LivestockResponse:
        livestock = LivestockRepository.get_by_id(db, livestock_id)
        if not livestock or livestock.status != "PUBLISHED" or not livestock.is_active or livestock.is_deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livestock listing is unavailable.")
        return LivestockService._map_to_response(db, livestock)

    @staticmethod
    def list_reviews(
        db: Session,
        livestock_id: uuid.UUID,
        page: int = 1,
        page_size: int = 10
    ) -> List[LivestockReviewResponse]:
        skip = (page - 1) * page_size
        reviews, _ = LivestockReviewRepository.list_reviews_by_livestock(
            db=db,
            livestock_id=livestock_id,
            skip=skip,
            limit=page_size
        )
        result = []
        for r in reviews:
            resp = LivestockReviewResponse(
                id=r.id,
                livestock_id=r.livestock_id,
                order_id=r.order_id,
                customer_id=r.customer_id,
                customer_name=r.customer.full_name if r.customer else "Verified Buyer",
                rating=r.rating,
                review_text=r.review_text,
                is_verified_purchase=r.is_verified_purchase,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            result.append(resp)
        return result
