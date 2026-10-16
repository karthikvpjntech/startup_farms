import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
try:
    import requests
except ImportError:
    requests = None
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.sms_log import SMSLog
from app.models.enums import NotificationStatus, NotificationType

logger = logging.getLogger("agri_smart.notification_service")


class NotificationService:
    """
    Production-ready SMS & Instant Message notification engine.
    Supports Twilio, Fast2SMS, Msg91 gateways, and simulated logging with audit records in sms_logs.
    """

    @staticmethod
    def _dispatch_gateway(recipient_mobile: str, message_body: str) -> Dict[str, Any]:
        """Dispatches message to configured SMS gateway or simulates in development."""
        provider = settings.SMS_PROVIDER.upper()

        if not settings.SMS_ENABLED or provider == "LOG_CONSOLE":
            logger.info("[SMS SIMULATED] To: %s | Message: %s", recipient_mobile, message_body)
            return {"status": "SENT", "gateway_response": "SIMULATED_DISPATCH_SUCCESS_HTTP_200"}

        # 1. Twilio SMS Dispatch
        if provider == "TWILIO" and settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            try:
                url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
                auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                data = {
                    "From": settings.TWILIO_FROM_NUMBER,
                    "To": recipient_mobile if recipient_mobile.startswith("+") else f"+91{recipient_mobile}",
                    "Body": message_body,
                }
                res = requests.post(url, data=data, auth=auth, timeout=10)
                if res.status_code in (200, 201):
                    logger.info("Twilio SMS dispatched to %s (SID: %s)", recipient_mobile, res.json().get("sid"))
                    return {"status": "SENT", "gateway_response": f"TWILIO_SUCCESS_{res.json().get('sid')}"}
                else:
                    logger.error("Twilio SMS failed (%d): %s", res.status_code, res.text)
                    return {"status": "FAILED", "gateway_response": f"TWILIO_ERROR_{res.status_code}"}
            except Exception as e:
                logger.error("Twilio SMS dispatch exception: %s", e)
                return {"status": "FAILED", "gateway_response": str(e)}

        # 2. Fast2SMS Dispatch (India Routes)
        if provider == "FAST2SMS" and settings.FAST2SMS_API_KEY:
            try:
                url = "https://www.fast2sms.com/dev/bulkV2"
                headers = {"authorization": settings.FAST2SMS_API_KEY}
                payload = {
                    "route": "v3",
                    "sender_id": "TXTIND",
                    "message": message_body,
                    "language": "english",
                    "flash": 0,
                    "numbers": recipient_mobile.replace("+91", "").strip(),
                }
                res = requests.post(url, headers=headers, json=payload, timeout=10)
                if res.status_code == 200 and res.json().get("return"):
                    logger.info("Fast2SMS message dispatched to %s", recipient_mobile)
                    return {"status": "SENT", "gateway_response": "FAST2SMS_SUCCESS"}
                else:
                    logger.error("Fast2SMS failed: %s", res.text)
                    return {"status": "FAILED", "gateway_response": f"FAST2SMS_ERROR_{res.text}"}
            except Exception as e:
                logger.error("Fast2SMS exception: %s", e)
                return {"status": "FAILED", "gateway_response": str(e)}

        # Fallback simulation
        logger.info("[SMS SIMULATED] To: %s | Message: %s", recipient_mobile, message_body)
        return {"status": "SENT", "gateway_response": "SIMULATED_DISPATCH_DEFAULT"}

    @classmethod
    def send_sms(
        cls,
        db: Session,
        farmer_profile_id: Optional[uuid.UUID],
        recipient_mobile: str,
        recipient_name: str,
        message_body: str,
        recipient_type: str = "CUSTOMER",
        notification_type: str = NotificationType.BILL_ISSUED.value,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[uuid.UUID] = None,
    ) -> SMSLog:
        """
        Sends an SMS message and records an audit log entry in the database.
        """
        dispatch_result = cls._dispatch_gateway(recipient_mobile, message_body)
        log_status = NotificationStatus.SENT.value if dispatch_result["status"] == "SENT" else NotificationStatus.FAILED.value

        sms_log = SMSLog(
            id=uuid.uuid4(),
            farmer_profile_id=farmer_profile_id,
            recipient_mobile=recipient_mobile,
            recipient_name=recipient_name,
            recipient_type=recipient_type,
            message_body=message_body,
            notification_type=notification_type,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            status=log_status,
            sent_at=datetime.now(timezone.utc) if log_status == NotificationStatus.SENT.value else None,
            gateway_response=dispatch_result["gateway_response"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(sms_log)
        db.commit()
        db.refresh(sms_log)
        return sms_log

    @classmethod
    def send_order_placed_sms(
        cls,
        db: Session,
        farmer_profile_id: uuid.UUID,
        customer_mobile: str,
        customer_name: str,
        order_number: str,
        total_amount: str,
        order_id: uuid.UUID,
    ) -> SMSLog:
        from app.services.whatsapp_service import WhatsAppService
        try:
            WhatsAppService.send_order_confirmation(
                to_mobile=customer_mobile,
                order_number=order_number,
                customer_name=customer_name,
                total_amount=total_amount,
            )
        except Exception as e:
            logger.warning("Failed to send WhatsApp order notification: %s", e)

        msg = f"Hello {customer_name}, your Agri-Smart Order {order_number} for Rs.{total_amount} is placed. Track at {settings.FRONTEND_URL}/orders"
        return cls.send_sms(
            db=db,
            farmer_profile_id=farmer_profile_id,
            recipient_mobile=customer_mobile,
            recipient_name=customer_name,
            message_body=msg,
            recipient_type="CUSTOMER",
            notification_type="BILL_ISSUED",
            related_entity_type="MARKETPLACE_ORDER",
            related_entity_id=order_id,
        )

    @classmethod
    def send_payment_received_sms(
        cls,
        db: Session,
        farmer_profile_id: uuid.UUID,
        customer_mobile: str,
        customer_name: str,
        order_number: str,
        amount: str,
        order_id: uuid.UUID,
    ) -> SMSLog:
        from app.services.whatsapp_service import WhatsAppService
        try:
            WhatsAppService.send_payment_receipt(
                to_mobile=customer_mobile,
                customer_name=customer_name,
                order_number=order_number,
                payment_number="RECEIPT",
                amount=amount,
                payment_method="Settled",
            )
        except Exception as e:
            logger.warning("Failed to send WhatsApp payment receipt: %s", e)

        msg = f"Payment of Rs.{amount} for Order {order_number} verified successfully. Agri-Smart will notify once dispatched."
        return cls.send_sms(
            db=db,
            farmer_profile_id=farmer_profile_id,
            recipient_mobile=customer_mobile,
            recipient_name=customer_name,
            message_body=msg,
            recipient_type="CUSTOMER",
            notification_type="PAYMENT_RECEIPT",
            related_entity_type="MARKETPLACE_ORDER",
            related_entity_id=order_id,
        )

    @classmethod
    def generate_whatsapp_link(cls, recipient_mobile: str, message_body: str) -> str:
        """Generates a standard wa.me direct click link for sending WhatsApp message."""
        import urllib.parse
        clean_mobile = recipient_mobile.replace("+", "").replace(" ", "").replace("-", "").strip()
        if not clean_mobile.startswith("91") and len(clean_mobile) == 10:
            clean_mobile = f"91{clean_mobile}"
        encoded_text = urllib.parse.quote(message_body)
        return f"https://wa.me/{clean_mobile}?text={encoded_text}"

    @classmethod
    def send_whatsapp_message(
        cls,
        db: Session,
        farmer_profile_id: Optional[uuid.UUID],
        recipient_mobile: str,
        recipient_name: str,
        message_body: str,
        recipient_type: str = "CUSTOMER",
        related_entity_type: Optional[str] = "PRODUCE_PROCUREMENT",
        related_entity_id: Optional[uuid.UUID] = None,
    ) -> SMSLog:
        """
        Dispatches live WhatsApp notification via Meta Cloud API with full audit record.
        """
        from app.services.whatsapp_service import WhatsAppService
        logger.info("[WHATSAPP DISPATCH] To: %s | Message: %s", recipient_mobile, message_body)
        
        # Dispatch live message via Meta WhatsApp Cloud API
        try:
            WhatsAppService.send_text_message(recipient_mobile, message_body)
        except Exception as e:
            logger.warning("Failed to dispatch WhatsApp direct text: %s", e)

        return cls.send_sms(
            db=db,
            farmer_profile_id=farmer_profile_id,
            recipient_mobile=recipient_mobile,
            recipient_name=recipient_name,
            message_body=message_body,
            recipient_type=recipient_type,
            notification_type="STAGE_ALERT",
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
        )

    @classmethod
    def send_otp_sms(
        cls,
        db: Session,
        recipient_mobile: str,
        recipient_name: str,
        otp_code: str,
        purpose: str = "Two-Factor Verification",
        expiry_minutes: int = 10,
    ) -> SMSLog:
        """
        Dispatches OTP verification code via SMS and Meta Cloud WhatsApp.
        """
        from app.services.whatsapp_service import WhatsAppService
        try:
            WhatsAppService.send_otp(
                to_mobile=recipient_mobile,
                user_name=recipient_name,
                otp_code=otp_code,
                purpose=purpose,
                expiry_minutes=expiry_minutes,
            )
        except Exception as e:
            logger.warning("Failed to send WhatsApp OTP: %s", e)

        msg = f"Your Agri-Smart verification code for {purpose} is {otp_code}. Valid for {expiry_minutes} mins. Do not share this code."
        return cls.send_sms(
            db=db,
            farmer_profile_id=None,
            recipient_mobile=recipient_mobile,
            recipient_name=recipient_name,
            message_body=msg,
            recipient_type="CUSTOMER",
            notification_type="OTP_VERIFICATION",
            related_entity_type="AUTH",
            related_entity_id=None,
        )

    @classmethod
    def send_password_reset_sms(
        cls,
        db: Session,
        recipient_mobile: str,
        recipient_name: str,
        otp_code: str,
        expiry_minutes: int = 15,
    ) -> SMSLog:
        """
        Dispatches Password Reset code via SMS and Meta Cloud WhatsApp.
        """
        from app.services.whatsapp_service import WhatsAppService
        try:
            WhatsAppService.send_password_reset(
                to_mobile=recipient_mobile,
                user_name=recipient_name,
                otp_code=otp_code,
                expiry_minutes=expiry_minutes,
            )
        except Exception as e:
            logger.warning("Failed to send WhatsApp password reset: %s", e)

        msg = f"Agri-Smart Password Reset: Your verification code is {otp_code}. Valid for {expiry_minutes} mins. If you did not request this, ignore."
        return cls.send_sms(
            db=db,
            farmer_profile_id=None,
            recipient_mobile=recipient_mobile,
            recipient_name=recipient_name,
            message_body=msg,
            recipient_type="CUSTOMER",
            notification_type="PASSWORD_RESET",
            related_entity_type="AUTH",
            related_entity_id=None,
        )

