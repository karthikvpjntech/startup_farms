import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, update, desc
from sqlalchemy.orm import Session
from app.models.otp_verification import OtpVerification


class OtpRepository:
    """Database repository for OTP operations (2FA, Password Reset, Passwordless)."""

    @staticmethod
    def create(
        db: Session,
        identifier: str,
        otp_code_hash: str,
        otp_type: str,
        expires_at: datetime,
        user_id: Optional[uuid.UUID] = None,
        session_token: Optional[str] = None,
        max_attempts: int = 5,
    ) -> OtpVerification:
        record = OtpVerification(
            id=uuid.uuid4(),
            user_id=user_id,
            identifier=identifier.strip().lower() if "@" in identifier else identifier.strip(),
            otp_code_hash=otp_code_hash,
            otp_type=otp_type,
            session_token=session_token,
            expires_at=expires_at,
            is_used=False,
            attempts=0,
            max_attempts=max_attempts,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_by_session_token(
        db: Session, session_token: str, otp_type: Optional[str] = None
    ) -> Optional[OtpVerification]:
        stmt = select(OtpVerification).where(OtpVerification.session_token == session_token)
        if otp_type:
            stmt = stmt.where(OtpVerification.otp_type == otp_type)
        return db.scalar(stmt)

    @staticmethod
    def get_latest_active_by_identifier(
        db: Session, identifier: str, otp_type: str
    ) -> Optional[OtpVerification]:
        clean_id = identifier.strip().lower() if "@" in identifier else identifier.strip()
        stmt = (
            select(OtpVerification)
            .where(
                OtpVerification.identifier == clean_id,
                OtpVerification.otp_type == otp_type,
                OtpVerification.is_used == False,
            )
            .order_by(desc(OtpVerification.created_at))
            .limit(1)
        )
        return db.scalar(stmt)

    @staticmethod
    def increment_attempts(db: Session, record: OtpVerification) -> int:
        record.attempts += 1
        record.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(record)
        return record.attempts

    @staticmethod
    def mark_used(db: Session, record: OtpVerification) -> None:
        record.is_used = True
        record.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(record)

    @staticmethod
    def invalidate_active_for_identifier(
        db: Session, identifier: str, otp_type: str
    ) -> int:
        clean_id = identifier.strip().lower() if "@" in identifier else identifier.strip()
        stmt = (
            update(OtpVerification)
            .where(
                OtpVerification.identifier == clean_id,
                OtpVerification.otp_type == otp_type,
                OtpVerification.is_used == False,
            )
            .values(is_used=True, updated_at=datetime.now(timezone.utc))
        )
        res = db.execute(stmt)
        db.commit()
        return res.rowcount
