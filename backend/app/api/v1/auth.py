from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    LoginResponse,
    TokenRefreshResponse,
    LogoutResponse,
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
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication & Security"])


def _set_auth_cookie(response: Response, raw_refresh_token: str):
    """Sets secure HttpOnly refresh token cookie."""
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=raw_refresh_token,
        httponly=settings.REFRESH_COOKIE_HTTPONLY,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth"
    )


@router.post(
    "/register",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User / Customer Registration"
)
def register(
    request: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Registers a new user account (defaults to CUSTOMER role or requested role),
    issues an RS256 access token, and sets a secure HttpOnly refresh token cookie.
    """
    login_response, raw_refresh_token = AuthService.register_user(db, request)
    if raw_refresh_token:
        _set_auth_cookie(response, raw_refresh_token)
    return login_response


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User & Super Admin Login"
)
def login(
    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Authenticates user credentials using email or mobile number and Argon2id password verification.
    If 2FA is active, returns requires_2fa=True with temporary two_factor_token and sends 6-digit OTP.
    Otherwise, issues an RS256 JWT access token and sets a secure HttpOnly refresh token cookie.
    """
    login_response, raw_refresh_token = AuthService.login_user(db, request)
    if raw_refresh_token:
        _set_auth_cookie(response, raw_refresh_token)
    return login_response


@router.post(
    "/login/2fa-verify",
    response_model=LoginResponse,
    summary="Verify Two-Factor Authentication (2FA) OTP"
)
def verify_2fa_login(
    request: TwoFactorVerifyRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Verifies the 6-digit OTP code sent during login and completes authentication.
    """
    login_response, raw_refresh_token = AuthService.verify_2fa_login(db, request)
    if raw_refresh_token:
        _set_auth_cookie(response, raw_refresh_token)
    return login_response


@router.post(
    "/login/otp-request",
    response_model=OtpLoginResponse,
    summary="Request Passwordless OTP Login"
)
def request_otp_login(
    request: OtpLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Sends a 6-digit one-time password to the user's registered email or mobile number for passwordless sign-in.
    """
    return AuthService.request_otp_login(db, request)


@router.post(
    "/login/otp-verify",
    response_model=LoginResponse,
    summary="Verify Passwordless OTP Login"
)
def verify_otp_login(
    request: OtpLoginVerifyRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Verifies the passwordless OTP code and logs the user in.
    """
    login_response, raw_refresh_token = AuthService.verify_otp_login(db, request)
    if raw_refresh_token:
        _set_auth_cookie(response, raw_refresh_token)
    return login_response


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    summary="Request Self-Service Password Reset"
)
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Sends a password reset OTP code and temporary session token to the user's registered contact.
    """
    return AuthService.forgot_password(db, request)


@router.post(
    "/verify-reset-otp",
    response_model=VerifyResetOtpResponse,
    summary="Verify Password Reset OTP Code"
)
def verify_reset_otp(
    request: VerifyResetOtpRequest,
    db: Session = Depends(get_db)
):
    """
    Verifies the 6-digit OTP code for password reset and grants password modification authority.
    """
    return AuthService.verify_reset_otp(db, request)


@router.post(
    "/reset-password",
    summary="Set New Password with Reset Token"
)
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Updates the account password with a new Argon2id hash and revokes all active refresh tokens for security.
    """
    return AuthService.reset_password(db, request)


@router.post(
    "/otp/resend",
    summary="Resend Active OTP Code"
)
def resend_otp(
    request: ResendOtpRequest,
    db: Session = Depends(get_db)
):
    """
    Resends fresh OTP verification code for 2FA, password reset, or passwordless login.
    """
    return AuthService.resend_otp(db, request)


@router.get(
    "/2fa/status",
    response_model=TwoFactorStatusResponse,
    summary="Get Two-Factor Authentication Status"
)
def get_2fa_status(
    current_user: User = Depends(get_current_user)
):
    """
    Returns whether 2FA is currently enabled for the authenticated user and preferred channel.
    """
    return AuthService.get_2fa_status(current_user)


@router.post(
    "/2fa/setup-request",
    summary="Initiate Two-Factor Authentication Setup"
)
def setup_2fa_request(
    request: TwoFactorSetupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sends confirmation OTP code to user's contact to verify before enabling 2FA.
    """
    return AuthService.setup_2fa_request(db, current_user, request)


@router.post(
    "/2fa/setup-confirm",
    response_model=TwoFactorStatusResponse,
    summary="Confirm OTP & Enable Two-Factor Authentication"
)
def setup_2fa_confirm(
    request: TwoFactorSetupConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validates confirmation OTP and activates Two-Factor Authentication.
    """
    return AuthService.setup_2fa_confirm(db, current_user, request)


@router.post(
    "/2fa/disable",
    response_model=TwoFactorStatusResponse,
    summary="Disable Two-Factor Authentication"
)
def disable_2fa(
    request: TwoFactorDisableRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disables Two-Factor Authentication for the account.
    """
    return AuthService.disable_2fa(db, current_user, request)


@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    summary="Refresh Access Token"
)
def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Validates the refresh token retrieved from the HttpOnly cookie, rotates the refresh token,
    sets a new HttpOnly cookie, and issues a fresh 15-minute RS256 access token.
    """
    cookie_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    token_response, new_raw_refresh = AuthService.refresh_access_token(db, cookie_token)
    _set_auth_cookie(response, new_raw_refresh)
    return token_response


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="User Logout"
)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Revokes the current refresh token session in the database and clears the HttpOnly cookie.
    """
    cookie_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    AuthService.logout_user(db, cookie_token)

    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path="/api/v1/auth"
    )

    return LogoutResponse(message="Logged out successfully")


@router.get(
    "/me",
    response_model=UserMeResponse,
    summary="Get Current Authenticated User"
)
def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the authenticated user identity and active roles via Bearer access token.
    """
    return AuthService.get_user_profile(current_user)
