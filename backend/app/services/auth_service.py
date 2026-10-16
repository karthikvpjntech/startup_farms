import uuid
import secrets
import logging
from datetime import datetime, timezone, timedelta
from typing import Tuple, List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_password, hash_password
from app.core.jwt import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from app.models.user import User
from app.models.farmer_profile import FarmerProfile
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    LoginResponse,
    TokenRefreshResponse,
    UserSummaryResponse,
    UserMeResponse,
    TwoFactorVerifyRequest,
    OtpLoginRequest,
    OtpLoginResponse,
    OtpLoginVerifyRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    VerifyResetOtpRequest,
    VerifyResetOtpResponse,
    ResetPasswordRequest,
    ResendOtpRequest,
    TwoFactorStatusResponse,
    TwoFactorSetupRequest,
    TwoFactorSetupConfirmRequest,
    TwoFactorDisableRequest,
)
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.otp_repository import OtpRepository
from app.services.otp_service import OtpService
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService

logger = logging.getLogger("agri_smart.auth_service")


class AuthService:
    """
    Production-ready Authentication & Authorization Service.
    Handles Argon2id authentication, RS256 token issuance, Refresh Token rotation,
    Two-Factor Authentication (2FA OTP), Passwordless OTP Login, and Self-Service Password Reset.
    """

    @classmethod
    def _issue_user_session(cls, db: Session, user: User) -> Tuple[LoginResponse, str]:
        """Internal helper to issue RS256 JWT access token and persist new refresh token."""
        roles = [ur.role.name for ur in user.user_roles if ur.role and ur.role.is_active]

        access_token = create_access_token(
            user_id=str(user.id),
            roles=roles,
        )

        raw_refresh_token = generate_refresh_token()
        token_hash = hash_refresh_token(raw_refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        RefreshTokenRepository.create(
            db,
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at
        )

        user_summary = UserSummaryResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            mobile_number=user.mobile_number,
            roles=roles,
            is_two_factor_enabled=user.is_two_factor_enabled,
            two_factor_method=user.two_factor_method,
        )

        login_response = LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_summary,
            requires_2fa=False,
            message="Authenticated successfully",
        )

        return login_response, raw_refresh_token

    @classmethod
    def login_user(cls, db: Session, request: LoginRequest) -> Tuple[LoginResponse, Optional[str]]:
        """
        Authenticates user credentials using email or mobile number with Argon2id password verification.
        If Two-Factor Authentication is active, triggers 6-digit OTP dispatch and returns 2FA session token.
        """
        # 1. Look up user by identifier (email or mobile)
        user = UserRepository.get_by_identifier(db, request.identifier)

        auth_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        if not user or user.is_deleted or not user.is_active:
            raise auth_exception

        # 2. Verify Argon2id password
        if not verify_password(request.password, user.password_hash):
            raise auth_exception

        # 3. Check Two-Factor Authentication (2FA) Requirement
        if user.is_two_factor_enabled:
            target_contact = user.email if (user.two_factor_method == "EMAIL" and user.email) else user.mobile_number
            record, raw_otp, session_token = OtpService.create_and_send_otp(
                db=db,
                identifier=target_contact,
                otp_type="TWO_FACTOR_AUTH",
                purpose="Two-Factor Sign-In",
                user=user,
                method=user.two_factor_method,
                expiry_minutes=settings.OTP_EXPIRE_MINUTES,
            )

            masked = OtpService.mask_identifier(target_contact)
            login_response = LoginResponse(
                access_token=None,
                token_type="bearer",
                expires_in=0,
                user=None,
                requires_2fa=True,
                two_factor_token=session_token,
                masked_identifier=masked,
                message=f"Two-Factor Authentication required. Security code sent to {masked}",
            )
            logger.info("2FA challenged for user ID: %s. OTP session: %s", user.id, session_token[:8])
            return login_response, None

        # 4. Standard Direct Login (No 2FA)
        logger.info("User authenticated directly (User ID: %s)", user.id)
        return cls._issue_user_session(db, user)

    @classmethod
    def verify_2fa_login(cls, db: Session, request: TwoFactorVerifyRequest) -> Tuple[LoginResponse, str]:
        """
        Validates 2FA OTP code and issues JWT access token + refresh token session.
        """
        is_valid, record, error_msg = OtpService.verify_otp(
            db=db,
            raw_otp=request.otp_code,
            session_token=request.two_factor_token,
            otp_type="TWO_FACTOR_AUTH"
        )

        if not is_valid or not record or not record.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg or "Invalid or expired Two-Factor verification code."
            )

        user = UserRepository.get_by_id(db, record.user_id)
        if not user or user.is_deleted or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive or disabled."
            )

        logger.info("2FA verification succeeded for user ID: %s", user.id)
        return cls._issue_user_session(db, user)

    @classmethod
    def request_otp_login(cls, db: Session, request: OtpLoginRequest) -> OtpLoginResponse:
        """
        Initiates passwordless OTP login via registered email or mobile number.
        """
        user = UserRepository.get_by_identifier(db, request.identifier)
        if not user or user.is_deleted or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active account found for '{request.identifier}'. Please check or register."
            )

        target_contact = user.email if ("@" in request.identifier and user.email) else user.mobile_number
        record, raw_otp, session_token = OtpService.create_and_send_otp(
            db=db,
            identifier=target_contact,
            otp_type="LOGIN_OTP",
            purpose="Passwordless Login",
            user=user,
            method="EMAIL" if "@" in target_contact else "SMS",
            expiry_minutes=settings.OTP_EXPIRE_MINUTES,
        )

        masked = OtpService.mask_identifier(target_contact)
        return OtpLoginResponse(
            message=f"Login verification code sent to {masked}",
            session_token=session_token,
            masked_identifier=masked,
            expires_in_minutes=settings.OTP_EXPIRE_MINUTES,
        )

    @classmethod
    def verify_otp_login(cls, db: Session, request: OtpLoginVerifyRequest) -> Tuple[LoginResponse, str]:
        """
        Completes passwordless OTP login and issues auth credentials.
        """
        is_valid, record, error_msg = OtpService.verify_otp(
            db=db,
            raw_otp=request.otp_code,
            session_token=request.session_token,
            otp_type="LOGIN_OTP"
        )

        if not is_valid or not record or not record.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg or "Invalid or expired login verification code."
            )

        user = UserRepository.get_by_id(db, record.user_id)
        if not user or user.is_deleted or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive or disabled."
            )

        logger.info("Passwordless OTP login succeeded for user ID: %s", user.id)
        return cls._issue_user_session(db, user)

    @classmethod
    def forgot_password(cls, db: Session, request: ForgotPasswordRequest) -> ForgotPasswordResponse:
        """
        Initiates self-service password reset flow.
        Dispatches OTP code and password reset session token.
        """
        user = UserRepository.get_by_identifier(db, request.identifier)

        # To prevent account enumeration, return safe message if user does not exist
        if not user or user.is_deleted or not user.is_active:
            logger.info("[FORGOT PASSWORD] Identifier '%s' not found. Returning safe mock response.", request.identifier)
            return ForgotPasswordResponse(
                message="If an active account exists with this contact, a password reset code has been sent.",
                session_token=secrets.token_urlsafe(32),
                masked_identifier=OtpService.mask_identifier(request.identifier),
                expires_in_minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES,
            )

        target_contact = user.email if ("@" in request.identifier and user.email) else (user.email or user.mobile_number)
        record, raw_otp, session_token = OtpService.create_and_send_otp(
            db=db,
            identifier=target_contact,
            otp_type="PASSWORD_RESET",
            purpose="Password Reset",
            user=user,
            method="EMAIL" if ("@" in target_contact and user.email) else "SMS",
            expiry_minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES,
        )

        masked = OtpService.mask_identifier(target_contact)
        return ForgotPasswordResponse(
            message=f"Password reset code dispatched to {masked}",
            session_token=session_token,
            masked_identifier=masked,
            expires_in_minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES,
        )

    @classmethod
    def verify_reset_otp(cls, db: Session, request: VerifyResetOtpRequest) -> VerifyResetOtpResponse:
        """
        Validates the password reset OTP code.
        """
        is_valid, record, error_msg = OtpService.verify_otp(
            db=db,
            raw_otp=request.otp_code,
            session_token=request.session_token,
            otp_type="PASSWORD_RESET"
        )

        if not is_valid or not record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg or "Invalid or expired password reset verification code."
            )

        return VerifyResetOtpResponse(
            message="Verification successful. You can now set your new password.",
            reset_token=record.session_token or request.session_token,
        )

    @classmethod
    def reset_password(cls, db: Session, request: ResetPasswordRequest) -> Dict[str, Any]:
        """
        Updates the user's password with Argon2id hash and revokes all existing refresh token sessions.
        """
        record = OtpRepository.get_by_session_token(db, request.reset_token, otp_type="PASSWORD_RESET")
        if not record or not record.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token."
            )

        # Check creation time to ensure reset token is used within expiry window
        now = datetime.now(timezone.utc)
        created = record.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        if (now - created).total_seconds() > (settings.PASSWORD_RESET_EXPIRE_MINUTES * 60):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset session has expired. Please request a new code."
            )

        user = UserRepository.get_by_id(db, record.user_id)
        if not user or user.is_deleted or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account not found or disabled."
            )

        # Validate password length
        if len(request.new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters in length."
            )

        # Update password hash
        new_hash = hash_password(request.new_password)
        user.password_hash = new_hash
        user.updated_at = now

        # Security: Revoke all active refresh sessions to disconnect any compromised sessions
        revoked_count = RefreshTokenRepository.revoke_all_for_user(db, user.id)
        logger.info("Revoked %d sessions after password reset for user ID: %s", revoked_count, user.id)

        db.commit()

        # Send security notification email and WhatsApp
        if user.email:
            try:
                EmailService.send_password_changed_email(user.email, user.full_name)
            except Exception as e:
                logger.warning("Failed to send password changed email notification: %s", e)
        if user.mobile_number:
            try:
                from app.services.whatsapp_service import WhatsAppService
                WhatsAppService.send_text_message(
                    user.mobile_number,
                    f"🔒 *Agri-Smart Security Alert*\n\nHello {user.full_name},\nYour Agri-Smart password was changed successfully. If you did not make this change, please contact support immediately."
                )
            except Exception as e:
                logger.warning("Failed to send password changed WhatsApp notification: %s", e)

        return {
            "success": True,
            "message": "Your password has been reset successfully. Please sign in with your new password."
        }

    @classmethod
    def resend_otp(cls, db: Session, request: ResendOtpRequest) -> Dict[str, Any]:
        """
        Resends an active OTP code for 2FA, password reset, or passwordless login.
        """
        otp_type = request.otp_type or "TWO_FACTOR_AUTH"
        target_user = None
        target_contact = request.identifier

        if request.session_token:
            existing = OtpRepository.get_by_session_token(db, request.session_token)
            if existing:
                target_contact = existing.identifier
                if existing.user_id:
                    target_user = UserRepository.get_by_id(db, existing.user_id)
                otp_type = existing.otp_type

        if not target_contact and target_user:
            target_contact = target_user.email or target_user.mobile_number

        if not target_contact:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Identifier or session token is required to resend verification code."
            )

        record, raw_otp, new_session_token = OtpService.create_and_send_otp(
            db=db,
            identifier=target_contact,
            otp_type=otp_type,
            purpose=f"{otp_type.replace('_', ' ').title()} Resend",
            user=target_user,
            method="EMAIL" if "@" in target_contact else "SMS",
            expiry_minutes=settings.OTP_EXPIRE_MINUTES,
        )

        masked = OtpService.mask_identifier(target_contact)
        return {
            "success": True,
            "message": f"Fresh verification code sent to {masked}",
            "session_token": new_session_token,
            "masked_identifier": masked,
            "expires_in_minutes": settings.OTP_EXPIRE_MINUTES,
        }

    @classmethod
    def get_2fa_status(cls, user: User) -> TwoFactorStatusResponse:
        """Returns 2FA status for the current user."""
        return TwoFactorStatusResponse(
            is_two_factor_enabled=user.is_two_factor_enabled,
            two_factor_method=user.two_factor_method,
            email=user.email,
            mobile_number=user.mobile_number,
        )

    @classmethod
    def setup_2fa_request(cls, db: Session, current_user: User, request: TwoFactorSetupRequest) -> Dict[str, Any]:
        """
        Dispatches test OTP to verify user contact before enabling 2FA.
        """
        method = request.method.upper()
        if method not in ["EMAIL", "SMS", "BOTH"]:
            method = "EMAIL"

        target_contact = current_user.email if (method in ["EMAIL", "BOTH"] and current_user.email) else current_user.mobile_number

        record, raw_otp, session_token = OtpService.create_and_send_otp(
            db=db,
            identifier=target_contact,
            otp_type="SETUP_2FA",
            purpose="Two-Factor Setup Confirmation",
            user=current_user,
            method=method,
            expiry_minutes=settings.OTP_EXPIRE_MINUTES,
        )

        masked = OtpService.mask_identifier(target_contact)
        return {
            "message": f"Verification code sent to {masked}. Please confirm to activate 2FA.",
            "session_token": session_token,
            "masked_identifier": masked,
            "method": method,
        }

    @classmethod
    def setup_2fa_confirm(cls, db: Session, current_user: User, request: TwoFactorSetupConfirmRequest) -> TwoFactorStatusResponse:
        """
        Confirms OTP and activates Two-Factor Authentication for the user.
        """
        is_valid, record, error_msg = OtpService.verify_otp(
            db=db,
            raw_otp=request.otp_code,
            session_token=request.session_token,
            otp_type="SETUP_2FA"
        )

        if not is_valid or not record or record.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg or "Invalid or expired confirmation code."
            )

        current_user.is_two_factor_enabled = True
        current_user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(current_user)

        logger.info("2FA activated for user ID: %s", current_user.id)
        return cls.get_2fa_status(current_user)

    @classmethod
    def disable_2fa(cls, db: Session, current_user: User, request: TwoFactorDisableRequest) -> TwoFactorStatusResponse:
        """
        Disables Two-Factor Authentication with optional password verification.
        """
        if request.password:
            if not verify_password(request.password, current_user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Incorrect password. Cannot disable Two-Factor Authentication."
                )

        current_user.is_two_factor_enabled = False
        current_user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(current_user)

        logger.info("2FA disabled for user ID: %s", current_user.id)
        return cls.get_2fa_status(current_user)

    @staticmethod
    def refresh_access_token(db: Session, raw_refresh_token: Optional[str]) -> Tuple[TokenRefreshResponse, str]:
        """
        Validates the refresh token from HttpOnly cookie, checks revocation/expiration,
        rotates the refresh token, and issues a fresh RS256 access token.
        """
        if not raw_refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is required.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_hash = hash_refresh_token(raw_refresh_token)
        token_record = RefreshTokenRepository.get_by_hash(db, token_hash)

        unauthorized_exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

        if not token_record:
            raise unauthorized_exc

        # If token was already revoked, flag potential token reuse and revoke all user sessions
        if token_record.is_revoked:
            logger.warning("Revoked refresh token reuse detected for user ID: %s", token_record.user_id)
            RefreshTokenRepository.revoke_all_for_user(db, token_record.user_id)
            raise unauthorized_exc

        # Check expiration
        now = datetime.now(timezone.utc)
        expires_at = token_record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < now:
            raise unauthorized_exc

        # Load and validate user
        user = UserRepository.get_by_id(db, token_record.user_id)
        if not user or user.is_deleted or not user.is_active:
            raise unauthorized_exc

        # Rotate refresh token: generate new token and record
        new_raw_refresh = generate_refresh_token()
        new_token_hash = hash_refresh_token(new_raw_refresh)
        new_expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        new_record = RefreshTokenRepository.create(
            db,
            user_id=user.id,
            token_hash=new_token_hash,
            expires_at=new_expires_at
        )

        # Invalidate old refresh token
        RefreshTokenRepository.revoke(db, token_record, replaced_by_token_id=new_record.id)

        # Load current active roles from DB
        roles = [ur.role.name for ur in user.user_roles if ur.role and ur.role.is_active]
        access_token = create_access_token(
            user_id=str(user.id),
            roles=roles,
        )

        token_response = TokenRefreshResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

        logger.info("Rotated refresh token for user ID: %s", user.id)
        return token_response, new_raw_refresh

    @staticmethod
    def logout_user(db: Session, raw_refresh_token: Optional[str]) -> bool:
        """
        Revokes the active refresh token session associated with the provided cookie.
        """
        if raw_refresh_token:
            token_hash = hash_refresh_token(raw_refresh_token)
            token_record = RefreshTokenRepository.get_by_hash(db, token_hash)
            if token_record and not token_record.is_revoked:
                RefreshTokenRepository.revoke(db, token_record)
                logger.info("Revoked refresh token for user ID: %s", token_record.user_id)
        return True

    @staticmethod
    def register_user(db: Session, request: RegisterRequest) -> Tuple[LoginResponse, str]:
        """
        Public self-registration for Customers and Farmers.
        """
        clean_mobile = request.mobile_number.strip()
        existing_mobile = UserRepository.get_by_mobile_any(db, clean_mobile)
        if existing_mobile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Mobile number '{clean_mobile}' is already registered."
            )

        clean_email = request.email.strip().lower() if request.email else None
        if clean_email:
            existing_email = UserRepository.get_by_email_any(db, clean_email)
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Email address '{clean_email}' is already registered."
                )

        target_role_name = (request.role or "CUSTOMER").strip().upper()
        role = RoleRepository.get_by_name(db, target_role_name)
        if not role:
            role = RoleRepository.create(db, name=target_role_name, description=f"{target_role_name} Role", is_active=True)

        hashed = hash_password(request.password)
        user = UserRepository.create_with_roles(
            db=db,
            full_name=request.full_name.strip(),
            mobile_number=clean_mobile,
            password_hash=hashed,
            email=clean_email,
            roles=[role],
            is_active=True
        )

        if target_role_name == "FARMER":
            profile = FarmerProfile(
                id=uuid.uuid4(),
                user_id=user.id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(profile)
            db.commit()

        try:
            if clean_email:
                EmailService.send_welcome_email(clean_email, request.full_name.strip(), target_role_name)
            if user.mobile_number:
                from app.services.whatsapp_service import WhatsAppService
                WhatsAppService.send_welcome(user.mobile_number, request.full_name.strip(), target_role_name)
        except Exception as e:
            logger.warning("Failed to dispatch welcome notification: %s", e)

        # Login automatically
        return AuthService._issue_user_session(db, user)

    @staticmethod
    def get_user_profile(user: User) -> UserMeResponse:
        """Builds safe profile representation."""
        roles = [ur.role.name for ur in user.user_roles if ur.role and ur.role.is_active]
        return UserMeResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            mobile_number=user.mobile_number,
            roles=roles,
            is_two_factor_enabled=user.is_two_factor_enabled,
            two_factor_method=user.two_factor_method,
        )
