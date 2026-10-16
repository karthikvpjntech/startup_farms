import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from app.models.enums import RoleEnum


def get_farmer_auth_headers(client: TestClient, mobile_number: str = "+919876543210") -> dict:
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Ramu Farmer",
            "mobile_number": mobile_number,
            "password": "FarmerPassword123!",
            "role": "FARMER"
        }
    )
    assert reg_resp.status_code in [200, 201]
    token = reg_resp.json()["access_token"]

    # Set up farmer profile
    headers = {"Authorization": f"Bearer {token}"}
    client.post(
        "/api/v1/farmer/profile",
        headers=headers,
        json={
            "village": "Alanganallur",
            "district": "Madurai",
            "state": "Tamil Nadu",
            "pincode": "625501"
        }
    )
    return headers


def get_customer_auth_headers(client: TestClient, mobile_number: str = "+919123456780") -> dict:
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Kavitha Buyer",
            "mobile_number": mobile_number,
            "password": "CustomerPassword123!",
            "role": "CUSTOMER"
        }
    )
    assert reg_resp.status_code in [200, 201]
    token = reg_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}



def test_create_and_list_farmer_selling_products(client: TestClient):
    headers = get_farmer_auth_headers(client, "+919876540001")

    # 1. Create Mango product
    payload = {
        "category": "FRUITS",
        "name": "Mango",
        "variety": "Panna",
        "description": "Naturally ripened sweet Panna mangoes straight from the orchard.",
        "primary_image": "/uploads/farm_products/mango_panna.jpg",
        "price": 120.00,
        "price_unit": "Kg",
        "unit": "Kg",
        "available_quantity": 100.00,
        "minimum_order_quantity": 2.00,
        "delivery_available": True,
        "cod_available": True,
        "online_payment_available": True,
        "direct_pickup_available": True,
        "additional_images": ["/uploads/farm_products/mango_panna_2.jpg"]
    }
    resp = client.post("/api/v1/farmer/products", headers=headers, json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Mango"
    assert data["variety"] == "Panna"
    assert Decimal(str(data["price"])) == Decimal("120.00")
    assert Decimal(str(data["available_quantity"])) == Decimal("100.00")
    assert len(data["images"]) >= 1

    prod_id = data["id"]

    # 2. Create Sapota product
    payload2 = {
        "category": "FRUITS",
        "name": "Sapota",
        "variety": "Cricket Ball",
        "description": "Fresh round sweet sapota fruits.",
        "primary_image": "/uploads/farm_products/sapota.jpg",
        "price": 60.00,
        "price_unit": "Kg",
        "unit": "Kg",
        "available_quantity": 50.00,
        "minimum_order_quantity": 1.00,
    }
    resp2 = client.post("/api/v1/farmer/products", headers=headers, json=payload2)
    assert resp2.status_code == 201

    # 3. List farmer products
    list_resp = client.get("/api/v1/farmer/products", headers=headers)
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] == 2
    assert len(list_data["items"]) == 2

    # 4. Check farmer dashboard stats
    stats_resp = client.get("/api/v1/farmer/products/stats", headers=headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_products"] == 2
    assert stats["active_products"] == 2
    assert stats["out_of_stock_products"] == 0


def test_public_search_and_filter_farm_products(client: TestClient):
    headers = get_farmer_auth_headers(client, "+919876540002")

    # Create Murungakkai & Pomegranate
    client.post(
        "/api/v1/farmer/products",
        headers=headers,
        json={
            "category": "VEGETABLES",
            "name": "Murungakkai",
            "variety": "PKM-1",
            "description": "Fresh green drumsticks from organic trees.",
            "primary_image": "/uploads/farm_products/murungakkai.jpg",
            "price": 40.00,
            "unit": "Bundle",
            "available_quantity": 30.00,
            "minimum_order_quantity": 1.00,
        }
    )

    client.post(
        "/api/v1/farmer/products",
        headers=headers,
        json={
            "category": "FRUITS",
            "name": "Mathulai",
            "variety": "Bhagwa",
            "description": "Rich red seeds sweet pomegranate.",
            "primary_image": "/uploads/farm_products/mathulai.jpg",
            "price": 180.00,
            "unit": "Kg",
            "available_quantity": 40.00,
            "minimum_order_quantity": 1.00,
        }
    )

    # 1. Search all public products
    res = client.get("/api/v1/farm-products")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 2

    # 2. Filter by category VEGETABLES
    veg_res = client.get("/api/v1/farm-products?category=VEGETABLES")
    assert veg_res.status_code == 200
    veg_data = veg_res.json()
    assert all(item["category"] == "VEGETABLES" for item in veg_data["items"])

    # 3. Search text "Drumstick" or "Murungakkai"
    search_res = client.get("/api/v1/farm-products?search=Murungakkai")
    assert search_res.status_code == 200
    assert search_res.json()["total"] >= 1


def test_cart_and_direct_purchase_flow(client: TestClient):
    farmer_headers = get_farmer_auth_headers(client, "+919876540003")
    customer_headers = get_customer_auth_headers(client, "+919123456789")

    # Create Coconut product
    create_res = client.post(
        "/api/v1/farmer/products",
        headers=farmer_headers,
        json={
            "category": "COCONUT",
            "name": "Coconut",
            "variety": "West Coast Tall",
            "description": "Fresh water-filled mature coconuts.",
            "primary_image": "/uploads/farm_products/coconut.jpg",
            "price": 30.00,
            "price_unit": "Piece",
            "unit": "Piece",
            "available_quantity": 50.00,
            "minimum_order_quantity": 2.00,
            "delivery_available": True,
            "cod_available": True,
            "direct_pickup_available": True
        }
    )
    assert create_res.status_code == 201
    prod = create_res.json()
    prod_id = prod["id"]

    # 1. Add to Customer Cart
    cart_add_res = client.post(
        "/api/v1/cart/items",
        headers=customer_headers,
        json={
            "farm_product_id": prod_id,
            "quantity": 5
        }
    )
    assert cart_add_res.status_code == 200
    cart_data = cart_add_res.json()
    assert cart_data["total_items_count"] == 5
    assert Decimal(str(cart_data["subtotal_amount"])) == Decimal("150.00")

    # 2. Instant Direct Buy Now Checkout (COD / Delivery)
    buy_now_res = client.post(
        "/api/v1/farm-products/buy-now",
        headers=customer_headers,
        json={
            "product_id": prod_id,
            "quantity": 10.00,
            "fulfillment_type": "FARMER_DELIVERY",
            "payment_method": "CASH_ON_DELIVERY",
            "delivery_contact_name": "Kavitha",
            "delivery_contact_phone": "+919123456789",
            "delivery_address": "12 Gandhi Road",
            "delivery_city": "Madurai",
            "delivery_pincode": "625001"
        }
    )
    assert buy_now_res.status_code == 201
    order = buy_now_res.json()
    assert order["status"] == "CONFIRMED"
    assert order["payment_status"] == "PENDING"
    assert Decimal(str(order["total_amount"])) == Decimal("300.00")

    # 3. Check inventory was deducted atomically (50 - 10 = 40)
    updated_prod_res = client.get(f"/api/v1/farm-products/{prod_id}")
    assert updated_prod_res.status_code == 200
    assert Decimal(str(updated_prod_res.json()["available_quantity"])) == Decimal("40.00")


def test_quick_stock_adjust_and_out_of_stock_transition(client: TestClient):
    headers = get_farmer_auth_headers(client, "+919876540004")

    # Create Lemon with 5 kg
    create_res = client.post(
        "/api/v1/farmer/products",
        headers=headers,
        json={
            "category": "FRUITS",
            "name": "Lemon",
            "variety": "Balaji",
            "description": "Juicy sour organic lemons.",
            "primary_image": "/uploads/farm_products/lemon.jpg",
            "price": 100.00,
            "unit": "Kg",
            "available_quantity": 5.00,
        }
    )
    prod_id = create_res.json()["id"]

    # 1. Update stock to 0 -> should automatically become OUT_OF_STOCK
    stock_res = client.patch(
        f"/api/v1/farmer/products/{prod_id}/stock",
        headers=headers,
        json={"available_quantity": 0.00}
    )
    assert stock_res.status_code == 200
    assert stock_res.json()["status"] == "OUT_OF_STOCK"
    assert stock_res.json()["is_out_of_stock"] is True

    # 2. Harvest fresh batch, update stock to 60 -> becomes ACTIVE
    restock_res = client.patch(
        f"/api/v1/farmer/products/{prod_id}/stock",
        headers=headers,
        json={"available_quantity": 60.00}
    )
    assert restock_res.status_code == 200
    assert restock_res.json()["status"] == "ACTIVE"
    assert restock_res.json()["is_out_of_stock"] is False
