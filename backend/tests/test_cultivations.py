import uuid
from decimal import Decimal
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient

from app.core.jwt import create_access_token
from app.core.security import get_password_hash
from app.models.enums import RoleEnum, CropCategory, LandAreaUnitEnum, ExpenseCategory, PaymentMode
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.repositories.farmer_profile_repository import FarmerProfileRepository
from app.repositories.farm_repository import FarmRepository
from app.repositories.crop_repository import CropRepository
from app.repositories.farm_crop_plan_repository import FarmCropPlanRepository
from tests.conftest import TestingSessionLocal


def setup_farmer_with_plan(db, name="Cultivation Farmer", mobile="9400000001", email="cult_f@agri.local") -> tuple[str, str, str]:
    """Helper returning (farmer_user_id, farmer_token, farm_crop_plan_id)."""
    roles = [RoleRepository.get_by_name(db, RoleEnum.FARMER.value)]
    user = UserRepository.create_with_roles(
        db=db,
        full_name=name,
        mobile_number=mobile,
        password_hash=get_password_hash("Password123!"),
        email=email,
        roles=roles,
        is_active=True
    )
    profile = FarmerProfileRepository.create(
        db=db,
        user_id=user.id,
        profile_data={"village": "Thanjavur", "district": "Thanjavur"}
    )
    farm = FarmRepository.create(
        db=db,
        farmer_profile_id=profile.id,
        farm_code="FARM-CULT01",
        farm_data={
            "farm_name": "Delta Green Farm",
            "ownership_type": "OWNED",
            "total_land_area": Decimal("10.0"),
            "land_area_unit": "ACRE",
        },
        created_by=user.id
    )
    crop = CropRepository.create(
        db=db,
        crop_code="CROP-PADDY1",
        crop_data={"crop_name": "Ponni Paddy", "crop_category": "CEREAL"},
        created_by=user.id
    )
    plan = FarmCropPlanRepository.create(
        db=db,
        plan_data={
            "farm_id": farm.id,
            "crop_id": crop.id,
            "season": "KHARIF",
            "planned_start_date": date.today(),
            "planned_area": Decimal("5.0"),
            "land_area_unit": "ACRE",
        },
        created_by=user.id
    )
    token = create_access_token(str(user.id), ["FARMER"])
    return str(user.id), token, str(plan.id)


def test_cultivation_lifecycle_and_expense_engine(client: TestClient):
    """End-to-end verification of cultivation run instantiation, 5-stage progression, and itemized expenses."""
    db = TestingSessionLocal()
    user_id, token, plan_id = setup_farmer_with_plan(db)
    db.close()

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Start Cultivation Run -> 201
    today = date.today()
    res_start = client.post("/api/v1/crops/cultivations", headers=headers, json={
        "farm_crop_plan_id": plan_id,
        "sowing_date": str(today),
        "maturity_days": 120,
    })
    assert res_start.status_code == 201
    cult_data = res_start.json()
    cultivation_id = cult_data["id"]
    assert cult_data["current_stage_order"] == 1
    assert len(cult_data["stages"]) == 5

    # Verify stages sequence and initial status
    stages = cult_data["stages"]
    assert stages[0]["stage_order"] == 1
    assert stages[0]["status"] == "IN_PROGRESS"
    assert stages[1]["stage_order"] == 2
    assert stages[1]["status"] == "PENDING"
    stage_1_id = stages[0]["id"]
    stage_2_id = stages[1]["id"]

    # 2. Add Labor Expense to Stage 1
    res_exp1 = client.post(f"/api/v1/crops/stages/{stage_1_id}/expenses", headers=headers, json={
        "expense_category": "LABOR",
        "title": "Tractor Driver & Land Preparation Labor",
        "amount": 3500.0,
        "payment_mode": "CASH",
        "worker_count": 2,
        "per_head_wage": 1750.0,
    })
    assert res_exp1.status_code == 201
    exp1_data = res_exp1.json()
    exp1_id = exp1_data["id"]
    assert float(exp1_data["amount"]) == 3500.0

    # 3. Add Input Material Expense to Stage 1
    res_exp2 = client.post(f"/api/v1/crops/stages/{stage_1_id}/expenses", headers=headers, json={
        "expense_category": "INPUT_MATERIAL",
        "title": "Organic Manure & Bio-fertilizer",
        "amount": 4200.0,
        "payment_mode": "UPI",
    })
    assert res_exp2.status_code == 201

    # 4. Advance Stage 1 to Stage 2 (complete-and-next)
    res_adv = client.post(f"/api/v1/crops/stages/{stage_1_id}/complete-and-next", headers=headers)
    assert res_adv.status_code == 200
    adv_data = res_adv.json()
    assert adv_data["current_stage_order"] == 2

    # Verify stage 1 is COMPLETED and stage 2 is IN_PROGRESS
    res_stages = client.get(f"/api/v1/crops/cultivations/{cultivation_id}/stages", headers=headers)
    assert res_stages.status_code == 200
    updated_stages = res_stages.json()
    assert updated_stages[0]["status"] == "COMPLETED"
    assert updated_stages[1]["status"] == "IN_PROGRESS"

    # 5. Soft-delete an expense and verify 6s undo restore
    res_del_exp = client.delete(f"/api/v1/crops/expenses/{exp1_id}", headers=headers)
    assert res_del_exp.status_code == 200
    assert res_del_exp.json()["is_deleted"] is True

    # Check listing of stage expenses excludes soft-deleted
    res_list_exp = client.get(f"/api/v1/crops/stages/{stage_1_id}/expenses", headers=headers)
    assert res_list_exp.status_code == 200
    assert len(res_list_exp.json()) == 1  # only exp2 remains

    # Restore expense (undo action)
    res_restore_exp = client.post(f"/api/v1/crops/expenses/{exp1_id}/restore", headers=headers)
    assert res_restore_exp.status_code == 200
    assert res_restore_exp.json()["is_deleted"] is False

    # Check listing now includes restored expense
    res_list_exp_restored = client.get(f"/api/v1/crops/stages/{stage_1_id}/expenses", headers=headers)
    assert res_list_exp_restored.status_code == 200
    assert len(res_list_exp_restored.json()) == 2

    # 6. Cultivation detail returns aggregate total expenses
    res_detail = client.get(f"/api/v1/crops/cultivations/{cultivation_id}", headers=headers)
    assert res_detail.status_code == 200
    detail_data = res_detail.json()
    assert float(detail_data["total_expenses"]) == 7700.0  # 3500 + 4200


