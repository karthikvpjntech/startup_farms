import uuid
import datetime
from datetime import timezone, timedelta
import pytest
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import get_password_hash
from app.core.jwt import create_access_token
from app.models.enums import RoleEnum
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.dependencies.authorization import require_roles, require_role
from tests.conftest import TestingSessionLocal


def create_test_user_with_roles(db, name: str, mobile: str, email: str, role_enums: list[RoleEnum]) -> tuple[str, User]:
    """Helper to create a user and assign specified roles, returning (user_id_str, user)."""
    user = UserRepository.create(
        db,
        full_name=name,
        mobile_number=mobile,
        email=email,
        password_hash=get_password_hash("Password123!"),
        is_active=True
    )
    for r_enum in role_enums:
        role = RoleRepository.get_by_name(db, r_enum.value)
        if not role:
            role = RoleRepository.create(db, name=r_enum.value, is_active=True)
        UserRepository.assign_role(db, user.id, role.id)
    return str(user.id), user


# --------------------------------------------------------------------------
# 1. Super Admin Only Protection Tests
# --------------------------------------------------------------------------

def test_super_admin_access(client):
    """SUPER_ADMIN user receives 200 OK on /admin/rbac-test."""
    login_res = client.post("/api/v1/auth/login", json={
        "identifier": "admin@agrismart.local",
        "password": "SuperAdminPass123!"
    })
    token = login_res.json()["access_token"]

    res = client.get("/api/v1/admin/rbac-test", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["message"] == "Super Admin access granted"


def test_wrong_role_forbidden(client):
    """User with FARMER role receives 403 Forbidden on SUPER_ADMIN endpoint."""
    db = TestingSessionLocal()
    farmer_id_str, _ = create_test_user_with_roles(
        db,
        name="Ramesh Farmer",
        mobile="9876543210",
        email="ramesh@example.com",
        role_enums=[RoleEnum.FARMER]
    )
    db.close()

    # Generate valid access token for Farmer
    farmer_token = create_access_token(user_id=farmer_id_str, roles=["FARMER"])

    res = client.get("/api/v1/admin/rbac-test", headers={"Authorization": f"Bearer {farmer_token}"})
    assert res.status_code == 403
    assert res.json()["detail"] == "You do not have permission to access this resource"


# --------------------------------------------------------------------------
# 2. Authentication vs Authorization Separation Tests
# --------------------------------------------------------------------------

def test_unauthenticated_request(client):
    """Unauthenticated request (no token) returns 401 Unauthorized, not 403."""
    res = client.get("/api/v1/admin/rbac-test")
    assert res.status_code == 401
    assert "missing" in res.json()["detail"].lower() or "credentials" in res.json()["detail"].lower()


def test_invalid_token(client):
    """Invalid token returns 401 Unauthorized, not 403."""
    res = client.get("/api/v1/admin/rbac-test", headers={"Authorization": "Bearer invalid.fake.token"})
    assert res.status_code == 401


def test_expired_token(client):
    """Expired token returns 401 Unauthorized."""
    db = TestingSessionLocal()
    admin = UserRepository.get_by_mobile(db, "9999999999")
    admin_id_str = str(admin.id)
    db.close()

    expired_token = create_access_token(
        user_id=admin_id_str,
        roles=["SUPER_ADMIN"],
        expires_delta=timedelta(minutes=-5)
    )

    res = client.get("/api/v1/admin/rbac-test", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower()


# --------------------------------------------------------------------------
# 3. Multiple Allowed Roles Endpoint Tests
# --------------------------------------------------------------------------

def test_multiple_allowed_roles(client):
    """Endpoint allowing [SUPER_ADMIN, FARMER] permits both, but rejects TRADER, DRIVER, WORKER with 403."""
    db = TestingSessionLocal()
    admin = UserRepository.get_by_mobile(db, "9999999999")
    admin_id_str = str(admin.id)
    farmer_id, _ = create_test_user_with_roles(db, "Farmer 1", "9876540001", "f1@agri.com", [RoleEnum.FARMER])
    trader_id, _ = create_test_user_with_roles(db, "Trader 1", "9876540002", "t1@agri.com", [RoleEnum.TRADER])
    driver_id, _ = create_test_user_with_roles(db, "Driver 1", "9876540003", "d1@agri.com", [RoleEnum.DRIVER])
    worker_id, _ = create_test_user_with_roles(db, "Worker 1", "9876540004", "w1@agri.com", [RoleEnum.WORKER])
    db.close()

    admin_token = create_access_token(admin_id_str, ["SUPER_ADMIN"])
    farmer_token = create_access_token(farmer_id, ["FARMER"])
    trader_token = create_access_token(trader_id, ["TRADER"])
    driver_token = create_access_token(driver_id, ["DRIVER"])
    worker_token = create_access_token(worker_id, ["WORKER"])

    # 1. SUPER_ADMIN -> 200 OK
    res_admin = client.get("/api/v1/rbac/multi-role-test", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    assert res_admin.json()["message"] == "Multi-role access granted"

    # 2. FARMER -> 200 OK
    res_farmer = client.get("/api/v1/rbac/multi-role-test", headers={"Authorization": f"Bearer {farmer_token}"})
    assert res_farmer.status_code == 200
    assert res_farmer.json()["message"] == "Multi-role access granted"

    # 3. TRADER -> 403 Forbidden
    res_trader = client.get("/api/v1/rbac/multi-role-test", headers={"Authorization": f"Bearer {trader_token}"})
    assert res_trader.status_code == 403
    assert res_trader.json()["detail"] == "You do not have permission to access this resource"

    # 4. DRIVER -> 403 Forbidden
    res_driver = client.get("/api/v1/rbac/multi-role-test", headers={"Authorization": f"Bearer {driver_token}"})
    assert res_driver.status_code == 403

    # 5. WORKER -> 403 Forbidden
    res_worker = client.get("/api/v1/rbac/multi-role-test", headers={"Authorization": f"Bearer {worker_token}"})
    assert res_worker.status_code == 403


# --------------------------------------------------------------------------
# 4. Multiple User Roles Tests
# --------------------------------------------------------------------------

def test_multiple_user_roles(client):
    """User possessing multiple roles (FARMER + TRADER) is granted access if ANY role matches."""
    db = TestingSessionLocal()
    multi_id, _ = create_test_user_with_roles(
        db,
        name="Farmer-Trader User",
        mobile="9876540099",
        email="ft@agri.com",
        role_enums=[RoleEnum.FARMER, RoleEnum.TRADER]
    )
    db.close()

    token = create_access_token(multi_id, ["FARMER", "TRADER"])

    # Matches FARMER on multi-role endpoint -> 200 OK
    res = client.get("/api/v1/rbac/multi-role-test", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["message"] == "Multi-role access granted"
    assert "FARMER" in res.json()["roles"]
    assert "TRADER" in res.json()["roles"]

    # Fails SUPER_ADMIN only endpoint -> 403 Forbidden
    res_admin = client.get("/api/v1/admin/rbac-test", headers={"Authorization": f"Bearer {token}"})
    assert res_admin.status_code == 403


# --------------------------------------------------------------------------
# 5. Role Revocation Immediate Effect Tests
# --------------------------------------------------------------------------

def test_role_removed_after_login(client):
    """
    CRITICAL: When a role is removed from the database after a JWT is issued,
    authorization immediately rejects subsequent requests with 403 Forbidden.
    """
    # 1. Login as Super Admin and get valid access token
    login_res = client.post("/api/v1/auth/login", json={
        "identifier": "admin@agrismart.local",
        "password": "SuperAdminPass123!"
    })
    token = login_res.json()["access_token"]

    # Verify initial access is granted
    res1 = client.get("/api/v1/admin/rbac-test", headers={"Authorization": f"Bearer {token}"})
    assert res1.status_code == 200

    # 2. Remove SUPER_ADMIN role assignment from database
    db = TestingSessionLocal()
    admin_user = UserRepository.get_by_mobile(db, "9999999999")
    admin_user_id = admin_user.id
    admin_role = RoleRepository.get_by_name(db, RoleEnum.SUPER_ADMIN.value)
    admin_role_id = admin_role.id
    removed = UserRepository.remove_role(db, admin_user_id, admin_role_id)
    assert removed is True
    db.close()

    # 3. Request with the EXACT SAME valid, unexpired JWT -> must return 403 Forbidden!
    res2 = client.get("/api/v1/admin/rbac-test", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 403
    assert res2.json()["detail"] == "You do not have permission to access this resource"

    # 4. Re-assign role in database -> must return 200 OK with the same token!
    db = TestingSessionLocal()
    UserRepository.assign_role(db, admin_user_id, admin_role_id)
    db.close()

    res3 = client.get("/api/v1/admin/rbac-test", headers={"Authorization": f"Bearer {token}"})
    assert res3.status_code == 200


# --------------------------------------------------------------------------
# 6. User Status Validation in RBAC Tests
# --------------------------------------------------------------------------

def test_inactive_user_rejected(client):
    """Inactive user is rejected with 401 before RBAC evaluation."""
    db = TestingSessionLocal()
    user_id, user = create_test_user_with_roles(
        db,
        name="Inactive Admin",
        mobile="9876541111",
        email="inactadmin@agri.com",
        role_enums=[RoleEnum.SUPER_ADMIN]
    )
    user.is_active = False
    db.commit()
    token = create_access_token(user_id, ["SUPER_ADMIN"])
    db.close()

    res = client.get("/api/v1/admin/rbac-test", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401


def test_deleted_user_rejected(client):
    """Soft-deleted user is rejected with 401 before RBAC evaluation."""
    db = TestingSessionLocal()
    user_id, user = create_test_user_with_roles(
        db,
        name="Deleted Admin",
        mobile="9876542222",
        email="deladmin@agri.com",
        role_enums=[RoleEnum.SUPER_ADMIN]
    )
    user.is_deleted = True
    user.deleted_at = datetime.datetime.now(timezone.utc)
    db.commit()
    token = create_access_token(user_id, ["SUPER_ADMIN"])
    db.close()

    res = client.get("/api/v1/admin/rbac-test", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401


# --------------------------------------------------------------------------
# 7. Helper / Alias Tests
# --------------------------------------------------------------------------

def test_require_role_alias(client):
    """Verify require_role works as a single-role alias."""
    temp_router = APIRouter(prefix="/test-alias")

    @temp_router.get("/driver-only")
    def driver_endpoint(user: User = Depends(require_role(RoleEnum.DRIVER))):
        return {"driver": True}

    app.include_router(temp_router)

    db = TestingSessionLocal()
    driver_id, _ = create_test_user_with_roles(db, "Test Driver", "9876543333", "driver@agri.com", [RoleEnum.DRIVER])
    admin = UserRepository.get_by_mobile(db, "9999999999")
    admin_id_str = str(admin.id)
    db.close()

    driver_token = create_access_token(driver_id, ["DRIVER"])
    admin_token = create_access_token(admin_id_str, ["SUPER_ADMIN"])

    # Driver succeeds -> 200
    res_driver = client.get("/test-alias/driver-only", headers={"Authorization": f"Bearer {driver_token}"})
    assert res_driver.status_code == 200
    assert res_driver.json()["driver"] is True

    # Admin fails (not in allowed list) -> 403
    res_admin = client.get("/test-alias/driver-only", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 403
