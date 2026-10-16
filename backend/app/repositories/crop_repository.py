import re
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from app.models.crop import Crop


class CropRepository:
    """Repository handling Crop Master database persistence operations."""

    @staticmethod
    def get_by_id(
        db: Session,
        crop_id: uuid.UUID,
        include_deleted: bool = False
    ) -> Optional[Crop]:
        """Retrieve crop by primary key with optional soft-delete filter."""
        stmt = select(Crop).where(Crop.id == crop_id)
        if not include_deleted:
            stmt = stmt.where(Crop.is_deleted == False)
        return db.scalar(stmt)

    @staticmethod
    def get_by_code(db: Session, crop_code: str) -> Optional[Crop]:
        """Find crop by unique human-readable crop_code (including deleted records)."""
        return db.scalar(select(Crop).where(Crop.crop_code == crop_code))

    @staticmethod
    def get_active_by_name(
        db: Session,
        crop_name: str,
        exclude_crop_id: Optional[uuid.UUID] = None
    ) -> Optional[Crop]:
        """Check if an active/non-deleted crop with the same name already exists."""
        clean_name = crop_name.strip()
        stmt = select(Crop).where(
            func.lower(Crop.crop_name) == func.lower(clean_name),
            Crop.is_deleted == False
        )
        if exclude_crop_id is not None:
            stmt = stmt.where(Crop.id != exclude_crop_id)
        return db.scalar(stmt)

    @staticmethod
    def generate_next_crop_code(db: Session) -> str:
        """
        Generate a unique, deterministic, monotonic crop code formatted as CROP-XXXXXX.
        Inspects existing codes in the database (including soft-deleted) to prevent code reuse.
        """
        codes = db.scalars(select(Crop.crop_code)).all()
        max_num = 0
        pattern = re.compile(r"^CROP-(\d+)$")
        for code in codes:
            match = pattern.match(code)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num

        next_num = max_num + 1
        return f"CROP-{next_num:06d}"

    @staticmethod
    def create(
        db: Session,
        crop_code: str,
        crop_data: Dict[str, Any],
        created_by: Optional[uuid.UUID] = None
    ) -> Crop:
        """Create a new Crop Master record."""
        category_val = crop_data["crop_category"]
        if hasattr(category_val, "value"):
            category_val = category_val.value
        else:
            category_val = str(category_val)

        crop = Crop(
            crop_code=crop_code,
            crop_name=crop_data["crop_name"].strip(),
            scientific_name=crop_data.get("scientific_name"),
            crop_category=category_val,
            description=crop_data.get("description"),
            is_active=True,
            is_deleted=False,
            created_by=created_by,
            updated_by=created_by,
        )
        db.add(crop)
        db.commit()
        db.refresh(crop)
        return crop

    @staticmethod
    def list_crops(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        include_deleted: bool = False
    ) -> List[Crop]:
        """List crop records with filtering and pagination."""
        stmt = select(Crop)
        if not include_deleted:
            stmt = stmt.where(Crop.is_deleted == False)
        if is_active is not None:
            stmt = stmt.where(Crop.is_active == is_active)
        if category:
            stmt = stmt.where(Crop.crop_category == category.upper())
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Crop.crop_name.ilike(pattern),
                    Crop.crop_code.ilike(pattern),
                    Crop.scientific_name.ilike(pattern),
                )
            )
        stmt = stmt.order_by(Crop.created_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    @staticmethod
    def count_crops(
        db: Session,
        search: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        include_deleted: bool = False
    ) -> int:
        """Count total crop records matching the given criteria."""
        stmt = select(func.count(Crop.id))
        if not include_deleted:
            stmt = stmt.where(Crop.is_deleted == False)
        if is_active is not None:
            stmt = stmt.where(Crop.is_active == is_active)
        if category:
            stmt = stmt.where(Crop.crop_category == category.upper())
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Crop.crop_name.ilike(pattern),
                    Crop.crop_code.ilike(pattern),
                    Crop.scientific_name.ilike(pattern),
                )
            )
        return db.scalar(stmt) or 0

    @staticmethod
    def update(
        db: Session,
        crop: Crop,
        update_data: Dict[str, Any],
        updated_by: Optional[uuid.UUID] = None
    ) -> Crop:
        """Update mutable fields of a crop master record."""
        now = datetime.now(timezone.utc)
        disallowed = {"id", "crop_code", "created_at", "created_by", "is_deleted", "deleted_at", "deleted_by"}
        for key, value in update_data.items():
            if key not in disallowed and hasattr(crop, key):
                if key == "crop_category" and value is not None:
                    setattr(crop, key, value.value if hasattr(value, "value") else str(value))
                else:
                    setattr(crop, key, value)
        crop.updated_by = updated_by
        crop.updated_at = now
        db.commit()
        db.refresh(crop)
        return crop

    @staticmethod
    def update_status(
        db: Session,
        crop: Crop,
        is_active: bool,
        updated_by: Optional[uuid.UUID] = None
    ) -> Crop:
        """Update active status of a crop master record."""
        crop.is_active = is_active
        crop.updated_by = updated_by
        crop.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(crop)
        return crop

    @staticmethod
    def soft_delete(
        db: Session,
        crop: Crop,
        deleted_by: Optional[uuid.UUID] = None
    ) -> Crop:
        """Soft-delete a crop master record."""
        now = datetime.now(timezone.utc)
        crop.is_deleted = True
        crop.deleted_at = now
        crop.deleted_by = deleted_by
        crop.updated_by = deleted_by
        crop.updated_at = now
        db.commit()
        db.refresh(crop)
        return crop

    @staticmethod
    def restore(
        db: Session,
        crop: Crop,
        updated_by: Optional[uuid.UUID] = None
    ) -> Crop:
        """Restore a soft-deleted crop master record."""
        now = datetime.now(timezone.utc)
        crop.is_deleted = False
        crop.deleted_at = None
        crop.deleted_by = None
        crop.updated_by = updated_by
        crop.updated_at = now
        db.commit()
        db.refresh(crop)
        return crop
