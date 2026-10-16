import datetime
import hashlib
import logging
import secrets
from datetime import timezone, timedelta
from typing import List, Optional, Dict, Any
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from app.core.config import settings

logger = logging.getLogger("agri_smart.jwt")

from pathlib import Path
import os

# Lazy-loaded in-memory RSA keypair for development/testing if no keys are provided in env
_dev_private_key_pem: Optional[str] = None
_dev_public_key_pem: Optional[str] = None


def _get_or_generate_dev_keys() -> tuple[str, str]:
    global _dev_private_key_pem, _dev_public_key_pem
    if _dev_private_key_pem is None or _dev_public_key_pem is None:
        keys_dir = Path(__file__).resolve().parent.parent.parent / "keys"
        priv_file = keys_dir / "jwt_dev_private.pem"
        pub_file = keys_dir / "jwt_dev_public.pem"

        if priv_file.is_file() and pub_file.is_file():
            try:
                _dev_private_key_pem = priv_file.read_text(encoding="utf-8").strip()
                _dev_public_key_pem = pub_file.read_text(encoding="utf-8").strip()
                return _dev_private_key_pem, _dev_public_key_pem
            except Exception as e:
                logger.warning("Failed to read cached dev keys: %s", e)

        logger.info("Generating persistent RSA 2048-bit keypair for development...")
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        _dev_private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode("utf-8")

        _dev_public_key_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode("utf-8")

        try:
            keys_dir.mkdir(parents=True, exist_ok=True)
            priv_file.write_text(_dev_private_key_pem, encoding="utf-8")
            pub_file.write_text(_dev_public_key_pem, encoding="utf-8")
        except Exception as e:
            logger.warning("Could not persist dev JWT keys to disk: %s", e)

    return _dev_private_key_pem, _dev_public_key_pem

def get_private_key() -> str:
    """Returns the RSA private key for RS256 signing."""
    if settings.JWT_PRIVATE_KEY_PATH and os.path.isfile(settings.JWT_PRIVATE_KEY_PATH):
        try:
            return Path(settings.JWT_PRIVATE_KEY_PATH).read_text(encoding="utf-8").strip()
        except Exception as e:
            logger.error("Failed to read JWT private key from %s: %s", settings.JWT_PRIVATE_KEY_PATH, e)
    if settings.JWT_PRIVATE_KEY and settings.JWT_PRIVATE_KEY.strip():
        return settings.JWT_PRIVATE_KEY.replace("\\n", "\n").strip()
    priv_key, _ = _get_or_generate_dev_keys()
    return priv_key


def get_public_key() -> str:
    """Returns the RSA public key for RS256 verification."""
    if settings.JWT_PUBLIC_KEY_PATH and os.path.isfile(settings.JWT_PUBLIC_KEY_PATH):
        try:
            return Path(settings.JWT_PUBLIC_KEY_PATH).read_text(encoding="utf-8").strip()
        except Exception as e:
            logger.error("Failed to read JWT public key from %s: %s", settings.JWT_PUBLIC_KEY_PATH, e)
    if settings.JWT_PUBLIC_KEY and settings.JWT_PUBLIC_KEY.strip():
        return settings.JWT_PUBLIC_KEY.replace("\\n", "\n").strip()
    _, pub_key = _get_or_generate_dev_keys()
    return pub_key


def create_access_token(
    user_id: str,
    roles: List[str],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Creates an RS256-signed short-lived access token (15 minutes).
    """
    now = datetime.datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "roles": roles,
        "type": "access",
        "jti": str(secrets.token_hex(16)),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    }

    private_key = get_private_key()
    return jwt.encode(payload, private_key, algorithm="RS256")


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and verifies an RS256 access token.
    Enforces algorithm='RS256', expiration check, and type='access'.
    Raises jwt.PyJWTError on invalid token.
    """
    public_key = get_public_key()
    payload = jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        options={"require": ["exp", "iat", "sub", "type"]}
    )

    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Invalid token type. Expected access token.")

    return payload


def generate_refresh_token() -> str:
    """
    Generates a cryptographically secure random refresh token string.
    """
    return secrets.token_urlsafe(64)


def hash_refresh_token(token: str) -> str:
    """
    Computes SHA-256 hash of a refresh token for secure database storage.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
