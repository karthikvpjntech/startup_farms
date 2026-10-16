import uuid
import datetime
from datetime import timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.core.jwt import create_access_token
from app.core.security import get_password_hash
from app.models.enums import RoleEnum, OwnershipTypeEnum, LandAreaUnitEnum
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.repositories.farmer_profile_repository import FarmerProfileRepository
from app.repositories.farm_repository import FarmRepository
from tests.conftest import TestingSessionLocal


def create_test_user_with_roles(db, full_name: str, mobile: str, email: str, role_enums: list[RoleEnum]) -> tuple[str, User]:
    """Helper to create user with assigned roles and return (user_id_str, user)."""
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


def create_test_farmer_with_profile(db, full_name: str, mobile: str, email: str) -> tuple[str, str]:
    """Helper to create a farmer with an active FarmerProfile and return (user_id_str, token)."""
    user_id_str, user = create_test_user_with_roles(db, full_name, mobile, email, [RoleEnum.FARMER])
    FarmerProfileRepository.create(
        db=db,
        user_id=user.id,
        profile_data={
            "address_line1": "123 Field Lane",
            "village": "Green Village",
            "district": "Namakkal",
            "state": "Tamil Nadu",
            "pincode": "637001"
        }
    )
    token = create_access_token(user_id_str, ["FARMER"])
    return user_id_str, token


# ==============================================================================
# 1. Authentication & Role Authorization Tests
# ==============================================================================

def test_unauthenticated_farm_access(client: TestClient):
    """Calling any farm endpoint without token returns 401 Unauthorized."""
    random_id = str(uuid.uuid4())
    assert client.get("/api/v1/farms").status_code == 401
    assert client.post("/api/v1/farms", json={}).status_code == 401
    assert client.get(f"/api/v1/farms/{random_id}").status_code == 401
    assert client.patch(f"/api/v1/farms/{random_id}", json={}).status_code == 401
    assert client.patch(f"/api/v1/farms/{random_id}/status", json={"is_active": True}).status_code == 401
    assert client.delete(f"/api/v1/farms/{random_id}").status_code == 401
    assert client.post(f"/api/v1/farms/{random_id}/restore").status_code == 401


def test_forbidden_roles_access(client: TestClient):
    """TRADER, DRIVER, WORKER, and SUPER_ADMIN (without FARMER role) are rejected with 403."""
    db = TestingSessionLocal()
    trader_id, _ = create_test_user_with_roles(db, "Trader Only", "9800000001", "trader@agri.local", [RoleEnum.TRADER])
    driver_id, _ = create_test_user_with_roles(db, "Driver Only", "9800000002", "driver@agri.local", [RoleEnum.DRIVER])
    worker_id, _ = create_test_user_with_roles(db, "Worker Only", "9800000003", "worker@agri.local", [RoleEnum.WORKER])
    admin_user = UserRepository.get_by_mobile(db, "9999999999")
    admin_id = str(admin_user.id)
    db.close()

    for uid, roles in [(trader_id, ["TRADER"]), (driver_id, ["DRIVER"]), (worker_id, ["WORKER"]), (admin_id, ["SUPER_ADMIN"])]:
        token = create_access_token(uid, roles)
        headers = {"Authorization": f"Bearer {token}"}
        res_list = client.get("/api/v1/farms", headers=headers)
        assert res_list.status_code == 403
        res_create = client.post("/api/v1/farms", headers=headers, json={"farm_name": "Test", "ownership_type": "OWNED", "total_land_area": 2.5, "land_area_unit": "ACRE"})
        assert res_create.status_code == 403


# ==============================================================================
# 2. Farmer Profile Prerequisite Tests
# ==============================================================================

def test_farmer_without_profile_rejected(client: TestClient):
    """User with FARMER role but without completed FarmerProfile receives 409 Conflict."""
    db = TestingSessionLocal()
    user_id_str, _ = create_test_user_with_roles(db, "Incomplete Farmer", "9800000010", "incomp_farmer@agri.local", [RoleEnum.FARMER])
    db.close()

    token = create_access_token(user_id_str, ["FARMER"])
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "farm_name": "Sunrise Valley",
        "ownership_type": "OWNED",
        "total_land_area": 5.0,
        "land_area_unit": "ACRE"
    }
    res_create = client.post("/api/v1/farms", headers=headers, json=payload)
    assert res_create.status_code == 409
    assert res_create.json()["detail"] == "Farmer profile must be completed before managing farms"

    res_list = client.get("/api/v1/farms", headers=headers)
    assert res_list.status_code == 409
    assert res_list.json()["detail"] == "Farmer profile must be completed before managing farms"


