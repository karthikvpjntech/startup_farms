import uuid
import datetime
from datetime import date, timezone
import pytest
from fastapi.testclient import TestClient

from app.core.jwt import create_access_token
from app.core.security import get_password_hash
from app.models.enums import RoleEnum
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.repositories.farmer_profile_repository import FarmerProfileRepository
from tests.conftest import TestingSessionLocal


def create_test_user_with_roles(db, full_name: str, mobile: str, email: str, role_enums: list[RoleEnum]) -> tuple[str, User]:
    """Helper to create user with roles and return (user_id_str, user)."""
    roles = [RoleRepository.get_by_name(db, r.value) for r in role_enums]
    roles = [r for r in roles if r is not None]
    user = UserRepository.create_with_roles(
        db=db,
        full_name=full_name,
        mobile_number=mobile,
        password_hash=get_password_hash("Password123!"),
        email=email,
        roles=roles,
        is_active=True
    )
    return str(user.id), user


# ==============================================================================
# 1. Authentication & Role Authorization Tests
# ==============================================================================

def test_unauthenticated_profile_access(client: TestClient):
    """Calling any profile endpoint without token returns 401 Unauthorized."""
    for path in ["/api/v1/farmers/profile", "/api/v1/traders/profile", "/api/v1/drivers/profile", "/api/v1/workers/profile"]:
        assert client.get(path).status_code == 401
        assert client.post(path, json={}).status_code == 401
        assert client.patch(path, json={}).status_code == 401


def test_cross_role_access_forbidden(client: TestClient):
    """User with one role cannot access other role-specific profile endpoints."""
    db = TestingSessionLocal()
    farmer_id, _ = create_test_user_with_roles(db, "Only Farmer", "9876100001", "farmer_only@agri.local", [RoleEnum.FARMER])
    trader_id, _ = create_test_user_with_roles(db, "Only Trader", "9876100002", "trader_only@agri.local", [RoleEnum.TRADER])
    driver_id, _ = create_test_user_with_roles(db, "Only Driver", "9876100003", "driver_only@agri.local", [RoleEnum.DRIVER])
    worker_id, _ = create_test_user_with_roles(db, "Only Worker", "9876100004", "worker_only@agri.local", [RoleEnum.WORKER])
    admin_user = UserRepository.get_by_mobile(db, "9999999999")
    admin_id = str(admin_user.id)
    db.close()

    farmer_token = create_access_token(farmer_id, ["FARMER"])
    trader_token = create_access_token(trader_id, ["TRADER"])
    driver_token = create_access_token(driver_id, ["DRIVER"])
    worker_token = create_access_token(worker_id, ["WORKER"])
    admin_token = create_access_token(admin_id, ["SUPER_ADMIN"])

    # 1. Farmer attempting Trader profile -> 403
    res1 = client.get("/api/v1/traders/profile", headers={"Authorization": f"Bearer {farmer_token}"})
    assert res1.status_code == 403

    # 2. Trader attempting Driver profile -> 403
    res2 = client.get("/api/v1/drivers/profile", headers={"Authorization": f"Bearer {trader_token}"})
    assert res2.status_code == 403

    # 3. Driver attempting Worker profile -> 403
    res3 = client.get("/api/v1/workers/profile", headers={"Authorization": f"Bearer {driver_token}"})
    assert res3.status_code == 403

    # 4. Worker attempting Farmer profile -> 403
    res4 = client.get("/api/v1/farmers/profile", headers={"Authorization": f"Bearer {worker_token}"})
    assert res4.status_code == 403

    # 5. Super Admin attempting Farmer profile (without holding FARMER role) -> 403
    res5 = client.get("/api/v1/farmers/profile", headers={"Authorization": f"Bearer {admin_token}"})
    assert res5.status_code == 403


# ==============================================================================
# 2. Farmer Profile CRUD Tests
# ==============================================================================

