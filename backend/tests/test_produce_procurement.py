import uuid
from datetime import date, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import RoleEnum
from app.models.user import User
from app.models.crop import Crop
from app.models.farmer_profile import FarmerProfile
from app.models.farm import Farm
from app.models.farm_crop_plan import FarmCropPlan
from app.models.cultivation import CultivationRun
from app.core.security import get_password_hash


def create_user_with_role(db: Session, mobile: str, name: str, role_name: str) -> User:
    from app.repositories.user_repository import UserRepository
    from app.repositories.role_repository import RoleRepository

    role = RoleRepository.get_by_name(db, role_name)
    if not role:
        role = RoleRepository.create(db, name=role_name, description=f"{role_name} Role", is_active=True)

    user = UserRepository.create_with_roles(
        db=db,
        full_name=name,
        mobile_number=mobile,
        password_hash=get_password_hash("Password123!"),
        email=f"{mobile}@test.com",
        roles=[role],
        is_active=True
    )

    if role_name == "FARMER":
        farmer_prof = FarmerProfile(
            id=uuid.uuid4(),
            user_id=user.id,
            village="Perundurai Village",
            district="Erode",
            state="Tamil Nadu"
        )
        db.add(farmer_prof)
        db.flush()

        farm = Farm(
            id=uuid.uuid4(),
            farmer_profile_id=farmer_prof.id,
            farm_name=f"{name}'s Organic Farm",
            farm_code=f"FARM-{mobile[-4:]}",
            ownership_type="OWNED",
            total_land_area=Decimal("10.0"),
            land_area_unit="ACRE",
            village="Perundurai Village",
            district="Erode",
            state="Tamil Nadu",
            is_active=True,
            is_deleted=False
        )
        db.add(farm)
        db.commit()

    return user