# ==============================================================================
# 3. Farm Creation & Auto Code Generation Tests
# ==============================================================================

def test_create_farm_success(client: TestClient):
    """Creating a farm generates unique farm_code, links farmer profile and audit user."""
    db = TestingSessionLocal()
    user_id, token = create_test_farmer_with_profile(db, "Farmer Alpha", "9800000020", "alpha@agri.local")
    farmer_prof = FarmerProfileRepository.get_by_user_id(db, uuid.UUID(user_id))
    expected_profile_id = str(farmer_prof.id)
    db.close()

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "farm_name": "Green Valley Farm",
        "ownership_type": "OWNED",
        "total_land_area": 2.5,
        "land_area_unit": "ACRE",
        "address_line1": "Survey No 45",
        "address_line2": "Behind Canal",
        "village": "Example Village",
        "district": "Namakkal",
        "state": "Tamil Nadu",
        "pincode": "637001",
        "latitude": 11.234567,
        "longitude": 78.167890
    }

    res = client.post("/api/v1/farms", headers=headers, json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["farm_name"] == "Green Valley Farm"
    assert data["farm_code"] == "FARM-000001"
    assert data["farmer_profile_id"] == expected_profile_id
    assert data["ownership_type"] == "OWNED"
    assert float(data["total_land_area"]) == 2.5
    assert data["land_area_unit"] == "ACRE"
    assert data["is_active"] is True
    assert data["is_deleted"] is False
    assert data["created_by"] == user_id
    assert float(data["latitude"]) == 11.234567
    assert float(data["longitude"]) == 78.167890


def test_multiple_farms_creation_and_listing(client: TestClient):
    """A farmer can create and list multiple independent farms."""
    db = TestingSessionLocal()
    user_id, token = create_test_farmer_with_profile(db, "Farmer Beta", "9800000030", "beta@agri.local")
    db.close()

    headers = {"Authorization": f"Bearer {token}"}

    farms_to_create = [
        {"farm_name": "North Field", "ownership_type": "OWNED", "total_land_area": 3.0, "land_area_unit": "ACRE"},
        {"farm_name": "South Orchard", "ownership_type": "LEASED", "total_land_area": 1.5, "land_area_unit": "HECTARE"},
        {"farm_name": "East Meadow", "ownership_type": "MANAGED", "total_land_area": 10000.0, "land_area_unit": "SQUARE_METER"},
    ]

    created_codes = []
    for f in farms_to_create:
        res = client.post("/api/v1/farms", headers=headers, json=f)
        assert res.status_code == 201
        created_codes.append(res.json()["farm_code"])

    assert created_codes == ["FARM-000001", "FARM-000002", "FARM-000003"]

    # List farms
    res_list = client.get("/api/v1/farms", headers=headers)
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert list_data["total"] == 3
    assert len(list_data["items"]) == 3
    assert list_data["page"] == 1
    assert list_data["total_pages"] == 1


# ==============================================================================
# 4. Ownership Isolation Tests
# ==============================================================================

def test_ownership_isolation(client: TestClient):
    """Farmer A cannot read, update, delete, or restore Farmer B's farm (returns 404)."""
    db = TestingSessionLocal()
    farmer_a_id, token_a = create_test_farmer_with_profile(db, "Farmer A", "9800000041", "farmer_a@agri.local")
    farmer_b_id, token_b = create_test_farmer_with_profile(db, "Farmer B", "9800000042", "farmer_b@agri.local")
    db.close()

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Farmer B creates Farm B
    res_b = client.post("/api/v1/farms", headers=headers_b, json={
        "farm_name": "Farmer B Secret Farm",
        "ownership_type": "OWNED",
        "total_land_area": 4.0,
        "land_area_unit": "ACRE"
    })
    assert res_b.status_code == 201
    farm_b_id = res_b.json()["id"]

    # Farmer A tries to access Farm B -> 404
    assert client.get(f"/api/v1/farms/{farm_b_id}", headers=headers_a).status_code == 404
    assert client.patch(f"/api/v1/farms/{farm_b_id}", headers=headers_a, json={"farm_name": "Hacked"}).status_code == 404
    assert client.patch(f"/api/v1/farms/{farm_b_id}/status", headers=headers_a, json={"is_active": False}).status_code == 404
    assert client.delete(f"/api/v1/farms/{farm_b_id}", headers=headers_a).status_code == 404
    assert client.post(f"/api/v1/farms/{farm_b_id}/restore", headers=headers_a).status_code == 404

    # Farmer A listing farms sees 0 farms
    list_a = client.get("/api/v1/farms", headers=headers_a)
    assert list_a.status_code == 200
    assert list_a.json()["total"] == 0


# ==============================================================================
# 5. Duplicate Farm Name Rules
# ==============================================================================

def test_duplicate_farm_name_same_farmer_rejected(client: TestClient):
    """Same farmer creating two active farms with identical names is rejected with 409."""
    db = TestingSessionLocal()
    _, token = create_test_farmer_with_profile(db, "Farmer Dup", "9800000050", "dup@agri.local")
    db.close()

    headers = {"Authorization": f"Bearer {token}"}
    payload = {"farm_name": "Kongu Farm", "ownership_type": "OWNED", "total_land_area": 2.0, "land_area_unit": "ACRE"}

    res1 = client.post("/api/v1/farms", headers=headers, json=payload)
    assert res1.status_code == 201

    # Duplicate name attempt
    res2 = client.post("/api/v1/farms", headers=headers, json={"farm_name": "  kongu farm  ", "ownership_type": "LEASED", "total_land_area": 1.0, "land_area_unit": "ACRE"})
    assert res2.status_code == 409
    assert res2.json()["detail"] == "A farm with this name already exists for your profile"


def test_duplicate_farm_name_different_farmers_allowed(client: TestClient):
    """Two different farmers can have farms with the same name."""
    db = TestingSessionLocal()
    _, token1 = create_test_farmer_with_profile(db, "Farmer 1", "9800000051", "f1@agri.local")
    _, token2 = create_test_farmer_with_profile(db, "Farmer 2", "9800000052", "f2@agri.local")
    db.close()

    h1 = {"Authorization": f"Bearer {token1}"}
    h2 = {"Authorization": f"Bearer {token2}"}

    payload = {"farm_name": "Green Farm", "ownership_type": "OWNED", "total_land_area": 2.0, "land_area_unit": "ACRE"}
    res1 = client.post("/api/v1/farms", headers=h1, json=payload)
    res2 = client.post("/api/v1/farms", headers=h2, json=payload)

    assert res1.status_code == 201
    assert res2.status_code == 201
    assert res1.json()["farm_code"] == "FARM-000001"
    assert res2.json()["farm_code"] == "FARM-000002"


# ==============================================================================
# 6. Farm Partial Update Tests
# ==============================================================================

def test_partial_update_farm(client: TestClient):
    """PATCH partially updates mutable fields without modifying other fields or immutable identifiers."""
    db = TestingSessionLocal()
    user_id, token = create_test_farmer_with_profile(db, "Farmer Update", "9800000060", "update@agri.local")
    db.close()

    headers = {"Authorization": f"Bearer {token}"}
    create_payload = {
        "farm_name": "Original Name",
        "ownership_type": "OWNED",
        "total_land_area": 5.0,
        "land_area_unit": "ACRE",
        "village": "Old Village",
        "district": "Namakkal",
        "latitude": 10.123456,
        "longitude": 77.123456
    }
    res_create = client.post("/api/v1/farms", headers=headers, json=create_payload)
    assert res_create.status_code == 201
    farm_id = res_create.json()["id"]
    orig_code = res_create.json()["farm_code"]

    # 1. Update only total_land_area and village
    res_patch = client.patch(f"/api/v1/farms/{farm_id}", headers=headers, json={
        "total_land_area": 7.5,
        "village": "New Village"
    })
    assert res_patch.status_code == 200
    updated = res_patch.json()
    assert float(updated["total_land_area"]) == 7.5
    assert updated["village"] == "New Village"
    assert updated["farm_name"] == "Original Name"  # Unchanged
    assert updated["district"] == "Namakkal"  # Unchanged
    assert updated["farm_code"] == orig_code  # Immutable
    assert updated["updated_by"] == user_id


# ==============================================================================
# 7. Validation Tests (Land Area & Coordinates)
# ==============================================================================

def test_validation_rules(client: TestClient):
    """Validation rules reject zero/negative land area, invalid units, and out-of-range coordinates."""
    db = TestingSessionLocal()
    _, token = create_test_farmer_with_profile(db, "Farmer Valid", "9800000070", "valid@agri.local")
    db.close()

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Zero land area -> 422
    assert client.post("/api/v1/farms", headers=headers, json={"farm_name": "Zero Area", "ownership_type": "OWNED", "total_land_area": 0, "land_area_unit": "ACRE"}).status_code == 422

    # 2. Negative land area -> 422
    assert client.post("/api/v1/farms", headers=headers, json={"farm_name": "Negative Area", "ownership_type": "OWNED", "total_land_area": -2.5, "land_area_unit": "ACRE"}).status_code == 422

    # 3. Invalid land unit -> 422
    assert client.post("/api/v1/farms", headers=headers, json={"farm_name": "Invalid Unit", "ownership_type": "OWNED", "total_land_area": 2.5, "land_area_unit": "KILOGRAM"}).status_code == 422

    # 4. Latitude > 90 -> 422
    assert client.post("/api/v1/farms", headers=headers, json={"farm_name": "Bad Lat", "ownership_type": "OWNED", "total_land_area": 2.5, "land_area_unit": "ACRE", "latitude": 95.0}).status_code == 422

    # 5. Latitude < -90 -> 422
    assert client.post("/api/v1/farms", headers=headers, json={"farm_name": "Bad Lat Neg", "ownership_type": "OWNED", "total_land_area": 2.5, "land_area_unit": "ACRE", "latitude": -95.0}).status_code == 422

    # 6. Longitude > 180 -> 422
    assert client.post("/api/v1/farms", headers=headers, json={"farm_name": "Bad Lon", "ownership_type": "OWNED", "total_land_area": 2.5, "land_area_unit": "ACRE", "longitude": 185.0}).status_code == 422

    # 7. Longitude < -180 -> 422
    assert client.post("/api/v1/farms", headers=headers, json={"farm_name": "Bad Lon Neg", "ownership_type": "OWNED", "total_land_area": 2.5, "land_area_unit": "ACRE", "longitude": -185.0}).status_code == 422


# ==============================================================================
# 8. Status Management & Soft Delete / Restore Tests
# ==============================================================================

def test_farm_status_toggle(client: TestClient):
    """Toggling is_active works, but is rejected on deleted farms."""
    db = TestingSessionLocal()
    _, token = create_test_farmer_with_profile(db, "Farmer Status", "9800000080", "status@agri.local")
    db.close()

    headers = {"Authorization": f"Bearer {token}"}
    res_create = client.post("/api/v1/farms", headers=headers, json={"farm_name": "Toggle Farm", "ownership_type": "OWNED", "total_land_area": 2.0, "land_area_unit": "ACRE"})
    farm_id = res_create.json()["id"]

    # Deactivate
    res_deact = client.patch(f"/api/v1/farms/{farm_id}/status", headers=headers, json={"is_active": False})
    assert res_deact.status_code == 200
    assert res_deact.json()["is_active"] is False

    # Reactivate
    res_act = client.patch(f"/api/v1/farms/{farm_id}/status", headers=headers, json={"is_active": True})
    assert res_act.status_code == 200
    assert res_act.json()["is_active"] is True


def test_soft_delete_and_restore_lifecycle(client: TestClient):
    """Soft delete hides farm from list and direct GET. Restore brings it back without altering is_active."""
    db = TestingSessionLocal()
    user_id, token = create_test_farmer_with_profile(db, "Farmer Delete", "9800000090", "del@agri.local")
    db.close()

    headers = {"Authorization": f"Bearer {token}"}
    res_create = client.post("/api/v1/farms", headers=headers, json={"farm_name": "Lifecycle Farm", "ownership_type": "OWNED", "total_land_area": 4.0, "land_area_unit": "ACRE"})
    farm_id = res_create.json()["id"]

    # Deactivate farm first
    client.patch(f"/api/v1/farms/{farm_id}/status", headers=headers, json={"is_active": False})

    # 1. Soft delete
    res_del = client.delete(f"/api/v1/farms/{farm_id}", headers=headers)
    assert res_del.status_code == 200
    del_data = res_del.json()
    assert del_data["is_deleted"] is True
    assert del_data["deleted_by"] == user_id
    assert del_data["deleted_at"] is not None

    # 2. Normal listing does not include deleted farm
    res_list = client.get("/api/v1/farms", headers=headers)
    assert res_list.status_code == 200
    assert res_list.json()["total"] == 0

    # 3. Direct GET returns 404
    assert client.get(f"/api/v1/farms/{farm_id}", headers=headers).status_code == 404

    # 4. Status update on deleted farm returns 400
    res_status = client.patch(f"/api/v1/farms/{farm_id}/status", headers=headers, json={"is_active": True})
    assert res_status.status_code == 400

    # 5. Restore farm
    res_restore = client.post(f"/api/v1/farms/{farm_id}/restore", headers=headers)
    assert res_restore.status_code == 200
    restored = res_restore.json()
    assert restored["is_deleted"] is False
    assert restored["deleted_at"] is None
    assert restored["deleted_by"] is None
    assert restored["is_active"] is False  # Restoring does NOT reset is_active to True!

    # 6. Farm is visible again
    res_get = client.get(f"/api/v1/farms/{farm_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["farm_name"] == "Lifecycle Farm"


# ==============================================================================
# 9. Role Removal & Reassignment Tests
# ==============================================================================

def test_role_removal_blocks_farms_preserves_data(client: TestClient):
    """Removing FARMER role immediately causes 403 on /farms; re-assigning restores access."""
    db = TestingSessionLocal()
    user_id_str, user = create_test_user_with_roles(db, "Revoke Farmer", "9800000100", "revoke_farm@agri.local", [RoleEnum.FARMER])
    user_uuid = user.id
    FarmerProfileRepository.create(
        db=db,
        user_id=user_uuid,
        profile_data={"village": "Test Village", "district": "Salem"}
    )
    farmer_role = RoleRepository.get_by_name(db, RoleEnum.FARMER.value)
    farmer_role_id = farmer_role.id
    db.close()

    token = create_access_token(user_id_str, ["FARMER"])
    headers = {"Authorization": f"Bearer {token}"}

    # Create farm
    res_create = client.post("/api/v1/farms", headers=headers, json={"farm_name": "Surviving Farm", "ownership_type": "OWNED", "total_land_area": 3.0, "land_area_unit": "ACRE"})
    assert res_create.status_code == 201
    farm_id = res_create.json()["id"]

    # Revoke FARMER role
    db = TestingSessionLocal()
    UserRepository.remove_role(db, user_uuid, farmer_role_id)
    db.close()

    # Immediate 403 on /farms endpoints
    assert client.get("/api/v1/farms", headers=headers).status_code == 403
    assert client.get(f"/api/v1/farms/{farm_id}", headers=headers).status_code == 403

    # Farm physically exists in DB
    db = TestingSessionLocal()
    farm_db = FarmRepository.get_by_id(db, uuid.UUID(farm_id))
    assert farm_db is not None
    assert farm_db.farm_name == "Surviving Farm"

    # Re-assign FARMER role
    UserRepository.assign_role(db, user_uuid, farmer_role_id)
    db.close()

    # Access is restored
    res_restored = client.get(f"/api/v1/farms/{farm_id}", headers=headers)
    assert res_restored.status_code == 200
    assert res_restored.json()["farm_name"] == "Surviving Farm"


# ==============================================================================
# 10. Farm Code Non-Reuse & Invariance Tests
# ==============================================================================

def test_farm_code_invariance_and_non_reuse(client: TestClient):
    """Farm code cannot be modified and deleted farm codes are never reused."""
    db = TestingSessionLocal()
    _, token = create_test_farmer_with_profile(db, "Farmer Code", "9800000110", "code@agri.local")
    db.close()

    headers = {"Authorization": f"Bearer {token}"}

    # Create Farm 1 (FARM-000001)
    res1 = client.post("/api/v1/farms", headers=headers, json={"farm_name": "Farm One", "ownership_type": "OWNED", "total_land_area": 2.0, "land_area_unit": "ACRE"})
    assert res1.json()["farm_code"] == "FARM-000001"
    farm1_id = res1.json()["id"]

    # Delete Farm 1
    client.delete(f"/api/v1/farms/{farm1_id}", headers=headers)

    # Create Farm 2 -> must receive FARM-000002, NOT FARM-000001!
    res2 = client.post("/api/v1/farms", headers=headers, json={"farm_name": "Farm Two", "ownership_type": "OWNED", "total_land_area": 2.0, "land_area_unit": "ACRE"})
    assert res2.json()["farm_code"] == "FARM-000002"


# ==============================================================================
# 11. Alembic Migration Upgrade / Downgrade Lifecycle Test
# ==============================================================================

def test_alembic_migrations_upgrade_and_downgrade_0004():
    """Verify that Alembic migrations including 0004 upgrade and downgrade smoothly."""
    import os
    import tempfile
    from alembic.config import Config
    from alembic import command

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_db_path = tmp.name

    try:
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{tmp_db_path}")
        # Upgrade to latest revision (0004_farms)
        command.upgrade(alembic_cfg, "head")
        # Downgrade 1 revision back to 0003_role_profiles
        command.downgrade(alembic_cfg, "-1")
        # Upgrade back to head
        command.upgrade(alembic_cfg, "head")
    finally:
        if os.path.exists(tmp_db_path):
            try:
                os.remove(tmp_db_path)
            except Exception:
                pass
