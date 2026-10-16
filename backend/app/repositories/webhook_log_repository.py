import uuid
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from app.models.payment_webhook_log import PaymentWebhookLog


class WebhookLogRepository:
    """Database repository for PaymentWebhookLog operations."""

    @staticmethod
    def create(
        db: Session,
        event_id: str,
        event_type: str,
        payload: str,
        status: str = "PROCESSED",
        signature: Optional[str] = None,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> PaymentWebhookLog:
        log = PaymentWebhookLog(
            id=uuid.uuid4(),
            event_id=event_id,
            event_type=event_type,
            signature=signature,
            payload=payload,
            status=status,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            error_message=error_message,
            created_at=datetime.now(timezone.utc),
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_by_event_id(db: Session, event_id: str) -> Optional[PaymentWebhookLog]:
        return db.scalar(
            select(PaymentWebhookLog).where(PaymentWebhookLog.event_id == event_id)
        )

    @staticmethod
    def list_logs(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Tuple[List[PaymentWebhookLog], int]:
        stmt = select(PaymentWebhookLog)
        if event_type:
            stmt = stmt.where(PaymentWebhookLog.event_type == event_type)
        if status:
            stmt = stmt.where(PaymentWebhookLog.status == status)

        from sqlalchemy import func
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        stmt = (
            stmt.order_by(desc(PaymentWebhookLog.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        logs = list(db.scalars(stmt).all())
        return logs, total
