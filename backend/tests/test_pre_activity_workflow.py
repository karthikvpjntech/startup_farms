import uuid
from decimal import Decimal
from datetime import date
import pytest
from fastapi.testclient import TestClient

from app.core.jwt import create_access_token
from app.core.security import get_password_hash
from app.models.enums import RoleEnum
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.repositories.farmer_profile_repository import FarmerProfileRepository
from app.repositories.farm_repository import FarmRepository
from app.repositories.crop_repository import CropRepository
from app.repositories.farm_crop_plan_repository import FarmCropPlanRepository
from app.seeds.crop_stages_seed import seed_crop_stages
from tests.conftest import TestingSessionLocal


def setup_farmer_with_onion_plan(db, name="Onion Farmer", mobile="9440000001", email="onion_f@agri.local"):
    """Helper creating farmer with Onion crop plan."""
    seed_crop_stages(db)
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
        profile_data={"village": "Perundurai", "district": "Erode"}
    )
    farm = FarmRepository.create(
        db=db,
        farmer_profile_id=profile.id,
        farm_code="FARM-ONION01",
        farm_data={
            "farm_name": "Kongu Onion Farm",
            "ownership_type": "OWNED",
            "total_land_area": Decimal("5.0"),
            "land_area_unit": "ACRE",
        },
        created_by=user.id
    )
    from app.models.crop import Crop
    onion_crop = db.query(Crop).filter(Crop.crop_name.ilike("%Onion%")).first()

    plan = FarmCropPlanRepository.create(
        db=db,
        plan_data={
            "farm_id": farm.id,
            "crop_id": onion_crop.id,
            "season": "RABI",
            "planned_start_date": date.today(),
            "planned_area": Decimal("2.0"),
            "land_area_unit": "ACRE",
        },
        created_by=user.id
    )
    token = create_access_token(str(user.id), ["FARMER"])
    return str(user.id), token, str(plan.id), str(onion_crop.id)


def test_crop_specific_stages_and_pre_activity_workflow(client: TestClient):
    """Verifies crop-specific stage seeding, pre-task planning with requirements, and 1-click ledger conversion."""
    db = TestingSessionLocal()
    user_id, token, plan_id, crop_id = setup_farmer_with_onion_plan(db)
    db.close()

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Start Cultivation Run without custom stages -> should auto-clone Onion's 8 stages
    res_start = client.post("/api/v1/crops/cultivations", headers=headers, json={
        "farm_crop_plan_id": plan_id,
        "sowing_date": str(date.today()),
        "maturity_days": 90,
    })
    assert res_start.status_code == 201
    cult_data = res_start.json()
    cultivation_id = cult_data["id"]
    stages = cult_data["stages"]

    # Verify 8 Onion stages seeded dynamically
    assert len(stages) == 8
    assert "உழவு" in stages[0]["stage_name"]
    stage_1_id = stages[0]["id"]

    # 2. Create Pre-Activity Plan on Stage 1 (Land Preparation)
    pre_task_payload = {
        "activity_name": "முதல் சால் உழவு & ரோட்டோவேட்டர்",
        "activity_type": "TILLAGE",
        "purpose": "மண் பொலபொலப்பு மற்றும் அடி உரம் கலக்குதல்",
        "machinery_mode": "RENTAL_TRACTOR",
        "machinery_details": {
            "machinery_type": "Tractor + Rotavator",
            "rental_hours": 3.0,
            "rental_rate_per_hour": 900.0,
            "total_machinery_cost": 2700.0,
        },
        "materials_details": [
            {
                "item_name": "எரு வண்டி வாடகை",
                "quantity": 2,
                "unit": "வண்டி",
                "unit_cost": 600.0,
                "total_cost": 1200.0,
            }
        ],
        "labor_details": {
            "estimated_workers": 2,
            "wage_per_head": 400.0,
            "total_labor_cost": 800.0,
        },
        "estimated_total_cost": 4700.0,
        "status": "PLANNED"
    }

    res_pre = client.post(f"/api/v1/stages/{stage_1_id}/pre-activities", headers=headers, json=pre_task_payload)
    assert res_pre.status_code == 201
    plan_data = res_pre.json()
    plan_id = plan_data["id"]
    assert plan_data["activity_name"] == "முதல் சால் உழவு & ரோட்டோவேட்டர்"
    assert plan_data["actual_converted"] is False
    assert float(plan_data["estimated_total_cost"]) == 4700.0

    # 3. List Pre-activities for this stage
    res_list = client.get(f"/api/v1/stages/{stage_1_id}/pre-activities", headers=headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1

    # 4. 1-Click Convert Pre-Activity Plan to Actual Expenses & Wages
    res_convert = client.post(
        f"/api/v1/pre-activities/{plan_id}/convert-to-expenses",
        headers=headers,
        json={"payment_mode": "CASH"}
    )
    assert res_convert.status_code == 200
    convert_data = res_convert.json()
    assert convert_data["expenses_created"] == 2  # Machinery (2700) + Material (1200)
    assert convert_data["worker_logs_created"] == 1  # Group labor (800)
    assert float(convert_data["total_logged_amount"]) == 4700.0

    # 5. Verify Cultivation Details now include the expenses and worker wages in the ledger
    res_detail = client.get(f"/api/v1/crops/cultivations/{cultivation_id}", headers=headers)
    assert res_detail.status_code == 200
    detail_data = res_detail.json()
    assert float(detail_data["total_expenses"]) == 4700.0
    assert float(detail_data["total_machinery_expenses"]) == 2700.0
    assert float(detail_data["total_material_expenses"]) == 1200.0
    assert float(detail_data["total_labor_wages"]) == 800.0
