import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

def test_public_subscription_settings(client: TestClient):
    resp = client.get("/api/v1/subscriptions/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_enabled"] is True
    assert data["free_retention_days"] == 30
    assert float(data["monthly_price"]) == 199.0
    assert float(data["annual_price"]) == 999.0


def test_public_subscription_my_status_unauthenticated(client: TestClient):
    resp = client.get("/api/v1/subscriptions/my-status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_subscription_required"] is True
    assert data["has_active_subscription"] is False
    assert data["is_unlocked"] is False


def test_admin_toggle_and_update_settings(client: TestClient):
    # 1. Login as super admin
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": "9999999999", "password": "SuperAdminPass123!"}
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Update settings (Deactivate gate)
    update_resp = client.put(
        "/api/v1/subscriptions/admin/settings",
        json={
            "is_enabled": False,
            "free_retention_days": 60,
            "monthly_price": 249.0,
            "annual_price": 1199.0
        },
        headers=headers
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["is_enabled"] is False
    assert data["free_retention_days"] == 60
    assert float(data["monthly_price"]) == 249.0

    # 3. Check status now: since is_enabled is False, is_unlocked should be True
    status_resp = client.get("/api/v1/subscriptions/my-status")
    assert status_resp.status_code == 200
    assert status_resp.json()["is_subscription_required"] is False
    assert status_resp.json()["is_unlocked"] is True
