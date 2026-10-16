import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.core.jwt import create_access_token
from app.core.security import get_password_hash
from app.models.enums import RoleEnum, CropCategoryEnum, CropSeasonEnum, LandAreaUnitEnum, OwnershipTypeEnum
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.repositories.farmer_profile_repository import FarmerProfileRepository
from app.repositories.farm_repository import FarmRepository
from app.repositories.crop_repository import CropRepository
from app.repositories.farm_crop_plan_repository import FarmCropPlanRepository
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


def setup_farmer_with_farm(db, full_name: str, mobile: str, email: str, farm_name: str = "Test Farm", area: float = 5.0, unit: str = "ACRE") -> tuple[str, str, str, str]:
    """Helper returning (user_id_str, token, farmer_profile_id_str, farm_id_str)."""
    user_id_str, user = create_test_user_with_roles(db, full_name, mobile, email, [RoleEnum.FARMER])
    profile = FarmerProfileRepository.create(
        db=db,
        user_id=user.id,
        profile_data={"village": "Green Village", "district": "Namakkal"}
    )
    farm = FarmRepository.create(
        db=db,
        farmer_profile_id=profile.id,
        farm_code=FarmRepository.generate_next_farm_code(db),
        farm_data={
            "farm_name": farm_name,
            "ownership_type": "OWNED",
            "total_land_area": Decimal(str(area)),
            "land_area_unit": unit,
        },
        created_by=user.id
    )
    token = create_access_token(user_id_str, ["FARMER"])
    return user_id_str, token, str(profile.id), str(farm.id)


def create_test_crop(db, name: str, category: str = "CEREAL", is_active: bool = True) -> tuple[str, str]:
    """Helper creating crop and returning (crop_id_str, crop_code)."""
    crop = CropRepository.create(
        db=db,
        crop_code=CropRepository.generate_next_crop_code(db),
        crop_data={"crop_name": name, "crop_category": category}
    )
    if not is_active:
        CropRepository.update_status(db, crop, is_active=False)
    return str(crop.id), crop.crop_code


# ==============================================================================
# 1. Authentication & Role Authorization Tests
# ==============================================================================

def test_unauthenticated_farm_crop_plans_access(client: TestClient):
    """Unauthenticated calls to /farm-crop-plans return 401."""
    random_id = str(uuid.uuid4())
    assert client.get("/api/v1/farm-crop-plans").status_code == 401
    assert client.post("/api/v1/farm-crop-plans", json={}).status_code == 401
    assert client.get(f"/api/v1/farm-crop-plans/{random_id}").status_code == 401
    assert client.patch(f"/api/v1/farm-crop-plans/{random_id}", json={}).status_code == 401
    assert client.patch(f"/api/v1/farm-crop-plans/{random_id}/status", json={"is_active": True}).status_code == 401
    assert client.delete(f"/api/v1/farm-crop-plans/{random_id}").status_code == 401
    assert client.post(f"/api/v1/farm-crop-plans/{random_id}/restore").status_code == 401


def test_forbidden_roles_on_farm_crop_plans(client: TestClient):
    """TRADER, DRIVER, WORKER, and SUPER_ADMIN (without FARMER role) get 403 Forbidden."""
    db = TestingSessionLocal()
    trader_id, _ = create_test_user_with_roles(db, "Trader Plan", "9600000001", "trader_p@agri.local", [RoleEnum.TRADER])
    driver_id, _ = create_test_user_with_roles(db, "Driver Plan", "9600000002", "driver_p@agri.local", [RoleEnum.DRIVER])
    admin_user = UserRepository.get_by_mobile(db, "9999999999")
    admin_id = str(admin_user.id)
    db.close()

    for uid, roles in [(trader_id, ["TRADER"]), (driver_id, ["DRIVER"]), (admin_id, ["SUPER_ADMIN"])]:
        token = create_access_token(uid, roles)
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/api/v1/farm-crop-plans", headers=headers).status_code == 403
        assert client.post("/api/v1/farm-crop-plans", headers=headers, json={}).status_code == 403


# ==============================================================================
# 2. Farmer Profile Prerequisite & Farm Ownership Tests
# ==============================================================================

