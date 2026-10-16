import uuid
import pytest
from fastapi.testclient import TestClient

from app.core.security import verify_password
from app.core.jwt import create_access_token
from app.models.enums import RoleEnum
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from tests.conftest import TestingSessionLocal


def get_admin_token(client: TestClient) -> str:
    """Helper to log in as default Super Admin and obtain access token."""
    res = client.post("/api/v1/auth/login", json={
        "identifier": "admin@agrismart.local",
        "password": "SuperAdminPass123!"
    })
    assert res.status_code == 200
    return res.json()["access_token"]


def create_user_with_role(db, full_name: str, mobile: str, email: str, role_name: str) -> User:
    """Helper to create test user in database."""
    role = RoleRepository.get_by_name(db, role_name)
    user = UserRepository.create_with_roles(
        db=db,
        full_name=full_name,
        mobile_number=mobile,
        password_hash="$argon2id$v=19$m=65536,t=3,p=4$somefakepasswordhash",
        email=email,
        roles=[role] if role else [],
        is_active=True
    )
    return user


# ==============================================================================
# 1. Authorization Tests
# ==============================================================================

def test_admin_endpoints_unauthenticated(client: TestClient):
    """Unauthenticated requests to admin user endpoints return 401."""
    res_get = client.get("/api/v1/admin/users")
    assert res_get.status_code == 401

    res_post = client.post("/api/v1/admin/users", json={})
    assert res_post.status_code == 401


def test_admin_endpoints_forbidden_for_non_admin(client: TestClient):
    """Non-admin users (e.g. FARMER) receive 403 on admin user endpoints."""
    db = TestingSessionLocal()
    farmer = create_user_with_role(db, "Test Farmer", "9876500001", "farmer1@agri.local", RoleEnum.FARMER.value)
    farmer_id_str = str(farmer.id)
    db.close()

    farmer_token = create_access_token(farmer_id_str, ["FARMER"])
    headers = {"Authorization": f"Bearer {farmer_token}"}

    res_get = client.get("/api/v1/admin/users", headers=headers)
    assert res_get.status_code == 403
    assert res_get.json()["detail"] == "You do not have permission to access this resource"

    res_post = client.post("/api/v1/admin/users", headers=headers, json={
        "full_name": "New User",
        "mobile_number": "9876500002",
        "email": "new@agri.local",
        "password": "Password123!",
        "roles": ["FARMER"]
    })
    assert res_post.status_code == 403


# ==============================================================================
# 2. Create User Tests
# ==============================================================================

def test_create_user_success(client: TestClient):
    """SUPER_ADMIN successfully creates user with initial roles and audit fields."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "full_name": "Ravi Farmer",
        "mobile_number": "9876511111",
        "email": "ravi.farmer@agri.local",
        "password": "FarmerSecretPass123!",
        "roles": ["FARMER"]
    }

    res = client.post("/api/v1/admin/users", headers=headers, json=payload)
    assert res.status_code == 201
    data = res.json()

    assert data["full_name"] == "Ravi Farmer"
    assert data["mobile_number"] in ("9876511111", "+919876511111")
    assert data["email"] == "ravi.farmer@agri.local"
    assert data["is_active"] is True
    assert data["is_deleted"] is False
    assert data["roles"] == ["FARMER"]
    assert "password" not in data
    assert "password_hash" not in data
    assert data["created_by"] is not None

    # Verify database persistence & Argon2id password hash
    db = TestingSessionLocal()
    user_db = UserRepository.get_by_mobile(db, "9876511111")
    assert user_db is not None
    assert user_db.password_hash.startswith("$argon2id$")
    assert verify_password("FarmerSecretPass123!", user_db.password_hash) is True
    db.close()


def test_create_user_multiple_roles(client: TestClient):
    """SUPER_ADMIN can create a user with multiple valid roles."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "full_name": "Multi Role Person",
        "mobile_number": "9876522222",
        "email": "multirole@agri.local",
        "password": "MultiRolePass123!",
        "roles": ["FARMER", "TRADER"]
    }

    res = client.post("/api/v1/admin/users", headers=headers, json=payload)
    assert res.status_code == 201
    data = res.json()
    assert set(data["roles"]) == {"FARMER", "TRADER"}


