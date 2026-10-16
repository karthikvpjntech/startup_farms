import io
import pytest
from fastapi import status
from app.core.jwt import create_access_token
from app.repositories.user_repository import UserRepository
from app.seeds.crop_stages_seed import seed_crop_stages


def get_admin_token(db_session):
    """Helper to generate Super Admin access token."""
    admin_user = UserRepository.get_by_mobile(db_session, "9999999999")
    return create_access_token(str(admin_user.id), ["SUPER_ADMIN"])


def test_seed_and_list_stages(client, db_session):
    """Verify seeding and public/admin retrieval of crop stages."""
    seed_result = seed_crop_stages(db_session)
    crop_id = seed_result["crop_id"]

    # 1. Public list stages
    res = client.get(f"/api/v1/crops/{crop_id}/process-stages")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total"] == 8
    assert len(data["items"]) == 8
    assert data["items"][0]["stage_order"] == 1
    assert data["items"][0]["visual_asset_type"] in ["SEED", "TILLAGE"]

    # 2. Admin list stages
    admin_token = get_admin_token(db_session)
    res_admin = client.get(
        f"/api/v1/admin/crops/{crop_id}/stages",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_admin.status_code == status.HTTP_200_OK
    assert res_admin.json()["total"] == 8


def test_admin_create_update_delete_stage(client, db_session):
    """Verify admin stage creation, updating, and soft-deletion."""
    seed_result = seed_crop_stages(db_session)
    crop_id = seed_result["crop_id"]
    admin_token = get_admin_token(db_session)

    # 1. Create a custom stage
    payload = {
        "stage_name": "Post-Harvest Processing",
        "stage_name_local": "பின் அறுவடை மேலாண்மை",
        "description": "Sun drying and curing under shed.",
        "duration_days": 12,
        "visual_asset_type": "YIELD_STORAGE",
        "visual_theme_color": "#059669",
        "recommended_activities": ["Aerated stacking", "Moisture inspection"],
        "recommended_inputs": []
    }
    res_create = client.post(
        f"/api/v1/admin/crops/{crop_id}/stages",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_create.status_code == status.HTTP_201_CREATED
    stage_id = res_create.json()["id"]
    assert res_create.json()["stage_order"] == 9

    # 2. Update the stage
    res_update = client.patch(
        f"/api/v1/admin/crops/{crop_id}/stages/{stage_id}",
        json={"duration_days": 14, "stage_name": "Post-Harvest Curing & Bagging"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_update.status_code == status.HTTP_200_OK
    assert res_update.json()["duration_days"] == 14
    assert res_update.json()["stage_name"] == "Post-Harvest Curing & Bagging"

    # 3. Delete stage
    res_delete = client.delete(
        f"/api/v1/admin/crops/{crop_id}/stages/{stage_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_delete.status_code == status.HTTP_200_OK
    assert res_delete.json()["is_deleted"] is True


def test_admin_reorder_stages(client, db_session):
    """Verify batch reordering of cultivation stages."""
    seed_result = seed_crop_stages(db_session)
    crop_id = seed_result["crop_id"]
    admin_token = get_admin_token(db_session)

    # Get current stages
    res = client.get(
        f"/api/v1/admin/crops/{crop_id}/stages",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    items = res.json()["items"]
    assert len(items) >= 2

    stage_1_id = items[0]["id"]
    stage_2_id = items[1]["id"]

    # Swap orders
    reorder_payload = {
        "stages": [
            {"stage_id": stage_1_id, "stage_order": 2},
            {"stage_id": stage_2_id, "stage_order": 1},
        ]
    }
    res_reorder = client.put(
        f"/api/v1/admin/crops/{crop_id}/stages/reorder",
        json=reorder_payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_reorder.status_code == status.HTTP_200_OK
    reordered_items = res_reorder.json()["items"]
    assert reordered_items[0]["id"] == stage_2_id
    assert reordered_items[0]["stage_order"] == 1
    assert reordered_items[1]["id"] == stage_1_id
    assert reordered_items[1]["stage_order"] == 2


def test_upload_stage_image(client, db_session):
    """Verify real photo upload for a stage."""
    seed_result = seed_crop_stages(db_session)
    crop_id = seed_result["crop_id"]
    admin_token = get_admin_token(db_session)

    # Get first stage
    res = client.get(
        f"/api/v1/admin/crops/{crop_id}/stages",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    stage_id = res.json()["items"][0]["id"]

    # Create dummy PNG file in memory
    fake_png = io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")

    res_upload = client.post(
        f"/api/v1/admin/crops/{crop_id}/stages/{stage_id}/image",
        files={"file": ("onion_seed.png", fake_png, "image/png")},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_upload.status_code == status.HTTP_200_OK
    upload_data = res_upload.json()
    assert "image_url" in upload_data
    assert upload_data["image_url"].startswith("/uploads/stages/")
