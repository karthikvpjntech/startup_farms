import hmac
import hashlib
import secrets
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.user import User
from app.models.otp_verification import OtpVerification
from app.repositories.otp_repository import OtpRepository
from app.repositories.user_repository import UserRepository
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService

logger = logging.getLogger("agri_smart.otp_service")


class OtpService:
    """
    Centralized One-Time Password (OTP) & Two-Factor Authentication (2FA) Service.
    Provides secure generation, cryptographic hashing, rate-limiting, and multi-channel dispatch.
    """

    @staticmethod
    def generate_otp_code(length: int = 6) -> str:
        """Generates cryptographically secure numeric OTP."""
        digits = "0123456789"
        return "".join(secrets.choice(digits) for _ in range(length))

    @staticmethod
    def hash_otp(otp_code: str) -> str:
        """HMAC-SHA256 hash of OTP code using JWT private/public key or app secret."""
        secret_key = (
            settings.JWT_PRIVATE_KEY
            or settings.RAZORPAY_KEY_SECRET
            or "agri_smart_secure_otp_salt_2026"
        )
        return hmac.new(
            secret_key.encode("utf-8"),
            otp_code.strip().encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    def generate_session_token() -> str:
        """Generates random secure URL-safe session token."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def mask_identifier(identifier: str) -> str:
        """Masks email address or mobile number for privacy."""
        if not identifier:
            return ""
        if "@" in identifier:
            parts = identifier.split("@")
            name = parts[0]
            domain = parts[1]
            if len(name) <= 2:
                masked_name = name[0] + "*"
            else:
                masked_name = name[0] + "*" * (len(name) - 2) + name[-1]
            return f"{masked_name}@{domain}"
        else:
            clean = identifier.strip()
            if len(clean) >= 10:
                return f"+91 ******{clean[-4:]}"
            return f"******{clean[-2:]}" if len(clean) > 2 else "****"

    @classmethod
    def create_and_send_otp(
        cls,
        db: Session,
        identifier: str,
        otp_type: str = "TWO_FACTOR_AUTH",
        purpose: str = "Two-Factor Verification",
        user: Optional[User] = None,
        method: Optional[str] = None,
        expiry_minutes: Optional[int] = None,
    ) -> Tuple[OtpVerification, str, str]:
        """
        Generates OTP, stores cryptographic hash in DB, and dispatches via Email / SMS.
        Returns (OtpVerification record, raw_otp, session_token).
        """
        expiry_mins = expiry_minutes or settings.OTP_EXPIRE_MINUTES
        raw_otp = cls.generate_otp_code(6)
        session_token = cls.generate_session_token()
        otp_hash = cls.hash_otp(raw_otp)

        # Invalidate existing active OTPs for same identifier and type
        OtpRepository.invalidate_active_for_identifier(db, identifier, otp_type)

        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expiry_mins)
        user_id = user.id if user else None

        record = OtpRepository.create(
            db=db,
            identifier=identifier,
            otp_code_hash=otp_hash,
            otp_type=otp_type,
            expires_at=expires_at,
            user_id=user_id,
            session_token=session_token,
            max_attempts=settings.OTP_MAX_ATTEMPTS,
        )

        # Determine user name and dispatch targets
        user_name = user.full_name if user else "Agri-Smart User"
        target_method = (method or (user.two_factor_method if user else "EMAIL")).upper()

        logger.info(
            "[OTP DISPATCH] Generated %s for %s (%s). Session: %s. Raw OTP: %s",
            otp_type,
            cls.mask_identifier(identifier),
            target_method,
            session_token[:8],
            raw_otp
        )

        # 1. Send via Email
        email_sent = False
        target_email = user.email if user and user.email else (identifier if "@" in identifier else None)
        if target_email and (target_method in ["EMAIL", "BOTH"]):
            try:
                if otp_type == "PASSWORD_RESET":
                    EmailService.send_password_reset_email(
                        to_email=target_email,
                        user_name=user_name,
                        otp_code=raw_otp,
                        expiry_minutes=expiry_mins,
                    )
                else:
                    EmailService.send_otp_email(
                        to_email=target_email,
                        user_name=user_name,
                        otp_code=raw_otp,
                        purpose=purpose,
                        expiry_minutes=expiry_mins,
                    )
                email_sent = True
            except Exception as e:
                logger.warning("Failed to dispatch OTP email: %s", e)

        # 2. Send via SMS
        target_mobile = user.mobile_number if user else (identifier if not "@" in identifier else None)
        if target_mobile and (target_method in ["SMS", "BOTH", "WHATSAPP"] or not email_sent):
            try:
                if otp_type == "PASSWORD_RESET":
                    NotificationService.send_password_reset_sms(
                        db=db,
                        recipient_mobile=target_mobile,
                        recipient_name=user_name,
                        otp_code=raw_otp,
                        expiry_minutes=expiry_mins,
                    )
                else:
                    NotificationService.send_otp_sms(
                        db=db,
                        recipient_mobile=target_mobile,
                        recipient_name=user_name,
                        otp_code=raw_otp,
                        purpose=purpose,
                        expiry_minutes=expiry_mins,
                    )
            except Exception as e:
                logger.warning("Failed to dispatch OTP SMS: %s", e)

        # 3. Send via Meta Cloud WhatsApp API
        if target_mobile:
            try:
                from app.services.whatsapp_service import WhatsAppService
                if otp_type == "PASSWORD_RESET":
                    WhatsAppService.send_password_reset(
                        to_mobile=target_mobile,
                        user_name=user_name,
                        otp_code=raw_otp,
                        expiry_minutes=expiry_mins,
                    )
                else:
                    WhatsAppService.send_otp(
                        to_mobile=target_mobile,
                        user_name=user_name,
                        otp_code=raw_otp,
                        purpose=purpose,
                        expiry_minutes=expiry_mins,
                    )
            except Exception as e:
                logger.warning("Failed to dispatch WhatsApp OTP: %s", e)

        return record, raw_otp, session_token

    @classmethod
    def verify_otp(
        cls,
        db: Session,
        raw_otp: str,
        session_token: Optional[str] = None,
        identifier: Optional[str] = None,
        otp_type: Optional[str] = None,
    ) -> Tuple[bool, Optional[OtpVerification], str]:
        """
        Validates OTP against cryptographic hash with expiry, lockout, and single-use checks.
        Returns (is_valid, record, message).
        """
        if session_token:
            record = OtpRepository.get_by_session_token(db, session_token, otp_type=otp_type)
        elif identifier and otp_type:
            record = OtpRepository.get_latest_active_by_identifier(db, identifier, otp_type=otp_type)
        else:
            return False, None, "Session token or identifier required for OTP verification."

        if not record:
            return False, None, "Verification session not found or already completed."

        if record.is_used:
            return False, record, "This verification code has already been used."

        if record.is_expired:
            return False, record, "Verification code has expired. Please request a new code."

        if record.is_locked:
            return False, record, "Too many failed attempts. For your security, this verification code has been locked."

        # Compute hash and compare
        provided_hash = cls.hash_otp(raw_otp)
        is_match = hmac.compare_digest(record.otp_code_hash, provided_hash)

        if not is_match:
            new_attempts = OtpRepository.increment_attempts(db, record)
            remaining = record.max_attempts - new_attempts
            if remaining <= 0:
                return False, record, "Invalid verification code. Maximum attempts reached. Please request a new code."
            return False, record, f"Invalid verification code. {remaining} attempt(s) remaining."

        # Success - mark used
        OtpRepository.mark_used(db, record)
        logger.info("OTP verified successfully for %s (Type: %s)", record.identifier, record.otp_type)
        return True, record, "Verification successful."
