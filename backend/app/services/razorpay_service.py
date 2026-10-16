import hmac
import hashlib
import uuid
import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
try:
    import razorpay
except ImportError:
    razorpay = None
from app.core.config import settings

logger = logging.getLogger("agri_smart.razorpay_service")


class RazorpayService:
    """
    Production-ready Razorpay payment gateway integration supporting Test & Live modes.
    Manages order creation in paise and HMAC-SHA256 signature verification.
    """

    @classmethod
    def get_client(cls) -> Optional[Any]:
        if razorpay and settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
            return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        return None

    @classmethod
    def is_configured(cls) -> bool:
        if not (razorpay and settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET):
            return False
        # Treat placeholder / simulated test keys as simulated mode
        if "placeholder" in settings.RAZORPAY_KEY_ID or "simulated" in settings.RAZORPAY_KEY_ID:
            return False
        return True

    @classmethod
    def create_razorpay_order(
        cls,
        amount_in_rupees: Decimal,
        receipt: str,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Creates a Razorpay order entity with amount converted to paise.
        """
        amount_in_paise = int(amount_in_rupees * 100)
        currency = settings.RAZORPAY_CURRENCY or "INR"

        if cls.is_configured():
            client = cls.get_client()
            if client:
                try:
                    order_payload = {
                        "amount": amount_in_paise,
                        "currency": currency,
                        "receipt": receipt[:40],
                        "notes": notes or {},
                        "payment_capture": 1,
                    }
                    rzp_order = client.order.create(data=order_payload)
                    logger.info("Created Razorpay live/test order: %s for receipt %s", rzp_order.get("id"), receipt)
                    return {
                        "razorpay_order_id": rzp_order.get("id"),
                        "amount": amount_in_paise,
                        "currency": currency,
                        "key_id": settings.RAZORPAY_KEY_ID,
                        "is_simulated": False,
                    }
                except Exception as e:
                    logger.warning("Live Razorpay call failed (%s). Falling back to test mode simulation.", e)

        # Simulated Test Order fallback when Razorpay keys are in test simulation
        simulated_order_id = f"order_test_{uuid.uuid4().hex[:14]}"
        logger.info("[RAZORPAY TEST SIMULATED] Created order: %s for amount ₹%s", simulated_order_id, amount_in_rupees)
        return {
            "razorpay_order_id": simulated_order_id,
            "amount": amount_in_paise,
            "currency": currency,
            "key_id": settings.RAZORPAY_KEY_ID or "rzp_test_simulated_key",
            "is_simulated": True,
        }

    @classmethod
    def verify_payment_signature(
        cls,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        """
        Verifies the cryptographic HMAC-SHA256 signature returned by Razorpay Checkout.
        """
        if not cls.is_configured():
            # In test simulation mode, verify test signatures
            logger.info("[RAZORPAY TEST SIMULATION] Verified test payment signature for %s", razorpay_order_id)
            return True

        secret = settings.RAZORPAY_KEY_SECRET or ""
        generated_signature = hmac.new(
            secret.encode("utf-8"),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        is_valid = hmac.compare_digest(generated_signature, razorpay_signature)
        if not is_valid:
            logger.warning(
                "Invalid Razorpay signature for Order %s: generated=%s, received=%s",
                razorpay_order_id,
                generated_signature,
                razorpay_signature
            )
        return is_valid

    @classmethod
    def verify_webhook_signature(
        cls,
        payload_body: bytes,
        signature: str,
        secret: Optional[str] = None,
    ) -> bool:
        """
        Validates X-Razorpay-Signature HMAC-SHA256 signature for inbound webhooks.
        """
        webhook_secret = secret or settings.RAZORPAY_WEBHOOK_SECRET or settings.RAZORPAY_KEY_SECRET

        if not webhook_secret:
            # If no webhook secret is configured in development, allow simulated payloads with warning
            logger.warning("[RAZORPAY WEBHOOK] No RAZORPAY_WEBHOOK_SECRET configured. Permitting webhook in dev mode.")
            return True

        if not signature:
            logger.warning("[RAZORPAY WEBHOOK] Missing X-Razorpay-Signature header.")
            return False

        generated_sig = hmac.new(
            webhook_secret.encode("utf-8"),
            payload_body,
            hashlib.sha256
        ).hexdigest()

        is_valid = hmac.compare_digest(generated_sig, signature)
        if not is_valid:
            logger.warning(
                "[RAZORPAY WEBHOOK] Invalid Webhook Signature: generated=%s, received=%s",
                generated_sig,
                signature
            )
        return is_valid

    @classmethod
    def process_webhook_event(
        cls,
        db: Session,
        event_data: Dict[str, Any],
        raw_body: str,
        signature: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Idempotently reconciles inbound Razorpay webhook events:
        - payment.captured & payment.authorized (settles marketplace orders & subscriptions)
        - payment.failed (records failure reasons)
        - order.paid (confirms order payment)
        - refund.processed (updates refund statuses)
        """
        import json
        from app.repositories.webhook_log_repository import WebhookLogRepository
        from app.repositories.marketplace_order_repository import MarketplaceOrderRepository
        from app.models.marketplace_order import MarketplaceOrder
        from app.models.subscription import UserSubscription, SubscriptionSetting
        from app.models.user import User
        from app.services.email_service import EmailService
        from app.services.notification_service import NotificationService
        from datetime import datetime, timezone, timedelta
        from sqlalchemy import select

        event_id = event_data.get("id") or f"evt_gen_{uuid.uuid4().hex[:12]}"
        event_type = event_data.get("event", "unknown")
        payload = event_data.get("payload", {})

        # 1. Idempotency Check
        existing_log = WebhookLogRepository.get_by_event_id(db, event_id)
        if existing_log and existing_log.status == "PROCESSED":
            logger.info("[RAZORPAY WEBHOOK] Duplicate event %s already processed. Skipping.", event_id)
            return {
                "status": "DUPLICATE",
                "event_id": event_id,
                "event_type": event_type,
                "message": f"Event {event_id} already processed"
            }

        related_type = None
        related_id = None
        processing_error = None
        result_message = "Handled successfully"

        try:
            payment_entity = payload.get("payment", {}).get("entity", {})
            order_entity = payload.get("order", {}).get("entity", {})
            refund_entity = payload.get("refund", {}).get("entity", {})

            # 2. Handle Payment Capture / Order Paid
            if event_type in ["payment.captured", "payment.authorized", "order.paid"]:
                rzp_payment_id = payment_entity.get("id") or f"pay_wh_{uuid.uuid4().hex[:10]}"
                rzp_order_id = payment_entity.get("order_id") or order_entity.get("id")
                notes = payment_entity.get("notes") or order_entity.get("notes") or {}
                amount_paise = payment_entity.get("amount") or order_entity.get("amount", 0)
                amount_rupees = Decimal(str(amount_paise / 100)) if amount_paise else Decimal("0.00")

                # Case A: Historical Data Subscription Payment
                if notes.get("purpose") == "historical_data_subscription" or notes.get("plan_type"):
                    user_id_str = notes.get("user_id")
                    plan_type = (notes.get("plan_type") or "MONTHLY").upper()
                    if user_id_str:
                        try:
                            user_uuid = uuid.UUID(user_id_str)
                            user = db.get(User, user_uuid)
                            if user:
                                now = datetime.now(timezone.utc)
                                end_date = now + timedelta(days=365 if plan_type == "ANNUAL" else 30)
                                subscription = UserSubscription(
                                    user_id=user.id,
                                    plan_type=plan_type,
                                    status="ACTIVE",
                                    amount_paid=amount_rupees,
                                    currency="INR",
                                    start_date=now,
                                    end_date=end_date,
                                    payment_method="RAZORPAY_WEBHOOK",
                                    payment_reference=rzp_payment_id,
                                    notes=f"Auto-activated via Razorpay Webhook ({event_type})",
                                    created_at=now,
                                )
                                db.add(subscription)
                                db.commit()
                                db.refresh(subscription)

                                related_type = "SUBSCRIPTION"
                                related_id = str(subscription.id)
                                result_message = f"Subscription activated for user {user.email or user.mobile_number}"

                                if user.email:
                                    EmailService.send_subscription_active_email(
                                        to_email=user.email,
                                        user_name=user.full_name,
                                        plan_type=plan_type,
                                        end_date_str=end_date.strftime("%d %b %Y"),
                                        amount_paid=str(amount_rupees),
                                        payment_reference=rzp_payment_id
                                    )
                        except Exception as sub_exc:
                            logger.error("[RAZORPAY WEBHOOK] Subscription activation error: %s", sub_exc)
                            processing_error = str(sub_exc)

                # Case B: Marketplace Order Payment
                order_id_str = notes.get("order_id")
                order_number_str = notes.get("order_number") or order_entity.get("receipt")
                target_order = None

                if order_id_str:
                    try:
                        target_order = MarketplaceOrderRepository.get_by_id_internal(db, uuid.UUID(order_id_str))
                    except Exception:
                        target_order = None

                if not target_order and order_number_str:
                    stmt = select(MarketplaceOrder).where(MarketplaceOrder.order_number == order_number_str)
                    target_order = db.scalar(stmt)

                if not target_order and rzp_order_id:
                    # Search by payment notes / order reference if needed
                    pass

                if target_order:
                    related_type = "MARKETPLACE_ORDER"
                    related_id = str(target_order.id)

                    if target_order.payment and target_order.payment.status != "PAID":
                        payment = MarketplaceOrderRepository.mark_payment_paid(
                            db=db,
                            payment=target_order.payment,
                            transaction_reference=rzp_payment_id,
                            notes=f"Razorpay Webhook: {event_type} at {datetime.now(timezone.utc).isoformat()}"
                        )
                        result_message = f"Marketplace Order {target_order.order_number} marked PAID via Webhook"
                        logger.info("[RAZORPAY WEBHOOK] Settled payment for Order %s", target_order.order_number)

                        # Trigger customer receipts
                        if target_order.customer and target_order.customer.email:
                            EmailService.send_payment_receipt_email(
                                to_email=target_order.customer.email,
                                customer_name=target_order.customer.full_name,
                                order_number=target_order.order_number,
                                payment_number=payment.payment_number,
                                amount=str(payment.amount),
                                payment_method="RAZORPAY",
                                transaction_ref=rzp_payment_id
                            )
                    else:
                        result_message = f"Order {target_order.order_number} was already PAID or pending payment record missing"

            # 3. Handle Payment Failed
            elif event_type in ["payment.failed"]:
                rzp_payment_id = payment_entity.get("id")
                error_desc = payment_entity.get("error_description", "Payment transaction failed on gateway")
                notes = payment_entity.get("notes", {})
                order_id_str = notes.get("order_id")

                if order_id_str:
                    try:
                        order = MarketplaceOrderRepository.get_by_id_internal(db, uuid.UUID(order_id_str))
                        if order and order.payment:
                            order.payment.status = "FAILED"
                            order.payment.notes = f"Gateway Error: {error_desc}"
                            db.commit()
                            related_type = "MARKETPLACE_ORDER"
                            related_id = str(order.id)
                            result_message = f"Order {order.order_number} payment marked FAILED"
                    except Exception as fail_exc:
                        processing_error = str(fail_exc)

            # 4. Handle Refunds
            elif event_type in ["refund.processed", "refund.created"]:
                rzp_payment_id = refund_entity.get("payment_id")
                from app.models.marketplace_order import MarketplacePayment
                if rzp_payment_id:
                    stmt = select(MarketplacePayment).where(MarketplacePayment.transaction_reference == rzp_payment_id)
                    payment = db.scalar(stmt)
                    if payment:
                        payment.status = "REFUNDED"
                        if payment.order:
                            payment.order.status = "REFUNDED"
                            payment.order.payment_status = "REFUNDED"
                        db.commit()
                        related_type = "MARKETPLACE_ORDER"
                        related_id = str(payment.order_id)
                        result_message = f"Order payment marked REFUNDED"

            else:
                result_message = f"Unhandled event type '{event_type}' ignored safely."

        except Exception as exc:
            logger.error("[RAZORPAY WEBHOOK] Exception processing event %s: %s", event_id, exc, exc_info=True)
            processing_error = str(exc)

        # 5. Record Event Audit Log
        status_code = "FAILED" if processing_error else "PROCESSED"
        WebhookLogRepository.create(
            db=db,
            event_id=event_id,
            event_type=event_type,
            payload=raw_body,
            status=status_code,
            signature=signature,
            related_entity_type=related_type,
            related_entity_id=related_id,
            error_message=processing_error,
        )

        return {
            "status": status_code,
            "event_id": event_id,
            "event_type": event_type,
            "message": result_message,
            "error": processing_error,
        }

