from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns expected structure."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Agri-Smart Ecosystem API"
    assert data["status"] == "running"


def test_health_check_endpoint():
    """Test the health check endpoint returns 200 and UP status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Agri-Smart API is running"
    assert data["data"]["status"] == "UP"


def test_swagger_docs():
    """Test the OpenAPI /docs endpoint is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
