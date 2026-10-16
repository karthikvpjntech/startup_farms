import uuid
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.livestock import LivestockReview


class LivestockReviewRepository:
    """Repository handling verified customer purchase reviews for livestock."""

    @staticmethod
    def get_existing_review(
        db: Session,
        order_id: uuid.UUID,
        livestock_id: uuid.UUID,
        customer_id: uuid.UUID
    ) -> Optional[LivestockReview]:
        return db.scalar(
            select(LivestockReview).where(
                LivestockReview.order_id == order_id,
                LivestockReview.livestock_id == livestock_id,
                LivestockReview.customer_id == customer_id
            )
        )

    @staticmethod
    def create_review(
        db: Session,
        order_id: uuid.UUID,
        livestock_id: uuid.UUID,
        customer_id: uuid.UUID,
        rating: int,
        review_text: Optional[str] = None
    ) -> LivestockReview:
        now = datetime.now(timezone.utc)
        review = LivestockReview(
            id=uuid.uuid4(),
            livestock_id=livestock_id,
            order_id=order_id,
            customer_id=customer_id,
            rating=rating,
            review_text=review_text.strip() if review_text else None,
            is_verified_purchase=True,
            created_at=now,
            updated_at=now
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        return review

    @staticmethod
    def list_reviews_by_livestock(
        db: Session,
        livestock_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[LivestockReview], int]:
        stmt = select(LivestockReview).where(LivestockReview.livestock_id == livestock_id)
        count_stmt = select(func.count(LivestockReview.id)).where(LivestockReview.livestock_id == livestock_id)
        total = db.scalar(count_stmt) or 0

        stmt = stmt.order_by(LivestockReview.created_at.desc()).offset(skip).limit(limit)
        items = list(db.scalars(stmt).all())
        return items, total

    @staticmethod
    def get_rating_summary(db: Session, livestock_id: uuid.UUID) -> Tuple[Optional[float], int]:
        stmt = select(
            func.avg(LivestockReview.rating),
            func.count(LivestockReview.id)
        ).where(LivestockReview.livestock_id == livestock_id)
        row = db.execute(stmt).one_or_none()
        if row and row[1] > 0:
            avg_rating = round(float(row[0]), 1) if row[0] is not None else None
            return avg_rating, row[1]
        return None, 0