def test_farmer_without_profile_cannot_plan(client: TestClient):
    """Farmer without completed FarmerProfile receives 409 Conflict."""
    db = TestingSessionLocal()
    user_id_str, _ = create_test_user_with_roles(db, "No Prof Farmer", "9600000010", "no_prof_p@agri.local", [RoleEnum.FARMER])
    crop_id, _ = create_test_crop(db, "Rice Crop")
    db.close()

    token = create_access_token(user_id_str, ["FARMER"])
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "farm_id": str(uuid.uuid4()),
        "crop_id": crop_id,
        "season": "KHARIF",
        "planned_start_date": "2026-06-01",
        "planned_area": 2.0,
        "land_area_unit": "ACRE"
    }
    res = client.post("/api/v1/farm-crop-plans", headers=headers, json=payload)
    assert res.status_code == 409
    assert res.json()["detail"] == "Farmer profile must be completed before managing crop plans"


def test_plan_creation_and_ownership_isolation(client: TestClient):
    """Farmer A cannot create, read, update, or delete plans on Farmer B's farm (404 Not Found)."""
    db = TestingSessionLocal()
    _, token_a, _, farm_a_id = setup_farmer_with_farm(db, "Farmer Alpha", "9600000021", "alpha_p@agri.local", area=10.0)
    _, token_b, _, farm_b_id = setup_farmer_with_farm(db, "Farmer Beta", "9600000022", "beta_p@agri.local", area=8.0)
    crop_id, _ = create_test_crop(db, "Sugarcane", "PLANTATION")
    db.close()

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. Farmer A creates Plan A on Farm A -> 201 Created
    plan_payload_a = {
        "farm_id": farm_a_id,
        "crop_id": crop_id,
        "season": "YEAR_ROUND",
        "planned_start_date": "2026-06-01",
        "planned_end_date": "2027-05-31",
        "planned_area": 4.5,
        "land_area_unit": "ACRE",
        "notes": "Sugarcane plantation"
    }
    res_a = client.post("/api/v1/farm-crop-plans", headers=headers_a, json=plan_payload_a)
    assert res_a.status_code == 201
    plan_a_id = res_a.json()["id"]
    assert res_a.json()["season"] == "YEAR_ROUND"
    assert float(res_a.json()["planned_area"]) == 4.5

    # 2. Farmer A attempts to create plan on Farmer B's Farm B -> 404 Not Found
    res_cross_create = client.post("/api/v1/farm-crop-plans", headers=headers_a, json={
        "farm_id": farm_b_id,
        "crop_id": crop_id,
        "season": "KHARIF",
        "planned_start_date": "2026-06-01",
        "planned_area": 2.0,
        "land_area_unit": "ACRE"
    })
    assert res_cross_create.status_code == 404
    assert res_cross_create.json()["detail"] == "Farm not found"

    # 3. Farmer B attempts to access Farmer A's Plan A -> 404
    assert client.get(f"/api/v1/farm-crop-plans/{plan_a_id}", headers=headers_b).status_code == 404
    assert client.patch(f"/api/v1/farm-crop-plans/{plan_a_id}", headers=headers_b, json={"notes": "Hacked"}).status_code == 404
    assert client.delete(f"/api/v1/farm-crop-plans/{plan_a_id}", headers=headers_b).status_code == 404
    assert client.post(f"/api/v1/farm-crop-plans/{plan_a_id}/restore", headers=headers_b).status_code == 404

    # 4. Farmer B listing plans sees 0 plans
    res_b_list = client.get("/api/v1/farm-crop-plans", headers=headers_b)
    assert res_b_list.status_code == 200
    assert res_b_list.json()["total"] == 0


# ==============================================================================
# 3. Crop Availability & Validation Tests
# ==============================================================================