def test_create_user_duplicate_mobile_fails(client: TestClient):
    """Creating user with duplicate mobile number returns 409 Conflict."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "full_name": "Duplicate User",
        "mobile_number": "9999999999",  # Seeded Super Admin's mobile
        "email": "unique@agri.local",
        "password": "Password123!",
        "roles": ["FARMER"]
    }

    res = client.post("/api/v1/admin/users", headers=headers, json=payload)
    assert res.status_code == 409
    assert "mobile number already exists" in res.json()["detail"].lower()


def test_create_user_duplicate_email_fails(client: TestClient):
    """Creating user with duplicate email returns 409 Conflict."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "full_name": "Duplicate Email User",
        "mobile_number": "9876533333",
        "email": "admin@agrismart.local",  # Seeded Super Admin's email
        "password": "Password123!",
        "roles": ["FARMER"]
    }

    res = client.post("/api/v1/admin/users", headers=headers, json=payload)
    assert res.status_code == 409
    assert "email already exists" in res.json()["detail"].lower()


def test_create_user_invalid_role_fails(client: TestClient):
    """Providing an invalid role name returns validation error and does not modify roles."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "full_name": "Bad Role User",
        "mobile_number": "9876544444",
        "email": "badrole@agri.local",
        "password": "Password123!",
        "roles": ["MANAGER"]  # Invalid role
    }

    res = client.post("/api/v1/admin/users", headers=headers, json=payload)
    assert res.status_code in (400, 422)

    db = TestingSessionLocal()
    assert RoleRepository.get_by_name(db, "MANAGER") is None
    db.close()


# ==============================================================================
# 3. List Users & Search / Filter Tests
# ==============================================================================

def test_list_users_pagination_and_search(client: TestClient):
    """Listing users supports pagination and search on name, email, mobile."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    db = TestingSessionLocal()
    create_user_with_role(db, "Karthik Raja", "9876501001", "karthik@agri.local", RoleEnum.FARMER.value)
    create_user_with_role(db, "Anand Kumar", "9876501002", "anand@agri.local", RoleEnum.TRADER.value)
    create_user_with_role(db, "Suresh Driver", "9876501003", "suresh@agri.local", RoleEnum.DRIVER.value)
    db.close()

    # 1. Base list
    res = client.get("/api/v1/admin/users?page=1&page_size=2", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total"] >= 4
    assert data["total_pages"] >= 2

    # 2. Search by name
    res_search = client.get("/api/v1/admin/users?search=Karthik", headers=headers)
    assert res_search.status_code == 200
    assert len(res_search.json()["items"]) == 1
    assert res_search.json()["items"][0]["full_name"] == "Karthik Raja"

    # 3. Search by email
    res_email = client.get("/api/v1/admin/users?search=anand@agri.local", headers=headers)
    assert res_email.status_code == 200
    assert len(res_email.json()["items"]) == 1
    assert res_email.json()["items"][0]["email"] == "anand@agri.local"

    # 4. Search by mobile
    res_mobile = client.get("/api/v1/admin/users?search=9876501003", headers=headers)
    assert res_mobile.status_code == 200
    assert len(res_mobile.json()["items"]) == 1
    assert res_mobile.json()["items"][0]["mobile_number"] == "9876501003"


def test_list_users_filters(client: TestClient):
    """Listing users supports role, is_active, and is_deleted filters."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    db = TestingSessionLocal()
    farmer = create_user_with_role(db, "Filter Farmer", "9876502001", "ff@agri.local", RoleEnum.FARMER.value)
    UserRepository.set_active_status(db, farmer, is_active=False)
    db.close()

    # Filter by role
    res_role = client.get("/api/v1/admin/users?role=FARMER", headers=headers)
    assert res_role.status_code == 200
    assert all("FARMER" in u["roles"] for u in res_role.json()["items"])

    # Filter by is_active=false
    res_inact = client.get("/api/v1/admin/users?is_active=false", headers=headers)
    assert res_inact.status_code == 200
    assert any(u["mobile_number"] == "9876502001" for u in res_inact.json()["items"])


# ==============================================================================
# 4. User Detail & Update Profile Tests
# ==============================================================================

def test_get_user_detail(client: TestClient):
    """Retrieve user details by user_id."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    db = TestingSessionLocal()
    farmer = create_user_with_role(db, "Detail Farmer", "9876503001", "detail@agri.local", RoleEnum.FARMER.value)
    farmer_id = str(farmer.id)
    db.close()

    # Success
    res = client.get(f"/api/v1/admin/users/{farmer_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["id"] == farmer_id
    assert res.json()["full_name"] == "Detail Farmer"

    # Non-existent
    fake_id = str(uuid.uuid4())
    res_404 = client.get(f"/api/v1/admin/users/{fake_id}", headers=headers)
    assert res_404.status_code == 404
    assert res_404.json()["detail"] == "User not found"


def test_update_user_profile(client: TestClient):
    """Super Admin updates user profile fields."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    db = TestingSessionLocal()
    farmer = create_user_with_role(db, "Original Name", "9876504001", "orig@agri.local", RoleEnum.FARMER.value)
    farmer_id = str(farmer.id)
    db.close()

    # Successful update
    res = client.patch(f"/api/v1/admin/users/{farmer_id}", headers=headers, json={
        "full_name": "Updated Name",
        "email": "updated@agri.local"
    })
    assert res.status_code == 200
    assert res.json()["full_name"] == "Updated Name"
    assert res.json()["email"] == "updated@agri.local"
    assert res.json()["mobile_number"] == "9876504001"

    # Duplicate mobile update fails
    res_dup = client.patch(f"/api/v1/admin/users/{farmer_id}", headers=headers, json={
        "mobile_number": "9999999999"
    })
    assert res_dup.status_code == 409


# ==============================================================================
# 5. User Status (Activate / Deactivate) Tests
# ==============================================================================

def test_user_status_deactivation_and_login_blocking(client: TestClient):
    """Deactivating a user blocks subsequent logins; reactivating restores login ability."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create active farmer
    res_create = client.post("/api/v1/admin/users", headers=headers, json={
        "full_name": "Status Farmer",
        "mobile_number": "9876505001",
        "email": "status.farmer@agri.local",
        "password": "FarmerPassword123!",
        "roles": ["FARMER"]
    })
    farmer_id = res_create.json()["id"]

    # Initial login works
    login1 = client.post("/api/v1/auth/login", json={
        "identifier": "9876505001",
        "password": "FarmerPassword123!"
    })
    assert login1.status_code == 200

    # 1. Deactivate farmer
    res_deact = client.patch(f"/api/v1/admin/users/{farmer_id}/status", headers=headers, json={
        "is_active": False
    })
    assert res_deact.status_code == 200
    assert res_deact.json()["is_active"] is False

    # Login now rejected with 401
    login_blocked = client.post("/api/v1/auth/login", json={
        "identifier": "9876505001",
        "password": "FarmerPassword123!"
    })
    assert login_blocked.status_code == 401

    # 2. Reactivate farmer
    res_react = client.patch(f"/api/v1/admin/users/{farmer_id}/status", headers=headers, json={
        "is_active": True
    })
    assert res_react.status_code == 200
    assert res_react.json()["is_active"] is True

    # Login works again
    login_restored = client.post("/api/v1/auth/login", json={
        "identifier": "9876505001",
        "password": "FarmerPassword123!"
    })
    assert login_restored.status_code == 200


# ==============================================================================
# 6. Soft Delete & Restore Tests
# ==============================================================================

def test_soft_delete_and_restore(client: TestClient):
    """Soft-deleting sets is_deleted=true & is_active=false. Restore resets is_deleted=false."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    res_create = client.post("/api/v1/admin/users", headers=headers, json={
        "full_name": "Delete Target",
        "mobile_number": "9876506001",
        "email": "deltarget@agri.local",
        "password": "DeletePass123!",
        "roles": ["TRADER"]
    })
    user_id = res_create.json()["id"]

    # 1. Soft delete
    res_del = client.delete(f"/api/v1/admin/users/{user_id}", headers=headers)
    assert res_del.status_code == 200
    data_del = res_del.json()
    assert data_del["is_deleted"] is True
    assert data_del["is_active"] is False
    assert data_del["deleted_at"] is not None
    assert data_del["deleted_by"] is not None

    # Login fails
    login_res = client.post("/api/v1/auth/login", json={
        "identifier": "9876506001",
        "password": "DeletePass123!"
    })
    assert login_res.status_code == 401

    # 2. Restore user
    res_rest = client.post(f"/api/v1/admin/users/{user_id}/restore", headers=headers)
    assert res_rest.status_code == 200
    data_rest = res_rest.json()
    assert data_rest["is_deleted"] is False
    assert data_rest["deleted_at"] is None
    assert data_rest["deleted_by"] is None
    # Crucial: is_active remains False until explicitly activated
    assert data_rest["is_active"] is False

    # Reactivate
    client.patch(f"/api/v1/admin/users/{user_id}/status", headers=headers, json={"is_active": True})
    login_after_restore = client.post("/api/v1/auth/login", json={
        "identifier": "9876506001",
        "password": "DeletePass123!"
    })
    assert login_after_restore.status_code == 200


# ==============================================================================
# 7. Role Assignment & Removal Tests
# ==============================================================================

def test_assign_and_remove_roles(client: TestClient):
    """Assign additional roles without duplication, and remove specific roles."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    res_create = client.post("/api/v1/admin/users", headers=headers, json={
        "full_name": "Role Test User",
        "mobile_number": "9876507001",
        "email": "roletest@agri.local",
        "password": "RolePass123!",
        "roles": ["FARMER"]
    })
    user_id = res_create.json()["id"]

    # 1. Assign TRADER role
    res_assign = client.post(f"/api/v1/admin/users/{user_id}/roles", headers=headers, json={
        "roles": ["TRADER"]
    })
    assert res_assign.status_code == 200
    assert set(res_assign.json()["roles"]) == {"FARMER", "TRADER"}

    # 2. Re-assigning FARMER does not duplicate
    res_dup = client.post(f"/api/v1/admin/users/{user_id}/roles", headers=headers, json={
        "roles": ["FARMER"]
    })
    assert res_dup.status_code == 200
    assert set(res_dup.json()["roles"]) == {"FARMER", "TRADER"}

    # 3. Remove TRADER role
    res_rem = client.delete(f"/api/v1/admin/users/{user_id}/roles/TRADER", headers=headers)
    assert res_rem.status_code == 200
    assert res_rem.json()["roles"] == ["FARMER"]


