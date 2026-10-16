import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.enums import RoleEnum, LivestockSellingModel, LivestockStatus
from app.models.user import User
from app.models.farmer_profile import FarmerProfile
from app.models.farm import Farm
from app.seeds.livestock_seed import seed_livestock_master
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
            village="Kangayam Village",
            district="Tiruppur",
            state="Tamil Nadu"
        )
        db.add(farmer_prof)
        db.flush()

        farm = Farm(
            id=uuid.uuid4(),
            farmer_profile_id=farmer_prof.id,
            farm_name=f"{name}'s Dairy & Poultry Farm",
            farm_code=f"FARM-{mobile[-4:]}",
            ownership_type="OWNED",
            total_land_area=Decimal("15.5"),
            land_area_unit="ACRE",
            village="Kangayam Village",
            district="Tiruppur",
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



def test_livestock_master_categories_and_breeds(client: TestClient, db_session: Session):
    seed_livestock_master(db_session)

    # 1. Public list categories
    res = client.get("/api/v1/livestock/categories")
    assert res.status_code == 200
    categories = res.json()
    assert len(categories) >= 10
    cat_codes = [c["code"] for c in categories]
    assert "GOAT" in cat_codes
    assert "CHICKEN" in cat_codes
    assert "COW" in cat_codes

    goat_cat = next(c for c in categories if c["code"] == "GOAT")
    assert goat_cat["name_ta"] == "ஆடு"
    assert len(goat_cat["breeds"]) >= 5

    # 2. Public list breeds by category
    res_b = client.get(f"/api/v1/livestock/breeds?category_id={goat_cat['id']}")
    assert res_b.status_code == 200
    breeds = res_b.json()
    breed_names = [b["name"] for b in breeds]
    assert "Kanni Adu" in breed_names
    assert "Salem Black" in breed_names


def test_farmer_livestock_crud_and_selling_models(client: TestClient, db_session: Session):
    seed_livestock_master(db_session)
    farmer = create_user_with_role(db_session, "9876543210", "Ramasamy Farmer", "FARMER")
    headers = get_auth_headers(client, "9876543210")

    cats_res = client.get("/api/v1/livestock/categories")
    goat_cat = next(c for c in cats_res.json() if c["code"] == "GOAT")
    kanni_breed = next(b for b in goat_cat["breeds"] if b["name"] == "Kanni Adu")
    farm_id = str(farmer.farmer_profile.farms[0].id)

    # 1. Create Model A (Individual Goat with Tag, Weight, DOB)
    goat_payload = {
        "farm_id": farm_id,
        "category_id": goat_cat["id"],
        "breed_id": kanni_breed["id"],
        "name": "Prize Kanni Breeding Buck",
        "tag_number": "TAG-GT-2026-001",
        "selling_model": "INDIVIDUAL",
        "gender": "MALE",
        "age": 18,
        "age_unit": "MONTHS",
        "weight": 32.5,
        "weight_unit": "KG",
        "health_status": "HEALTHY",
        "vaccination_status": "UP_TO_DATE",
        "price": 18500.00,
        "price_type": "PER_UNIT",
        "available_quantity": 1,
        "images": [
            {"image_url": "https://images.unsplash.com/photo-goat-main.jpg", "image_type": "MAIN", "is_primary": True},
            {"image_url": "https://images.unsplash.com/photo-goat-side.jpg", "image_type": "SIDE", "is_primary": False}
        ]
    }
    create_res = client.post("/api/v1/farmer/livestock", json=goat_payload, headers=headers)
    assert create_res.status_code == 201
    goat_data = create_res.json()
    assert goat_data["livestock_code"].startswith("LS-")
    assert goat_data["status"] == "DRAFT"
    assert goat_data["available_quantity"] == 1
    assert len(goat_data["images"]) == 2
    goat_id = goat_data["id"]

    # 2. Create Model B (Quantity-based Country Chickens)
    chicken_cat = next(c for c in cats_res.json() if c["code"] == "CHICKEN")
    country_breed = next(b for b in chicken_cat["breeds"] if b["name"] == "Country Chicken")
    chicken_payload = {
        "farm_id": farm_id,
        "category_id": chicken_cat["id"],
        "breed_id": country_breed["id"],
        "name": "Organic Free-Range Country Chickens (8-Week Batch)",
        "selling_model": "QUANTITY",
        "gender": "MIXED_HERD",
        "age": 8,
        "age_unit": "WEEKS",
        "weight": 1.1,
        "weight_unit": "KG",
        "health_status": "HEALTHY",
        "vaccination_status": "UP_TO_DATE",
        "price": 450.00,
        "price_type": "PER_UNIT",
        "available_quantity": 50,
        "minimum_order_quantity": 2,
        "maximum_order_quantity": 25,
        "images": [
            {"image_url": "https://images.unsplash.com/photo-chickens.jpg", "image_type": "MAIN", "is_primary": True}
        ]
    }
    create_chk_res = client.post("/api/v1/farmer/livestock", json=chicken_payload, headers=headers)
    assert create_chk_res.status_code == 201
    chk_data = create_chk_res.json()
    assert chk_data["available_quantity"] == 50
    chk_id = chk_data["id"]

    # 3. Publish both to marketplace
    pub_res1 = client.post(f"/api/v1/farmer/livestock/{goat_id}/publish", headers=headers)
    assert pub_res1.status_code == 200
    assert pub_res1.json()["status"] == "PUBLISHED"

    pub_res2 = client.post(f"/api/v1/farmer/livestock/{chk_id}/publish", headers=headers)
    assert pub_res2.status_code == 200
    assert pub_res2.json()["status"] == "PUBLISHED"

    # 4. Check farmer dashboard stats
    stats_res = client.get("/api/v1/farmer/livestock/stats", headers=headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_livestock"] == 2
    assert stats["available_count"] == 2


def test_public_marketplace_search_and_filter(client: TestClient, db_session: Session):
    seed_livestock_master(db_session)
    farmer = create_user_with_role(db_session, "9876543211", "Muthu Farmer", "FARMER")
    headers = get_auth_headers(client, "9876543211")

    cats_res = client.get("/api/v1/livestock/categories")
    cow_cat = next(c for c in cats_res.json() if c["code"] == "COW")
    kangayam_breed = next(b for b in cow_cat["breeds"] if b["name"] == "Kangayam")
    farm_id = str(farmer.farmer_profile.farms[0].id)

    client.post(
        "/api/v1/farmer/livestock",
        json={
            "farm_id": farm_id,
            "category_id": cow_cat["id"],
            "breed_id": kangayam_breed["id"],
            "name": "Pure Kangayam Cow with Calf",
            "tag_number": "TAG-COW-101",
            "selling_model": "INDIVIDUAL",
            "gender": "FEMALE",
            "price": 65000.00,
            "available_quantity": 1,
        },
        headers=headers
    )
    # Get created item and publish it
    f_list = client.get("/api/v1/farmer/livestock", headers=headers).json()
    cow_id = f_list["items"][0]["id"]
    client.post(f"/api/v1/farmer/livestock/{cow_id}/publish", headers=headers)

    # 1. Search public marketplace
    res_search = client.get("/api/v1/marketplace/livestock?search=Kangayam")
    assert res_search.status_code == 200
    items = res_search.json()["items"]
    assert len(items) == 1
    assert items[0]["name"] == "Pure Kangayam Cow with Calf"

    # 2. Filter by category
    res_cat = client.get("/api/v1/marketplace/livestock?category_code=COW")
    assert res_cat.status_code == 200
    assert len(res_cat.json()["items"]) == 1

    # 3. Filter by price mismatch -> 0 results
    res_price = client.get("/api/v1/marketplace/livestock?max_price=50000")
    assert res_price.status_code == 200
    assert len(res_price.json()["items"]) == 0


def test_cart_checkout_and_concurrency_protection(client: TestClient, db_session: Session):
    seed_livestock_master(db_session)
    farmer = create_user_with_role(db_session, "9876543212", "Velu Farmer", "FARMER")
    customer_a = create_user_with_role(db_session, "9876543213", "Buyer Anbu", "CUSTOMER")
    customer_b = create_user_with_role(db_session, "9876543214", "Buyer Bala", "CUSTOMER")

    farmer_headers = get_auth_headers(client, "9876543212")
    cust_a_headers = get_auth_headers(client, "9876543213")
    cust_b_headers = get_auth_headers(client, "9876543214")

    cats_res = client.get("/api/v1/livestock/categories")
    chicken_cat = next(c for c in cats_res.json() if c["code"] == "CHICKEN")
    farm_id = str(farmer.farmer_profile.farms[0].id)

    # Farmer creates limited batch of 10 Chickens
    chk_res = client.post(
        "/api/v1/farmer/livestock",
        json={
            "farm_id": farm_id,
            "category_id": chicken_cat["id"],
            "name": "Kadaknath Heritage Batch (10 birds remaining)",
            "selling_model": "QUANTITY",
            "gender": "MIXED_HERD",
            "price": 800.00,
            "available_quantity": 10,
        },
        headers=farmer_headers
    )
    chk_id = chk_res.json()["id"]
    client.post(f"/api/v1/farmer/livestock/{chk_id}/publish", headers=farmer_headers)

    # 1. Customer A adds 6 chickens to cart
    add_a = client.post("/api/v1/cart/items", json={"livestock_id": chk_id, "quantity": 6}, headers=cust_a_headers)
    assert add_a.status_code == 200
    cart_a = add_a.json()
    assert cart_a["total_items_count"] == 6
    assert Decimal(str(cart_a["subtotal_amount"])) == Decimal("4800.00")

    # 2. Customer A checks out successfully
    checkout_payload_a = {
        "delivery_type": "FARM_PICKUP",
        "delivery_contact_name": "Buyer Anbu",
        "delivery_contact_phone": "9876543213",
        "payment_method": "UPI"
    }
    chk_out_a = client.post("/api/v1/marketplace/orders/checkout", json=checkout_payload_a, headers=cust_a_headers)
    assert chk_out_a.status_code == 201
    orders_a = chk_out_a.json()
    assert len(orders_a) == 1
    order_a = orders_a[0]
    assert Decimal(str(order_a["total_amount"])) == Decimal("4800.00")
    assert order_a["total_items_count"] == 6
    order_a_id = order_a["id"]

    # 3. CRITICAL CONCURRENCY CHECK: Customer B attempts to purchase 6 birds (only 4 remain)
    # Direct Buy Now / Checkout must fail with HTTP 409 Conflict
    checkout_payload_b = {
        "livestock_id": chk_id,
        "quantity": 6,
        "delivery_type": "FARM_PICKUP",
        "delivery_contact_name": "Buyer Bala",
        "delivery_contact_phone": "9876543214",
        "payment_method": "UPI"
    }
    chk_out_b = client.post("/api/v1/marketplace/orders/buy-now", json=checkout_payload_b, headers=cust_b_headers)
    assert chk_out_b.status_code == 409
    assert "Insufficient inventory" in chk_out_b.json()["detail"]

    # 4. Customer B purchases remaining 4 birds -> succeeds and marks batch SOLD (available_quantity = 0)
    checkout_payload_b["quantity"] = 4
    chk_out_b_valid = client.post("/api/v1/marketplace/orders/buy-now", json=checkout_payload_b, headers=cust_b_headers)
    assert chk_out_b_valid.status_code == 201

    # Verify inventory is 0 and status is SOLD in database
    chk_detail = client.get(f"/api/v1/farmer/livestock/{chk_id}", headers=farmer_headers).json()
    assert chk_detail["available_quantity"] == 0
    assert chk_detail["status"] == "SOLD"

    # 5. Customer A verifies payment
    pay_res = client.post(
        f"/api/v1/marketplace/orders/{order_a_id}/verify-payment",
        json={"transaction_reference": "UPI-REF-2026-99887766"},
        headers=cust_a_headers
    )
    assert pay_res.status_code == 200
    assert pay_res.json()["payment_status"] == "PAID"
    assert pay_res.json()["status"] == "CONFIRMED"

    # 6. Farmer accepts and fulfills order to DELIVERED
    f_orders = client.get("/api/v1/farmer/orders", headers=farmer_headers).json()
    assert f_orders["total"] == 2

    client.patch(
        f"/api/v1/farmer/orders/{order_a_id}/status",
        json={"status": "DELIVERED", "notes": "Handed over at farm"},
        headers=farmer_headers
    )

    # 7. Customer A submits verified review
    rev_res = client.post(
        f"/api/v1/marketplace/orders/{order_a_id}/review",
        json={
            "livestock_id": chk_id,
            "rating": 5,
            "review_text": "Excellent quality healthy Kadaknath birds! Highly recommended."
        },
        headers=cust_a_headers
    )
    assert rev_res.status_code == 201
    assert rev_res.json()["rating"] == 5
    assert rev_res.json()["is_verified_purchase"] is True


def test_super_admin_marketplace_dashboard(client: TestClient, db_session: Session):
    admin_headers = get_auth_headers(client, "9999999999", password="SuperAdminPass123!")
    res = client.get("/api/v1/admin/marketplace/metrics", headers=admin_headers)
    assert res.status_code == 200
    metrics = res.json()
    assert "total_listings" in metrics
    assert "total_orders" in metrics
    assert "total_sales_volume" in metrics


def test_livestock_search_typo_and_distance_filtering(client: TestClient, db_session: Session):
    seed_livestock_master(db_session)
    farmer = create_user_with_role(db_session, "9876543299", "Velu Poultry Farmer", "FARMER")
    farmer_headers = get_auth_headers(client, "9876543299")

    # Set farm GPS coordinates
    farm = farmer.farmer_profile.farms[0]
    farm.latitude = Decimal("11.0055")
    farm.longitude = Decimal("77.5611")
    farm.village = "Kangayam"
    farm.district = "Tiruppur"
    db_session.commit()

    cats_res = client.get("/api/v1/livestock/categories")
    chk_cat = next(c for c in cats_res.json() if c["code"] == "CHICKEN")

    # Create Country Chicken batch listing
    chk_payload = {
        "farm_id": str(farm.id),
        "category_id": chk_cat["id"],
        "name": "Organic Free-Range Country Chicken (Nati Koli)",
        "selling_model": "QUANTITY",
        "gender": "UNSPECIFIED",
        "price": 450.00,
        "price_type": "PER_UNIT",
        "available_quantity": 25,
        "minimum_order_quantity": 1,
        "health_status": "HEALTHY",
        "vaccination_status": "UP_TO_DATE",
        "images": [{"image_url": "https://images.unsplash.com/chicken.jpg", "image_type": "MAIN", "is_primary": True}]
    }
    c_res = client.post("/api/v1/farmer/livestock", json=chk_payload, headers=farmer_headers)
    assert c_res.status_code == 201
    chk_id = c_res.json()["id"]

    # Publish listing
    client.post(f"/api/v1/farmer/livestock/{chk_id}/publish", headers=farmer_headers)

    # 1. Test search with typo "chiken"
    search_typo = client.get("/api/v1/marketplace/livestock?search=chiken")
    assert search_typo.status_code == 200
    items = search_typo.json()["items"]
    assert len(items) >= 1
    found = next((i for i in items if i["id"] == chk_id), None)
    assert found is not None
    assert "Country Chicken" in found["name"]

    # 2. Test buyer near 10 km (User coordinates at 11.0100, 77.5650, approx 0.7 km away)
    near_res = client.get("/api/v1/marketplace/livestock?search=chiken&latitude=11.0100&longitude=77.5650&max_distance_km=10")
    assert near_res.status_code == 200
    near_items = near_res.json()["items"]
    assert len(near_items) >= 1
    near_found = next((i for i in near_items if i["id"] == chk_id), None)
    assert near_found is not None
    assert near_found["distance_km"] is not None
    assert near_found["distance_km"] <= 10.0
    assert near_found["is_near_you"] is True

    # 3. Test buyer far away (> 10 km e.g. Chennai 13.0827, 80.2707) with max_distance_km=10
    far_res = client.get("/api/v1/marketplace/livestock?search=chiken&latitude=13.0827&longitude=80.2707&max_distance_km=10")
    assert far_res.status_code == 200
    far_items = far_res.json()["items"]
    far_found = next((i for i in far_items if i["id"] == chk_id), None)
    assert far_found is None  # filtered out because distance > 10 km

    # 4. Test price filter and sort
    price_res = client.get("/api/v1/marketplace/livestock?search=chicken&min_price=400&max_price=500&sort_by=price_asc")
    assert price_res.status_code == 200
    p_items = price_res.json()["items"]
    p_found = next((i for i in p_items if i["id"] == chk_id), None)
    assert float(p_found["price"]) == 450.0


