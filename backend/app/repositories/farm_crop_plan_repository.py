import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from app.models.farm import Farm
from app.models.crop import Crop
from app.models.farm_crop_plan import FarmCropPlan


class FarmCropPlanRepository:
    """Repository handling FarmCropPlan database persistence operations."""

    @staticmethod
    def get_by_id(
        db: Session,
        plan_id: uuid.UUID,
        include_deleted: bool = False
    ) -> Optional[FarmCropPlan]:
        """Retrieve farm crop plan by primary key."""
        stmt = select(FarmCropPlan).where(FarmCropPlan.id == plan_id)
        if not include_deleted:
            stmt = stmt.where(FarmCropPlan.is_deleted == False)
        return db.scalar(stmt)

    @staticmethod
    def get_owned_plan(
        db: Session,
        plan_id: uuid.UUID,
        farmer_profile_id: uuid.UUID,
        include_deleted: bool = False
    ) -> Optional[FarmCropPlan]:
        """Retrieve farm crop plan ensuring it belongs to a farm owned by the specified farmer profile."""
        stmt = (
            select(FarmCropPlan)
            .join(Farm, FarmCropPlan.farm_id == Farm.id)
            .where(
                FarmCropPlan.id == plan_id,
                Farm.farmer_profile_id == farmer_profile_id
            )
        )
        if not include_deleted:
            stmt = stmt.where(FarmCropPlan.is_deleted == False, Farm.is_deleted == False)
        return db.scalar(stmt)

    @staticmethod
    def get_active_plan(
        db: Session,
        farm_id: uuid.UUID,
        crop_id: uuid.UUID,
        season: str,
        exclude_plan_id: Optional[uuid.UUID] = None
    ) -> Optional[FarmCropPlan]:
        """Check if an active, non-deleted crop plan already exists for this farm + crop + season combination."""
        clean_season = season.strip().upper()
        stmt = select(FarmCropPlan).where(
            FarmCropPlan.farm_id == farm_id,
            FarmCropPlan.crop_id == crop_id,
            func.upper(FarmCropPlan.season) == clean_season,
            FarmCropPlan.is_active == True,
            FarmCropPlan.is_deleted == False
        )
        if exclude_plan_id is not None:
            stmt = stmt.where(FarmCropPlan.id != exclude_plan_id)
        return db.scalar(stmt)

    @staticmethod
    def create(
        db: Session,
        plan_data: Dict[str, Any],
        created_by: Optional[uuid.UUID] = None
    ) -> FarmCropPlan:
        """Create a new farm crop plan record."""
        season_val = plan_data["season"]
        if hasattr(season_val, "value"):
            season_val = season_val.value
        else:
            season_val = str(season_val)

        unit_val = plan_data["land_area_unit"]
        if hasattr(unit_val, "value"):
            unit_val = unit_val.value
        else:
            unit_val = str(unit_val)

        seed_rate = plan_data.get("seed_rate_per_acre")
        total_seed = plan_data.get("total_seed_quantity")

        plan = FarmCropPlan(
            farm_id=plan_data["farm_id"],
            crop_id=plan_data["crop_id"],
            season=season_val,
            planned_start_date=plan_data.get("planned_start_date"),
            planned_end_date=plan_data.get("planned_end_date"),
            planned_area=Decimal(str(plan_data["planned_area"])),
            land_area_unit=unit_val,
            notes=plan_data.get("notes"),
            seed_variety=plan_data.get("seed_variety"),
            seed_rate_per_acre=Decimal(str(seed_rate)) if seed_rate is not None else None,
            seed_rate_unit=plan_data.get("seed_rate_unit") or "kg/acre",
            total_seed_quantity=Decimal(str(total_seed)) if total_seed is not None else None,
            sowing_method=plan_data.get("sowing_method") or "DIRECT_SEEDING",
            seed_brand_or_source=plan_data.get("seed_brand_or_source"),
            remind_next_year=plan_data.get("remind_next_year", True) if plan_data.get("remind_next_year") is not None else True,
            is_active=True,
            is_deleted=False,
            created_by=created_by,
            updated_by=created_by,
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def list_by_farmer_profile(
        db: Session,
        farmer_profile_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        farm_id: Optional[uuid.UUID] = None,
        crop_id: Optional[uuid.UUID] = None,
        season: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        include_deleted: bool = False
    ) -> List[FarmCropPlan]:
        """List crop plans for farms owned by a farmer profile with filters and pagination."""
        stmt = (
            select(FarmCropPlan)
            .join(Farm, FarmCropPlan.farm_id == Farm.id)
            .join(Crop, FarmCropPlan.crop_id == Crop.id)
            .where(Farm.farmer_profile_id == farmer_profile_id)
        )
        if not include_deleted:
            stmt = stmt.where(FarmCropPlan.is_deleted == False, Farm.is_deleted == False)
        if farm_id is not None:
            stmt = stmt.where(FarmCropPlan.farm_id == farm_id)
        if crop_id is not None:
            stmt = stmt.where(FarmCropPlan.crop_id == crop_id)
        if season:
            stmt = stmt.where(func.upper(FarmCropPlan.season) == season.strip().upper())
        if is_active is not None:
            stmt = stmt.where(FarmCropPlan.is_active == is_active)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Crop.crop_name.ilike(pattern),
                    Crop.crop_code.ilike(pattern),
                    Farm.farm_name.ilike(pattern),
                    Farm.farm_code.ilike(pattern),
                    FarmCropPlan.notes.ilike(pattern),
                )
            )
        stmt = stmt.order_by(FarmCropPlan.created_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    @staticmethod
    def count_by_farmer_profile(
        db: Session,
        farmer_profile_id: uuid.UUID,
        farm_id: Optional[uuid.UUID] = None,
        crop_id: Optional[uuid.UUID] = None,
        season: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        include_deleted: bool = False
    ) -> int:
        """Count total crop plans for farms owned by a farmer profile."""
        stmt = (
            select(func.count(FarmCropPlan.id))
            .join(Farm, FarmCropPlan.farm_id == Farm.id)
            .join(Crop, FarmCropPlan.crop_id == Crop.id)
            .where(Farm.farmer_profile_id == farmer_profile_id)
        )
        if not include_deleted:
            stmt = stmt.where(FarmCropPlan.is_deleted == False, Farm.is_deleted == False)
        if farm_id is not None:
            stmt = stmt.where(FarmCropPlan.farm_id == farm_id)
        if crop_id is not None:
            stmt = stmt.where(FarmCropPlan.crop_id == crop_id)
        if season:
            stmt = stmt.where(func.upper(FarmCropPlan.season) == season.strip().upper())
        if is_active is not None:
            stmt = stmt.where(FarmCropPlan.is_active == is_active)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Crop.crop_name.ilike(pattern),
                    Crop.crop_code.ilike(pattern),
                    Farm.farm_name.ilike(pattern),
                    Farm.farm_code.ilike(pattern),
                    FarmCropPlan.notes.ilike(pattern),
                )
            )
        return db.scalar(stmt) or 0

    @staticmethod
    def update(
        db: Session,
        plan: FarmCropPlan,
        update_data: Dict[str, Any],
        updated_by: Optional[uuid.UUID] = None
    ) -> FarmCropPlan:
        """Update mutable fields of a farm crop plan."""
        now = datetime.now(timezone.utc)
        disallowed = {"id", "farm_id", "created_at", "created_by", "is_deleted", "deleted_at", "deleted_by"}
        for key, value in update_data.items():
            if key not in disallowed and hasattr(plan, key):
                if key in {"planned_area", "seed_rate_per_acre", "total_seed_quantity"} and value is not None:
                    setattr(plan, key, Decimal(str(value)))
                elif key in {"season", "land_area_unit"} and value is not None:
                    setattr(plan, key, value.value if hasattr(value, "value") else str(value))
                else:
                    setattr(plan, key, value)
        plan.updated_by = updated_by
        plan.updated_at = now
        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def update_status(
        db: Session,
        plan: FarmCropPlan,
        is_active: bool,
        updated_by: Optional[uuid.UUID] = None
    ) -> FarmCropPlan:
        """Update active status of a farm crop plan."""
        plan.is_active = is_active
        plan.updated_by = updated_by
        plan.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def soft_delete(
        db: Session,
        plan: FarmCropPlan,
        deleted_by: Optional[uuid.UUID] = None
    ) -> FarmCropPlan:
        """Soft-delete a farm crop plan."""
        now = datetime.now(timezone.utc)
        plan.is_deleted = True
        plan.deleted_at = now
        plan.deleted_by = deleted_by
        plan.updated_by = deleted_by
        plan.updated_at = now
        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def restore(
        db: Session,
        plan: FarmCropPlan,
        updated_by: Optional[uuid.UUID] = None
    ) -> FarmCropPlan:
        """Restore a soft-deleted farm crop plan."""
        now = datetime.now(timezone.utc)
        plan.is_deleted = False
        plan.deleted_at = None
        plan.deleted_by = None
        plan.updated_by = updated_by
        plan.updated_at = now
        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def list_seed_history_by_farmer(
        db: Session,
        farmer_profile_id: uuid.UUID,
        farm_id: Optional[uuid.UUID] = None,
        crop_id: Optional[uuid.UUID] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Retrieve previous season seed usage history with yield metrics."""
        from app.models.cultivation import CultivationRun

        stmt = (
            select(
                FarmCropPlan,
                Farm.farm_name,
                Crop.crop_name,
                CultivationRun.yield_quantity,
                CultivationRun.yield_unit
            )
            .join(Farm, FarmCropPlan.farm_id == Farm.id)
            .join(Crop, FarmCropPlan.crop_id == Crop.id)
            .outerjoin(CultivationRun, CultivationRun.farm_crop_plan_id == FarmCropPlan.id)
            .where(
                Farm.farmer_profile_id == farmer_profile_id,
                FarmCropPlan.is_deleted == False,
                Farm.is_deleted == False
            )
        )
        if farm_id is not None:
            stmt = stmt.where(FarmCropPlan.farm_id == farm_id)
        if crop_id is not None:
            stmt = stmt.where(FarmCropPlan.crop_id == crop_id)

        stmt = stmt.order_by(FarmCropPlan.created_at.desc()).limit(limit)
        results = db.execute(stmt).all()

        history_items = []
        for plan, farm_name, crop_name, yield_qty, yield_unit in results:
            yield_per_acre = None
            if yield_qty is not None and plan.planned_area and plan.planned_area > 0:
                yield_per_acre = Decimal(str(yield_qty)) / plan.planned_area

            history_items.append({
                "plan_id": plan.id,
                "farm_id": plan.farm_id,
                "farm_name": farm_name,
                "crop_id": plan.crop_id,
                "crop_name": crop_name,
                "crop_name_local": getattr(plan.crop, "crop_name_tamil", None) if hasattr(plan, "crop") and plan.crop else None,
                "season": plan.season,
                "planned_start_date": plan.planned_start_date,
                "planned_area": plan.planned_area,
                "land_area_unit": plan.land_area_unit,
                "seed_variety": plan.seed_variety,
                "seed_rate_per_acre": plan.seed_rate_per_acre,
                "seed_rate_unit": plan.seed_rate_unit or "kg/acre",
                "total_seed_quantity": plan.total_seed_quantity,
                "sowing_method": plan.sowing_method,
                "seed_brand_or_source": plan.seed_brand_or_source,
                "achieved_yield_quantity": yield_qty,
                "yield_unit": yield_unit,
                "yield_per_acre": yield_per_acre,
                "created_at": plan.created_at,
            })
        return history_items
