import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from app.models.user import User
from app.models.crop import Crop
from app.models.farm import Farm
from app.models.farm_crop_plan import FarmCropPlan
from app.models.cultivation import CultivationRun, StageExpenseLog
from app.schemas.trash_bin import TrashEntityType, TrashBinItemResponse


class TrashBinRepository:
    """Universal repository for querying, restoring, and physically deleting soft-deleted entities."""

    @staticmethod
    def get_stats(db: Session) -> Dict[str, int]:
        """Returns the count of soft-deleted records grouped by entity type."""
        user_count = db.query(func.count(User.id)).filter(User.is_deleted == True).scalar() or 0
        crop_count = db.query(func.count(Crop.id)).filter(Crop.is_deleted == True).scalar() or 0
        farm_count = db.query(func.count(Farm.id)).filter(Farm.is_deleted == True).scalar() or 0
        plan_count = db.query(func.count(FarmCropPlan.id)).filter(FarmCropPlan.is_deleted == True).scalar() or 0
        cult_count = db.query(func.count(CultivationRun.id)).filter(CultivationRun.is_deleted == True).scalar() or 0
        exp_count = db.query(func.count(StageExpenseLog.id)).filter(StageExpenseLog.is_deleted == True).scalar() or 0

        return {
            TrashEntityType.USER.value: user_count,
            TrashEntityType.CROP.value: crop_count,
            TrashEntityType.FARM.value: farm_count,
            TrashEntityType.FARM_CROP_PLAN.value: plan_count,
            TrashEntityType.CULTIVATION.value: cult_count,
            TrashEntityType.STAGE_EXPENSE.value: exp_count,
            "ALL": user_count + crop_count + farm_count + plan_count + cult_count + exp_count,
        }

    @staticmethod
    def list_trash_items(
        db: Session,
        entity_type: Optional[TrashEntityType] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[TrashBinItemResponse], int]:
        """Aggregates and paginates soft-deleted items across the database."""
        all_items: List[TrashBinItemResponse] = []

        # 1. Users
        if entity_type is None or entity_type == TrashEntityType.USER:
            q = db.query(User).filter(User.is_deleted == True)
            if search:
                term = f"%{search}%"
                q = q.filter(or_(User.full_name.ilike(term), User.mobile_number.ilike(term), User.email.ilike(term)))
            for u in q.all():
                all_items.append(
                    TrashBinItemResponse(
                        id=u.id,
                        entity_type=TrashEntityType.USER,
                        entity_name=u.full_name,
                        entity_code=u.mobile_number,
                        deleted_at=u.deleted_at,
                        deleted_by=u.deleted_by,
                        created_at=u.created_at,
                        details={"email": u.email, "is_active": u.is_active},
                    )
                )

        # 2. Crops
        if entity_type is None or entity_type == TrashEntityType.CROP:
            q = db.query(Crop).filter(Crop.is_deleted == True)
            if search:
                term = f"%{search}%"
                q = q.filter(or_(Crop.crop_name.ilike(term), Crop.crop_code.ilike(term)))
            for c in q.all():
                all_items.append(
                    TrashBinItemResponse(
                        id=c.id,
                        entity_type=TrashEntityType.CROP,
                        entity_name=c.crop_name,
                        entity_code=c.crop_code,
                        deleted_at=c.deleted_at,
                        deleted_by=c.deleted_by,
                        created_at=c.created_at,
                        details={"category": c.crop_category, "scientific_name": c.scientific_name},
                    )
                )

        # 3. Farms
        if entity_type is None or entity_type == TrashEntityType.FARM:
            q = db.query(Farm).filter(Farm.is_deleted == True)
            if search:
                term = f"%{search}%"
                q = q.filter(or_(Farm.farm_name.ilike(term), Farm.farm_code.ilike(term), Farm.village.ilike(term)))
            for f in q.all():
                all_items.append(
                    TrashBinItemResponse(
                        id=f.id,
                        entity_type=TrashEntityType.FARM,
                        entity_name=f.farm_name,
                        entity_code=f.farm_code,
                        deleted_at=f.deleted_at,
                        deleted_by=f.deleted_by,
                        created_at=f.created_at,
                        details={
                            "ownership_type": f.ownership_type,
                            "total_land_area": float(f.total_land_area),
                            "land_area_unit": f.land_area_unit,
                            "village": f.village,
                        },
                    )
                )

        # 4. Farm Crop Plans
        if entity_type is None or entity_type == TrashEntityType.FARM_CROP_PLAN:
            q = db.query(FarmCropPlan).filter(FarmCropPlan.is_deleted == True)
            for p in q.all():
                farm_name = p.farm.farm_name if p.farm else "Unknown Farm"
                crop_name = p.crop.crop_name if p.crop else "Unknown Crop"
                label = f"{crop_name} ({p.season}) @ {farm_name}"
                if search and search.lower() not in label.lower():
                    continue
                all_items.append(
                    TrashBinItemResponse(
                        id=p.id,
                        entity_type=TrashEntityType.FARM_CROP_PLAN,
                        entity_name=label,
                        entity_code=f"PLAN-{str(p.id)[:8].upper()}",
                        deleted_at=p.deleted_at,
                        deleted_by=p.deleted_by,
                        created_at=p.created_at,
                        details={
                            "season": p.season,
                            "planned_area": float(p.planned_area),
                            "land_area_unit": p.land_area_unit,
                            "farm_id": str(p.farm_id),
                            "crop_id": str(p.crop_id),
                        },
                    )
                )

        # 5. Cultivation Runs
        if entity_type is None or entity_type == TrashEntityType.CULTIVATION:
            q = db.query(CultivationRun).filter(CultivationRun.is_deleted == True)
            for c in q.all():
                label = f"Cultivation Run #{str(c.id)[:8].upper()}"
                if search and search.lower() not in label.lower():
                    continue
                all_items.append(
                    TrashBinItemResponse(
                        id=c.id,
                        entity_type=TrashEntityType.CULTIVATION,
                        entity_name=label,
                        entity_code=f"CULT-{str(c.id)[:8].upper()}",
                        deleted_at=c.deleted_at,
                        deleted_by=c.deleted_by,
                        created_at=c.created_at,
                        details={
                            "sowing_date": str(c.sowing_date),
                            "maturity_days": c.maturity_days,
                            "target_harvest_date": str(c.target_harvest_date),
                            "current_stage_order": c.current_stage_order,
                        },
                    )
                )

        # 6. Stage Expenses
        if entity_type is None or entity_type == TrashEntityType.STAGE_EXPENSE:
            q = db.query(StageExpenseLog).filter(StageExpenseLog.is_deleted == True)
            if search:
                term = f"%{search}%"
                q = q.filter(or_(StageExpenseLog.title.ilike(term), StageExpenseLog.expense_category.ilike(term)))
            for e in q.all():
                all_items.append(
                    TrashBinItemResponse(
                        id=e.id,
                        entity_type=TrashEntityType.STAGE_EXPENSE,
                        entity_name=e.title,
                        entity_code=f"EXP-₹{float(e.amount):,.2f}",
                        deleted_at=e.deleted_at,
                        deleted_by=e.deleted_by,
                        created_at=e.created_at,
                        details={
                            "amount": float(e.amount),
                            "category": e.expense_category,
                            "payment_mode": e.payment_mode,
                        },
                    )
                )

        # Sort by deleted_at descending
        all_items.sort(key=lambda x: x.deleted_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

        total = len(all_items)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = all_items[start_idx:end_idx]

        return paginated, total

    @staticmethod
    def restore_entity(db: Session, entity_type: TrashEntityType, entity_id: uuid.UUID) -> bool:
        """Restores a soft-deleted entity by clearing deleted flags."""
        if entity_type == TrashEntityType.USER:
            user = db.query(User).filter(User.id == entity_id, User.is_deleted == True).first()
            if not user:
                return False
            user.is_deleted = False
            user.deleted_at = None
            user.deleted_by = None
            db.commit()
            return True

        elif entity_type == TrashEntityType.CROP:
            crop = db.query(Crop).filter(Crop.id == entity_id, Crop.is_deleted == True).first()
            if not crop:
                return False
            crop.is_deleted = False
            crop.deleted_at = None
            crop.deleted_by = None
            db.commit()
            return True

        elif entity_type == TrashEntityType.FARM:
            farm = db.query(Farm).filter(Farm.id == entity_id, Farm.is_deleted == True).first()
            if not farm:
                return False
            farm.is_deleted = False
            farm.deleted_at = None
            farm.deleted_by = None
            db.commit()
            return True

        elif entity_type == TrashEntityType.FARM_CROP_PLAN:
            plan = db.query(FarmCropPlan).filter(FarmCropPlan.id == entity_id, FarmCropPlan.is_deleted == True).first()
            if not plan:
                return False
            plan.is_deleted = False
            plan.deleted_at = None
            plan.deleted_by = None
            db.commit()
            return True

        elif entity_type == TrashEntityType.CULTIVATION:
            cult = db.query(CultivationRun).filter(CultivationRun.id == entity_id, CultivationRun.is_deleted == True).first()
            if not cult:
                return False
            cult.is_deleted = False
            cult.deleted_at = None
            cult.deleted_by = None
            db.commit()
            return True

        elif entity_type == TrashEntityType.STAGE_EXPENSE:
            exp = db.query(StageExpenseLog).filter(StageExpenseLog.id == entity_id, StageExpenseLog.is_deleted == True).first()
            if not exp:
                return False
            exp.is_deleted = False
            exp.deleted_at = None
            exp.deleted_by = None
            db.commit()
            return True

        return False

    @staticmethod
    def hard_delete_entity(db: Session, entity_type: TrashEntityType, entity_id: uuid.UUID) -> bool:
        """Physically deletes a soft-deleted entity from the database ledger."""
        if entity_type == TrashEntityType.USER:
            user = db.query(User).filter(User.id == entity_id).first()
            if not user:
                return False
            db.delete(user)
            db.commit()
            return True

        elif entity_type == TrashEntityType.CROP:
            crop = db.query(Crop).filter(Crop.id == entity_id).first()
            if not crop:
                return False
            db.delete(crop)
            db.commit()
            return True

        elif entity_type == TrashEntityType.FARM:
            farm = db.query(Farm).filter(Farm.id == entity_id).first()
            if not farm:
                return False
            db.delete(farm)
            db.commit()
            return True

        elif entity_type == TrashEntityType.FARM_CROP_PLAN:
            plan = db.query(FarmCropPlan).filter(FarmCropPlan.id == entity_id).first()
            if not plan:
                return False
            db.delete(plan)
            db.commit()
            return True

        elif entity_type == TrashEntityType.CULTIVATION:
            cult = db.query(CultivationRun).filter(CultivationRun.id == entity_id).first()
            if not cult:
                return False
            db.delete(cult)
            db.commit()
            return True

        elif entity_type == TrashEntityType.STAGE_EXPENSE:
            exp = db.query(StageExpenseLog).filter(StageExpenseLog.id == entity_id).first()
            if not exp:
                return False
            db.delete(exp)
            db.commit()
            return True

        return False