# ==============================================================================
# 8. Immediate RBAC Effect Tests
# ==============================================================================

def test_immediate_rbac_effect_on_role_assignment_and_removal(client: TestClient):
    """Role assignment and removal immediately changes access without token re-issuance."""
    admin_token = get_admin_token(client)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create a Farmer
    res_create = client.post("/api/v1/admin/users", headers=admin_headers, json={
        "full_name": "Dynamic RBAC User",
        "mobile_number": "9876508001",
        "email": "dynamic@agri.local",
        "password": "DynamicPass123!",
        "roles": ["FARMER"]
    })
    user_id = res_create.json()["id"]

    # Login as this user
    login_res = client.post("/api/v1/auth/login", json={
        "identifier": "9876508001",
        "password": "DynamicPass123!"
    })
    user_token = login_res.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # Initial access to Super Admin endpoint fails -> 403
    res_admin1 = client.get("/api/v1/admin/rbac-test", headers=user_headers)
    assert res_admin1.status_code == 403

    # Admin promotes user to SUPER_ADMIN
    client.post(f"/api/v1/admin/users/{user_id}/roles", headers=admin_headers, json={
        "roles": ["SUPER_ADMIN"]
    })

    # Same access token immediately succeeds on Super Admin endpoint -> 200
    res_admin2 = client.get("/api/v1/admin/rbac-test", headers=user_headers)
    assert res_admin2.status_code == 200

    # Admin revokes SUPER_ADMIN role
    client.delete(f"/api/v1/admin/users/{user_id}/roles/SUPER_ADMIN", headers=admin_headers)

    # Same access token immediately gets 403 Forbidden
    res_admin3 = client.get("/api/v1/admin/rbac-test", headers=user_headers)
    assert res_admin3.status_code == 403


