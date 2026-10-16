import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.driver_profile import DriverProfile


class DriverProfileRepository:
    """Repository for DriverProfile database operations."""

    @staticmethod
    def get_by_user_id(db: Session, user_id: uuid.UUID) -> Optional[DriverProfile]:
        return db.scalar(select(DriverProfile).where(DriverProfile.user_id == user_id))

    @staticmethod
    def create(
        db: Session,
        user_id: uuid.UUID,
        profile_data: Dict[str, Any]
    ) -> DriverProfile:
        profile = DriverProfile(
            user_id=user_id,
            license_number=profile_data.get("license_number"),
            license_expiry_date=profile_data.get("license_expiry_date"),
            address_line1=profile_data.get("address_line1"),
            district=profile_data.get("district"),
            state=profile_data.get("state"),
            pincode=profile_data.get("pincode"),
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def update(
        db: Session,
        profile: DriverProfile,
        update_data: Dict[str, Any]
    ) -> DriverProfile:
        now = datetime.now(timezone.utc)
        for key, value in update_data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        profile.updated_at = now
        db.commit()
        db.refresh(profile)
        return profile
