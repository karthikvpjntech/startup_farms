import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base
from app.core.security import get_password_hash, verify_password
from app.models.enums import RoleEnum
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.seeds.roles_seed import seed_roles
from app.seeds.super_admin_seed import seed_super_admin


@pytest.fixture
def db_session():
    """Create a clean in-memory database session for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# 1. Test Argon2id Password Hashing
def test_argon2id_password_hashing():
    raw_password = "SecureSuperAdminPass123!"
    password_hash = get_password_hash(raw_password)

    # Verify hash starts with $argon2id$
    assert password_hash.startswith("$argon2id$")

    # Verify correct password
    assert verify_password(raw_password, password_hash) is True

    # Verify incorrect password
    assert verify_password("WrongPassword!", password_hash) is False

    # Verify empty/invalid input
    assert verify_password("", password_hash) is False
    assert verify_password(raw_password, "") is False

    with pytest.raises(ValueError, match="Password cannot be empty"):
        get_password_hash("")


# 2. Test 1: Fresh Database Seed (Roles + Super Admin Creation + Role Assignment)
def test_seed_fresh_database(db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.SUPER_ADMIN_NAME", "Root Admin")
    monkeypatch.setattr("app.core.config.settings.SUPER_ADMIN_MOBILE", "9999999999")
    monkeypatch.setattr("app.core.config.settings.SUPER_ADMIN_EMAIL", "admin@agrismart.local")
    monkeypatch.setattr("app.core.config.settings.SUPER_ADMIN_PASSWORD", "SuperSecurePass999")

    # 1. Seed Roles
    roles_res = seed_roles(db_session)
    assert len(roles_res["created"]) == len(RoleEnum)
    assert len(roles_res["existing"]) == 0

    # Verify all system roles exist in DB
    all_roles = RoleRepository.get_all(db_session)
    role_names = {r.name for r in all_roles}
    assert role_names == {r.value for r in RoleEnum}

    # 2. Seed Super Admin
    admin_res = seed_super_admin(db_session)
    assert admin_res["created"] is True

    # Verify Super Admin in DB
    admin = UserRepository.get_by_mobile(db_session, "9999999999")
    assert admin is not None
    assert admin.full_name == "Root Admin"
    assert admin.email == "admin@agrismart.local"
    assert admin.is_active is True
    assert admin.is_deleted is False

    # Verify password hash
    assert verify_password("SuperSecurePass999", admin.password_hash) is True

    # Verify SUPER_ADMIN role assignment
    admins = UserRepository.get_users_by_role_name(db_session, RoleEnum.SUPER_ADMIN.value)
    assert len(admins) == 1
    assert admins[0].id == admin.id


# 3. Test 2: Idempotency & Re-running Seed
def test_seed_idempotency(db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.SUPER_ADMIN_NAME", "Root Admin")
    monkeypatch.setattr("app.core.config.settings.SUPER_ADMIN_MOBILE", "9999999999")
    monkeypatch.setattr("app.core.config.settings.SUPER_ADMIN_EMAIL", "admin@agrismart.local")
    monkeypatch.setattr("app.core.config.settings.SUPER_ADMIN_PASSWORD", "SuperSecurePass999")

    # First run
    seed_roles(db_session)
    seed_super_admin(db_session)

    initial_role_count = RoleRepository.count(db_session)
    initial_user_count = UserRepository.count(db_session)

    # Second run
    roles_res_2 = seed_roles(db_session)
    admin_res_2 = seed_super_admin(db_session)

    assert len(roles_res_2["created"]) == 0
    assert len(roles_res_2["existing"]) == len(RoleEnum)
    assert admin_res_2["created"] is False
    assert "already exists" in admin_res_2["message"]

    # Ensure no duplicates were created
    assert RoleRepository.count(db_session) == initial_role_count
    assert UserRepository.count(db_session) == initial_user_count


# 4. Test 3: Missing SUPER_ADMIN_PASSWORD Fails Safely
def test_seed_missing_password_fails_safely(db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.SUPER_ADMIN_PASSWORD", None)

    with pytest.raises(ValueError, match="SUPER_ADMIN_PASSWORD is not set"):
        seed_super_admin(db_session, password_override=None)


# 5. Test 4: Existing User With Matching Mobile Gets Assigned SUPER_ADMIN
def test_seed_existing_user_assigned_role(db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.SUPER_ADMIN_MOBILE", "8888888888")
    monkeypatch.setattr("app.core.config.settings.SUPER_ADMIN_PASSWORD", "SomePassword123")

    # Pre-create user without SUPER_ADMIN role
    seed_roles(db_session)
    user = UserRepository.create(
        db_session,
        full_name="Existing User",
        mobile_number="8888888888",
        email="existing@example.com",
        password_hash=get_password_hash("OldPass"),
        is_active=True
    )

    # Run seed
    res = seed_super_admin(db_session)
    assert res["created"] is False
    assert "Assigned SUPER_ADMIN role" in res["message"]

    # Verify role was assigned
    admins = UserRepository.get_users_by_role_name(db_session, RoleEnum.SUPER_ADMIN.value)
    assert len(admins) == 1
    assert admins[0].id == user.id