def test_farmer_profile_lifecycle(client: TestClient):
    """Full lifecycle: 404 on initial GET -> POST -> GET -> PATCH -> Duplicate 409."""
    db = TestingSessionLocal()
    farmer_id, _ = create_test_user_with_roles(db, "Farmer Life", "9876100010", "farmer_life@agri.local", [RoleEnum.FARMER])
    db.close()

    token = create_access_token(farmer_id, ["FARMER"])
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET before creation -> 404
    res_init = client.get("/api/v1/farmers/profile", headers=headers)
    assert res_init.status_code == 404
    assert res_init.json()["detail"] == "Profile not found"

    # 2. POST create profile -> 201
    payload = {
        "profile_image_url": "https://storage.example.com/avatar1.jpg",
        "address_line1": "Green Field Road 10",
        "address_line2": "Near Canal",
        "village": "Tiruchengode Village",
        "district": "Namakkal",
        "state": "Tamil Nadu",
        "pincode": "637211"
    }
    res_create = client.post("/api/v1/farmers/profile", headers=headers, json=payload)
    assert res_create.status_code == 201
    data = res_create.json()
    assert data["user_id"] == farmer_id
    assert data["village"] == "Tiruchengode Village"
    assert data["district"] == "Namakkal"
    assert "password" not in data
    assert "password_hash" not in data

    # 3. GET after creation -> 200
    res_get = client.get("/api/v1/farmers/profile", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["village"] == "Tiruchengode Village"
    assert res_get.json()["pincode"] == "637211"

    # 4. PATCH update profile -> 200
    res_patch = client.patch("/api/v1/farmers/profile", headers=headers, json={
        "village": "Updated Green Village",
        "pincode": "637212"
    })
    assert res_patch.status_code == 200
    assert res_patch.json()["village"] == "Updated Green Village"
    assert res_patch.json()["pincode"] == "637212"
    assert res_patch.json()["district"] == "Namakkal"  # Preserved

    # 5. Duplicate POST -> 409
    res_dup = client.post("/api/v1/farmers/profile", headers=headers, json=payload)
    assert res_dup.status_code == 409
    assert res_dup.json()["detail"] == "Profile already exists"


# ==============================================================================
# 3. Trader Profile CRUD Tests
# ==============================================================================

def test_trader_profile_lifecycle(client: TestClient):
    """Trader profile: 404 -> POST -> GET -> PATCH -> 409 on duplicate."""
    db = TestingSessionLocal()
    trader_id, _ = create_test_user_with_roles(db, "Trader Life", "9876100020", "trader_life@agri.local", [RoleEnum.TRADER])
    db.close()

    token = create_access_token(trader_id, ["TRADER"])
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET -> 404
    assert client.get("/api/v1/traders/profile", headers=headers).status_code == 404

    # 2. POST -> 201
    payload = {
        "business_name": "Kongu Agro Traders",
        "business_registration_number": "GSTIN33ABCDE1234F1Z5",
        "address_line1": "Mandi Shop #14",
        "district": "Salem",
        "state": "Tamil Nadu",
        "pincode": "636001"
    }
    res_create = client.post("/api/v1/traders/profile", headers=headers, json=payload)
    assert res_create.status_code == 201
    assert res_create.json()["business_name"] == "Kongu Agro Traders"

    # 3. GET -> 200
    res_get = client.get("/api/v1/traders/profile", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["business_registration_number"] == "GSTIN33ABCDE1234F1Z5"

    # 4. PATCH -> 200
    res_patch = client.patch("/api/v1/traders/profile", headers=headers, json={
        "business_name": "Kongu Agro Enterprises"
    })
    assert res_patch.status_code == 200
    assert res_patch.json()["business_name"] == "Kongu Agro Enterprises"

    # 5. Duplicate POST -> 409
    assert client.post("/api/v1/traders/profile", headers=headers, json=payload).status_code == 409


# ==============================================================================
# 4. Driver Profile CRUD Tests
# ==============================================================================

def test_driver_profile_lifecycle(client: TestClient):
    """Driver profile: 404 -> POST -> GET -> PATCH -> 409 on duplicate."""
    db = TestingSessionLocal()
    driver_id, _ = create_test_user_with_roles(db, "Driver Life", "9876100030", "driver_life@agri.local", [RoleEnum.DRIVER])
    db.close()

    token = create_access_token(driver_id, ["DRIVER"])
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET -> 404
    assert client.get("/api/v1/drivers/profile", headers=headers).status_code == 404

    # 2. POST -> 201
    payload = {
        "license_number": "TN28-20210001234",
        "license_expiry_date": "2031-12-31",
        "address_line1": "45 Lorry Stand Road",
        "district": "Erode",
        "state": "Tamil Nadu",
        "pincode": "638001"
    }
    res_create = client.post("/api/v1/drivers/profile", headers=headers, json=payload)
    assert res_create.status_code == 201
    assert res_create.json()["license_number"] == "TN28-20210001234"
    assert res_create.json()["license_expiry_date"] == "2031-12-31"

    # 3. GET -> 200
    res_get = client.get("/api/v1/drivers/profile", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["license_number"] == "TN28-20210001234"

    # 4. PATCH -> 200
    res_patch = client.patch("/api/v1/drivers/profile", headers=headers, json={
        "district": "Coimbatore"
    })
    assert res_patch.status_code == 200
    assert res_patch.json()["district"] == "Coimbatore"

    # 5. Duplicate POST -> 409
    assert client.post("/api/v1/drivers/profile", headers=headers, json=payload).status_code == 409


# ==============================================================================
# 5. Worker Profile CRUD Tests
# ==============================================================================

def test_worker_profile_lifecycle(client: TestClient):
    """Worker profile: 404 -> POST -> GET -> PATCH -> 409 on duplicate."""
    db = TestingSessionLocal()
    worker_id, _ = create_test_user_with_roles(db, "Worker Life", "9876100040", "worker_life@agri.local", [RoleEnum.WORKER])
    db.close()

    token = create_access_token(worker_id, ["WORKER"])
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET -> 404
    assert client.get("/api/v1/workers/profile", headers=headers).status_code == 404

    # 2. POST -> 201
    payload = {
        "address_line1": "Colony Main Street",
        "district": "Dharmapuri",
        "state": "Tamil Nadu",
        "pincode": "636701"
    }
    res_create = client.post("/api/v1/workers/profile", headers=headers, json=payload)
    assert res_create.status_code == 201
    assert res_create.json()["district"] == "Dharmapuri"

    # 3. GET -> 200
    res_get = client.get("/api/v1/workers/profile", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["pincode"] == "636701"

    # 4. PATCH -> 200
    res_patch = client.patch("/api/v1/workers/profile", headers=headers, json={
        "state": "Kerala"
    })
    assert res_patch.status_code == 200
    assert res_patch.json()["state"] == "Kerala"

    # 5. Duplicate POST -> 409
    assert client.post("/api/v1/workers/profile", headers=headers, json=payload).status_code == 409


# ==============================================================================
# 6. Multi-Role Profiles Independence Tests
# ==============================================================================

def test_multi_role_user_profiles_independence(client: TestClient):
    """A user with multiple roles can maintain independent role profiles."""
    db = TestingSessionLocal()
    multi_id, _ = create_test_user_with_roles(
        db,
        "Farmer Trader Person",
        "9876100050",
        "multi_profile@agri.local",
        [RoleEnum.FARMER, RoleEnum.TRADER]
    )
    db.close()

    token = create_access_token(multi_id, ["FARMER", "TRADER"])
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Farmer Profile
    res_f = client.post("/api/v1/farmers/profile", headers=headers, json={
        "village": "Farmer Village",
        "district": "Namakkal"
    })
    assert res_f.status_code == 201

    # 2. Create Trader Profile
    res_t = client.post("/api/v1/traders/profile", headers=headers, json={
        "business_name": "Multi Agro Trading",
        "district": "Salem"
    })
    assert res_t.status_code == 201

    # 3. Retrieve both independently
    get_f = client.get("/api/v1/farmers/profile", headers=headers)
    assert get_f.status_code == 200
    assert get_f.json()["village"] == "Farmer Village"

    get_t = client.get("/api/v1/traders/profile", headers=headers)
    assert get_t.status_code == 200
    assert get_t.json()["business_name"] == "Multi Agro Trading"


# ==============================================================================
# 7. Role Removal Effect & Profile Data Preservation
# ==============================================================================

def test_role_removal_blocks_api_preserves_profile_data(client: TestClient):
    """When a role is removed, API access is rejected (403), but profile data remains in database."""
    db = TestingSessionLocal()
    farmer_id, user = create_test_user_with_roles(db, "Revoke Farmer", "9876100060", "revoke_farmer@agri.local", [RoleEnum.FARMER])
    user_uuid = user.id
    farmer_role = RoleRepository.get_by_name(db, RoleEnum.FARMER.value)
    farmer_role_id = farmer_role.id
    db.close()

    token = create_access_token(farmer_id, ["FARMER"])
    headers = {"Authorization": f"Bearer {token}"}

    # Create profile
    res_create = client.post("/api/v1/farmers/profile", headers=headers, json={
        "village": "Preserved Village",
        "district": "Namakkal"
    })
    assert res_create.status_code == 201

    # Admin removes FARMER role from database
    db = TestingSessionLocal()
    UserRepository.remove_role(db, user_uuid, farmer_role_id)
    db.close()

    # Same access token immediately gets 403 on /farmers/profile
    res_blocked = client.get("/api/v1/farmers/profile", headers=headers)
    assert res_blocked.status_code == 403

    # Verify profile record still physically exists in database!
    db = TestingSessionLocal()
    profile_in_db = FarmerProfileRepository.get_by_user_id(db, user_uuid)
    assert profile_in_db is not None
    assert profile_in_db.village == "Preserved Village"
    db.close()

    # Admin re-assigns FARMER role
    db = TestingSessionLocal()
    UserRepository.assign_role(db, user_uuid, farmer_role_id)
    db.close()

    # Access is immediately restored and returns the preserved profile
    res_restored = client.get("/api/v1/farmers/profile", headers=headers)
    assert res_restored.status_code == 200
    assert res_restored.json()["village"] == "Preserved Village"


# ==============================================================================
# 8. Inactive and Soft-Deleted User Protection Tests
# ==============================================================================

def test_inactive_and_deleted_user_cannot_access_profile(client: TestClient):
    """Inactive or soft-deleted users receive 401 Unauthorized on profile endpoints."""
    db = TestingSessionLocal()
    user_id, user = create_test_user_with_roles(db, "Inactive Worker", "9876100070", "inact_worker@agri.local", [RoleEnum.WORKER])
    token = create_access_token(user_id, ["WORKER"])
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Inactive user -> 401
    user.is_active = False
    db.commit()
    db.close()

    assert client.get("/api/v1/workers/profile", headers=headers).status_code == 401

    # 2. Deleted user -> 401
    db = TestingSessionLocal()
    user_db = UserRepository.get_by_id(db, uuid.UUID(user_id), include_deleted=True)
    user_db.is_active = True
    user_db.is_deleted = True
    user_db.deleted_at = datetime.datetime.now(timezone.utc)
    db.commit()
    db.close()

    assert client.get("/api/v1/workers/profile", headers=headers).status_code == 401


# ==============================================================================
# 9. Alembic Migration Upgrade / Downgrade Verification
# ==============================================================================

def test_alembic_migrations_upgrade_and_downgrade():
    """Verify that Alembic migrations including 0003 upgrade and downgrade smoothly."""
    import os
    import tempfile
    from alembic.config import Config
    from alembic import command

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_db_path = tmp.name
    
    try:
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{tmp_db_path}")
        # Upgrade to latest revision (0003_role_profiles)
        command.upgrade(alembic_cfg, "head")
        # Downgrade 1 revision back to 0002_refresh_tokens
        command.downgrade(alembic_cfg, "-1")
        # Upgrade back to head
        command.upgrade(alembic_cfg, "head")
    finally:
        if os.path.exists(tmp_db_path):
            try:
                os.remove(tmp_db_path)
            except Exception:
                pass
