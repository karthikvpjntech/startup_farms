import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.farmer_profile import FarmerProfile


class FarmerProfileRepository:
    """Repository for FarmerProfile database operations."""

    @staticmethod
    def get_by_user_id(db: Session, user_id: uuid.UUID) -> Optional[FarmerProfile]:
        return db.scalar(select(FarmerProfile).where(FarmerProfile.user_id == user_id))

    @staticmethod
    def create(
        db: Session,
        user_id: uuid.UUID,
        profile_data: Dict[str, Any]
    ) -> FarmerProfile:
        profile = FarmerProfile(
            user_id=user_id,
            profile_image_url=profile_data.get("profile_image_url"),
            address_line1=profile_data.get("address_line1"),
            address_line2=profile_data.get("address_line2"),
            village=profile_data.get("village"),
            district=profile_data.get("district"),
            state=profile_data.get("state"),
            pincode=profile_data.get("pincode"),
            latitude=profile_data.get("latitude"),
            longitude=profile_data.get("longitude"),
            location_url=profile_data.get("location_url"),
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def update(
        db: Session,
        profile: FarmerProfile,
        update_data: Dict[str, Any]
    ) -> FarmerProfile:
        now = datetime.now(timezone.utc)
        for key, value in update_data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        profile.updated_at = now
        db.commit()
        db.refresh(profile)
        return profile
