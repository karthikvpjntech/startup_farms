import uuid
import datetime
from datetime import timezone, timedelta
import pytest
import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.core.jwt import create_access_token, decode_access_token, get_private_key, get_public_key, generate_refresh_token, hash_refresh_token
from app.models.enums import RoleEnum
from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.seeds.roles_seed import seed_roles
from app.seeds.super_admin_seed import seed_super_admin


from tests.conftest import TestingSessionLocal


# --------------------------------------------------------------------------
# 1. Login & Credential Validation Tests
# --------------------------------------------------------------------------

def test_login_super_admin_via_email(client):
    """Super Admin can log in using email identifier."""
    response = client.post("/api/v1/auth/login", json={
        "identifier": "admin@agrismart.local",
        "password": "SuperAdminPass123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 900
    assert data["user"]["email"] == "admin@agrismart.local"
    assert data["user"]["mobile_number"] == "9999999999"
    assert "SUPER_ADMIN" in data["user"]["roles"]

    # Ensure password and hash are not in response
    assert "password" not in data
    assert "password_hash" not in data
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]

    # Ensure HttpOnly refresh cookie is set
    assert settings.REFRESH_COOKIE_NAME in response.cookies
    assert len(response.cookies[settings.REFRESH_COOKIE_NAME]) > 20


def test_login_super_admin_via_mobile(client):
    """Super Admin can log in using mobile_number identifier."""
    response = client.post("/api/v1/auth/login", json={
        "identifier": "9999999999",
        "password": "SuperAdminPass123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["full_name"] == "System Administrator"
    assert "SUPER_ADMIN" in data["user"]["roles"]


def test_login_wrong_password_returns_generic_401(client):
    """Invalid password returns generic 401 detail."""
    response = client.post("/api/v1/auth/login", json={
        "identifier": "admin@agrismart.local",
        "password": "IncorrectPassword!"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_login_nonexistent_identifier_returns_generic_401(client):
    """Unknown email or mobile returns generic 401 without enumeration leak."""
    response = client.post("/api/v1/auth/login", json={
        "identifier": "unknown@example.com",
        "password": "SuperAdminPass123!"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_login_disabled_user_fails(client):
    """Inactive user cannot log in and receives 401."""
    db = TestingSessionLocal()
    user = UserRepository.create(
        db,
        full_name="Disabled User",
        mobile_number="9111111111",
        email="disabled@example.com",
        password_hash=get_password_hash("Password123!"),
        is_active=False
    )
    db.close()

    response = client.post("/api/v1/auth/login", json={
        "identifier": "disabled@example.com",
        "password": "Password123!"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_login_deleted_user_fails(client):
    """Soft-deleted user cannot log in and receives 401."""
    db = TestingSessionLocal()
    user = UserRepository.create(
        db,
        full_name="Deleted User",
        mobile_number="9222222222",
        email="deleted@example.com",
        password_hash=get_password_hash("Password123!"),
        is_active=True
    )
    user.is_deleted = True
    user.deleted_at = datetime.datetime.now(timezone.utc)
    db.commit()
    db.close()

    response = client.post("/api/v1/auth/login", json={
        "identifier": "9222222222",
        "password": "Password123!"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


# --------------------------------------------------------------------------
# 2. RS256 JWT Access Token Verification Tests
# --------------------------------------------------------------------------

def test_access_token_structure_and_claims(client):
    """Verify RS256 algorithm, claims (sub, type, roles, jti, iat, exp), and 15m expiration."""
    res = client.post("/api/v1/auth/login", json={
        "identifier": "admin@agrismart.local",
        "password": "SuperAdminPass123!"
    })
    token = res.json()["access_token"]

    # Decode and inspect raw header
    unverified_header = jwt.get_unverified_header(token)
    assert unverified_header["alg"] == "RS256"

    # Decode and verify payload
    payload = decode_access_token(token)
    assert payload["type"] == "access"
    assert "sub" in payload
    assert payload["roles"] == ["SUPER_ADMIN"]
    assert "jti" in payload
    assert "iat" in payload
    assert "exp" in payload

    # Expiry is roughly 900 seconds in future
    assert payload["exp"] - payload["iat"] == 900


def test_access_token_requires_access_type():
    """Tokens with type != 'access' fail decoding."""
    # Create fake refresh payload signed with RS256
    fake_refresh = {
        "sub": str(uuid.uuid4()),
        "type": "refresh",
        "iat": int(datetime.datetime.now(timezone.utc).timestamp()),
        "exp": int((datetime.datetime.now(timezone.utc) + timedelta(days=7)).timestamp())
    }
    priv_key = get_private_key()
    token = jwt.encode(fake_refresh, priv_key, algorithm="RS256")

    with pytest.raises(jwt.InvalidTokenError, match="Invalid token type"):
        decode_access_token(token)


# --------------------------------------------------------------------------
# 3. Current User Endpoint (/me) Tests
# --------------------------------------------------------------------------

def test_get_me_with_valid_token(client):
    """Valid Bearer token returns current user profile with active roles."""
    login_res = client.post("/api/v1/auth/login", json={
        "identifier": "admin@agrismart.local",
        "password": "SuperAdminPass123!"
    })
    token = login_res.json()["access_token"]

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "admin@agrismart.local"
    assert data["mobile_number"] == "9999999999"
    assert data["roles"] == ["SUPER_ADMIN"]
    assert "password" not in data
    assert "password_hash" not in data


def test_get_me_missing_token_fails(client):
    """Missing Authorization header returns 401."""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401


def test_get_me_invalid_token_fails(client):
    """Invalid token returns 401."""
    res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.value"})
    assert res.status_code == 401


def test_get_me_expired_token_fails(client):
    """Expired token returns 401."""
    db = TestingSessionLocal()
    admin = UserRepository.get_by_mobile(db, "9999999999")
    db.close()

    # Generate token expired 5 minutes ago
    expired_token = create_access_token(
        user_id=str(admin.id),
        roles=["SUPER_ADMIN"],
        expires_delta=timedelta(minutes=-5)
    )

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401
    assert "expired" in res.json()["detail"]


def test_get_me_soft_deleted_user_token_rejected(client):
    """If user is deleted after token issuance, /me rejects with 401."""
    login_res = client.post("/api/v1/auth/login", json={
        "identifier": "admin@agrismart.local",
        "password": "SuperAdminPass123!"
    })
    token = login_res.json()["access_token"]

    # Mark user soft-deleted
    db = TestingSessionLocal()
    admin = UserRepository.get_by_mobile(db, "9999999999")
    admin.is_deleted = True
    db.commit()
    db.close()

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401


# --------------------------------------------------------------------------
# 4. Refresh Token & Rotation Tests
# --------------------------------------------------------------------------

def test_refresh_token_rotation_success(client):
    """Refresh token in HttpOnly cookie rotates token and issues new access token."""
    login_res = client.post("/api/v1/auth/login", json={
        "identifier": "admin@agrismart.local",
        "password": "SuperAdminPass123!"
    })
    old_access_token = login_res.json()["access_token"]
    old_cookie = login_res.cookies.get(settings.REFRESH_COOKIE_NAME)

    # Call /refresh with cookie
    client.cookies.set(settings.REFRESH_COOKIE_NAME, old_cookie)
    refresh_res = client.post("/api/v1/auth/refresh")
    assert refresh_res.status_code == 200
    data = refresh_res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 900
    assert "refresh_token" not in data  # Never returned in JSON

    new_access_token = data["access_token"]
    new_cookie = refresh_res.cookies.get(settings.REFRESH_COOKIE_NAME)

    assert new_access_token != old_access_token
    assert new_cookie != old_cookie

    # Attempting to reuse old refresh token triggers revocation and fails with 401
    client.cookies.set(settings.REFRESH_COOKIE_NAME, old_cookie)
    reuse_res = client.post("/api/v1/auth/refresh")
    assert reuse_res.status_code == 401


def test_refresh_missing_cookie_fails(client):
    """Calling /refresh without cookie returns 401."""
    client.cookies.clear()
    res = client.post("/api/v1/auth/refresh")
    assert res.status_code == 401


def test_refresh_expired_token_fails(client):
    """Expired refresh token fails with 401."""
    db = TestingSessionLocal()
    admin = UserRepository.get_by_mobile(db, "9999999999")
    raw_token = generate_refresh_token()
    token_hash = hash_refresh_token(raw_token)
    # Create expired record
    RefreshTokenRepository.create(
        db,
        user_id=admin.id,
        token_hash=token_hash,
        expires_at=datetime.datetime.now(timezone.utc) - timedelta(days=1)
    )
    db.close()

    client.cookies.set(settings.REFRESH_COOKIE_NAME, raw_token)
    res = client.post("/api/v1/auth/refresh")
    assert res.status_code == 401


# --------------------------------------------------------------------------
# 5. Logout & Revocation Tests
# --------------------------------------------------------------------------

def test_logout_revokes_session_and_clears_cookie(client):
    """Logout invalidates refresh session in DB and deletes cookie."""
    login_res = client.post("/api/v1/auth/login", json={
        "identifier": "admin@agrismart.local",
        "password": "SuperAdminPass123!"
    })
    cookie = login_res.cookies.get(settings.REFRESH_COOKIE_NAME)

    client.cookies.set(settings.REFRESH_COOKIE_NAME, cookie)
    logout_res = client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200
    assert logout_res.json()["message"] == "Logged out successfully"

    # Refreshing with the logged-out cookie should fail
    client.cookies.set(settings.REFRESH_COOKIE_NAME, cookie)
    refresh_res = client.post("/api/v1/auth/refresh")
    assert refresh_res.status_code == 401


def test_logout_is_idempotent_without_cookie(client):
    """Calling logout without cookie returns 200 without error."""
    client.cookies.clear()
    logout_res = client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200
    assert logout_res.json()["message"] == "Logged out successfully"
