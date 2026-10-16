import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.worker_profile import WorkerProfile


class WorkerProfileRepository:
    """Repository for WorkerProfile database operations."""

    @staticmethod
    def get_by_user_id(db: Session, user_id: uuid.UUID) -> Optional[WorkerProfile]:
        return db.scalar(select(WorkerProfile).where(WorkerProfile.user_id == user_id))

    @staticmethod
    def create(
        db: Session,
        user_id: uuid.UUID,
        profile_data: Dict[str, Any]
    ) -> WorkerProfile:
        profile = WorkerProfile(
            user_id=user_id,
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
        profile: WorkerProfile,
        update_data: Dict[str, Any]
    ) -> WorkerProfile:
        now = datetime.now(timezone.utc)
        for key, value in update_data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        profile.updated_at = now
        db.commit()
        db.refresh(profile)
        return profile