def test_crop_availability_validation(client: TestClient):
    """Inactive or deleted crops cannot be selected for new crop plans (400 Bad Request)."""
    db = TestingSessionLocal()
    _, token, _, farm_id = setup_farmer_with_farm(db, "Farmer Avail", "9600000030", "avail_p@agri.local")
    crop_inactive_id, _ = create_test_crop(db, "Inactive Cotton", "FIBER", is_active=False)
    crop_del_id, _ = create_test_crop(db, "Deleted Maize", "CEREAL", is_active=True)
    crop_del = CropRepository.get_by_id(db, uuid.UUID(crop_del_id))
    CropRepository.soft_delete(db, crop_del)
    db.close()

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Inactive crop -> 400
    res_inact = client.post("/api/v1/farm-crop-plans", headers=headers, json={
        "farm_id": farm_id,
        "crop_id": crop_inactive_id,
        "season": "KHARIF",
        "planned_start_date": "2026-06-01",
        "planned_area": 2.0,
        "land_area_unit": "ACRE"
    })
    assert res_inact.status_code == 400
    assert res_inact.json()["detail"] == "Selected crop is currently inactive or unavailable"

    # 2. Deleted crop -> 400
    res_del = client.post("/api/v1/farm-crop-plans", headers=headers, json={
        "farm_id": farm_id,
        "crop_id": crop_del_id,
        "season": "KHARIF",
        "planned_start_date": "2026-06-01",
        "planned_area": 2.0,
        "land_area_unit": "ACRE"
    })
    assert res_del.status_code == 400
    assert res_del.json()["detail"] == "Selected crop is currently inactive or unavailable"


def test_area_unit_and_date_validations(client: TestClient):
    """Validates land unit match, area bounds, required start date, and chronological date order."""
    db = TestingSessionLocal()
    _, token, _, farm_id = setup_farmer_with_farm(db, "Farmer Val", "9600000040", "val_p@agri.local", area=5.0, unit="ACRE")
    crop_id, _ = create_test_crop(db, "Groundnut Crop", "OILSEED")
    db.close()

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Missing planned_start_date -> 422
    assert client.post("/api/v1/farm-crop-plans", headers=headers, json={"farm_id": farm_id, "crop_id": crop_id, "season": "KHARIF", "planned_area": 2.0, "land_area_unit": "ACRE"}).status_code == 422

    # 2. Zero area -> 422
    assert client.post("/api/v1/farm-crop-plans", headers=headers, json={"farm_id": farm_id, "crop_id": crop_id, "season": "KHARIF", "planned_start_date": "2026-06-01", "planned_area": 0, "land_area_unit": "ACRE"}).status_code == 422

    # 3. Negative area -> 422
    assert client.post("/api/v1/farm-crop-plans", headers=headers, json={"farm_id": farm_id, "crop_id": crop_id, "season": "KHARIF", "planned_start_date": "2026-06-01", "planned_area": -1.5, "land_area_unit": "ACRE"}).status_code == 422

    # 4. Area unit mismatch (HECTARE instead of farm's ACRE) -> 422
    res_unit = client.post("/api/v1/farm-crop-plans", headers=headers, json={
        "farm_id": farm_id,
        "crop_id": crop_id,
        "season": "KHARIF",
        "planned_start_date": "2026-06-01",
        "planned_area": 2.0,
        "land_area_unit": "HECTARE"
    })
    assert res_unit.status_code == 422
    assert res_unit.json()["detail"] == "Area unit must match farm land area unit"

    # 5. Planned area > farm total area (6.0 > 5.0) -> 422
    res_area = client.post("/api/v1/farm-crop-plans", headers=headers, json={
        "farm_id": farm_id,
        "crop_id": crop_id,
        "season": "KHARIF",
        "planned_start_date": "2026-06-01",
        "planned_area": 6.0,
        "land_area_unit": "ACRE"
    })
    assert res_area.status_code == 422
    assert "cannot exceed farm total land area" in res_area.json()["detail"]

    # 6. Invalid date ordering (end_date < start_date) -> 422
    res_date = client.post("/api/v1/farm-crop-plans", headers=headers, json={
        "farm_id": farm_id,
        "crop_id": crop_id,
        "season": "KHARIF",
        "planned_start_date": "2026-10-01",
        "planned_end_date": "2026-06-01",
        "planned_area": 2.0,
        "land_area_unit": "ACRE"
    })
    assert res_date.status_code == 422
    assert res_date.status_code == 422


