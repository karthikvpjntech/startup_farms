import uuid
import pytest
from fastapi.testclient import TestClient

from app.core.jwt import create_access_token
from app.core.security import get_password_hash
from app.models.enums import RoleEnum, CropCategoryEnum
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
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


# ==============================================================================
# 1. Crop Master Authorization Tests
# ==============================================================================

def test_unauthenticated_crop_admin_access(client: TestClient):
    """Calling admin crop endpoints without token returns 401 Unauthorized."""
    random_id = str(uuid.uuid4())
    assert client.get("/api/v1/admin/crops").status_code == 401
    assert client.post("/api/v1/admin/crops", json={}).status_code == 401
    assert client.get(f"/api/v1/admin/crops/{random_id}").status_code == 401
    assert client.patch(f"/api/v1/admin/crops/{random_id}", json={}).status_code == 401
    assert client.patch(f"/api/v1/admin/crops/{random_id}/status", json={"is_active": True}).status_code == 401
    assert client.delete(f"/api/v1/admin/crops/{random_id}").status_code == 401
    assert client.post(f"/api/v1/admin/crops/{random_id}/restore").status_code == 401


def test_forbidden_roles_on_admin_crops(client: TestClient):
    """FARMER, TRADER, DRIVER, WORKER cannot manage crop master records (403 Forbidden)."""
    db = TestingSessionLocal()
    farmer_id, _ = create_test_user_with_roles(db, "Farmer Only", "9700000001", "farmer_crop@agri.local", [RoleEnum.FARMER])
    trader_id, _ = create_test_user_with_roles(db, "Trader Only", "9700000002", "trader_crop@agri.local", [RoleEnum.TRADER])
    driver_id, _ = create_test_user_with_roles(db, "Driver Only", "9700000003", "driver_crop@agri.local", [RoleEnum.DRIVER])
    worker_id, _ = create_test_user_with_roles(db, "Worker Only", "9700000004", "worker_crop@agri.local", [RoleEnum.WORKER])
    db.close()

    for uid, roles in [(farmer_id, ["FARMER"]), (trader_id, ["TRADER"]), (driver_id, ["DRIVER"]), (worker_id, ["WORKER"])]:
        token = create_access_token(uid, roles)
        headers = {"Authorization": f"Bearer {token}"}
        res_list = client.get("/api/v1/admin/crops", headers=headers)
        assert res_list.status_code == 403
        res_create = client.post("/api/v1/admin/crops", headers=headers, json={"crop_name": "Wheat", "crop_category": "CEREAL"})
        assert res_create.status_code == 403


# ==============================================================================
# 2. Crop Master CRUD & Lifecycle Tests (Super Admin)
# ==============================================================================