def test_harvest_yield_and_net_result_calculation(client: TestClient):
    """Verifies harvest recording, gross revenue, net result (surplus/deficit) calculation."""
    db = TestingSessionLocal()
    user_id, token, plan_id = setup_farmer_with_plan(db, name="Harvest Farmer", mobile="9400000002", email="harvest_f@agri.local")
    db.close()

    headers = {"Authorization": f"Bearer {token}"}

    # Start cultivation
    res_start = client.post("/api/v1/crops/cultivations", headers=headers, json={
        "farm_crop_plan_id": plan_id,
        "sowing_date": str(date.today()),
        "maturity_days": 90,
    })
    assert res_start.status_code == 201
    cult_id = res_start.json()["id"]
    stage_1_id = res_start.json()["stages"][0]["id"]

    # Log expense: ₹5,000
    client.post(f"/api/v1/crops/stages/{stage_1_id}/expenses", headers=headers, json={
        "expense_category": "INPUT_MATERIAL",
        "title": "Seed Bulbs",
        "amount": 5000.0,
        "payment_mode": "CASH",
    })

    # Record Harvest: 100 bags @ ₹2000/bag = ₹2,00,000 Gross Revenue
    res_harvest = client.patch(f"/api/v1/crops/cultivations/{cult_id}/harvest-yield", headers=headers, json={
        "yield_quantity": 100.0,
        "yield_unit": "Bags / மூட்டை",
        "selling_price_per_unit": 2000.0,
        "gross_revenue": 200000.0,
    })
    assert res_harvest.status_code == 200
    data = res_harvest.json()
    assert float(data["gross_revenue"]) == 200000.0
    assert float(data["total_expenses"]) == 5000.0
    assert float(data["net_result"]) == 195000.0
    assert data["net_result_status"] == "SURPLUS"


def test_previous_year_comparison_real_database_only(client: TestClient):
    """Verifies comparison returns 'No previous-year data available' when no records exist without generating fake numbers."""
    db = TestingSessionLocal()
    user_id, token, plan_id = setup_farmer_with_plan(db, name="Comp Farmer", mobile="9400000003", email="comp_f@agri.local")
    db.close()

    headers = {"Authorization": f"Bearer {token}"}

    # Query comparison before creating any runs
    res_comp = client.get("/api/v1/crops/cultivations/comparison", headers=headers)
    assert res_comp.status_code == 200
    comp_data = res_comp.json()
    assert comp_data["has_previous_data"] is False
    assert comp_data["message"] == "No previous-year data available."
    assert len(comp_data["breakdown_metrics"]) == 0