# ==============================================================================
# 4. Duplicate Plan Prevention & Multiple Plans Support
# ==============================================================================

def test_duplicate_plan_prevention(client: TestClient):
    """Same (farm, crop, season) with active status is rejected with 409 Conflict."""
    db = TestingSessionLocal()
    _, token, _, farm_id = setup_farmer_with_farm(db, "Farmer Dup", "9600000050", "dup_p@agri.local", area=10.0)
    crop_id, _ = create_test_crop(db, "Turmeric", "SPICE")
    db.close()

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "farm_id": farm_id,
        "crop_id": crop_id,
        "season": "KHARIF",
        "planned_start_date": "2026-06-01",
        "planned_area": 3.0,
        "land_area_unit": "ACRE"
    }

    # First plan succeeds -> 201
    res1 = client.post("/api/v1/farm-crop-plans", headers=headers, json=payload)
    assert res1.status_code == 201

    # Duplicate plan -> 409
    res2 = client.post("/api/v1/farm-crop-plans", headers=headers, json=payload)
    assert res2.status_code == 409
    assert res2.json()["detail"] == "An active crop plan for this farm, crop, and season already exists"


def test_multiple_plans_per_farm(client: TestClient):
    """A farm can have multiple plans for different crops or seasons."""
    db = TestingSessionLocal()
    _, token, _, farm_id = setup_farmer_with_farm(db, "Farmer Multi", "9600000060", "multi_p@agri.local", area=15.0)
    crop1_id, _ = create_test_crop(db, "Rice Season", "CEREAL")
    crop2_id, _ = create_test_crop(db, "Wheat Season", "CEREAL")
    db.close()

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Rice in KHARIF
    res1 = client.post("/api/v1/farm-crop-plans", headers=headers, json={"farm_id": farm_id, "crop_id": crop1_id, "season": "KHARIF", "planned_start_date": "2026-06-01", "planned_area": 5.0, "land_area_unit": "ACRE"})
    assert res1.status_code == 201

    # 2. Wheat in RABI
    res2 = client.post("/api/v1/farm-crop-plans", headers=headers, json={"farm_id": farm_id, "crop_id": crop2_id, "season": "RABI", "planned_start_date": "2026-10-01", "planned_area": 5.0, "land_area_unit": "ACRE"})
    assert res2.status_code == 201

    # 3. Rice in RABI (same crop, different season)
    res3 = client.post("/api/v1/farm-crop-plans", headers=headers, json={"farm_id": farm_id, "crop_id": crop1_id, "season": "RABI", "planned_start_date": "2026-10-01", "planned_area": 4.0, "land_area_unit": "ACRE"})
    assert res3.status_code == 201

    # List all plans
    res_list = client.get("/api/v1/farm-crop-plans", headers=headers)
    assert res_list.status_code == 200
    assert res_list.json()["total"] == 3


# ==============================================================================
# 5. Status Management & Soft Delete / Restore Lifecycle
# ==============================================================================

