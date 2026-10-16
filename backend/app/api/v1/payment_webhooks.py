import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Request, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.dependencies.auth import get_current_user
from app.dependencies.authorization import require_roles
from app.models.user import User
from app.models.enums import RoleEnum
from app.schemas.payment_webhook import PaymentWebhookResponse, WebhookLogListResponse, WebhookLogItemResponse
from app.services.razorpay_service import RazorpayService
from app.repositories.webhook_log_repository import WebhookLogRepository

logger = logging.getLogger("agri_smart.payment_webhooks")

router = APIRouter(prefix="/payments/webhooks", tags=["Payment Gateway Webhooks"])


@router.post(
    "",
    response_model=PaymentWebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Razorpay Inbound Webhook Handler"
)
@router.post(
    "/razorpay",
    response_model=PaymentWebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Razorpay Inbound Webhook Handler (Alias)"
)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
    db: Session = Depends(get_db),
):
    """
    Asynchronous, resilient Webhook receiver for Razorpay payment notifications.
    Validates HMAC-SHA256 signature, ensures event idempotency, and reconciles:
    - payment.captured (settles orders, activates subscriptions)
    - payment.failed (records failure status & error telemetry)
    - order.paid (confirms order payment settlement)
    - refund.processed (updates refund statuses)
    """
    # 1. Read raw binary body for HMAC validation
    raw_body_bytes = await request.body()
    raw_body_str = raw_body_bytes.decode("utf-8")

    # 2. Verify Cryptographic Signature
    is_valid_sig = RazorpayService.verify_webhook_signature(
        payload_body=raw_body_bytes,
        signature=x_razorpay_signature or "",
    )

    if not is_valid_sig:
        logger.warning("[RAZORPAY WEBHOOK] Rejected request with invalid HMAC signature: %s", x_razorpay_signature)
        # Log invalid signature attempt
        try:
            WebhookLogRepository.create(
                db=db,
                event_id=f"invalid_sig_{hash(raw_body_str)}",
                event_type="signature.invalid",
                payload=raw_body_str,
                status="INVALID_SIGNATURE",
                signature=x_razorpay_signature,
                error_message="Cryptographic signature mismatch on X-Razorpay-Signature",
            )
        except Exception:
            pass

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid cryptographic webhook signature."
        )

    # 3. Parse JSON Event Payload
    try:
        event_data = json.loads(raw_body_str)
    except json.JSONDecodeError as err:
        logger.error("[RAZORPAY WEBHOOK] Malformed JSON payload: %s", err)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed JSON payload."
        )

    # 4. Process Event with Idempotency & Reconciliation
    result = RazorpayService.process_webhook_event(
        db=db,
        event_data=event_data,
        raw_body=raw_body_str,
        signature=x_razorpay_signature,
    )

    return PaymentWebhookResponse(
        status=result["status"],
        event_id=result["event_id"],
        event_type=result["event_type"],
        message=result["message"],
        error=result.get("error"),
    )


@router.get(
    "/logs",
    response_model=WebhookLogListResponse,
    summary="List Payment Webhook Audit Logs (Super Admin)",
    dependencies=[Depends(require_roles([RoleEnum.SUPER_ADMIN.value]))]
)
def list_webhook_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    event_type: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Admin diagnostic overview of all processed payment webhooks and recovery logs.
    """
    logs, total = WebhookLogRepository.list_logs(
        db=db,
        page=page,
        page_size=page_size,
        event_type=event_type,
        status=status,
    )
    return WebhookLogListResponse(
        items=[WebhookLogItemResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
    )
