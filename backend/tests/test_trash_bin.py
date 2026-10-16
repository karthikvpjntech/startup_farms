import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.core.jwt import create_access_token
from app.core.security import get_password_hash
from app.models.enums import RoleEnum, CropCategory, LandAreaUnitEnum
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.repositories.farmer_profile_repository import FarmerProfileRepository
from app.repositories.farm_repository import FarmRepository
from app.repositories.crop_repository import CropRepository
from tests.conftest import TestingSessionLocal


def create_user_with_roles(db, full_name: str, mobile: str, email: str, roles_list: list[RoleEnum]) -> tuple[str, str]:
    """Creates a user and returns (user_id_str, access_token)."""
    roles = [RoleRepository.get_by_name(db, r.value) for r in roles_list]
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
    token = create_access_token(str(user.id), [r.value for r in roles_list])
    return str(user.id), token


def test_trash_bin_unauthorized(client: TestClient):
    """Unauthenticated and non-admin calls are blocked."""
    assert client.get("/api/v1/admin/trash-bin").status_code == 401

    db = TestingSessionLocal()
    _, farmer_token = create_user_with_roles(db, "Farmer Test", "9500000001", "farmer_tb@agri.local", [RoleEnum.FARMER])
    db.close()

    farmer_headers = {"Authorization": f"Bearer {farmer_token}"}
    assert client.get("/api/v1/admin/trash-bin", headers=farmer_headers).status_code == 403
    assert client.post(f"/api/v1/admin/trash-bin/CROP/{uuid.uuid4()}/restore", headers=farmer_headers).status_code == 403
    assert client.delete(f"/api/v1/admin/trash-bin/CROP/{uuid.uuid4()}/hard-delete", headers=farmer_headers).status_code == 403


def test_trash_bin_listing_and_restoration(client: TestClient):
    """Super Admin can audit soft-deleted entities, restore them, and view updated stats."""
    db = TestingSessionLocal()
    admin_user = UserRepository.get_by_mobile(db, "9999999999")
    admin_id = str(admin_user.id)
    admin_token = create_access_token(admin_id, ["SUPER_ADMIN"])
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Create and soft-delete a crop
    crop = CropRepository.create(
        db=db,
        crop_code="CROP-TB0001",
        crop_data={"crop_name": "Trash Test Crop", "crop_category": "CEREAL"},
        created_by=admin_user.id
    )
    crop_id = str(crop.id)
    CropRepository.soft_delete(db, crop, deleted_by=admin_user.id)
    db.close()

    # 1. Listing should show the soft-deleted crop
    res_list = client.get("/api/v1/admin/trash-bin?entity_type=CROP", headers=admin_headers)
    assert res_list.status_code == 200
    data = res_list.json()
    assert data["total"] >= 1
    found_item = next((item for item in data["items"] if item["id"] == crop_id), None)
    assert found_item is not None
    assert found_item["entity_name"] == "Trash Test Crop"
    assert found_item["entity_type"] == "CROP"

    # 2. Restore the crop
    res_restore = client.post(f"/api/v1/admin/trash-bin/CROP/{crop_id}/restore", headers=admin_headers)
    assert res_restore.status_code == 200
    assert res_restore.json()["success"] is True

    # 3. Listing now should NOT contain the restored crop
    res_list_after = client.get("/api/v1/admin/trash-bin?entity_type=CROP", headers=admin_headers)
    assert res_list_after.status_code == 200
    found_after = next((item for item in res_list_after.json()["items"] if item["id"] == crop_id), None)
    assert found_after is None

    # 4. Verify the crop is active and readable via normal crops API
    db = TestingSessionLocal()
    crop_db = CropRepository.get_by_id(db, uuid.UUID(crop_id))
    assert crop_db is not None
    assert crop_db.is_deleted is False
    db.close()


def test_trash_bin_hard_deletion(client: TestClient):
    """Super Admin can permanently hard-delete a soft-deleted entity with safety checks."""
    db = TestingSessionLocal()
    admin_user = UserRepository.get_by_mobile(db, "9999999999")
    admin_id = str(admin_user.id)
    admin_token = create_access_token(admin_id, ["SUPER_ADMIN"])
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Create and soft-delete a farm
    user_id_str, _ = create_user_with_roles(db, "Farmer HD", "9500000002", "farmer_hd@agri.local", [RoleEnum.FARMER])
    profile = FarmerProfileRepository.create(db=db, user_id=uuid.UUID(user_id_str), profile_data={"village": "Salem"})
    farm = FarmRepository.create(
        db=db,
        farmer_profile_id=profile.id,
        farm_code="FARM-HD001",
        farm_data={
            "farm_name": "Hard Delete Farm",
            "ownership_type": "OWNED",
            "total_land_area": Decimal("4.0"),
            "land_area_unit": "ACRE",
        },
        created_by=uuid.UUID(user_id_str)
    )
    farm_id = str(farm.id)
    FarmRepository.soft_delete(db, farm, deleted_by=admin_user.id)
    db.close()

    # 1. Attempt self-hard-deletion of active admin account -> 400
    res_self = client.delete(f"/api/v1/admin/trash-bin/USER/{admin_id}/hard-delete", headers=admin_headers)
    assert res_self.status_code == 400
    assert "cannot execute hard-deletion on their own" in res_self.json()["detail"]

    # 2. Hard delete the farm -> 200
    res_hd = client.delete(f"/api/v1/admin/trash-bin/FARM/{farm_id}/hard-delete", headers=admin_headers)
    assert res_hd.status_code == 200
    assert res_hd.json()["success"] is True

    # 3. Database record is completely removed
    db = TestingSessionLocal()
    farm_db = FarmRepository.get_by_id(db, uuid.UUID(farm_id))
    assert farm_db is None
    db.close()