def test_farm_crop_plan_status_and_soft_delete(client: TestClient):
    """Status toggle, soft-deletion, direct GET 404, status block on deleted, and restore."""
    db = TestingSessionLocal()
    user_id, token, _, farm_id = setup_farmer_with_farm(db, "Farmer Del", "9600000070", "del_p@agri.local", area=5.0)
    crop_id, _ = create_test_crop(db, "Banana", "FRUIT")
    db.close()

    headers = {"Authorization": f"Bearer {token}"}
    res_create = client.post("/api/v1/farm-crop-plans", headers=headers, json={
        "farm_id": farm_id,
        "crop_id": crop_id,
        "season": "YEAR_ROUND",
        "planned_start_date": "2026-06-01",
        "planned_area": 2.5,
        "land_area_unit": "ACRE"
    })
    plan_id = res_create.json()["id"]

    # 1. Deactivate
    res_deact = client.patch(f"/api/v1/farm-crop-plans/{plan_id}/status", headers=headers, json={"is_active": False})
    assert res_deact.status_code == 200
    assert res_deact.json()["is_active"] is False

    # 2. Reactivate
    res_act = client.patch(f"/api/v1/farm-crop-plans/{plan_id}/status", headers=headers, json={"is_active": True})
    assert res_act.status_code == 200
    assert res_act.json()["is_active"] is True

    # 3. Soft Delete
    res_del = client.delete(f"/api/v1/farm-crop-plans/{plan_id}", headers=headers)
    assert res_del.status_code == 200
    assert res_del.json()["is_deleted"] is True
    assert res_del.json()["deleted_by"] == user_id

    # 4. Normal listing excludes deleted plan
    res_list = client.get("/api/v1/farm-crop-plans", headers=headers)
    assert res_list.status_code == 200
    assert res_list.json()["total"] == 0

    # 5. Direct GET returns 404
    assert client.get(f"/api/v1/farm-crop-plans/{plan_id}", headers=headers).status_code == 404

    # 6. Status change on deleted plan returns 400
    assert client.patch(f"/api/v1/farm-crop-plans/{plan_id}/status", headers=headers, json={"is_active": True}).status_code == 400

    # 7. Restore Plan
    res_restore = client.post(f"/api/v1/farm-crop-plans/{plan_id}/restore", headers=headers)
    assert res_restore.status_code == 200
    assert res_restore.json()["is_deleted"] is False
    assert res_restore.json()["deleted_at"] is None


# ==============================================================================
# 6. Crop Deactivation Effect on Existing & New Plans
# ==============================================================================

def test_crop_deactivation_effect(client: TestClient):
    """Deactivating a crop preserves existing plans historically, but blocks new plans for that crop."""
    db = TestingSessionLocal()
    admin_user = UserRepository.get_by_mobile(db, "9999999999")
    admin_id = str(admin_user.id)
    _, farmer_token, _, farm_id = setup_farmer_with_farm(db, "Farmer Deact Crop", "9600000080", "deact_c_p@agri.local", area=5.0)
    crop_id, _ = create_test_crop(db, "Cotton Test", "FIBER", is_active=True)
    db.close()

    admin_token = create_access_token(admin_id, ["SUPER_ADMIN"])
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    farmer_headers = {"Authorization": f"Bearer {farmer_token}"}

    # 1. Create plan while crop is active -> 201
    res_plan = client.post("/api/v1/farm-crop-plans", headers=farmer_headers, json={
        "farm_id": farm_id,
        "crop_id": crop_id,
        "season": "KHARIF",
        "planned_start_date": "2026-06-01",
        "planned_area": 3.0,
        "land_area_unit": "ACRE"
    })
    assert res_plan.status_code == 201
    plan_id = res_plan.json()["id"]

    # 2. Super Admin deactivates Cotton crop
    client.patch(f"/api/v1/admin/crops/{crop_id}/status", headers=admin_headers, json={"is_active": False})

    # 3. Existing plan is still readable!
    res_get_plan = client.get(f"/api/v1/farm-crop-plans/{plan_id}", headers=farmer_headers)
    assert res_get_plan.status_code == 200
    assert res_get_plan.json()["season"] == "KHARIF"

    # 4. Attempting to create a new plan with the now-inactive crop is blocked -> 400
    res_new_plan = client.post("/api/v1/farm-crop-plans", headers=farmer_headers, json={
        "farm_id": farm_id,
        "crop_id": crop_id,
        "season": "RABI",
        "planned_start_date": "2026-10-01",
        "planned_area": 2.0,
        "land_area_unit": "ACRE"
    })
    assert res_new_plan.status_code == 400
    assert res_new_plan.json()["detail"] == "Selected crop is currently inactive or unavailable"


# ==============================================================================
# 7. Role Revocation & Reassignment Tests
# ==============================================================================

