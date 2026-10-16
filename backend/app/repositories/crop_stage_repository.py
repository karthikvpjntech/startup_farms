import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from app.models.crop_stage import CropCultivationStage


class CropStageRepository:
    """Repository handling database operations for Crop Cultivation Process Stages."""

    @staticmethod
    def list_by_crop_id(
        db: Session,
        crop_id: uuid.UUID,
        include_inactive: bool = True,
        include_deleted: bool = False
    ) -> List[CropCultivationStage]:
        """Fetches all stages for a crop, ordered by stage_order ascending."""
        filters = [CropCultivationStage.crop_id == crop_id]
        if not include_deleted:
            filters.append(CropCultivationStage.is_deleted.is_(False))
        if not include_inactive:
            filters.append(CropCultivationStage.is_active.is_(True))

        stmt = (
            select(CropCultivationStage)
            .where(and_(*filters))
            .order_by(CropCultivationStage.stage_order.asc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_by_id(
        db: Session,
        stage_id: uuid.UUID,
        include_deleted: bool = False
    ) -> Optional[CropCultivationStage]:
        """Fetches a single stage by its UUID."""
        filters = [CropCultivationStage.id == stage_id]
        if not include_deleted:
            filters.append(CropCultivationStage.is_deleted.is_(False))

        stmt = select(CropCultivationStage).where(and_(*filters))
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_next_stage_order(db: Session, crop_id: uuid.UUID) -> int:
        """Calculates the next available sequential stage order for a crop."""
        stmt = (
            select(func.coalesce(func.max(CropCultivationStage.stage_order), 0))
            .where(
                and_(
                    CropCultivationStage.crop_id == crop_id,
                    CropCultivationStage.is_deleted.is_(False)
                )
            )
        )
        max_order = db.execute(stmt).scalar() or 0
        return int(max_order) + 1

    @staticmethod
    def create(
        db: Session,
        crop_id: uuid.UUID,
        stage_data: Dict[str, Any],
        created_by: Optional[uuid.UUID] = None,
        explicit_order: Optional[int] = None
    ) -> CropCultivationStage:
        """Creates and persists a new cultivation stage."""
        if explicit_order is not None and explicit_order >= 1:
            order = explicit_order
            # Shift existing stages at or above this order to avoid collisions and keep sequence ordered
            existing = (
                db.query(CropCultivationStage)
                .filter(
                    CropCultivationStage.crop_id == crop_id,
                    CropCultivationStage.is_deleted == False,
                    CropCultivationStage.stage_order >= order,
                )
                .order_by(CropCultivationStage.stage_order.desc())
                .all()
            )
            for s in existing:
                s.stage_order += 1
            db.flush()
        else:
            order = CropStageRepository.get_next_stage_order(db, crop_id)
        
        stage = CropCultivationStage(
            crop_id=crop_id,
            stage_order=order,
            stage_name=stage_data["stage_name"],
            stage_name_local=stage_data.get("stage_name_local"),
            description=stage_data.get("description"),
            duration_days=stage_data.get("duration_days", 15),
            image_url=stage_data.get("image_url"),
            thumbnail_url=stage_data.get("thumbnail_url"),
            visual_asset_type=stage_data.get("visual_asset_type", "VEGETATIVE"),
            visual_theme_color=stage_data.get("visual_theme_color", "#10b981"),
            recommended_activities=stage_data.get("recommended_activities", []),
            recommended_inputs=stage_data.get("recommended_inputs", []),
            is_active=stage_data.get("is_active", True),
            created_by=created_by,
            updated_by=created_by,
        )
        db.add(stage)
        db.commit()
        db.refresh(stage)
        return stage

    @staticmethod
    def update(
        db: Session,
        stage: CropCultivationStage,
        update_data: Dict[str, Any],
        updated_by: Optional[uuid.UUID] = None
    ) -> CropCultivationStage:
        """Updates fields of an existing cultivation stage."""
        for field, value in update_data.items():
            if hasattr(stage, field) and value is not None:
                setattr(stage, field, value)
        
        stage.updated_by = updated_by
        stage.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(stage)
        return stage

    @staticmethod
    def reorder_stages(
        db: Session,
        crop_id: uuid.UUID,
        order_mappings: List[Dict[str, Any]],
        updated_by: Optional[uuid.UUID] = None
    ) -> List[CropCultivationStage]:
        """
        Batch updates stage orders for a crop.
        order_mappings is a list of {'stage_id': UUID, 'stage_order': int}.
        """
        now = datetime.now(timezone.utc)
        # Use temporary offset to avoid unique constraint violations during reordering
        for item in order_mappings:
            stage = db.get(CropCultivationStage, item["stage_id"])
            if stage and stage.crop_id == crop_id and not stage.is_deleted:
                stage.stage_order = item["stage_order"] + 10000
        db.flush()

        for item in order_mappings:
            stage = db.get(CropCultivationStage, item["stage_id"])
            if stage and stage.crop_id == crop_id and not stage.is_deleted:
                stage.stage_order = item["stage_order"]
                stage.updated_by = updated_by
                stage.updated_at = now

        db.commit()
        return CropStageRepository.list_by_crop_id(db, crop_id, include_inactive=True, include_deleted=False)

    @staticmethod
    def soft_delete(
        db: Session,
        stage: CropCultivationStage,
        deleted_by: Optional[uuid.UUID] = None
    ) -> CropCultivationStage:
        """Soft deletes a cultivation stage."""
        stage.is_deleted = True
        stage.deleted_at = datetime.now(timezone.utc)
        stage.deleted_by = deleted_by
        db.commit()
        db.refresh(stage)
        return stage
