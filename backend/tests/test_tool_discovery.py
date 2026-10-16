import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.core.jwt import create_access_token
from app.models.enums import RoleEnum, ToolInterestType, ToolInterestStatus
from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole
from app.models.farmer_profile import FarmerProfile
from app.models.tool_interest import ToolInterest, DiscoveredToolLocation
from app.services.tool_discovery_service import ToolDiscoveryService


def _create_authenticated_farmer(db, mobile="9876543299", email="farmer.tractor@agri.local"):
    farmer_role = db.query(Role).filter(Role.name == RoleEnum.FARMER.value).first()
    if not farmer_role:
        farmer_role = Role(name=RoleEnum.FARMER.value, description="Farmer Role")
        db.add(farmer_role)
        db.commit()

    user = User(
        full_name="Farmer Shivaraj",
        mobile_number=mobile,
        email=email,
        password_hash=get_password_hash("FarmerPass123!"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    user_role = UserRole(user_id=user.id, role_id=farmer_role.id)
    db.add(user_role)
    db.commit()

    profile = FarmerProfile(
        user_id=user.id,
        village="Mysuru Rural",
        district="Mysuru",
        state="Karnataka",
        pincode="570028",
        latitude=Decimal("12.295800"),
        longitude=Decimal("76.639400"),
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    token = create_access_token(user_id=str(user.id), roles=[RoleEnum.FARMER.value])
    headers = {"Authorization": f"Bearer {token}"}
    return user, profile, headers


def test_create_tool_interest_and_auto_discovery(client: TestClient, db_session):
    user, profile, headers = _create_authenticated_farmer(db_session, mobile="9845011111", email="shiva.tractor@test.local")

    payload = {
        "tool_name": "Tractor",
        "tool_type": "RENTAL",
        "required_location": "Mysuru",
        "specifications": "45-55 HP, 4WD with Rotavator",
        "geofence_radius_meters": 500,
        "search_radius_km": 25,
        "auto_discovery_enabled": True,
    }

    res = client.post("/api/v1/farmer/tool-interests", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()["data"]

    assert data["tool_name"] == "Tractor"
    assert data["tool_type"] == "RENTAL"
    assert data["required_location"] == "Mysuru"
    assert data["discovered_locations_count"] > 0
    assert len(data["discovered_locations"]) > 0

    first_vendor = data["discovered_locations"][0]
    assert "business_name" in first_vendor
    assert "latitude" in first_vendor
    assert "longitude" in first_vendor
    assert first_vendor["phone_number"] is not None


def test_list_and_get_tool_interests(client: TestClient, db_session):
    user, profile, headers = _create_authenticated_farmer(db_session, mobile="9845022222", email="shiva.list@test.local")

    # Create interest
    payload = {
        "tool_name": "Combine Harvester",
        "tool_type": "RENTAL",
        "required_location": "Mandya",
        "geofence_radius_meters": 600,
    }
    create_res = client.post("/api/v1/farmer/tool-interests", json=payload, headers=headers)
    assert create_res.status_code == 201
    interest_id = create_res.json()["data"]["id"]

    # List
    list_res = client.get("/api/v1/farmer/tool-interests", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()["data"]
    assert list_data["total"] >= 1
    assert any(item["id"] == interest_id for item in list_data["items"])

    # Get Single
    get_res = client.get(f"/api/v1/farmer/tool-interests/{interest_id}", headers=headers)
    assert get_res.status_code == 200
    get_data = get_res.json()["data"]
    assert get_data["id"] == interest_id
    assert get_data["tool_name"] == "Combine Harvester"
    assert get_data["required_location"] == "Mandya"


def test_proximity_check_geofence_alert_triggered(client: TestClient, db_session):
    """
    Simulates the farmer traveling and reaching within 500m of the discovered vendor.
    Verifies that the geofence engine generates the real-time proximity alert.
    """
    user, profile, headers = _create_authenticated_farmer(db_session, mobile="9845033333", email="shiva.geo@test.local")

    # Create Tractor demand in Mysuru
    create_res = client.post(
        "/api/v1/farmer/tool-interests",
        json={
            "tool_name": "Tractor",
            "tool_type": "RENTAL",
            "required_location": "Mysuru",
            "geofence_radius_meters": 500,
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    interest_data = create_res.json()["data"]
    first_vendor = interest_data["discovered_locations"][0]

    vendor_lat = first_vendor["latitude"]
    vendor_lng = first_vendor["longitude"]

    # Farmer is ~100m away from the vendor
    farmer_nearby_lat = vendor_lat + 0.0005
    farmer_nearby_lng = vendor_lng + 0.0005

    # Check Proximity
    prox_res = client.post(
        "/api/v1/farmer/tool-interests/check-proximity",
        json={
            "latitude": farmer_nearby_lat,
            "longitude": farmer_nearby_lng,
            "record_notification": True,
        },
        headers=headers,
    )
    assert prox_res.status_code == 200
    prox_data = prox_res.json()["data"]
    assert prox_data["nearby_alerts_count"] >= 1

    alert = prox_data["alerts"][0]
    assert alert["tool_name"] == "Tractor"
    assert alert["business_name"] == first_vendor["business_name"]
    assert alert["distance_meters"] <= 500
    assert "Tractor Service Available Near You" in alert["notification_title"]


def test_proximity_check_out_of_range(client: TestClient, db_session):
    """
    Simulates farmer being 25 km away: no proximity alert should trigger.
    """
    user, profile, headers = _create_authenticated_farmer(db_session, mobile="9845044444", email="shiva.far@test.local")

    client.post(
        "/api/v1/farmer/tool-interests",
        json={
            "tool_name": "Rotavator",
            "tool_type": "RENTAL",
            "required_location": "Mysuru",
            "geofence_radius_meters": 500,
        },
        headers=headers,
    )

    # Far coordinates (e.g. 15 km away)
    prox_res = client.post(
        "/api/v1/farmer/tool-interests/check-proximity",
        json={
            "latitude": 12.0000,
            "longitude": 76.2000,
        },
        headers=headers,
    )
    assert prox_res.status_code == 200
    assert prox_res.json()["data"]["nearby_alerts_count"] == 0


def test_refresh_discovery_and_delete(client: TestClient, db_session):
    user, profile, headers = _create_authenticated_farmer(db_session, mobile="9845055555", email="shiva.del@test.local")

    create_res = client.post(
        "/api/v1/farmer/tool-interests",
        json={
            "tool_name": "Power Sprayer",
            "tool_type": "RENTAL",
            "required_location": "Hassan",
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    interest_id = create_res.json()["data"]["id"]

    # Refresh
    ref_res = client.post(f"/api/v1/farmer/tool-interests/{interest_id}/refresh-discovery", headers=headers)
    assert ref_res.status_code == 200
    assert ref_res.json()["data"]["discovered_count"] > 0

    # Delete
    del_res = client.delete(f"/api/v1/farmer/tool-interests/{interest_id}", headers=headers)
    assert del_res.status_code == 200

    # Verify not in active list
    list_res = client.get("/api/v1/farmer/tool-interests", headers=headers)
    assert list_res.status_code == 200
    assert not any(item["id"] == interest_id for item in list_res.json()["data"]["items"])


def test_urea_uriya_fertilizer_demand_and_proximity_alert(client: TestClient, db_session):
    """
    Verifies that searching / registering Urea / Uriya automatically discovers
    fertilizer depots, IFFCO/KRIBHCO seva kendras, and triggers urea-specific proximity alerts.
    """
    user, profile, headers = _create_authenticated_farmer(db_session, mobile="9845066666", email="shiva.urea@test.local")

    create_res = client.post(
        "/api/v1/farmer/tool-interests",
        json={
            "tool_name": "Neem Coated Uriya (Urea)",
            "tool_type": "FERTILIZER",
            "required_location": "Mysuru",
            "specifications": "45kg Bag @ ₹266.50 Govt Subsidized MRP",
            "geofence_radius_meters": 500,
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    data = create_res.json()["data"]

    assert data["category"] == "FERTILIZERS"
    assert data["discovered_locations_count"] >= 1

    first_vendor = data["discovered_locations"][0]
    assert "Urea" in first_vendor["business_name"] or "Fertilizer" in first_vendor["business_name"]
    assert first_vendor["products_available"] is not None
    assert "Urea" in first_vendor["products_available"] or "₹266.50" in first_vendor["products_available"]

    # Trigger proximity
    prox_res = client.post(
        "/api/v1/farmer/tool-interests/check-proximity",
        json={
            "latitude": first_vendor["latitude"] + 0.0004,
            "longitude": first_vendor["longitude"] + 0.0004,
            "record_notification": True,
        },
        headers=headers,
    )
    assert prox_res.status_code == 200
    prox_data = prox_res.json()["data"]
    assert prox_data["nearby_alerts_count"] >= 1
    alert = prox_data["alerts"][0]
    assert "Fertilizer Trader" in alert["notification_title"] or "Uriya" in alert["notification_title"] or "Urea" in alert["notification_title"]


def test_certified_seeds_demand_discovery(client: TestClient, db_session):
    """
    Verifies that searching / registering Seeds (e.g. Certified Paddy Seeds)
    discovers NSC seed agencies, hybrid seed traders, and returns germ rate and lot info.
    """
    user, profile, headers = _create_authenticated_farmer(db_session, mobile="9845077777", email="shiva.seeds@test.local")

    create_res = client.post(
        "/api/v1/farmer/tool-interests",
        json={
            "tool_name": "Certified Paddy Seeds (Aman / Ponni)",
            "tool_type": "SEEDS",
            "required_location": "Mandya",
            "specifications": "10kg Bag, High Germination certified lot",
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    data = create_res.json()["data"]

    assert data["category"] == "SEEDS"
    assert data["discovered_locations_count"] >= 1
    first_vendor = data["discovered_locations"][0]
    assert "Seed" in first_vendor["business_name"] or "Seeds" in first_vendor["category"]