def test_role_revocation_and_data_preservation(client: TestClient):
    """Revoking FARMER role causes immediate 403 on /farm-crop-plans; DB data is preserved and restored on reassign."""
    db = TestingSessionLocal()
    user_id_str, farmer_token, _, farm_id = setup_farmer_with_farm(db, "Revoke Farmer", "9600000090", "revoke_p@agri.local", area=5.0)
    user_uuid = uuid.UUID(user_id_str)
    farmer_role = RoleRepository.get_by_name(db, RoleEnum.FARMER.value)
    farmer_role_id = farmer_role.id
    crop_id, _ = create_test_crop(db, "Millet", "CEREAL")
    db.close()

    farmer_headers = {"Authorization": f"Bearer {farmer_token}"}

    # Create plan
    res_plan = client.post("/api/v1/farm-crop-plans", headers=farmer_headers, json={
        "farm_id": farm_id,
        "crop_id": crop_id,
        "season": "KHARIF",
        "planned_start_date": "2026-06-01",
        "planned_area": 2.5,
        "land_area_unit": "ACRE"
    })
    assert res_plan.status_code == 201
    plan_id = res_plan.json()["id"]

    # Revoke FARMER role
    db = TestingSessionLocal()
    UserRepository.remove_role(db, user_uuid, farmer_role_id)
    db.close()

    # Immediate 403
    assert client.get("/api/v1/farm-crop-plans", headers=farmer_headers).status_code == 403
    assert client.get(f"/api/v1/farm-crop-plans/{plan_id}", headers=farmer_headers).status_code == 403

    # Database records persist physically
    db = TestingSessionLocal()
    plan_db = FarmCropPlanRepository.get_by_id(db, uuid.UUID(plan_id))
    assert plan_db is not None
    assert plan_db.season == "KHARIF"

    # Re-assign FARMER role
    UserRepository.assign_role(db, user_uuid, farmer_role_id)
    db.close()

    # Access is restored
    res_restored = client.get(f"/api/v1/farm-crop-plans/{plan_id}", headers=farmer_headers)
    assert res_restored.status_code == 200
    assert res_restored.json()["season"] == "KHARIF"


# ==============================================================================
# 8. Alembic Migration Upgrade / Downgrade Lifecycle Test
# ==============================================================================

def test_alembic_migrations_upgrade_and_downgrade_0005():
    """Verify that Alembic migrations including 0005 upgrade and downgrade smoothly."""
    import os
    import tempfile
    from alembic.config import Config
    from alembic import command

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_db_path = tmp.name

    try:
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{tmp_db_path}")
        # Upgrade to latest revision (0005_crops_and_plans)
        command.upgrade(alembic_cfg, "head")
        # Downgrade 1 revision back to 0004_farms
        command.downgrade(alembic_cfg, "-1")
        # Upgrade back to head
        command.upgrade(alembic_cfg, "head")
    finally:
        if os.path.exists(tmp_db_path):
            try:
                os.remove(tmp_db_path)
            except Exception:
                pass


# ==============================================================================
# 9. Seed Variety, Per-Acre Rate & Next-Year Memory Notification Tests
# ==============================================================================

def test_seed_recommendations_catalog(client: TestClient):
    """Test agronomic seed recommendations for crops (Paddy, Onion, Groundnut, etc.)."""
    db = TestingSessionLocal()
    crop_id, _ = create_test_crop(db, "Paddy Deluxe", "CEREAL")
    db.close()

    # 1. Fetch all recommendations
    res_all = client.get("/api/v1/farm-crop-plans/seed-recommendations")
    assert res_all.status_code == 200
    catalog = res_all.json()
    assert len(catalog) >= 3
    paddy_entry = next((item for item in catalog if "Paddy" in item["crop_name"] or "Nel" in item.get("crop_name_local", "")), None)
    assert paddy_entry is not None
    assert float(paddy_entry["default_seed_rate_per_acre"]) == 20.0
    assert any(v["variety_name"] == "CO-51" for v in paddy_entry["varieties"])

    # 2. Fetch specific crop recommendations by crop_id
    res_crop = client.get(f"/api/v1/farm-crop-plans/seed-recommendations?crop_id={crop_id}")
    assert res_crop.status_code == 200
    recs = res_crop.json()
    assert len(recs) == 1
    assert recs[0]["crop_name"] == "Paddy Deluxe"
    assert len(recs[0]["varieties"]) >= 1


