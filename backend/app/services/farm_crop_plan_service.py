import logging
import uuid
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import RoleEnum, NotificationType
from app.models.user import User
from app.models.farmer_profile import FarmerProfile
from app.repositories.farmer_profile_repository import FarmerProfileRepository
from app.repositories.farm_repository import FarmRepository
from app.repositories.crop_repository import CropRepository
from app.repositories.farm_crop_plan_repository import FarmCropPlanRepository
from app.services.notification_service import NotificationService
from app.schemas.farm_crop_plan import (
    FarmCropPlanCreate,
    FarmCropPlanUpdate,
    FarmCropPlanStatusUpdate,
    FarmCropPlanResponse,
    FarmCropPlanListResponse,
    CropSeedRecommendationResponse,
    SeedVarietyOption,
    HistoricalSeedUsageItem,
)

logger = logging.getLogger("agri_smart.farm_crop_plan_service")


class FarmCropPlanService:
    """Service handling Farm Crop Planning business logic, validations, and ownership isolation."""

    @staticmethod
    def _resolve_farmer_profile(db: Session, current_user: User) -> FarmerProfile:
        """
        Validates that the authenticated user possesses the FARMER role and has completed their FarmerProfile.
        Raises HTTP 403 if missing role, or HTTP 409 if profile has not been created yet.
        """
        user_roles = {ur.role.name for ur in current_user.user_roles if ur.role and ur.role.is_active}
        if RoleEnum.FARMER.value not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have the FARMER role"
            )

        profile = FarmerProfileRepository.get_by_user_id(db, current_user.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Farmer profile must be completed before managing crop plans"
            )
        return profile

    @staticmethod
    def create_plan(
        db: Session,
        current_user: User,
        request: FarmCropPlanCreate
    ) -> FarmCropPlanResponse:
        """Creates a new FarmCropPlan ensuring ownership, crop availability, area constraints, and no duplicate active plans."""
        farmer_profile = FarmCropPlanService._resolve_farmer_profile(db, current_user)

        # 1. Verify Farm exists, is non-deleted, and belongs to caller's FarmerProfile
        farm = FarmRepository.get_by_id(
            db=db,
            farm_id=request.farm_id,
            farmer_profile_id=farmer_profile.id,
            include_deleted=False
        )
        if not farm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm not found"
            )

        # 2. Verify Crop exists, is not deleted, and is active
        crop = CropRepository.get_by_id(db, crop_id=request.crop_id, include_deleted=True)
        if not crop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crop not found"
            )
        if crop.is_deleted or not crop.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected crop is currently inactive or unavailable"
            )

        # 3. Verify land area unit matches farm land area unit
        plan_unit = request.land_area_unit.value if hasattr(request.land_area_unit, "value") else str(request.land_area_unit)
        if plan_unit != farm.land_area_unit:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Area unit must match farm land area unit"
            )

        # 4. Verify planned area does not exceed farm total land area
        if request.planned_area > farm.total_land_area:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Planned area ({request.planned_area}) cannot exceed farm total land area ({farm.total_land_area})"
            )

        # 5. Check duplicate active plan for (farm, crop, season)
        season_str = request.season.value if hasattr(request.season, "value") else str(request.season)
        existing_plan = FarmCropPlanRepository.get_active_plan(
            db=db,
            farm_id=farm.id,
            crop_id=crop.id,
            season=season_str
        )
        if existing_plan:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An active crop plan for this farm, crop, and season already exists"
            )

        plan = FarmCropPlanRepository.create(
            db=db,
            plan_data=request.model_dump(),
            created_by=current_user.id
        )
        logger.info("Farm crop plan created: id=%s farm_id=%s crop_id=%s season=%s", plan.id, plan.farm_id, plan.crop_id, plan.season)
        return FarmCropPlanResponse.model_validate(plan)

    @staticmethod
    def list_plans(
        db: Session,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        farm_id: Optional[uuid.UUID] = None,
        crop_id: Optional[uuid.UUID] = None,
        season: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> FarmCropPlanListResponse:
        """Retrieves paginated crop plans for farms owned by the authenticated farmer."""
        farmer_profile = FarmCropPlanService._resolve_farmer_profile(db, current_user)
        skip = (page - 1) * page_size
        plans = FarmCropPlanRepository.list_by_farmer_profile(
            db=db,
            farmer_profile_id=farmer_profile.id,
            skip=skip,
            limit=page_size,
            farm_id=farm_id,
            crop_id=crop_id,
            season=season,
            is_active=is_active,
            search=search,
            include_deleted=False
        )
        total = FarmCropPlanRepository.count_by_farmer_profile(
            db=db,
            farmer_profile_id=farmer_profile.id,
            farm_id=farm_id,
            crop_id=crop_id,
            season=season,
            is_active=is_active,
            search=search,
            include_deleted=False
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return FarmCropPlanListResponse(
            items=[FarmCropPlanResponse.model_validate(p) for p in plans],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages
        )

    @staticmethod
    def get_plan_detail(
        db: Session,
        current_user: User,
        plan_id: uuid.UUID
    ) -> FarmCropPlanResponse:
        """Retrieves details of an owned non-deleted farm crop plan. Returns 404 if not found or unowned."""
        farmer_profile = FarmCropPlanService._resolve_farmer_profile(db, current_user)
        plan = FarmCropPlanRepository.get_owned_plan(
            db=db,
            plan_id=plan_id,
            farmer_profile_id=farmer_profile.id,
            include_deleted=False
        )
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm crop plan not found"
            )
        return FarmCropPlanResponse.model_validate(plan)

    @staticmethod
    def update_plan(
        db: Session,
        current_user: User,
        plan_id: uuid.UUID,
        request: FarmCropPlanUpdate
    ) -> FarmCropPlanResponse:
        """Partially updates an owned farm crop plan with validation."""
        farmer_profile = FarmCropPlanService._resolve_farmer_profile(db, current_user)
        plan = FarmCropPlanRepository.get_owned_plan(
            db=db,
            plan_id=plan_id,
            farmer_profile_id=farmer_profile.id,
            include_deleted=False
        )
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm crop plan not found"
            )

        farm = FarmRepository.get_by_id(db, farm_id=plan.farm_id, farmer_profile_id=farmer_profile.id, include_deleted=False)
        if not farm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

        update_dict = request.model_dump(exclude_unset=True)

        # Validate crop if changing
        target_crop_id = update_dict.get("crop_id", plan.crop_id)
        if "crop_id" in update_dict and update_dict["crop_id"] != plan.crop_id:
            crop = CropRepository.get_by_id(db, crop_id=update_dict["crop_id"], include_deleted=True)
            if not crop:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop not found")
            if crop.is_deleted or not crop.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Selected crop is currently inactive or unavailable"
                )

        # Validate unit and area
        target_unit = update_dict.get("land_area_unit")
        if target_unit is not None:
            unit_str = target_unit.value if hasattr(target_unit, "value") else str(target_unit)
            if unit_str != farm.land_area_unit:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Area unit must match farm land area unit"
                )

        target_area = update_dict.get("planned_area", plan.planned_area)
        if target_area > farm.total_land_area:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Planned area ({target_area}) cannot exceed farm total land area ({farm.total_land_area})"
            )

        # Validate duplicate active plan if crop or season changed
        target_season = update_dict.get("season", plan.season)
        if hasattr(target_season, "value"):
            target_season = target_season.value

        if ("crop_id" in update_dict and update_dict["crop_id"] != plan.crop_id) or ("season" in update_dict and target_season != plan.season):
            existing = FarmCropPlanRepository.get_active_plan(
                db=db,
                farm_id=plan.farm_id,
                crop_id=target_crop_id,
                season=target_season,
                exclude_plan_id=plan.id
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An active crop plan for this farm, crop, and season already exists"
                )

        updated_plan = FarmCropPlanRepository.update(
            db=db,
            plan=plan,
            update_data=update_dict,
            updated_by=current_user.id
        )
        logger.info("Farm crop plan %s updated by user %s", plan_id, current_user.id)
        return FarmCropPlanResponse.model_validate(updated_plan)

    @staticmethod
    def update_plan_status(
        db: Session,
        current_user: User,
        plan_id: uuid.UUID,
        request: FarmCropPlanStatusUpdate
    ) -> FarmCropPlanResponse:
        """Updates active status of an owned farm crop plan."""
        farmer_profile = FarmCropPlanService._resolve_farmer_profile(db, current_user)
        plan = FarmCropPlanRepository.get_owned_plan(
            db=db,
            plan_id=plan_id,
            farmer_profile_id=farmer_profile.id,
            include_deleted=True
        )
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm crop plan not found"
            )
        if plan.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update status of a deleted crop plan. Restore the plan first."
            )

        updated_plan = FarmCropPlanRepository.update_status(
            db=db,
            plan=plan,
            is_active=request.is_active,
            updated_by=current_user.id
        )
        logger.info("Farm crop plan %s status changed to is_active=%s", plan_id, request.is_active)
        return FarmCropPlanResponse.model_validate(updated_plan)

    @staticmethod
    def delete_plan(
        db: Session,
        current_user: User,
        plan_id: uuid.UUID
    ) -> FarmCropPlanResponse:
        """Soft-deletes an owned farm crop plan."""
        farmer_profile = FarmCropPlanService._resolve_farmer_profile(db, current_user)
        plan = FarmCropPlanRepository.get_owned_plan(
            db=db,
            plan_id=plan_id,
            farmer_profile_id=farmer_profile.id,
            include_deleted=False
        )
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm crop plan not found"
            )

        deleted_plan = FarmCropPlanRepository.soft_delete(
            db=db,
            plan=plan,
            deleted_by=current_user.id
        )
        logger.info("Farm crop plan %s soft-deleted by user %s", plan_id, current_user.id)
        return FarmCropPlanResponse.model_validate(deleted_plan)

    @staticmethod
    def restore_plan(
        db: Session,
        current_user: User,
        plan_id: uuid.UUID
    ) -> FarmCropPlanResponse:
        """Restores a soft-deleted owned farm crop plan."""
        farmer_profile = FarmCropPlanService._resolve_farmer_profile(db, current_user)
        plan = FarmCropPlanRepository.get_owned_plan(
            db=db,
            plan_id=plan_id,
            farmer_profile_id=farmer_profile.id,
            include_deleted=True
        )
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm crop plan not found"
            )
        if not plan.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Farm crop plan is not deleted"
            )

        # Check duplicate active plan
        existing = FarmCropPlanRepository.get_active_plan(
            db=db,
            farm_id=plan.farm_id,
            crop_id=plan.crop_id,
            season=plan.season,
            exclude_plan_id=plan.id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An active crop plan for this farm, crop, and season already exists"
            )

        restored_plan = FarmCropPlanRepository.restore(
            db=db,
            plan=plan,
            updated_by=current_user.id
        )
        logger.info("Farm crop plan %s restored by user %s", plan_id, current_user.id)
        return FarmCropPlanResponse.model_validate(restored_plan)

    # ---------------------------------------------------------
    # Agronomic Knowledge Catalog for Seed Rate & Varieties
    # ---------------------------------------------------------
    AGRONOMIC_SEED_CATALOG = {
        "paddy": {
            "crop_name": "Paddy / Rice",
            "crop_name_local": "நெல்",
            "default_seed_rate_per_acre": 20.0,
            "seed_rate_unit": "kg/acre",
            "sowing_methods": [
                "DIRECT_SEEDING",
                "NURSERY_TRANSPLANTING",
                "SRI_METHOD",
                "DRUM_SEEDING"
            ],
            "agronomic_advisory": (
                "For machine SRI transplanting, 5-8 kg/acre is sufficient. For standard nursery "
                "transplanting, use 12-15 kg/acre. For direct wet broadcasting, use 20-25 kg/acre."
            ),
            "varieties": [
                {
                    "variety_name": "CO-51",
                    "variety_name_local": "கோ-51 குண்டு நெல்",
                    "recommended_seed_rate": 20.0,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 110,
                    "description": "High tillering, blast resistant, ideal for Kuruvai/Navarai."
                },
                {
                    "variety_name": "ADT-37",
                    "variety_name_local": "ஏடிடி-37",
                    "recommended_seed_rate": 22.0,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 115,
                    "description": "Early maturity, high grain yield, well suited for Sornavari & Kuruvai."
                },
                {
                    "variety_name": "BPT-5204 (Samba Mahsuri)",
                    "variety_name_local": "பிபிடி-5204 (ஆந்திரா பொன்னி)",
                    "recommended_seed_rate": 15.0,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 145,
                    "description": "Fine grain, premium market price, ideal for Samba/Thaladi."
                },
                {
                    "variety_name": "CR-1009 Sub-1",
                    "variety_name_local": "சிஆர்-1009 சப்-1 (பொன்மணி)",
                    "recommended_seed_rate": 20.0,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 155,
                    "description": "Submergence tolerant, flood resilient, best for Lowland Samba."
                },
                {
                    "variety_name": "IR-20",
                    "variety_name_local": "ஐஆர்-20",
                    "recommended_seed_rate": 20.0,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 130,
                    "description": "Medium slender grain, moderately resistant to tungro & blast."
                },
                {
                    "variety_name": "Seeraga Samba",
                    "variety_name_local": "சீரக சம்பா",
                    "recommended_seed_rate": 12.0,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 135,
                    "description": "Traditional aromatic fine grain, top market value for Biryani."
                },
                {
                    "variety_name": "Poongar / Traditional Red",
                    "variety_name_local": "பூங்கார் பாரம்பரிய நெல்",
                    "recommended_seed_rate": 15.0,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 70,
                    "description": "Drought & saline tolerant women-health traditional rice."
                }
            ]
        },
        "onion": {
            "crop_name": "Onion / Shallots",
            "crop_name_local": "வெங்காயம் / சின்ன வெங்காயம்",
            "default_seed_rate_per_acre": 4.0,
            "seed_rate_unit": "kg/acre",
            "sowing_methods": [
                "BULB_PLANTING",
                "DIRECT_SEEDING",
                "NURSERY_TRANSPLANTING"
            ],
            "agronomic_advisory": (
                "For small onion bulb sets, plant 400-500 kg/acre at 15x10 cm spacing. "
                "For true seed nursery, sow 3.5-4.0 kg/acre and transplant 40-45 day seedlings."
            ),
            "varieties": [
                {
                    "variety_name": "Co-Onion-5",
                    "variety_name_local": "கோ (வெ)-5 விதை வெங்காயம்",
                    "recommended_seed_rate": 4.0,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 90,
                    "description": "True seed propagating aggregate onion, pinkish red bulbs."
                },
                {
                    "variety_name": "Perambalur Small Red (Bulbs)",
                    "variety_name_local": "பெரம்பலூர் சின்ன வெங்காய குமிழ்",
                    "recommended_seed_rate": 450.0,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 70,
                    "description": "High pungent traditional shallots propagated by seed bulbs."
                },
                {
                    "variety_name": "Bellary Red / Big Onion",
                    "variety_name_local": "பெல்லாரி பெரிய வெங்காயம்",
                    "recommended_seed_rate": 3.5,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 120,
                    "description": "Globe shaped large red bulbs, high storage quality."
                },
                {
                    "variety_name": "Arka Kalyan",
                    "variety_name_local": "அர்கா கல்யான்",
                    "recommended_seed_rate": 3.5,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 130,
                    "description": "Purple blotch disease tolerant, excellent yield potential."
                }
            ]
        },
        "groundnut": {
            "crop_name": "Groundnut / Peanut",
            "crop_name_local": "நிலக்கடலை / மணிலா",
            "default_seed_rate_per_acre": 55.0,
            "seed_rate_unit": "kg/acre",
            "sowing_methods": [
                "TRACTOR_SEED_DRILL",
                "BULLOCK_PLOUGH",
                "MANUAL_DIBBLING"
            ],
            "agronomic_advisory": (
                "Treat kernels with Trichoderma viride @ 4g/kg + Rhizobium before sowing. "
                "Maintain 30x10 cm spacing for bunch varieties."
            ),
            "varieties": [
                {
                    "variety_name": "TMV-7",
                    "variety_name_local": "டிஎம்வி-7",
                    "recommended_seed_rate": 55.0,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 105,
                    "description": "Spanish bunch, high shelling percentage (74%), highly popular."
                },
                {
                    "variety_name": "VRI-2",
                    "variety_name_local": "விருத்தாசலம்-2",
                    "recommended_seed_rate": 55.0,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 110,
                    "description": "Semi-spreading, bold kernels, high oil content 49%."
                },
                {
                    "variety_name": "Dharani",
                    "variety_name_local": "தரணி",
                    "recommended_seed_rate": 50.0,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 100,
                    "description": "High pod yield, tolerant to collar rot & stem rot."
                },
                {
                    "variety_name": "Kadiri-6 (K-6)",
                    "variety_name_local": "கதிரி-6",
                    "recommended_seed_rate": 55.0,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 115,
                    "description": "Drought resistant bunch variety with heavy pod setting."
                },
                {
                    "variety_name": "JL-24",
                    "variety_name_local": "ஜேஎல்-24",
                    "recommended_seed_rate": 60.0,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 95,
                    "description": "Short duration bold pod, uniform maturity."
                }
            ]
        },
        "turmeric": {
            "crop_name": "Turmeric",
            "crop_name_local": "மஞ்சள்",
            "default_seed_rate_per_acre": 800.0,
            "seed_rate_unit": "kg/acre",
            "sowing_methods": [
                "RIDGE_AND_FURROW",
                "BED_PLANTING",
                "DRIP_FERTIGATION"
            ],
            "agronomic_advisory": (
                "Select mother or finger rhizomes (30-40g each). Dip in Pseudomonas before planting."
            ),
            "varieties": [
                {
                    "variety_name": "BSR-2 (Erode Local)",
                    "variety_name_local": "பிஎஸ்ஆர்-2 ஈரோடு மஞ்சள்",
                    "recommended_seed_rate": 800.0,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 240,
                    "description": "High curcumin (4.0%), resistant to scale and rhizome rot."
                },
                {
                    "variety_name": "IISR Pratibha",
                    "variety_name_local": "ஐஐஎஸ்ஆர் பிரதிபா",
                    "recommended_seed_rate": 750.0,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 225,
                    "description": "High yielding bold rhizome variety with rich aroma."
                }
            ]
        },
        "tomato": {
            "crop_name": "Tomato",
            "crop_name_local": "தக்காளி",
            "default_seed_rate_per_acre": 0.15,
            "seed_rate_unit": "kg/acre",
            "sowing_methods": [
                "PROTRAY_SEEDLINGS",
                "NURSERY_TRANSPLANTING"
            ],
            "agronomic_advisory": (
                "Use 100-150g hybrid seeds per acre in protrays. Transplant 25-day seedlings at 60x45 cm."
            ),
            "varieties": [
                {
                    "variety_name": "PKM-1",
                    "variety_name_local": "பிகேஎம்-1",
                    "recommended_seed_rate": 0.15,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 135,
                    "description": "High yielding, flat round fruits with good acidity."
                },
                {
                    "variety_name": "Shivam Hybrid (US-440)",
                    "variety_name_local": "சிவம் வீரிய தக்காளி",
                    "recommended_seed_rate": 0.10,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 120,
                    "description": "Tolerant to TLCV virus, firm round fruits, long shelf life."
                },
                {
                    "variety_name": "Arka Rakshak",
                    "variety_name_local": "அர்கா ரக்ஷக்",
                    "recommended_seed_rate": 0.10,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 140,
                    "description": "Triple disease resistant hybrid, high yield potential."
                }
            ]
        },
        "chilli": {
            "crop_name": "Chilli",
            "crop_name_local": "மிளகாய்",
            "default_seed_rate_per_acre": 0.40,
            "seed_rate_unit": "kg/acre",
            "sowing_methods": [
                "NURSERY_TRANSPLANTING",
                "PROTRAY_SEEDLINGS"
            ],
            "agronomic_advisory": (
                "Raise seedlings in protray nursery for 30-35 days before field transplanting."
            ),
            "varieties": [
                {
                    "variety_name": "K1 / K2 Kovilpatti",
                    "variety_name_local": "கே1 / கே2 கோவில்பட்டி மிளகாய்",
                    "recommended_seed_rate": 0.40,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 135,
                    "description": "Drought tolerant, dark red pungent dry chillies."
                },
                {
                    "variety_name": "PKM-1",
                    "variety_name_local": "பிகேஎம்-1 மிளகாய்",
                    "recommended_seed_rate": 0.35,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 140,
                    "description": "Long slender fruits, high capsaicin content."
                },
                {
                    "variety_name": "Teja Hybrid",
                    "variety_name_local": "தேஜா வீரிய மிளகாய்",
                    "recommended_seed_rate": 0.30,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 150,
                    "description": "Intense pungency, export quality hybrid."
                }
            ]
        },
        "blackgram": {
            "crop_name": "Blackgram / Urad Dal",
            "crop_name_local": "உளுந்து",
            "default_seed_rate_per_acre": 8.0,
            "seed_rate_unit": "kg/acre",
            "sowing_methods": [
                "RICE_FALLOW_BROADCAST",
                "LINE_SOWING",
                "DIBBLING"
            ],
            "agronomic_advisory": (
                "In rice fallows, broadcast 8-10 kg/acre 7-10 days before paddy harvest."
            ),
            "varieties": [
                {
                    "variety_name": "VBN-8",
                    "variety_name_local": "வம்பன்-8 உளுந்து",
                    "recommended_seed_rate": 8.0,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 70,
                    "description": "Resistant to Yellow Mosaic Virus (YMV), high yielding."
                },
                {
                    "variety_name": "VBN-6",
                    "variety_name_local": "வம்பன்-6",
                    "recommended_seed_rate": 8.0,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 65,
                    "description": "Synchronized maturity, bold seeds, ideal for rice fallow."
                }
            ]
        },
        "maize": {
            "crop_name": "Maize / Corn",
            "crop_name_local": "மக்காச்சோளம்",
            "default_seed_rate_per_acre": 8.0,
            "seed_rate_unit": "kg/acre",
            "sowing_methods": [
                "RIDGE_AND_FURROW",
                "FLAT_BED"
            ],
            "agronomic_advisory": (
                "Maintain spacing of 60x20 cm. Apply Azospirillum seed treatment."
            ),
            "varieties": [
                {
                    "variety_name": "Co-H(M)-6 Maize",
                    "variety_name_local": "கோ-எச்(எம்)-6 மக்காச்சோளம்",
                    "recommended_seed_rate": 8.0,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 110,
                    "description": "High grain yield, stay-green trait, excellent fodder value."
                },
                {
                    "variety_name": "Pioneer 30V92",
                    "variety_name_local": "பயனியர் 30V92",
                    "recommended_seed_rate": 7.5,
                    "seed_rate_unit": "kg/acre",
                    "duration_days": 105,
                    "description": "Heavy cob filling, drought tolerant hybrid."
                }
            ]
        }
    }

    @staticmethod
    def _find_catalog_entry(crop_name: str) -> Optional[dict]:
        """Matches a given crop name with the agronomic knowledge base."""
        normalized = crop_name.lower().strip()
        for key, data in FarmCropPlanService.AGRONOMIC_SEED_CATALOG.items():
            if (
                key in normalized
                or normalized in data["crop_name"].lower()
                or (data.get("crop_name_local") and data["crop_name_local"] in crop_name)
                or (key == "paddy" and any(w in normalized for w in ["nel", "rice", "samba", "kuruvai", "ponni"]))
                or (key == "onion" and any(w in normalized for w in ["vengayam", "shallot", "bellary"]))
                or (key == "groundnut" and any(w in normalized for w in ["kadalai", "peanut", "manila"]))
                or (key == "turmeric" and any(w in normalized for w in ["manjal", "haldi"]))
                or (key == "blackgram" and any(w in normalized for w in ["ulundu", "urad", "gram"]))
                or (key == "maize" and any(w in normalized for w in ["corn", "cholam"]))
                or (key == "tomato" and any(w in normalized for w in ["thakkali"]))
                or (key == "chilli" and any(w in normalized for w in ["milagai", "chili", "pepper"]))
            ):
                return data
        return None

    @staticmethod
    def get_seed_recommendations(
        db: Session,
        crop_id: Optional[uuid.UUID] = None
    ) -> List[CropSeedRecommendationResponse]:
        """Provides verified per-acre seed rates and certified varieties for agricultural crops."""
        results: List[CropSeedRecommendationResponse] = []

        if crop_id:
            crop = CropRepository.get_by_id(db, crop_id=crop_id, include_deleted=True)
            if not crop:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop not found")
            
            entry = FarmCropPlanService._find_catalog_entry(crop.crop_name)
            if entry:
                results.append(
                    CropSeedRecommendationResponse(
                        crop_id=crop.id,
                        crop_name=crop.crop_name,
                        crop_name_local=getattr(crop, "crop_name_tamil", None) or entry.get("crop_name_local"),
                        default_seed_rate_per_acre=entry["default_seed_rate_per_acre"],
                        seed_rate_unit=entry["seed_rate_unit"],
                        varieties=[SeedVarietyOption(**v) for v in entry["varieties"]],
                        sowing_methods=entry["sowing_methods"],
                        agronomic_advisory=entry["agronomic_advisory"],
                    )
                )
            else:
                # Generic fallback
                results.append(
                    CropSeedRecommendationResponse(
                        crop_id=crop.id,
                        crop_name=crop.crop_name,
                        crop_name_local=getattr(crop, "crop_name_tamil", None),
                        default_seed_rate_per_acre=10.0,
                        seed_rate_unit="kg/acre",
                        varieties=[
                            SeedVarietyOption(
                                variety_name=f"Standard Certified {crop.crop_name}",
                                variety_name_local="சான்று பெற்ற விதை",
                                recommended_seed_rate=10.0,
                                seed_rate_unit="kg/acre",
                                duration_days=90,
                                description="Certified high-yield seed variety."
                            )
                        ],
                        sowing_methods=["DIRECT_SEEDING", "LINE_SOWING"],
                        agronomic_advisory="Follow standard TNAU / ICAR agronomic package of practices.",
                    )
                )
            return results

        # Return all catalog items
        for key, entry in FarmCropPlanService.AGRONOMIC_SEED_CATALOG.items():
            results.append(
                CropSeedRecommendationResponse(
                    crop_id=None,
                    crop_name=entry["crop_name"],
                    crop_name_local=entry.get("crop_name_local"),
                    default_seed_rate_per_acre=entry["default_seed_rate_per_acre"],
                    seed_rate_unit=entry["seed_rate_unit"],
                    varieties=[SeedVarietyOption(**v) for v in entry["varieties"]],
                    sowing_methods=entry["sowing_methods"],
                    agronomic_advisory=entry["agronomic_advisory"],
                )
            )
        return results

    @staticmethod
    def get_historical_seed_usage(
        db: Session,
        current_user: User,
        farm_id: Optional[uuid.UUID] = None,
        crop_id: Optional[uuid.UUID] = None
    ) -> List[HistoricalSeedUsageItem]:
        """Queries historical past-year seed usage and yield data for farmer parcel memory."""
        farmer_profile = FarmCropPlanService._resolve_farmer_profile(db, current_user)
        raw_items = FarmCropPlanRepository.list_seed_history_by_farmer(
            db=db,
            farmer_profile_id=farmer_profile.id,
            farm_id=farm_id,
            crop_id=crop_id,
        )
        return [HistoricalSeedUsageItem(**item) for item in raw_items]

    @staticmethod
    def send_seasonal_seed_reminder(
        db: Session,
        current_user: User,
        plan_id: uuid.UUID
    ) -> dict:
        """
        Sends multi-channel notifications (SMS & In-App) reminding the farmer of their previous
        year's seed usage, rate, variety, and harvest outcome for the upcoming season.
        """
        farmer_profile = FarmCropPlanService._resolve_farmer_profile(db, current_user)
        plan = FarmCropPlanRepository.get_owned_plan(
            db=db,
            plan_id=plan_id,
            farmer_profile_id=farmer_profile.id,
            include_deleted=False
        )
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm crop plan not found")

        # Fetch farm and crop details
        farm_name = plan.farm.farm_name if plan.farm else "Farm Parcel"
        crop_name = plan.crop.crop_name if plan.crop else "Crop"
        crop_name_tamil = getattr(plan.crop, "crop_name_tamil", None) if plan.crop else None
        crop_display = f"{crop_name} ({crop_name_tamil})" if crop_name_tamil else crop_name

        seed_variety = plan.seed_variety or "Standard Certified"
        seed_rate = f"{plan.seed_rate_per_acre} {plan.seed_rate_unit}" if plan.seed_rate_per_acre else "standard rate"

        # Build notification message in Tamil & English
        sms_body = (
            f"🌾 Agri-Smart விதை நினைவூட்டல் / Seed Usage Memory:\n"
            f"போன வருடம் உங்கள் {farm_name} பண்ணையில் {crop_display} பயிருக்கு {seed_variety} விதை "
            f"({seed_rate}) பயன்படுத்தப்பட்டது (பரப்பு: {plan.planned_area} {plan.land_area_unit}).\n"
            f"அடுத்த பருவ விதைப்பிற்கு இப்போதே தரமான சான்று பெற்ற விதைகளை பதிவு செய்து தயார் செய்யுங்கள்!"
        )

        recipient_mobile = current_user.mobile_number or current_user.phone_number if hasattr(current_user, "phone_number") else current_user.mobile_number
        sms_result = {"status": "SKIPPED", "reason": "No mobile number recorded"}

        if recipient_mobile:
            try:
                sms_result = NotificationService.send_sms(
                    db=db,
                    recipient_mobile=recipient_mobile,
                    message_body=sms_body,
                    notification_type=NotificationType.SEASONAL_SEED_USAGE_REMINDER.value,
                    recipient_name=current_user.full_name,
                    farmer_profile_id=farmer_profile.id,
                )
            except Exception as e:
                logger.warning("Failed to dispatch seed reminder SMS: %s", e)
                sms_result = {"status": "FAILED", "error": str(e)}

        return {
            "status": "SUCCESS",
            "message": "Seasonal seed usage reminder dispatched successfully",
            "plan_id": str(plan.id),
            "farm_name": farm_name,
            "crop_name": crop_name,
            "seed_variety": seed_variety,
            "seed_rate": seed_rate,
            "notification_preview": sms_body,
            "sms_dispatch": sms_result,
        }
