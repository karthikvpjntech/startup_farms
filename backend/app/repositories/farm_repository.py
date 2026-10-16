import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from app.models.farm import Farm


class FarmRepository:
    """Repository handling Farm database persistence operations."""

    @staticmethod
    def get_by_id(
        db: Session,
        farm_id: uuid.UUID,
        farmer_profile_id: Optional[uuid.UUID] = None,
        include_deleted: bool = False
    ) -> Optional[Farm]:
        """Retrieve farm by primary key with optional ownership isolation and soft-delete filter."""
        stmt = select(Farm).where(Farm.id == farm_id)
        if farmer_profile_id is not None:
            stmt = stmt.where(Farm.farmer_profile_id == farmer_profile_id)
        if not include_deleted:
            stmt = stmt.where(Farm.is_deleted == False)
        return db.scalar(stmt)

    @staticmethod
    def get_by_code(db: Session, farm_code: str) -> Optional[Farm]:
        """Find farm by unique human-readable farm_code (including deleted records)."""
        return db.scalar(select(Farm).where(Farm.farm_code == farm_code))

    @staticmethod
    def get_active_by_name(
        db: Session,
        farmer_profile_id: uuid.UUID,
        farm_name: str,
        exclude_farm_id: Optional[uuid.UUID] = None
    ) -> Optional[Farm]:
        """Check if an active/non-deleted farm with the same name already exists for this farmer."""
        clean_name = farm_name.strip()
        stmt = select(Farm).where(
            Farm.farmer_profile_id == farmer_profile_id,
            func.lower(Farm.farm_name) == func.lower(clean_name),
            Farm.is_deleted == False
        )
        if exclude_farm_id is not None:
            stmt = stmt.where(Farm.id != exclude_farm_id)
        return db.scalar(stmt)

    @staticmethod
    def generate_next_farm_code(db: Session) -> str:
        """
        Generate a unique, deterministic, monotonic farm code formatted as FARM-XXXXXX.
        Inspects existing codes in the database (including soft-deleted) to prevent code reuse.
        """
        codes = db.scalars(select(Farm.farm_code)).all()
        max_num = 0
        pattern = re.compile(r"^FARM-(\d+)$")
        for code in codes:
            match = pattern.match(code)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num

        next_num = max_num + 1
        new_code = f"FARM-{next_num:06d}"
        return new_code

    @staticmethod
    def create(
        db: Session,
        farmer_profile_id: uuid.UUID,
        farm_code: str,
        farm_data: Dict[str, Any],
        created_by: Optional[uuid.UUID] = None
    ) -> Farm:
        """Create a new farm record linked to the farmer profile."""
        ownership_val = farm_data["ownership_type"]
        if hasattr(ownership_val, "value"):
            ownership_val = ownership_val.value
        else:
            ownership_val = str(ownership_val)

        unit_val = farm_data["land_area_unit"]
        if hasattr(unit_val, "value"):
            unit_val = unit_val.value
        else:
            unit_val = str(unit_val)

        farm = Farm(
            farmer_profile_id=farmer_profile_id,
            farm_code=farm_code,
            farm_name=farm_data["farm_name"],
            ownership_type=ownership_val,
            total_land_area=Decimal(str(farm_data["total_land_area"])),
            land_area_unit=unit_val,
            address_line1=farm_data.get("address_line1"),
            address_line2=farm_data.get("address_line2"),
            village=farm_data.get("village"),
            district=farm_data.get("district"),
            state=farm_data.get("state"),
            pincode=farm_data.get("pincode"),
            latitude=Decimal(str(farm_data["latitude"])) if farm_data.get("latitude") is not None else None,
            longitude=Decimal(str(farm_data["longitude"])) if farm_data.get("longitude") is not None else None,
            is_active=True,
            is_deleted=False,
            created_by=created_by,
            updated_by=created_by,
        )
        db.add(farm)
        db.commit()
        db.refresh(farm)
        return farm

    @staticmethod
    def list_by_farmer_profile(
        db: Session,
        farmer_profile_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        include_deleted: bool = False
    ) -> List[Farm]:
        """List farms belonging to a farmer profile with pagination and search."""
        stmt = select(Farm).where(Farm.farmer_profile_id == farmer_profile_id)
        if not include_deleted:
            stmt = stmt.where(Farm.is_deleted == False)
        if is_active is not None:
            stmt = stmt.where(Farm.is_active == is_active)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Farm.farm_name.ilike(pattern),
                    Farm.farm_code.ilike(pattern),
                    Farm.village.ilike(pattern),
                    Farm.district.ilike(pattern),
                    Farm.state.ilike(pattern),
                )
            )
        stmt = stmt.order_by(Farm.created_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    @staticmethod
    def count_by_farmer_profile(
        db: Session,
        farmer_profile_id: uuid.UUID,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        include_deleted: bool = False
    ) -> int:
        """Count total farms belonging to a farmer profile for pagination."""
        stmt = select(func.count(Farm.id)).where(Farm.farmer_profile_id == farmer_profile_id)
        if not include_deleted:
            stmt = stmt.where(Farm.is_deleted == False)
        if is_active is not None:
            stmt = stmt.where(Farm.is_active == is_active)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Farm.farm_name.ilike(pattern),
                    Farm.farm_code.ilike(pattern),
                    Farm.village.ilike(pattern),
                    Farm.district.ilike(pattern),
                    Farm.state.ilike(pattern),
                )
            )
        return db.scalar(stmt) or 0

    @staticmethod
    def update(
        db: Session,
        farm: Farm,
        update_data: Dict[str, Any],
        updated_by: Optional[uuid.UUID] = None
    ) -> Farm:
        """Update mutable fields of an existing farm."""
        now = datetime.now(timezone.utc)
        disallowed_fields = {
            "id", "farm_code", "farmer_profile_id", "created_at",
            "created_by", "is_deleted", "deleted_at", "deleted_by"
        }
        for key, value in update_data.items():
            if key not in disallowed_fields and hasattr(farm, key):
                if key in {"total_land_area", "latitude", "longitude"} and value is not None:
                    setattr(farm, key, Decimal(str(value)))
                elif key in {"ownership_type", "land_area_unit"} and value is not None:
                    setattr(farm, key, value.value if hasattr(value, "value") else str(value))
                else:
                    setattr(farm, key, value)
        farm.updated_by = updated_by
        farm.updated_at = now
        db.commit()
        db.refresh(farm)
        return farm

    @staticmethod
    def update_status(
        db: Session,
        farm: Farm,
        is_active: bool,
        updated_by: Optional[uuid.UUID] = None
    ) -> Farm:
        """Update active status of a farm."""
        farm.is_active = is_active
        farm.updated_by = updated_by
        farm.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(farm)
        return farm

    @staticmethod
    def soft_delete(
        db: Session,
        farm: Farm,
        deleted_by: Optional[uuid.UUID] = None
    ) -> Farm:
        """Soft-delete a farm record."""
        now = datetime.now(timezone.utc)
        farm.is_deleted = True
        farm.deleted_at = now
        farm.deleted_by = deleted_by
        farm.updated_by = deleted_by
        farm.updated_at = now
        db.commit()
        db.refresh(farm)
        return farm

    @staticmethod
    def restore(
        db: Session,
        farm: Farm,
        updated_by: Optional[uuid.UUID] = None
    ) -> Farm:
        """Restore a soft-deleted farm record (does not alter is_active)."""
        now = datetime.now(timezone.utc)
        farm.is_deleted = False
        farm.deleted_at = None
        farm.deleted_by = None
        farm.updated_by = updated_by
        farm.updated_at = now
        db.commit()
        db.refresh(farm)
        return farm