def test_crop_master_lifecycle(client: TestClient):
    """Complete Super Admin lifecycle: create, get, list, patch, duplicate prevention, status, soft-delete, restore."""
    db = TestingSessionLocal()
    admin_user = UserRepository.get_by_mobile(db, "9999999999")
    admin_id = str(admin_user.id)
    db.close()

    admin_token = create_access_token(admin_id, ["SUPER_ADMIN"])
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create Crop
    payload = {
        "crop_name": "Paddy / Rice",
        "scientific_name": "Oryza sativa",
        "crop_category": "CEREAL",
        "description": "Primary staple food crop cultivated in monsoon."
    }
    res_create = client.post("/api/v1/admin/crops", headers=headers, json=payload)
    assert res_create.status_code == 201
    crop_data = res_create.json()
    crop_id = crop_data["id"]
    assert crop_data["crop_name"] == "Paddy / Rice"
    assert crop_data["crop_code"] == "CROP-000001"
    assert crop_data["crop_category"] == "CEREAL"
    assert crop_data["is_active"] is True
    assert crop_data["is_deleted"] is False
    assert crop_data["created_by"] == admin_id

    # 2. Duplicate active crop name rejected -> 409
    res_dup = client.post("/api/v1/admin/crops", headers=headers, json={
        "crop_name": "  paddy / rice  ",
        "crop_category": "CEREAL"
    })
    assert res_dup.status_code == 409
    assert res_dup.json()["detail"] == "An active crop with this name already exists"

    # 3. Get Details
    res_get = client.get(f"/api/v1/admin/crops/{crop_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["scientific_name"] == "Oryza sativa"

    # 4. Partial Update
    res_patch = client.patch(f"/api/v1/admin/crops/{crop_id}", headers=headers, json={
        "scientific_name": "Oryza sativa L.",
        "description": "Updated agronomic description."
    })
    assert res_patch.status_code == 200
    assert res_patch.json()["scientific_name"] == "Oryza sativa L."
    assert res_patch.json()["crop_code"] == "CROP-000001"  # Immutable

    # 5. Status Toggle (Deactivate / Reactivate)
    res_deact = client.patch(f"/api/v1/admin/crops/{crop_id}/status", headers=headers, json={"is_active": False})
    assert res_deact.status_code == 200
    assert res_deact.json()["is_active"] is False

    res_act = client.patch(f"/api/v1/admin/crops/{crop_id}/status", headers=headers, json={"is_active": True})
    assert res_act.status_code == 200
    assert res_act.json()["is_active"] is True

    # 6. Soft Delete
    res_del = client.delete(f"/api/v1/admin/crops/{crop_id}", headers=headers)
    assert res_del.status_code == 200
    assert res_del.json()["is_deleted"] is True
    assert res_del.json()["deleted_by"] == admin_id

    # 7. Status update on deleted crop -> 400
    res_stat_del = client.patch(f"/api/v1/admin/crops/{crop_id}/status", headers=headers, json={"is_active": True})
    assert res_stat_del.status_code == 400

    # 8. Restore Crop
    res_restore = client.post(f"/api/v1/admin/crops/{crop_id}/restore", headers=headers)
    assert res_restore.status_code == 200
    assert res_restore.json()["is_deleted"] is False
    assert res_restore.json()["deleted_at"] is None


# ==============================================================================
# 3. Farmer Crop Catalog Read-Only Tests
# ==============================================================================

def test_farmer_crop_catalog_access(client: TestClient):
    """Farmers can list only active, non-deleted crops with search and category filters."""
    db = TestingSessionLocal()
    admin_user = UserRepository.get_by_mobile(db, "9999999999")
    admin_id = str(admin_user.id)
    farmer_id, _ = create_test_user_with_roles(db, "Farmer Catalog", "9700000010", "catalog_farmer@agri.local", [RoleEnum.FARMER])
    trader_id, _ = create_test_user_with_roles(db, "Trader Catalog", "9700000011", "catalog_trader@agri.local", [RoleEnum.TRADER])
    db.close()

    admin_token = create_access_token(admin_id, ["SUPER_ADMIN"])
    farmer_token = create_access_token(farmer_id, ["FARMER"])
    trader_token = create_access_token(trader_id, ["TRADER"])

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    farmer_headers = {"Authorization": f"Bearer {farmer_token}"}
    trader_headers = {"Authorization": f"Bearer {trader_token}"}

    # Admin seeds 3 crops: 1 active CEREAL, 1 active VEGETABLE, 1 inactive PULSE, 1 deleted OILSEED
    res1 = client.post("/api/v1/admin/crops", headers=admin_headers, json={"crop_name": "Wheat", "crop_category": "CEREAL"})
    res2 = client.post("/api/v1/admin/crops", headers=admin_headers, json={"crop_name": "Tomato", "crop_category": "VEGETABLE"})
    res3 = client.post("/api/v1/admin/crops", headers=admin_headers, json={"crop_name": "Chickpea", "crop_category": "PULSE"})
    res4 = client.post("/api/v1/admin/crops", headers=admin_headers, json={"crop_name": "Groundnut", "crop_category": "OILSEED"})

    # Deactivate Chickpea
    client.patch(f"/api/v1/admin/crops/{res3.json()['id']}/status", headers=admin_headers, json={"is_active": False})
    # Soft-delete Groundnut
    client.delete(f"/api/v1/admin/crops/{res4.json()['id']}", headers=admin_headers)

    # 1. TRADER cannot access farmer catalog -> 403
    assert client.get("/api/v1/crops", headers=trader_headers).status_code == 403

    # 2. FARMER gets only active, non-deleted crops (Wheat, Tomato)
    res_farmer = client.get("/api/v1/crops", headers=farmer_headers)
    assert res_farmer.status_code == 200
    farmer_data = res_farmer.json()
    assert farmer_data["total"] == 2
    crop_names = [c["crop_name"] for c in farmer_data["items"]]
    assert "Wheat" in crop_names
    assert "Tomato" in crop_names
    assert "Chickpea" not in crop_names
    assert "Groundnut" not in crop_names

    # 3. Category filtering
    res_cat = client.get("/api/v1/crops?category=VEGETABLE", headers=farmer_headers)
    assert res_cat.status_code == 200
    assert res_cat.json()["total"] == 1
    assert res_cat.json()["items"][0]["crop_name"] == "Tomato"

    # 4. Search filtering
    res_search = client.get("/api/v1/crops?search=whe", headers=farmer_headers)
    assert res_search.status_code == 200
    assert res_search.json()["total"] == 1
    assert res_search.json()["items"][0]["crop_name"] == "Wheat"
