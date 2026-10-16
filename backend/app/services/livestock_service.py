import logging
import uuid
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.enums import LivestockStatus, LivestockSellingModel
from app.models.livestock import Livestock, LivestockCategory, LivestockBreed
from app.schemas.livestock import (
    LivestockCreateRequest,
    LivestockUpdateRequest,
    LivestockResponse,
    LivestockListResponse,
    FarmerLivestockStatsResponse,
    LivestockCategoryCreateRequest,
    LivestockCategoryUpdateRequest,
    LivestockCategoryResponse,
    LivestockBreedCreateRequest,
    LivestockBreedUpdateRequest,
    LivestockBreedResponse,
    LivestockImageResponse,
    LivestockFarmSummary,
    LivestockFarmerSummary,
)
from app.repositories.livestock_repository import LivestockRepository
from app.repositories.livestock_category_repository import LivestockCategoryRepository
from app.repositories.farm_repository import FarmRepository
from app.repositories.livestock_review_repository import LivestockReviewRepository

logger = logging.getLogger("agri_smart.livestock_service")


class LivestockService:
    """Business service handling Livestock Master Data, Farmer Livestock CRUD, and Status Transitions."""

    # ========================================================================
    # Category & Breed Master Administration
    # ========================================================================

    @staticmethod
    def list_categories(db: Session, is_active_only: bool = True) -> List[LivestockCategoryResponse]:
        categories = LivestockCategoryRepository.list_categories(db, is_active_only=is_active_only)
        result = []
        for cat in categories:
            breeds_resp = [
                LivestockBreedResponse.model_validate(b)
                for b in cat.breeds
                if not is_active_only or b.is_active
            ]
            cat_resp = LivestockCategoryResponse(
                id=cat.id,
                code=cat.code,
                name=cat.name,
                name_ta=cat.name_ta,
                description=cat.description,
                icon_slug=cat.icon_slug,
                display_order=cat.display_order,
                is_active=cat.is_active,
                breeds_count=len(breeds_resp),
                breeds=breeds_resp,
                created_at=cat.created_at,
                updated_at=cat.updated_at,
            )
            result.append(cat_resp)
        return result

    @staticmethod
    def create_category(db: Session, request: LivestockCategoryCreateRequest) -> LivestockCategoryResponse:
        existing = LivestockCategoryRepository.get_category_by_code(db, request.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category code '{request.code.upper()}' already exists."
            )
        category = LivestockCategoryRepository.create_category(db, request.model_dump())
        logger.info("Category %s created by admin", category.name)
        return LivestockCategoryResponse(
            id=category.id,
            code=category.code,
            name=category.name,
            name_ta=category.name_ta,
            description=category.description,
            icon_slug=category.icon_slug,
            display_order=category.display_order,
            is_active=category.is_active,
            breeds_count=0,
            breeds=[],
            created_at=category.created_at,
            updated_at=category.updated_at,
        )

    @staticmethod
    def update_category(db: Session, category_id: uuid.UUID, request: LivestockCategoryUpdateRequest) -> LivestockCategoryResponse:
        category = LivestockCategoryRepository.get_category_by_id(db, category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
        updated = LivestockCategoryRepository.update_category(db, category, request.model_dump(exclude_unset=True))
        return LivestockCategoryResponse.model_validate(updated)

    @staticmethod
    def list_breeds(db: Session, category_id: Optional[uuid.UUID] = None, is_active_only: bool = True) -> List[LivestockBreedResponse]:
        breeds = LivestockCategoryRepository.list_breeds(db, category_id=category_id, is_active_only=is_active_only)
        return [LivestockBreedResponse.model_validate(b) for b in breeds]

    @staticmethod
    def create_breed(db: Session, request: LivestockBreedCreateRequest) -> LivestockBreedResponse:
        category = LivestockCategoryRepository.get_category_by_id(db, request.category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
        breed = LivestockCategoryRepository.create_breed(db, request.model_dump())
        logger.info("Breed %s created under %s", breed.name, category.name)
        return LivestockBreedResponse.model_validate(breed)

    @staticmethod
    def update_breed(db: Session, breed_id: uuid.UUID, request: LivestockBreedUpdateRequest) -> LivestockBreedResponse:
        breed = LivestockCategoryRepository.get_breed_by_id(db, breed_id)
        if not breed:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Breed not found.")
        updated = LivestockCategoryRepository.update_breed(db, breed, request.model_dump(exclude_unset=True))
        return LivestockBreedResponse.model_validate(updated)

    # ========================================================================
    # Farmer Livestock CRUD & Management
    # ========================================================================

    @staticmethod
    def _map_to_response(
        db: Session,
        item: Livestock,
        distance_km: Optional[float] = None,
        is_near_you: Optional[bool] = None,
        is_in_district: Optional[bool] = None
    ) -> LivestockResponse:
        primary_img = next((img.image_url for img in item.images if img.is_primary), None)
        if not primary_img and item.images:
            primary_img = item.images[0].image_url

        avg_rating, review_count = LivestockReviewRepository.get_rating_summary(db, item.id)

        farm_summary = None
        if item.farm:
            farm_summary = LivestockFarmSummary(
                id=item.farm.id,
                farm_name=item.farm.farm_name,
                farm_code=item.farm.farm_code,
                village=item.farm.village,
                district=item.farm.district,
                state=item.farm.state,
                pincode=item.farm.pincode,
                latitude=item.farm.latitude,
                longitude=item.farm.longitude,
            )

        farmer_summary = None
        if item.farmer_profile:
            farmer_summary = LivestockFarmerSummary(
                id=item.farmer_profile.id,
                village=item.farmer_profile.village,
                district=item.farmer_profile.district,
                state=item.farmer_profile.state,
            )

        return LivestockResponse(
            id=item.id,
            livestock_code=item.livestock_code,
            farmer_profile_id=item.farmer_profile_id,
            farm_id=item.farm_id,
            category_id=item.category_id,
            breed_id=item.breed_id,
            name=item.name,
            tag_number=item.tag_number,
            selling_model=item.selling_model,
            gender=item.gender,
            date_of_birth=item.date_of_birth,
            age=item.age,
            age_unit=item.age_unit,
            weight=item.weight,
            weight_unit=item.weight_unit,
            health_status=item.health_status,
            vaccination_status=item.vaccination_status,
            vaccination_date=item.vaccination_date,
            health_certificate_url=item.health_certificate_url,
            description=item.description,
            location_summary=item.location_summary or (f"{item.farm.village}, {item.farm.district}" if item.farm else None),
            price=item.price,
            price_type=item.price_type,
            available_quantity=item.available_quantity,
            minimum_order_quantity=item.minimum_order_quantity,
            maximum_order_quantity=item.maximum_order_quantity,
            status=item.status,
            is_active=item.is_active,
            is_deleted=item.is_deleted,
            created_at=item.created_at,
            updated_at=item.updated_at,
            category_name=item.category.name if item.category else "",
            category_name_ta=item.category.name_ta if item.category else None,
            breed_name=item.breed.name if item.breed else None,
            breed_name_ta=item.breed.name_ta if item.breed else None,
            primary_image_url=primary_img,
            images=[LivestockImageResponse.model_validate(img) for img in item.images],
            farm=farm_summary,
            farmer=farmer_summary,
            average_rating=avg_rating,
            total_reviews_count=review_count,
            distance_km=distance_km,
            is_near_you=is_near_you,
            is_in_district=is_in_district,
        )

    @staticmethod
    def create_livestock(
        db: Session,
        current_user: User,
        request: LivestockCreateRequest
    ) -> LivestockResponse:
        farmer_profile = current_user.farmer_profile
        if not farmer_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Farmer profile must be registered before adding livestock."
            )

        # Validate farm ownership
        farm = FarmRepository.get_by_id(db, request.farm_id, farmer_profile_id=farmer_profile.id)
        if not farm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Selected farm was not found in your farm holdings."
            )

        # Validate category
        category = LivestockCategoryRepository.get_category_by_id(db, request.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid livestock category specified."
            )

        # Validate breed if provided
        if request.breed_id:
            breed = LivestockCategoryRepository.get_breed_by_id(db, request.breed_id)
            if not breed or breed.category_id != category.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Specified breed does not match the selected category."
                )

        # Validate Individual selling model rules
        if request.selling_model == LivestockSellingModel.INDIVIDUAL:
            if request.available_quantity != 1:
                request.available_quantity = 1

        code = LivestockRepository.generate_next_livestock_code(db)
        livestock = LivestockRepository.create(
            db=db,
            farmer_profile_id=farmer_profile.id,
            code=code,
            data=request.model_dump(),
            created_by=current_user.id
        )

        logger.info("Farmer %s created livestock %s (%s)", current_user.id, livestock.name, livestock.livestock_code)
        return LivestockService._map_to_response(db, livestock)

    @staticmethod
    def get_livestock_detail(
        db: Session,
        livestock_id: uuid.UUID,
        current_user: Optional[User] = None
    ) -> LivestockResponse:
        farmer_profile_id = current_user.farmer_profile.id if current_user and current_user.farmer_profile else None
        livestock = LivestockRepository.get_by_id(db, livestock_id, farmer_profile_id=farmer_profile_id)
        if not livestock:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livestock not found.")
        return LivestockService._map_to_response(db, livestock)

    @staticmethod
    def update_livestock(
        db: Session,
        current_user: User,
        livestock_id: uuid.UUID,
        request: LivestockUpdateRequest
    ) -> LivestockResponse:
        farmer_profile = current_user.farmer_profile
        if not farmer_profile:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Farmer profile required.")

        livestock = LivestockRepository.get_by_id(db, livestock_id, farmer_profile_id=farmer_profile.id)
        if not livestock:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livestock not found.")

        if request.farm_id:
            farm = FarmRepository.get_by_id(db, request.farm_id, farmer_profile_id=farmer_profile.id)
            if not farm:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specified farm not found.")

        updated = LivestockRepository.update(
            db=db,
            livestock=livestock,
            data=request.model_dump(exclude_unset=True),
            updated_by=current_user.id
        )
        return LivestockService._map_to_response(db, updated)

    @staticmethod
    def publish_livestock(db: Session, current_user: User, livestock_id: uuid.UUID) -> LivestockResponse:
        farmer_profile = current_user.farmer_profile
        if not farmer_profile:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Farmer profile required.")

        livestock = LivestockRepository.get_by_id(db, livestock_id, farmer_profile_id=farmer_profile.id)
        if not livestock:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livestock not found.")

        if livestock.available_quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot publish livestock with 0 available quantity."
            )

        updated = LivestockRepository.set_status(db, livestock, LivestockStatus.PUBLISHED.value, updated_by=current_user.id)
        logger.info("Livestock %s published to marketplace by farmer %s", livestock.livestock_code, current_user.id)
        return LivestockService._map_to_response(db, updated)

    @staticmethod
    def unpublish_livestock(db: Session, current_user: User, livestock_id: uuid.UUID) -> LivestockResponse:
        farmer_profile = current_user.farmer_profile
        if not farmer_profile:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Farmer profile required.")

        livestock = LivestockRepository.get_by_id(db, livestock_id, farmer_profile_id=farmer_profile.id)
        if not livestock:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livestock not found.")

        updated = LivestockRepository.set_status(db, livestock, LivestockStatus.DRAFT.value, updated_by=current_user.id)
        return LivestockService._map_to_response(db, updated)

    @staticmethod
    def archive_livestock(db: Session, current_user: User, livestock_id: uuid.UUID) -> LivestockResponse:
        farmer_profile = current_user.farmer_profile
        if not farmer_profile:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Farmer profile required.")

        livestock = LivestockRepository.get_by_id(db, livestock_id, farmer_profile_id=farmer_profile.id)
        if not livestock:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livestock not found.")

        updated = LivestockRepository.set_status(db, livestock, LivestockStatus.ARCHIVED.value, updated_by=current_user.id)
        return LivestockService._map_to_response(db, updated)

    @staticmethod
    def delete_livestock(db: Session, current_user: User, livestock_id: uuid.UUID) -> LivestockResponse:
        farmer_profile = current_user.farmer_profile
        if not farmer_profile:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Farmer profile required.")

        livestock = LivestockRepository.get_by_id(db, livestock_id, farmer_profile_id=farmer_profile.id)
        if not livestock:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livestock not found.")

        deleted = LivestockRepository.soft_delete(db, livestock, deleted_by=current_user.id)
        return LivestockService._map_to_response(db, deleted)

    @staticmethod
    def list_farmer_livestock(
        db: Session,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        category_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> LivestockListResponse:
        farmer_profile = current_user.farmer_profile
        if not farmer_profile:
            return LivestockListResponse(items=[], total=0, page=page, page_size=page_size, total_pages=0)

        skip = (page - 1) * page_size
        items, total = LivestockRepository.list_farmer_livestock(
            db=db,
            farmer_profile_id=farmer_profile.id,
            skip=skip,
            limit=page_size,
            category_id=category_id,
            status=status,
            search=search
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        responses = [LivestockService._map_to_response(db, item) for item in items]
        return LivestockListResponse(
            items=responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    @staticmethod
    def get_farmer_dashboard_stats(db: Session, current_user: User) -> FarmerLivestockStatsResponse:
        farmer_profile = current_user.farmer_profile
        if not farmer_profile:
            return FarmerLivestockStatsResponse()

        stats = LivestockRepository.get_farmer_stats(db, farmer_profile.id)
        from app.models.marketplace_order import MarketplaceOrder

        farmer_orders = list(db.scalars(
            select(MarketplaceOrder).where(
                MarketplaceOrder.farmer_profile_id == farmer_profile.id,
                MarketplaceOrder.is_deleted == False
            )
        ).unique().all())

        pending_orders = sum(1 for o in farmer_orders if o.status in {"PENDING", "CONFIRMED", "PROCESSING"})
        sales_count = sum(1 for o in farmer_orders if o.status in {"FARMER_ACCEPTED", "PROCESSING", "READY_FOR_PICKUP", "OUT_FOR_DELIVERY", "DELIVERED"})
        revenue = sum(o.total_amount for o in farmer_orders if o.status in {"FARMER_ACCEPTED", "PROCESSING", "READY_FOR_PICKUP", "OUT_FOR_DELIVERY", "DELIVERED"})

        return FarmerLivestockStatsResponse(
            total_livestock=stats.get("total_livestock", 0),
            available_count=stats.get("available_count", 0),
            reserved_count=stats.get("reserved_count", 0),
            sold_count=stats.get("sold_count", 0),
            drafts_count=stats.get("drafts_count", 0),
            total_sales_count=sales_count,
            sales_count=sales_count,
            pending_orders_count=pending_orders,
            pending_orders=pending_orders,
            total_revenue=revenue,
            revenue=revenue,
        )

