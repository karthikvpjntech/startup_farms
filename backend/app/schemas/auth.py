import uuid
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.core.phone_utils import validate_and_format_phone


class LoginRequest(BaseModel):
    """
    Login request schema supporting either email or mobile_number as identifier.
    """
    identifier: str = Field(..., min_length=3, max_length=255, description="Registered email address or mobile number")
    password: str = Field(..., min_length=1, max_length=128, description="User password")


class RegisterRequest(BaseModel):
    """
    Registration request for new users (defaults to CUSTOMER role).
    """
    full_name: str = Field(..., min_length=2, max_length=255)
    mobile_number: str = Field(..., min_length=3, max_length=20)
    email: Optional[str] = Field(default=None, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)
    role: Optional[str] = Field(default="CUSTOMER", description="Role to assign, e.g. CUSTOMER or FARMER")

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        res = validate_and_format_phone(v)
        if not res:
            raise ValueError("Mobile number is required.")
        return res


class UserSummaryResponse(BaseModel):
    """
    Safe authenticated user representation returned in login and profile responses.
    Never exposes password_hash or deleted status.
    """
    id: uuid.UUID
    full_name: str
    email: Optional[str] = None
    mobile_number: str
    roles: List[str]
    is_two_factor_enabled: bool = False
    two_factor_method: str = "EMAIL"

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    """
    Response returned upon login attempt.
    Supports instant direct access token OR 2FA challenge requirement.
    """
    access_token: Optional[str] = Field(default=None, description="RS256-signed JWT access token (omitted if 2FA challenge is active)")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=900, description="Access token expiration in seconds (15 minutes)")
    user: Optional[UserSummaryResponse] = None
    requires_2fa: bool = Field(default=False, description="True if Two-Factor OTP verification is required")
    two_factor_token: Optional[str] = Field(default=None, description="Temporary session token for 2FA OTP verification step")
    masked_identifier: Optional[str] = Field(default=None, description="Masked email/phone where OTP was dispatched")
    message: Optional[str] = None


class TwoFactorVerifyRequest(BaseModel):
    """
    Request to complete 2FA login verification with 6-digit OTP code.
    """
    two_factor_token: str = Field(..., description="Temporary session token provided by /login")
    otp_code: str = Field(..., min_length=4, max_length=10, description="6-digit verification code")


class OtpLoginRequest(BaseModel):
    """
    Request to initiate passwordless OTP login via email or mobile number.
    """
    identifier: str = Field(..., min_length=3, max_length=255, description="Registered email address or mobile number")


class OtpLoginResponse(BaseModel):
    """
    Response acknowledging OTP dispatch for passwordless login.
    """
    message: str
    session_token: str
    masked_identifier: str
    expires_in_minutes: int = 10


class OtpLoginVerifyRequest(BaseModel):
    """
    Request to authenticate via passwordless OTP code.
    """
    session_token: str
    otp_code: str = Field(..., min_length=4, max_length=10)


class ForgotPasswordRequest(BaseModel):
    """
    Request to initiate self-service password reset.
    """
    identifier: str = Field(..., min_length=3, max_length=255, description="Registered email address or mobile number")


class ForgotPasswordResponse(BaseModel):
    """
    Response acknowledging password reset OTP dispatch.
    """
    message: str
    session_token: str
    masked_identifier: str
    expires_in_minutes: int = 15


class VerifyResetOtpRequest(BaseModel):
    """
    Request to verify 6-digit OTP for password reset.
    """
    session_token: str
    otp_code: str = Field(..., min_length=4, max_length=10)


class VerifyResetOtpResponse(BaseModel):
    """
    Response providing authorized reset token for password modification.
    """
    message: str
    reset_token: str


class ResetPasswordRequest(BaseModel):
    """
    Request to set a new account password using verified reset token.
    """
    reset_token: str = Field(..., description="Verified password reset token")
    new_password: str = Field(..., min_length=6, max_length=128, description="New secure password")


class ResendOtpRequest(BaseModel):
    """
    Request to resend an active OTP code.
    """
    session_token: Optional[str] = None
    identifier: Optional[str] = None
    otp_type: Optional[str] = "TWO_FACTOR_AUTH"


class TwoFactorStatusResponse(BaseModel):
    """
    Status of Two-Factor Authentication for the currently authenticated user.
    """
    is_two_factor_enabled: bool
    two_factor_method: str
    email: Optional[str] = None
    mobile_number: str


class TwoFactorSetupRequest(BaseModel):
    """
    Request to initiate Two-Factor Authentication activation.
    """
    method: str = Field(default="EMAIL", description="Preferred OTP channel: EMAIL, SMS, or BOTH")


class TwoFactorSetupConfirmRequest(BaseModel):
    """
    Request to confirm OTP and activate Two-Factor Authentication.
    """
    session_token: str
    otp_code: str = Field(..., min_length=4, max_length=10)


class TwoFactorDisableRequest(BaseModel):
    """
    Request to disable Two-Factor Authentication.
    """
    password: Optional[str] = Field(default=None, description="Account password for confirmation")


class TokenRefreshResponse(BaseModel):
    """
    Response returned upon successful refresh token rotation.
    """
    access_token: str = Field(..., description="RS256-signed JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=900, description="Access token expiration in seconds (15 minutes)")


class LogoutResponse(BaseModel):
    """
    Response returned upon successful logout.
    """
    message: str = "Logged out successfully"


class UserMeResponse(BaseModel):
    """
    Response model for /me endpoint.
    """
    id: uuid.UUID
    full_name: str
    email: Optional[str] = None
    mobile_number: str
    roles: List[str]
    is_two_factor_enabled: bool = False
    two_factor_method: str = "EMAIL"

    model_config = ConfigDict(from_attributes=True)
