from typing import List, Union, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Agri-Smart Ecosystem"
    APP_ENV: str = "development"
    DEBUG: bool = True

    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # Database Configuration (Supports SQLite local dev or Supabase / PostgreSQL)
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/agri_smart"

    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://127.0.0.1:3000"

    # Initial Super Admin Seed Settings
    SUPER_ADMIN_NAME: str = "System Administrator"
    SUPER_ADMIN_MOBILE: str = "9999999999"
    SUPER_ADMIN_EMAIL: Optional[str] = "admin@agrismart.local"
    SUPER_ADMIN_PASSWORD: Optional[str] = None

    # JWT Authentication Settings (RS256)
    JWT_ALGORITHM: str = "RS256"
    JWT_PRIVATE_KEY: Optional[str] = None
    JWT_PUBLIC_KEY: Optional[str] = None
    JWT_PRIVATE_KEY_PATH: Optional[str] = None
    JWT_PUBLIC_KEY_PATH: Optional[str] = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Refresh Cookie Settings
    REFRESH_COOKIE_NAME: str = "refresh_token"
    REFRESH_COOKIE_SECURE: bool = False
    REFRESH_COOKIE_SAMESITE: str = "lax"
    REFRESH_COOKIE_HTTPONLY: bool = True

    # Cloudinary Media Storage Settings
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None
    CLOUDINARY_SECURE: bool = True
    CLOUDINARY_FOLDER: str = "agri_smart"

    # Email / SMTP Notification Settings
    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "notifications@agrismart.local"
    SMTP_FROM_NAME: str = "Agri-Smart Ecosystem"
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False

    # SMS / Message Notification Settings
    SMS_ENABLED: bool = False
    SMS_PROVIDER: str = "LOG_CONSOLE"  # LOG_CONSOLE, TWILIO, FAST2SMS, MSG91
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_FROM_NUMBER: Optional[str] = None
    FAST2SMS_API_KEY: Optional[str] = None

    # WhatsApp Cloud API Settings (Meta Graph API)
    WHATSAPP_ENABLED: bool = True
    WHATSAPP_API_URL: str = "https://graph.facebook.com/v21.0"
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = "1293807073823510"
    WHATSAPP_BUSINESS_ACCOUNT_ID: Optional[str] = "1086890310886122"
    WHATSAPP_PHONE_NUMBER: Optional[str] = "+1 (555) 647-7754"
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_OTP_TEMPLATE_NAME: Optional[str] = None
    WHATSAPP_OTP_TEMPLATE_LANG: str = "en_US"

    # Razorpay Payment Gateway Settings (Test / Live Mode)
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = None
    RAZORPAY_CURRENCY: str = "INR"
    RAZORPAY_ENABLED: bool = False

    # Two-Factor Authentication & OTP Settings
    OTP_EXPIRE_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 5
    PASSWORD_RESET_EXPIRE_MINUTES: int = 15

    # Google Places & Location Geofencing Settings
    GOOGLE_PLACES_API_KEY: Optional[str] = None
    GOOGLE_MAPS_API_KEY: Optional[str] = None
    DEFAULT_GEOFENCE_RADIUS_METERS: float = 500.0
    DEFAULT_SEARCH_RADIUS_KM: float = 25.0

    @property
    def cors_origins(self) -> List[str]:
        if isinstance(self.ALLOWED_ORIGINS, list):
            return self.ALLOWED_ORIGINS
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