# ==============================================================================
# 9. Final Super Admin Protection Tests
# ==============================================================================

def test_last_active_super_admin_protection(client: TestClient):
    """System prevents deactivating, soft-deleting, or removing role from the only active SUPER_ADMIN."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    db = TestingSessionLocal()
    admin_user = UserRepository.get_by_mobile(db, "9999999999")
    admin_id = str(admin_user.id)
    active_count = UserRepository.count_active_super_admins(db)
    assert active_count == 1
    db.close()

    # Create a secondary admin to test target operations on non-self account
    res_sec = client.post("/api/v1/admin/users", headers=headers, json={
        "full_name": "Secondary Admin",
        "mobile_number": "9876509001",
        "email": "secadmin@agri.local",
        "password": "SecAdminPass123!",
        "roles": ["SUPER_ADMIN"]
    })
    sec_id = res_sec.json()["id"]

    # Deactivate original admin (self-action would be blocked by self-protection, but secondary admin can act on primary if > 1 admin)
    login_sec = client.post("/api/v1/auth/login", json={
        "identifier": "9876509001",
        "password": "SecAdminPass123!"
    })
    sec_token = login_sec.json()["access_token"]
    sec_headers = {"Authorization": f"Bearer {sec_token}"}

    # Secondary admin deactivates primary admin -> allowed since 2 admins exist
    res_deact1 = client.patch(f"/api/v1/admin/users/{admin_id}/status", headers=sec_headers, json={"is_active": False})
    assert res_deact1.status_code == 200

    # Now only 1 active Super Admin remains (secadmin). Attempting to remove SUPER_ADMIN from secadmin fails with 409
    # (Secadmin cannot remove own SUPER_ADMIN due to self protection & last admin check)
    res_rem = client.delete(f"/api/v1/admin/users/{sec_id}/roles/SUPER_ADMIN", headers=sec_headers)
    assert res_rem.status_code == 409

    # If primary admin reactivated, then we have 2 admins again
    client.patch(f"/api/v1/admin/users/{admin_id}/status", headers=sec_headers, json={"is_active": True})


# ==============================================================================
# 10. Self Protection Tests
# ==============================================================================

def test_self_protection_prevent_lockout(client: TestClient):
    """Super Admin cannot delete self, deactivate self, or remove own SUPER_ADMIN role."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    db = TestingSessionLocal()
    admin_user = UserRepository.get_by_mobile(db, "9999999999")
    admin_id = str(admin_user.id)
    db.close()

    # 1. Attempt self-deactivation -> 409
    res_deact = client.patch(f"/api/v1/admin/users/{admin_id}/status", headers=headers, json={"is_active": False})
    assert res_deact.status_code == 409
    assert "own account" in res_deact.json()["detail"].lower()

    # 2. Attempt self-deletion -> 409
    res_del = client.delete(f"/api/v1/admin/users/{admin_id}", headers=headers)
    assert res_del.status_code == 409
    assert "own account" in res_del.json()["detail"].lower()

    # 3. Attempt self-removal of SUPER_ADMIN role -> 409
    res_rem = client.delete(f"/api/v1/admin/users/{admin_id}/roles/SUPER_ADMIN", headers=headers)
    assert res_rem.status_code == 409
    assert "own account" in res_rem.json()["detail"].lower()


