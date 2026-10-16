import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    """Repository for RefreshToken database operations."""

    @staticmethod
    def create(
        db: Session,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime
    ) -> RefreshToken:
        token_record = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False
        )
        db.add(token_record)
        db.commit()
        db.refresh(token_record)
        return token_record

    @staticmethod
    def get_by_hash(db: Session, token_hash: str) -> Optional[RefreshToken]:
        return db.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )

    @staticmethod
    def revoke(
        db: Session,
        token_record: RefreshToken,
        replaced_by_token_id: Optional[uuid.UUID] = None
    ) -> None:
        token_record.is_revoked = True
        token_record.revoked_at = datetime.now(timezone.utc)
        if replaced_by_token_id:
            token_record.replaced_by_token_id = replaced_by_token_id
        db.commit()
        db.refresh(token_record)

    @staticmethod
    def revoke_all_for_user(db: Session, user_id: uuid.UUID) -> int:
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
            .values(is_revoked=True, revoked_at=datetime.now(timezone.utc))
        )
        result = db.execute(stmt)
        db.commit()
        return result.rowcount