def test_create_and_update_plan_with_seed_options(client: TestClient):
    """Verify creating and updating farm crop plan with per-acre seed rate, variety, and next-year reminder."""
    db = TestingSessionLocal()
    _, farmer_token, _, farm_id = setup_farmer_with_farm(db, "Seed Farmer", "9600000095", "seed_farmer@agri.local", area=5.0)
    crop_id, _ = create_test_crop(db, "Paddy Co-51", "CEREAL")
    db.close()

    headers = {"Authorization": f"Bearer {farmer_token}"}

    # 1. Create plan with seed specifications
    res_create = client.post("/api/v1/farm-crop-plans", headers=headers, json={
        "farm_id": farm_id,
        "crop_id": crop_id,
        "season": "KHARIF",
        "planned_start_date": "2026-06-15",
        "planned_area": 3.0,
        "land_area_unit": "ACRE",
        "seed_variety": "CO-51",
        "seed_rate_per_acre": 20.0,
        "seed_rate_unit": "kg/acre",
        "total_seed_quantity": 60.0,
        "sowing_method": "NURSERY_TRANSPLANTING",
        "seed_brand_or_source": "TNAU Certified Seed Center",
        "remind_next_year": True,
        "notes": "Kuruvai season sowing"
    })
    assert res_create.status_code == 201
    plan = res_create.json()
    plan_id = plan["id"]
    assert plan["seed_variety"] == "CO-51"
    assert float(plan["seed_rate_per_acre"]) == 20.0
    assert float(plan["total_seed_quantity"]) == 60.0
    assert plan["sowing_method"] == "NURSERY_TRANSPLANTING"
    assert plan["seed_brand_or_source"] == "TNAU Certified Seed Center"
    assert plan["remind_next_year"] is True

    # 2. Update seed variety and rate
    res_update = client.patch(f"/api/v1/farm-crop-plans/{plan_id}", headers=headers, json={
        "seed_variety": "ADT-37",
        "seed_rate_per_acre": 22.0,
        "total_seed_quantity": 66.0
    })
    assert res_update.status_code == 200
    updated = res_update.json()
    assert updated["seed_variety"] == "ADT-37"
    assert float(updated["seed_rate_per_acre"]) == 22.0
    assert float(updated["total_seed_quantity"]) == 66.0


def test_seed_history_and_seasonal_reminder(client: TestClient):
    """Verify seed usage memory history querying and seasonal reminder notification dispatch."""
    db = TestingSessionLocal()
    _, farmer_token, _, farm_id = setup_farmer_with_farm(db, "Memory Farmer", "9600000096", "mem_farmer@agri.local", area=4.0)
    crop_id, _ = create_test_crop(db, "Vengayam Small", "VEGETABLE")
    db.close()

    headers = {"Authorization": f"Bearer {farmer_token}"}

    # 1. Create plan
    res_create = client.post("/api/v1/farm-crop-plans", headers=headers, json={
        "farm_id": farm_id,
        "crop_id": crop_id,
        "season": "RABI",
        "planned_start_date": "2025-10-10",
        "planned_area": 2.0,
        "land_area_unit": "ACRE",
        "seed_variety": "Co-Onion-5",
        "seed_rate_per_acre": 4.0,
        "seed_rate_unit": "kg/acre",
        "total_seed_quantity": 8.0,
        "sowing_method": "DIRECT_SEEDING",
        "remind_next_year": True
    })
    assert res_create.status_code == 201
    plan_id = res_create.json()["id"]

    # 2. Query seed history memory
    res_hist = client.get("/api/v1/farm-crop-plans/seed-history", headers=headers)
    assert res_hist.status_code == 200
    history = res_hist.json()
    assert len(history) >= 1
    item = next(h for h in history if h["plan_id"] == plan_id)
    assert item["seed_variety"] == "Co-Onion-5"
    assert float(item["seed_rate_per_acre"]) == 4.0
    assert item["farm_name"] is not None

    # 3. Trigger seasonal seed reminder notification
    res_remind = client.post(f"/api/v1/farm-crop-plans/{plan_id}/remind-seed-usage", headers=headers)
    assert res_remind.status_code == 200
    remind_data = res_remind.json()
    assert remind_data["status"] == "SUCCESS"
    assert "Co-Onion-5" in remind_data["notification_preview"]
    assert "விதை நினைவூட்டல்" in remind_data["notification_preview"]

