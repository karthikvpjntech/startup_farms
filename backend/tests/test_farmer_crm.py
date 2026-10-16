import uuid
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.models.enums import RoleEnum, CropCategory, LandAreaUnitEnum, OwnershipTypeEnum, PaymentMethod, BillType
from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole
from app.models.farmer_profile import FarmerProfile
from app.models.farm import Farm
from app.models.crop import Crop
from app.models.farm_crop_plan import FarmCropPlan
from app.models.cultivation import CultivationRun, CultivationStage
from app.models.supplier import Supplier
from app.core.jwt import create_access_token


def _create_authenticated_farmer(db, mobile="9876543210", email="farmer@agri.local"):
    """Helper fixture to create a verified FARMER user and return auth headers & models."""
    farmer_role = db.query(Role).filter(Role.name == RoleEnum.FARMER.value).first()
    if not farmer_role:
        farmer_role = Role(name=RoleEnum.FARMER.value, description="Farmer Role")
        db.add(farmer_role)
        db.commit()

    user = User(
        full_name="Farmer Ramesh",
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
        village="Erode",
        district="Erode",
        state="Tamil Nadu",
        pincode="638001",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    farm = Farm(
        farmer_profile_id=profile.id,
        farm_name="Green Field",
        farm_code="FARM-GF01",
        ownership_type=OwnershipTypeEnum.OWNED.value,
        total_land_area=Decimal("3.00"),
        land_area_unit=LandAreaUnitEnum.ACRE.value,
        village="Erode",
        district="Erode",
        state="Tamil Nadu",
        pincode="638001",
    )
    db.add(farm)
    db.commit()
    db.refresh(farm)

    crop = Crop(
        crop_name="Onion",
        crop_code="ONION-01",
        crop_category=CropCategory.VEGETABLE.value,
        created_by=user.id,
    )
    db.add(crop)
    db.commit()
    db.refresh(crop)

    plan = FarmCropPlan(
        farm_id=farm.id,
        crop_id=crop.id,
        season="Rabi",
        planned_start_date=date.today(),
        planned_area=Decimal("2.00"),
        land_area_unit="ACRE",
        created_by=user.id,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    # Instantiate Cultivation Run
    run = CultivationRun(
        farm_crop_plan_id=plan.id,
        farmer_profile_id=profile.id,
        sowing_date=date.today(),
        maturity_days=90,
        target_harvest_date=date.today(),
        current_stage_order=1,
        farming_method="CONVENTIONAL",
        land_area=Decimal("2.00"),
        land_area_unit="ACRE",
        created_by=user.id,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Add default stages
    stage1 = CultivationStage(
        cultivation_id=run.id,
        stage_order=1,
        stage_name="Land Preparation",
        status="IN_PROGRESS",
        start_date=date.today(),
        created_by=user.id,
    )
    stage2 = CultivationStage(
        cultivation_id=run.id,
        stage_order=2,
        stage_name="Seeding",
        status="PENDING",
        created_by=user.id,
    )
    db.add_all([stage1, stage2])
    db.commit()
    db.refresh(stage1)
    db.refresh(stage2)

    # Supplier
    supplier = Supplier(
        supplier_code="SUP-ABC01",
        supplier_name="ABC Agro Supplier",
        phone_number="9842112233",
        address_line1="Main Road",
        village_city="Erode",
        district="Erode",
        state="Tamil Nadu",
        pincode="638001",
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)

    token = create_access_token(
        user_id=str(user.id), roles=[RoleEnum.FARMER.value]
    )
    headers = {"Authorization": f"Bearer {token}"}

    return {
        "user": user,
        "profile": profile,
        "farm": farm,
        "crop": crop,
        "plan": plan,
        "run": run,
        "stage1": stage1,
        "stage2": stage2,
        "supplier": supplier,
        "headers": headers,
    }


def test_worker_master_lifecycle(client: TestClient, db_session):
    """Test Worker Master registration, duplicate prevention, and search."""
    ctx = _create_authenticated_farmer(db_session)
    headers = ctx["headers"]

    # 1. Register new Worker
    worker_payload = {
        "full_name": "Ramesh Laborer",
        "mobile_number": "9898989898",
        "gender": "MALE",
        "skill": "LAND_PREPARATION",
        "daily_salary": "800.00",
        "village": "Perundurai",
        "payment_preference": "UPI",
    }
    resp = client.post("/api/v1/farmer/crm/workers", json=worker_payload, headers=headers)
    assert resp.status_code == 201
    worker_data = resp.json()
    assert worker_data["full_name"] == "Ramesh Laborer"
    assert worker_data["worker_code"].startswith("WKR-")
    assert worker_data["daily_salary"] == "800.00"
    worker_id = worker_data["id"]

    # 2. Register same worker again -> should reuse existing record without duplicate
    resp_dup = client.post("/api/v1/farmer/crm/workers", json=worker_payload, headers=headers)
    assert resp_dup.status_code == 201
    assert resp_dup.json()["id"] == worker_id

    # 3. List & Search workers
    resp_list = client.get("/api/v1/farmer/crm/workers?search=Ramesh", headers=headers)
    assert resp_list.status_code == 200
    assert resp_list.json()["total"] == 1
    assert resp_list.json()["items"][0]["mobile_number"] in ("9898989898", "+919898989898")

    # 4. Update worker
    resp_up = client.put(
        f"/api/v1/farmer/crm/workers/{worker_id}",
        json={"daily_salary": "850.00", "skill": "GENERAL_LABOR"},
        headers=headers,
    )
    assert resp_up.status_code == 200
    assert resp_up.json()["daily_salary"] == "850.00"


def test_machine_master_lifecycle(client: TestClient, db_session):
    """Test Machine Master registration and search."""
    ctx = _create_authenticated_farmer(db_session)
    headers = ctx["headers"]

    machine_payload = {
        "machine_name": "Mahindra 575 DI Tractor",
        "machine_type": "TRACTOR",
        "ownership_type": "OWNED",
        "rate_per_hour": "1000.00",
        "rate_per_day": "7000.00",
        "operator_included": True,
    }
    resp = client.post("/api/v1/farmer/crm/machines", json=machine_payload, headers=headers)
    assert resp.status_code == 201
    machine_data = resp.json()
    assert machine_data["machine_code"].startswith("MCH-")
    assert machine_data["machine_type"] == "TRACTOR"
    assert machine_data["rate_per_hour"] == "1000.00"

    resp_list = client.get("/api/v1/farmer/crm/machines", headers=headers)
    assert resp_list.status_code == 200
    assert resp_list.json()["total"] == 1


def test_full_cultivation_stage_operation_and_billing(client: TestClient, db_session):
    """
    Test Land Preparation operation:
    - Worker assignment & Attendance with wage calculation
    - Machine assignment & usage calculation
    - Consolidated Stage Bill generation
    - Payment checkout with UPI
    - SMS Notification log creation
    """
    ctx = _create_authenticated_farmer(db_session)
    headers = ctx["headers"]
    stage1 = ctx["stage1"]

    # 1. Register 2 Workers in Master
    w1 = client.post(
        "/api/v1/farmer/crm/workers",
        json={"full_name": "Ramesh", "mobile_number": "9811111111", "daily_salary": "800.00", "skill": "LAND_PREPARATION"},
        headers=headers,
    ).json()

    w2 = client.post(
        "/api/v1/farmer/crm/workers",
        json={"full_name": "Suresh", "mobile_number": "9822222222", "daily_salary": "700.00", "skill": "LAND_PREPARATION"},
        headers=headers,
    ).json()

    # 2. Register Machine
    m1 = client.post(
        "/api/v1/farmer/crm/machines",
        json={"machine_name": "Tractor", "machine_type": "TRACTOR", "rate_per_hour": "1000.00"},
        headers=headers,
    ).json()

    # 3. Log Worker Attendance: Ramesh (2 days = ₹1,600), Suresh (2 days = ₹1,400)
    att1 = client.post(
        f"/api/v1/farmer/crm/stages/{stage1.id}/attendance",
        json={"worker_id": w1["id"], "working_days": "2.00", "start_time": "08:00 AM", "end_time": "05:00 PM"},
        headers=headers,
    )
    assert att1.status_code == 201
    assert att1.json()["calculated_amount"] == "1600.00"

    att2 = client.post(
        f"/api/v1/farmer/crm/stages/{stage1.id}/attendance",
        json={"worker_id": w2["id"], "working_days": "2.00"},
        headers=headers,
    )
    assert att2.status_code == 201
    assert att2.json()["calculated_amount"] == "1400.00"

    # 4. Log Machine Usage: Tractor 2.5 hours @ ₹1000 = ₹2,500
    mach_use = client.post(
        f"/api/v1/farmer/crm/stages/{stage1.id}/machines",
        json={"machine_id": m1["id"], "hours_used": "2.50"},
        headers=headers,
    )
    assert mach_use.status_code == 201
    assert mach_use.json()["total_cost"] == "2500.00"

    # 5. Generate Consolidated Stage Bill
    # Total = ₹1600 + ₹1400 + ₹2500 = ₹5,500
    gen_bill_resp = client.post(
        "/api/v1/farmer/crm/bills/generate-stage-bill",
        json={"stage_id": str(stage1.id)},
        headers=headers,
    )
    assert gen_bill_resp.status_code == 201
    bill_data = gen_bill_resp.json()
    assert bill_data["total_amount"] == "5500.00"
    assert bill_data["paid_amount"] == "0.00"
    assert bill_data["pending_amount"] == "5500.00"
    assert bill_data["status"] == "PENDING"
    assert len(bill_data["items"]) == 3
    bill_id = bill_data["id"]

    # 6. Payment Checkout (UPI)
    pay_resp = client.post(
        "/api/v1/farmer/crm/payments",
        json={
            "bill_id": bill_id,
            "amount": "5500.00",
            "payment_method": "UPI",
            "transaction_reference": "UPI9876543210REF",
            "send_sms_notification": True,
        },
        headers=headers,
    )
    assert pay_resp.status_code == 201
    pay_data = pay_resp.json()
    assert pay_data["amount"] == "5500.00"
    assert pay_data["payment_method"] == "UPI"
    assert pay_data["status"] == "PAID"

    # 7. Verify Bill status is now fully PAID
    bill_check = client.get(f"/api/v1/farmer/crm/bills/{bill_id}", headers=headers)
    assert bill_check.json()["status"] == "PAID"
    assert bill_check.json()["pending_amount"] == "0.00"

    # 8. Verify Worker Attendance payment status is now updated to PAID
    att_list = client.get(f"/api/v1/farmer/crm/stages/{stage1.id}/attendance", headers=headers)
    assert att_list.json()[0]["payment_status"] == "PAID"

    # 9. Verify SMS Notification log was created
    sms_logs = client.get("/api/v1/farmer/crm/notifications", headers=headers)
    assert sms_logs.status_code == 200
    assert sms_logs.json()["total"] >= 1
    assert "PAID" in sms_logs.json()["items"][0]["message_body"]


def test_material_purchase_and_logistics(client: TestClient, db_session):
    """Test material purchasing from supplier and post-harvest logistics."""
    ctx = _create_authenticated_farmer(db_session)
    headers = ctx["headers"]
    supplier = ctx["supplier"]
    run = ctx["run"]
    farm = ctx["farm"]

    # 1. Purchase Fertilizer (100 KG @ ₹120/KG = ₹12,000)
    pur_resp = client.post(
        "/api/v1/farmer/crm/purchases",
        json={
            "supplier_id": str(supplier.id),
            "cultivation_id": str(run.id),
            "material_category": "FERTILIZER",
            "material_name": "Complex Fertilizer 100KG",
            "quantity": "100.00",
            "unit": "KG",
            "unit_rate": "120.00",
        },
        headers=headers,
    )
    assert pur_resp.status_code == 201
    pur_data = pur_resp.json()
    assert pur_data["subtotal"] == "12000.00"
    assert pur_data["total_amount"] == "12000.00"

    # 2. Record Logistics Dispatch (Transport 100 Bags Onion to Mandi)
    log_resp = client.post(
        "/api/v1/farmer/crm/logistics",
        json={
            "cultivation_id": str(run.id),
            "farm_id": str(farm.id),
            "harvest_location": "Green Field Farm, Erode",
            "destination": "Koyambedu Wholesale Market, Chennai",
            "vehicle_number": "TN-33-AB-1234",
            "driver_name": "Murugan",
            "driver_contact": "9876500000",
            "quantity_transported": "5000.00",
            "quantity_unit": "KG",
            "transport_cost": "6000.00",
            "loading_cost": "500.00",
            "unloading_cost": "500.00",
        },
        headers=headers,
    )
    assert log_resp.status_code == 201
    log_data = log_resp.json()
    assert log_data["total_logistics_cost"] == "7000.00"
    assert log_data["status"] == "PLANNED"


def test_crm_dashboard_summary_and_reports(client: TestClient, db_session):
    """Test CRM summary KPIs, Cultivation Detail CRM record, and Reports."""
    ctx = _create_authenticated_farmer(db_session)
    headers = ctx["headers"]
    run = ctx["run"]

    # 1. Check CRM Dashboard Summary
    dash_resp = client.get("/api/v1/farmer/crm/dashboard-summary", headers=headers)
    assert dash_resp.status_code == 200
    summary = dash_resp.json()
    assert summary["total_farms"] == 1
    assert summary["active_crop_plans"] == 1
    assert summary["active_cultivations"] == 1
    assert summary["current_crop_stage"] is not None

    # 2. Check Cultivation CRM Detail Record
    detail_resp = client.get(f"/api/v1/farmer/crm/cultivations/{run.id}/crm-detail", headers=headers)
    assert detail_resp.status_code == 200
    crm_rec = detail_resp.json()
    assert crm_rec["crop_name"] == "Onion"
    assert len(crm_rec["stages"]) >= 2
    assert len(crm_rec["timeline_events"]) >= 1

    # 3. Check Reports
    rep_crop = client.get("/api/v1/farmer/crm/reports/crop-cost", headers=headers)
    assert rep_crop.status_code == 200
    assert len(rep_crop.json()) >= 1

    rep_worker = client.get("/api/v1/farmer/crm/reports/worker-payments", headers=headers)
    assert rep_worker.status_code == 200

    rep_supplier = client.get("/api/v1/farmer/crm/reports/supplier-purchases", headers=headers)
    assert rep_supplier.status_code == 200

    rep_expense = client.get("/api/v1/farmer/crm/reports/farm-expenses", headers=headers)
    assert rep_expense.status_code == 200


def test_worker_attendance_future_date_validation_and_salary_math(client: TestClient, db_session):
    """Verifies that future attendance dates are rejected, and backend calculates (working_days * daily_salary) + overtime."""
    ctx = _create_authenticated_farmer(db_session)
    headers = ctx["headers"]
    stage = ctx["stage1"]

    # 1. Register Worker
    w_res = client.post(
        "/api/v1/farmer/crm/workers",
        json={
            "full_name": "Velu",
            "mobile_number": "9876541111",
            "gender": "MALE",
            "skill": "GENERAL_LABOR",
            "daily_salary": "500.00",
        },
        headers=headers,
    )
    assert w_res.status_code == 201
    worker_id = w_res.json()["id"]

    # 2. Attempt future attendance -> MUST be rejected with HTTP 422 or 400
    future_date = date.today() + timedelta(days=3)
    future_res = client.post(
        f"/api/v1/farmer/crm/stages/{stage.id}/attendance",
        json={
            "worker_id": worker_id,
            "work_date": str(future_date),
            "working_days": "1.00",
            "daily_salary": "500.00",
        },
        headers=headers,
    )
    assert future_res.status_code in (400, 422)

    # 3. Log valid attendance today -> 2.5 days @ ₹500/day + ₹100 overtime = ₹1350
    valid_res = client.post(
        f"/api/v1/farmer/crm/stages/{stage.id}/attendance",
        json={
            "worker_id": worker_id,
            "work_date": str(date.today()),
            "working_days": "2.50",
            "daily_salary": "500.00",
            "overtime_amount": "100.00",
        },
        headers=headers,
    )
    assert valid_res.status_code == 201
    att_data = valid_res.json()
    assert att_data["calculated_amount"] == "1350.00"
    assert att_data["payment_status"] == "PENDING"

    # 4. Check worker payment report: earned=1350, paid=0, pending=1350
    rep_res = client.get("/api/v1/farmer/crm/reports/worker-payments", headers=headers)
    assert rep_res.status_code == 200
    items = [i for i in rep_res.json() if i["worker_id"] == worker_id]
    assert len(items) == 1
    assert float(items[0]["total_salary"]) == 1350.0
    assert float(items[0]["paid_amount"]) == 0.0
    assert float(items[0]["pending_amount"]) == 1350.0


def test_cultivation_cost_summary_with_plan_id_and_empty_cultivation(client: TestClient, db_session):
    """Verifies that cost summary works seamlessly with both CultivationRun.id and FarmCropPlan.id."""
    ctx = _create_authenticated_farmer(db_session)
    headers = ctx["headers"]
    run = ctx["run"]
    plan = ctx["plan"]

    # 1. Query cost summary with CultivationRun ID
    cost_by_run = client.get(f"/api/v1/farmer/crm/cultivations/{run.id}/cost-summary", headers=headers)
    assert cost_by_run.status_code == 200
    data_run = cost_by_run.json()
    assert data_run["crop_name"] == "Onion"
    assert "total_cultivation_cost" in data_run

    # 2. Query cost summary with FarmCropPlan ID (that has active cultivation run)
    cost_by_plan = client.get(f"/api/v1/farmer/crm/cultivations/{plan.id}/cost-summary", headers=headers)
    assert cost_by_plan.status_code == 200
    data_plan = cost_by_plan.json()
    assert data_plan["crop_name"] == "Onion"
    assert data_plan["cultivation_id"] == str(run.id)

    # 3. Create a brand new FarmCropPlan WITHOUT creating any CultivationRun
    from app.models.farm_crop_plan import FarmCropPlan
    from app.models.enums import CropSeasonEnum
    new_plan = FarmCropPlan(
        id=uuid.uuid4(),
        farm_id=ctx["farm"].id,
        crop_id=ctx["crop"].id,
        season="KHARIF",
        planned_start_date=date.today(),
        planned_area=Decimal("3.50"),
        land_area_unit="ACRE",
        is_active=True,
        is_deleted=False,
        created_by=ctx["user"].id,
    )
    db_session.add(new_plan)
    db_session.commit()

    # 4. Query cost summary for new plan with no cultivation run -> should return 200 and zeroed costs
    new_plan_cost = client.get(f"/api/v1/farmer/crm/cultivations/{new_plan.id}/cost-summary", headers=headers)
    assert new_plan_cost.status_code == 200
    new_cost_data = new_plan_cost.json()
    assert new_cost_data["crop_name"] == "Onion"
    assert float(new_cost_data["total_cultivation_cost"]) == 0.0
    assert float(new_cost_data["land_area"]) == 3.50
    assert len(new_cost_data["stages"]) == 0

    # 5. Query CRM detail for new plan with no cultivation run -> should return 200 with PLANNED status
    new_plan_detail = client.get(f"/api/v1/farmer/crm/cultivations/{new_plan.id}/crm-detail", headers=headers)
    assert new_plan_detail.status_code == 200
    new_detail_data = new_plan_detail.json()
    assert new_detail_data["status"] == "PLANNED"
    assert float(new_detail_data["total_cost"]) == 0.0