def get_auth_headers(client: TestClient, identifier: str, password: str = "Password123!") -> dict:
    resp = client.post("/api/v1/auth/login", json={"identifier": identifier, "password": password})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_produce_procurement_workflow(client: TestClient, db_session: Session):
    # 1. Setup Farmer, Customer/Buyer, and Crop with Cultivation
    farmer = create_user_with_role(db_session, "9876543201", "Murugan Farmer", "FARMER")
    customer = create_user_with_role(db_session, "9876543202", "Anand Trader", "CUSTOMER")

    farmer_prof = db_session.query(FarmerProfile).filter_by(user_id=farmer.id).first()
    farm = db_session.query(Farm).filter_by(farmer_profile_id=farmer_prof.id).first()

    crop = Crop(
        id=uuid.uuid4(),
        crop_name="Turmeric",
        crop_name_local="மஞ்சள்",
        crop_code="CROP-TURM",
        crop_category="SPICE",
        is_active=True,
        is_deleted=False
    )
    db_session.add(crop)
    db_session.flush()

    plan = FarmCropPlan(
        id=uuid.uuid4(),
        farm_id=farm.id,
        crop_id=crop.id,
        season="KHARIF",
        planned_start_date=date.today() - timedelta(days=200),
        planned_end_date=date.today() + timedelta(days=70),
        planned_area=Decimal("5.0"),
        land_area_unit="ACRE",
        created_by=farmer.id,
        is_active=True,
        is_deleted=False
    )
    db_session.add(plan)
    db_session.flush()

    cultivation = CultivationRun(
        id=uuid.uuid4(),
        farmer_profile_id=farmer_prof.id,
        farm_crop_plan_id=plan.id,
        sowing_date=date.today() - timedelta(days=200),
        target_harvest_date=date.today() + timedelta(days=70),
        maturity_days=270,
        current_stage_order=5,
        yield_quantity=Decimal("2500.00"),
        yield_unit="kg",
        selling_price_per_unit=Decimal("85.00"),
        gross_revenue=Decimal("212500.00"),
        is_active=True,
        is_deleted=False
    )
    db_session.add(cultivation)
    db_session.commit()

    farmer_headers = get_auth_headers(client, "9876543201")
    customer_headers = get_auth_headers(client, "9876543202")

    # 2. Public Produce Discovery
    res = client.get("/api/v1/produce-procurement/available")
    assert res.status_code == 200
    available = res.json()
    assert len(available) >= 1
    item = next(i for i in available if i["crop_id"] == str(crop.id))
    assert item["crop_name"] == "Turmeric"
    assert item["farmer_name"] == "Murugan Farmer"
    assert float(item["unit_price"]) == 85.0

    # 2b. Public Harvest Alerts & Subscriptions
    alerts_res = client.get("/api/v1/produce-procurement/harvest-alerts")
    assert alerts_res.status_code == 200
    assert len(alerts_res.json()) >= 1

    sub_res = client.post(
        "/api/v1/produce-procurement/subscribe-alerts",
        json={
            "name": "Karthik Buyer",
            "mobile_number": "9876543299",
            "email": "karthik@buyer.test",
            "crops_interested": ["Nel / Paddy", "Vengayam / Onion", "Kadalai / Groundnut"],
            "preferred_quantity_type": "WHOLESALE"
        }
    )
    assert sub_res.status_code == 200
    assert sub_res.json()["success"] is True

    # 3. Customer Creates Produce Procurement Requisition
    req_payload = {
        "crop_id": str(crop.id),
        "farmer_profile_id": str(farmer_prof.id),
        "farm_id": str(farm.id),
        "cultivation_id": str(cultivation.id),
        "quantity": 500,
        "unit": "kg",
        "required_date": str(date.today() + timedelta(days=10)),
        "delivery_location": "No 12, APMC Mandi Yard, Erode",
        "delivery_city": "Erode",
        "delivery_pincode": "638001",
        "contact_name": "Anand Trader",
        "contact_phone": "9876543202",
        "notes": "Premium quality grade A turmeric rhizomes"
    }
    create_res = client.post("/api/v1/produce-procurement", json=req_payload, headers=customer_headers)
    assert create_res.status_code == 201
    proc_data = create_res.json()
    proc_id = proc_data["id"]
    assert proc_data["status"] == "PENDING"
    assert float(proc_data["total_amount"]) == 42500.0  # 500 * 85
    assert proc_data["request_code"].startswith("PR-")

    # 4. Customer Views My Requests
    my_res = client.get("/api/v1/produce-procurement/my-requests", headers=customer_headers)
    assert my_res.status_code == 200
    assert my_res.json()["total"] >= 1

    # 5. Farmer Views Received Requests
    farmer_res = client.get("/api/v1/produce-procurement/farmer-requests", headers=farmer_headers)
    assert farmer_res.status_code == 200
    assert farmer_res.json()["total"] >= 1

    # 6. Farmer Confirms Request (sends pickup location & WhatsApp / SMS confirmation)
    confirm_res = client.post(
        f"/api/v1/produce-procurement/{proc_id}/confirm",
        json={
            "pickup_location": "Murugan Organic Farm, Gate 2, Perundurai Village, Erode",
            "pickup_instructions": "Bring burlap sacks. Farm open 7 AM - 6 PM.",
            "send_whatsapp": True,
            "send_sms": True
        },
        headers=farmer_headers
    )
    assert confirm_res.status_code == 200
    confirm_data = confirm_res.json()
    assert confirm_data["status"] == "FARMER_CONFIRMED"
    assert "Perundurai" in confirm_data["pickup_location"]
    assert "maps" in confirm_data["google_maps_url"]
    assert "wa.me" in confirm_data["whatsapp_url"]
    assert "கொள்முதல் உறுதிப்படுத்தல்" in confirm_data["whatsapp_message_preview"]

    # 7. Settle Payment
    payment_payload = {
        "payment_method": "UPI",
        "payment_reference": "UPI/12345678/PROD"
    }
    pay_res = client.post(
        f"/api/v1/produce-procurement/{proc_id}/pay",
        json=payment_payload,
        headers=customer_headers
    )
    assert pay_res.status_code == 200
    assert pay_res.json()["status"] == "CONFIRMED"
    assert pay_res.json()["payment_status"] == "PAID"

    # 8. Logistics Progress: OUT_FOR_DELIVERY
    dispatch_payload = {
        "status": "OUT_FOR_DELIVERY",
        "driver_name": "Selvam",
        "driver_contact": "9876500000",
        "vehicle_number": "TN 33 AB 1234",
        "tracking_notes": "Dispatched via Erode Agri Freight"
    }
    dispatch_res = client.patch(
        f"/api/v1/produce-procurement/{proc_id}/delivery",
        json=dispatch_payload,
        headers=customer_headers
    )
    assert dispatch_res.status_code == 200
    assert dispatch_res.json()["status"] == "OUT_FOR_DELIVERY"
    assert dispatch_res.json()["driver_name"] == "Selvam"

    assert pay_res.json()["payment_status"] == "PAID"
    assert pay_res.json()["payment_reference"] == "UPI/12345678/PROD"
