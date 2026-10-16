import uuid
from decimal import Decimal
from datetime import date
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import RoleEnum, MarketplaceOrderStatus
from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole
from app.models.farmer_profile import FarmerProfile
from app.models.marketplace_order import MarketplaceOrder, MarketplaceOrderItem
from app.core.security import get_password_hash
from app.core.jwt import create_access_token


class TestShipmentsAndTransport:
    @pytest.fixture
    def test_data(self, db_session: Session):
        # 1. Farmer
        farmer_role = db_session.query(Role).filter(Role.name == RoleEnum.FARMER.value).first()
        farmer = User(
            email="farmer_logistics@example.com",
            mobile_number="9876543210",
            full_name="Ramasamy Gounder",
            password_hash=get_password_hash("FarmerPass123!"),
            is_active=True,
        )
        db_session.add(farmer)
        db_session.flush()

        db_session.add(UserRole(user_id=farmer.id, role_id=farmer_role.id))
        farmer_profile = FarmerProfile(
            user_id=farmer.id,
            village="Pollachi",
            district="Coimbatore",
            state="Tamil Nadu",
            pincode="642001",
        )
        db_session.add(farmer_profile)
        db_session.flush()

        # 2. Customer
        customer_role = db_session.query(Role).filter(Role.name == RoleEnum.CUSTOMER.value).first()
        customer = User(
            email="customer_logistics@example.com",
            mobile_number="9876543211",
            full_name="Karthik Mohan",
            password_hash=get_password_hash("CustomerPass123!"),
            is_active=True,
        )
        db_session.add(customer)
        db_session.flush()
        db_session.add(UserRole(user_id=customer.id, role_id=customer_role.id))

        # 3. Driver
        driver_role = db_session.query(Role).filter(Role.name == RoleEnum.DRIVER.value).first()
        driver = User(
            email="driver_logistics@example.com",
            mobile_number="9876543212",
            full_name="Velu Driver",
            password_hash=get_password_hash("DriverPass123!"),
            is_active=True,
        )
        db_session.add(driver)
        db_session.flush()
        db_session.add(UserRole(user_id=driver.id, role_id=driver_role.id))

        # 4. Super Admin
        super_admin_role = db_session.query(Role).filter(Role.name == RoleEnum.SUPER_ADMIN.value).first()
        super_admin = User(
            email="superadmin_logistics@example.com",
            mobile_number="9876543213",
            full_name="Super Admin User",
            password_hash=get_password_hash("AdminPass123!"),
            is_active=True,
        )
        db_session.add(super_admin)
        db_session.flush()
        db_session.add(UserRole(user_id=super_admin.id, role_id=super_admin_role.id))

        # 5. Order
        order = MarketplaceOrder(
            order_number="ORD-20261006-0001",
            customer_id=customer.id,
            farmer_profile_id=farmer_profile.id,
            total_items_count=2,
            subtotal_amount=Decimal("1500.00"),
            delivery_charge=Decimal("100.00"),
            total_amount=Decimal("1600.00"),
            status=MarketplaceOrderStatus.CONFIRMED.value,
            payment_status="PAID",
            delivery_type="LOGISTICS_PARTNER",
            delivery_address="42, Cross Cut Road, Gandhipuram",
            delivery_city="Coimbatore",
            delivery_pincode="641012",
            delivery_contact_name="Karthik Mohan",
            delivery_contact_phone="9876543211",
        )
        db_session.add(order)
        db_session.commit()

        # Auth Tokens
        farmer_token = create_access_token(user_id=str(farmer.id), roles=[RoleEnum.FARMER.value])
        customer_token = create_access_token(user_id=str(customer.id), roles=[RoleEnum.CUSTOMER.value])
        driver_token = create_access_token(user_id=str(driver.id), roles=[RoleEnum.DRIVER.value])
        admin_token = create_access_token(user_id=str(super_admin.id), roles=[RoleEnum.SUPER_ADMIN.value])

        return {
            "farmer": farmer,
            "farmer_profile": farmer_profile,
            "customer": customer,
            "driver": driver,
            "admin": super_admin,
            "order": order,
            "farmer_headers": {"Authorization": f"Bearer {farmer_token}"},
            "customer_headers": {"Authorization": f"Bearer {customer_token}"},
            "driver_headers": {"Authorization": f"Bearer {driver_token}"},
            "admin_headers": {"Authorization": f"Bearer {admin_token}"},
        }

    def test_farmer_create_shipment_and_public_tracking(self, client: TestClient, test_data: dict):
        order = test_data["order"]
        headers = test_data["farmer_headers"]

        payload = {
            "order_id": str(order.id),
            "origin_address": "Thottipalayam Farm Gate, Pollachi",
            "origin_city": "Pollachi",
            "origin_pincode": "642001",
            "destination_address": "42, Cross Cut Road, Gandhipuram",
            "destination_city": "Coimbatore",
            "destination_pincode": "641012",
            "is_perishable": True,
            "special_handling": "KEEP_COOL",
            "packages": [
                {
                    "item_description": "Farm Fresh Alphonso Mangoes (Crate)",
                    "weight_kg": 5.5,
                    "package_type": "PLASTIC_CRATE"
                },
                {
                    "item_description": "Tender Coconuts (Pack of 6)",
                    "weight_kg": 8.0,
                    "package_type": "JUTE_BAG"
                }
            ],
            "request_pickup": True,
            "pickup_time_window": "MORNING_7_11"
        }

        # 1. Create Shipment
        res = client.post("/api/v1/farmer/shipments", json=payload, headers=headers)
        assert res.status_code == 201
        data = res.json()
        assert data["shipment_number"].startswith("SHP-")
        assert data["tracking_number"].startswith("AGRI")
        assert data["current_status"] == "READY_FOR_PICKUP"
        assert len(data["packages"]) == 2
        assert float(data["total_weight_kg"]) == 13.5
        assert len(data["pickup_requests"]) == 1
        assert data["pickup_requests"][0]["status"] == "PENDING"

        tracking_number = data["tracking_number"]
        shipment_id = data["id"]

        # 2. Public Tracking Endpoint (No Auth)
        track_res = client.get(f"/api/v1/tracking/{tracking_number}")
        assert track_res.status_code == 200
        track_data = track_res.json()
        assert track_data["tracking_number"] == tracking_number
        assert track_data["current_status"] == "READY_FOR_PICKUP"
        assert track_data["destination_city"] == "Coimbatore"
        # Verify privacy masking: "Karthik Mohan" -> "K***k M"
        assert track_data["masked_customer_name"] == "K***k M"
        assert len(track_data["tracking_events"]) >= 1

    def test_driver_scan_and_complete_delivery_flow(self, client: TestClient, test_data: dict):
        order = test_data["order"]
        farmer_headers = test_data["farmer_headers"]
        driver_headers = test_data["driver_headers"]

        # Create shipment
        payload = {
            "order_id": str(order.id),
            "origin_address": "Pollachi Farm",
            "origin_city": "Pollachi",
            "origin_pincode": "642001",
            "destination_address": "Coimbatore Main",
            "destination_city": "Coimbatore",
            "destination_pincode": "641012",
            "is_perishable": False,
            "special_handling": "GENERAL",
            "packages": [
                {"item_description": "Organic Paddy Bag", "weight_kg": 25.0, "package_type": "JUTE_BAG"}
            ],
            "request_pickup": True
        }
        res = client.post("/api/v1/farmer/shipments", json=payload, headers=farmer_headers)
        shipment_data = res.json()
        shipment_id = shipment_data["id"]
        tracking_number = shipment_data["tracking_number"]

        # 1. Driver Scans Barcode
        scan_res = client.get(f"/api/v1/driver/shipments/scan/{tracking_number}", headers=driver_headers)
        assert scan_res.status_code == 200
        assert scan_res.json()["match_type"] == "TRACKING_NUMBER"
        assert scan_res.json()["shipment"]["id"] == shipment_id

        # 2. Driver Confirms Pickup at Farm Gate
        pickup_res = client.post(
            f"/api/v1/driver/shipments/{shipment_id}/confirm-pickup?location_hub=Pollachi%20Origin%20Hub",
            headers=driver_headers
        )
        assert pickup_res.status_code == 200
        assert pickup_res.json()["current_status"] == "PICKED_UP"

        # 3. Invalid Transition check: Cannot jump directly from PICKED_UP to DELIVERED
        invalid_res = client.post(
            f"/api/v1/driver/shipments/{shipment_id}/update-status",
            json={"status": "DELIVERED", "remarks": "Skipping hubs"},
            headers=driver_headers
        )
        assert invalid_res.status_code == 400

        # 4. In Transit
        transit_res = client.post(
            f"/api/v1/driver/shipments/{shipment_id}/update-status",
            json={"status": "IN_TRANSIT", "location_hub": "NH-544 Salem-Coimbatore Highway", "remarks": "On vehicle"},
            headers=driver_headers
        )
        assert transit_res.status_code == 200
        assert transit_res.json()["current_status"] == "IN_TRANSIT"

        # 5. Out For Delivery
        out_res = client.post(
            f"/api/v1/driver/shipments/{shipment_id}/update-status",
            json={"status": "OUT_FOR_DELIVERY", "location_hub": "Gandhipuram Distribution Hub", "remarks": "Driver out for doorstep delivery"},
            headers=driver_headers
        )
        assert out_res.status_code == 200
        assert out_res.json()["current_status"] == "OUT_FOR_DELIVERY"

        # 6. Driver Confirms Delivery with Recipient note
        deliv_res = client.post(
            f"/api/v1/driver/shipments/{shipment_id}/confirm-delivery",
            json={
                "recipient_name": "Karthik Mohan",
                "recipient_signature_note": "Signed on mobile device",
                "driver_notes": "Delivered in good condition"
            },
            headers=driver_headers
        )
        assert deliv_res.status_code == 200
        deliv_data = deliv_res.json()
        assert deliv_data["current_status"] == "DELIVERED"
        assert deliv_data["actual_delivery_date"] is not None
        assert len(deliv_data["delivery_attempts"]) == 1
        assert deliv_data["delivery_attempts"][0]["attempt_status"] == "SUCCESS"

    def test_admin_transport_dashboard_and_provider_management(self, client: TestClient, test_data: dict):
        admin_headers = test_data["admin_headers"]

        # 1. Create Transport Provider
        provider_payload = {
            "provider_name": "Kongu Agri Logistics Express",
            "provider_code": "KONGU_EXP",
            "contact_person": "Senthil Kumar",
            "phone_number": "9443322110",
            "email": "logistics@konguagri.in",
            "vehicle_type": "Reefer Mini Truck (2.5 Ton)",
            "vehicle_number": "TN 38 AY 4521",
            "service_areas": "Coimbatore, Tiruppur, Erode, Salem",
            "is_active": True
        }
        create_res = client.post("/api/v1/admin/transport/providers", json=provider_payload, headers=admin_headers)
        assert create_res.status_code == 201
        provider_data = create_res.json()
        assert provider_data["provider_code"] == "KONGU_EXP"
        provider_id = provider_data["id"]

        # 2. List Providers
        list_res = client.get("/api/v1/admin/transport/providers", headers=admin_headers)
        assert list_res.status_code == 200
        assert len(list_res.json()) >= 1

        # 3. Get Dashboard Metrics
        stats_res = client.get("/api/v1/admin/transport/dashboard", headers=admin_headers)
        assert stats_res.status_code == 200
        stats = stats_res.json()
        assert "total_shipments" in stats
        assert "active_providers_count" in stats
        assert stats["active_providers_count"] >= 1
