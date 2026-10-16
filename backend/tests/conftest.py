import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.seeds.roles_seed import seed_roles
from app.seeds.super_admin_seed import seed_super_admin

# Unified in-memory SQLite database with StaticPool for test isolation
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Setup clean tables and seed default roles and Super Admin before each test."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    seed_roles(db)
    seed_super_admin(db, password_override="SuperAdminPass123!")
    db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