# ==============================================================================
# 11. Additional Edge Case Tests
# ==============================================================================

def test_remove_unassigned_or_invalid_role(client: TestClient):
    """Removing an unassigned role or invalid role returns 404."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    db = TestingSessionLocal()
    farmer = create_user_with_role(db, "Role Edge Farmer", "9876599001", "edge@agri.local", RoleEnum.FARMER.value)
    farmer_id = str(farmer.id)
    db.close()

    # Attempt to remove TRADER (not assigned) -> 404
    res_unassigned = client.delete(f"/api/v1/admin/users/{farmer_id}/roles/TRADER", headers=headers)
    assert res_unassigned.status_code == 404
    assert "not assigned" in res_unassigned.json()["detail"].lower()

    # Attempt to remove non-existent role -> 404
    res_nonexistent = client.delete(f"/api/v1/admin/users/{farmer_id}/roles/NOT_A_ROLE", headers=headers)
    assert res_nonexistent.status_code == 404


def test_assign_invalid_role_rejected(client: TestClient):
    """Assigning an invalid role name returns validation error."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    db = TestingSessionLocal()
    farmer = create_user_with_role(db, "Role Edge 2", "9876599002", "edge2@agri.local", RoleEnum.FARMER.value)
    farmer_id = str(farmer.id)
    db.close()

    res = client.post(f"/api/v1/admin/users/{farmer_id}/roles", headers=headers, json={"roles": ["INVALID_ROLE"]})
    assert res.status_code in (400, 422)


def test_list_deleted_users_filter(client: TestClient):
    """Filter by is_deleted=true specifically returns soft-deleted users."""
    token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    res_create = client.post("/api/v1/admin/users", headers=headers, json={
        "full_name": "Deleted List User",
        "mobile_number": "9876599003",
        "email": "deluser@agri.local",
        "password": "Password123!",
        "roles": ["DRIVER"]
    })
    user_id = res_create.json()["id"]

    # Soft-delete user
    client.delete(f"/api/v1/admin/users/{user_id}", headers=headers)

    # Query with is_deleted=true
    res_del_list = client.get("/api/v1/admin/users?is_deleted=true", headers=headers)
    assert res_del_list.status_code == 200
    items = res_del_list.json()["items"]
    assert any(u["id"] == user_id for u in items)
    assert all(u["is_deleted"] is True for u in items)
