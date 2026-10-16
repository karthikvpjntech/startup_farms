import json
import uuid
import hmac
import hashlib
from decimal import Decimal
from fastapi import status
from sqlalchemy import select
from app.core.config import settings
from app.models.user import User
from app.models.otp_verification import OtpVerification
from app.models.marketplace_order import MarketplaceOrder, MarketplacePayment
from app.models.subscription import UserSubscription
from app.models.farmer_profile import FarmerProfile
from app.models.enums import MarketplacePaymentStatus, MarketplaceOrderStatus
from app.services.otp_service import OtpService
from app.services.razorpay_service import RazorpayService


def test_standard_user_registration_and_login(client):
    """Test user registration and standard login without 2FA."""
    # Register
    reg_payload = {
        "full_name": "Ravi Kumar",
        "mobile_number": "9876543210",
        "email": "ravi.kumar@example.com",
        "password": "Password123!",
        "role": "FARMER"
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == status.HTTP_201_CREATED
    data = reg_res.json()
    assert data["access_token"] is not None
    assert data["requires_2fa"] is False
    assert data["user"]["full_name"] == "Ravi Kumar"
    assert data["user"]["is_two_factor_enabled"] is False

    # Login
    login_res = client.post("/api/v1/auth/login", json={
        "identifier": "9876543210",
        "password": "Password123!"
    })
    assert login_res.status_code == status.HTTP_200_OK
    login_data = login_res.json()
    assert login_data["access_token"] is not None
    assert login_data["requires_2fa"] is False


def test_two_factor_setup_and_challenge_flow(client, db_session):
    """Test setting up 2FA, confirming OTP, and subsequent login requiring 2FA OTP."""
    # 1. Register user
    reg_payload = {
        "full_name": "Priya Sharma",
        "mobile_number": "9123456789",
        "email": "priya.sharma@example.com",
        "password": "SecurePassword123!",
        "role": "CUSTOMER"
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check initial 2FA status
    status_res = client.get("/api/v1/auth/2fa/status", headers=headers)
    assert status_res.status_code == status.HTTP_200_OK
    assert status_res.json()["is_two_factor_enabled"] is False

    # 3. Request 2FA Setup OTP
    setup_req = client.post("/api/v1/auth/2fa/setup-request", json={"method": "EMAIL"}, headers=headers)
    assert setup_req.status_code == status.HTTP_200_OK
    setup_data = setup_req.json()
    session_token = setup_data["session_token"]

    # In test DB, find generated OTP
    otp_record = db_session.scalar(
        select(OtpVerification).where(OtpVerification.session_token == session_token)
    )
    assert otp_record is not None

    # Test with invalid OTP code
    bad_confirm = client.post("/api/v1/auth/2fa/setup-confirm", json={
        "session_token": session_token,
        "otp_code": "000000"
    }, headers=headers)
    assert bad_confirm.status_code == status.HTTP_400_BAD_REQUEST

    # Confirm with correct OTP (generate hash matches)
    # Since OtpService hashes OTP, we can trigger create_and_send_otp directly or re-create
    # Let's test using OtpService verification
    test_otp = "123456"
    otp_record.otp_code_hash = OtpService.hash_otp(test_otp)
    otp_record.attempts = 0
    db_session.commit()

    confirm_res = client.post("/api/v1/auth/2fa/setup-confirm", json={
        "session_token": session_token,
        "otp_code": test_otp
    }, headers=headers)
    assert confirm_res.status_code == status.HTTP_200_OK
    assert confirm_res.json()["is_two_factor_enabled"] is True

    # 4. Now Login should require 2FA!
    login_res = client.post("/api/v1/auth/login", json={
        "identifier": "priya.sharma@example.com",
        "password": "SecurePassword123!"
    })
    assert login_res.status_code == status.HTTP_200_OK
    login_data = login_res.json()
    assert login_data["requires_2fa"] is True
    assert login_data["access_token"] is None
    assert login_data["two_factor_token"] is not None
    login_session_token = login_data["two_factor_token"]

    # Find the login OTP in DB and set known test OTP
    login_otp_record = db_session.scalar(
        select(OtpVerification).where(OtpVerification.session_token == login_session_token)
    )
    assert login_otp_record is not None
    login_otp_record.otp_code_hash = OtpService.hash_otp("654321")
    db_session.commit()

    # Verify 2FA Login
    verify_2fa_res = client.post("/api/v1/auth/login/2fa-verify", json={
        "two_factor_token": login_session_token,
        "otp_code": "654321"
    })
    assert verify_2fa_res.status_code == status.HTTP_200_OK
    verified_data = verify_2fa_res.json()
    assert verified_data["access_token"] is not None
    assert verified_data["user"]["full_name"] == "Priya Sharma"

    # 5. Disable 2FA
    new_token = verified_data["access_token"]
    disable_res = client.post("/api/v1/auth/2fa/disable", json={
        "password": "SecurePassword123!"
    }, headers={"Authorization": f"Bearer {new_token}"})
    assert disable_res.status_code == status.HTTP_200_OK
    assert disable_res.json()["is_two_factor_enabled"] is False


def test_passwordless_otp_login(client, db_session):
    """Test passwordless OTP login flow."""
    # Register
    client.post("/api/v1/auth/register", json={
        "full_name": "Suresh Raina",
        "mobile_number": "9811122233",
        "email": "suresh@example.com",
        "password": "OldPassword123!",
    })

    # Request passwordless OTP
    req_res = client.post("/api/v1/auth/login/otp-request", json={
        "identifier": "9811122233"
    })
    assert req_res.status_code == status.HTTP_200_OK
    session_token = req_res.json()["session_token"]

    # Mock OTP code in DB
    otp_record = db_session.scalar(
        select(OtpVerification).where(OtpVerification.session_token == session_token)
    )
    assert otp_record is not None
    otp_record.otp_code_hash = OtpService.hash_otp("888999")
    db_session.commit()

    # Verify OTP login
    verify_res = client.post("/api/v1/auth/login/otp-verify", json={
        "session_token": session_token,
        "otp_code": "888999"
    })
    assert verify_res.status_code == status.HTTP_200_OK
    assert verify_res.json()["access_token"] is not None
    assert verify_res.json()["user"]["full_name"] == "Suresh Raina"


def test_forgot_password_and_reset_flow(client, db_session):
    """Test requesting password reset, verifying OTP, and setting new password."""
    # Register
    client.post("/api/v1/auth/register", json={
        "full_name": "Ananya Roy",
        "mobile_number": "9777888999",
        "email": "ananya@example.com",
        "password": "InitialPass123!",
    })

    # 1. Forgot password request
    forgot_res = client.post("/api/v1/auth/forgot-password", json={
        "identifier": "ananya@example.com"
    })
    assert forgot_res.status_code == status.HTTP_200_OK
    session_token = forgot_res.json()["session_token"]

    # 2. Mock OTP code in DB
    otp_record = db_session.scalar(
        select(OtpVerification).where(OtpVerification.session_token == session_token)
    )
    assert otp_record is not None
    otp_record.otp_code_hash = OtpService.hash_otp("555444")
    db_session.commit()

    # 3. Verify Reset OTP
    verify_res = client.post("/api/v1/auth/verify-reset-otp", json={
        "session_token": session_token,
        "otp_code": "555444"
    })
    assert verify_res.status_code == status.HTTP_200_OK
    reset_token = verify_res.json()["reset_token"]

    # 4. Set New Password
    reset_res = client.post("/api/v1/auth/reset-password", json={
        "reset_token": reset_token,
        "new_password": "BrandNewSuperSecretPass456!"
    })
    assert reset_res.status_code == status.HTTP_200_OK
    assert reset_res.json()["success"] is True

    # 5. Verify old password fails and new password succeeds
    old_login = client.post("/api/v1/auth/login", json={
        "identifier": "ananya@example.com",
        "password": "InitialPass123!"
    })
    assert old_login.status_code == status.HTTP_401_UNAUTHORIZED

    new_login = client.post("/api/v1/auth/login", json={
        "identifier": "ananya@example.com",
        "password": "BrandNewSuperSecretPass456!"
    })
    assert new_login.status_code == status.HTTP_200_OK
    assert new_login.json()["access_token"] is not None


def test_razorpay_webhook_order_reconciliation(client, db_session):
    """Test inbound Razorpay webhook settling a marketplace order."""
    # 1. Setup customer and farmer in database
    customer = User(
        id=uuid.uuid4(),
        full_name="Marketplace Buyer",
        mobile_number="9988776655",
        email="buyer@example.com",
        password_hash="somehash",
    )
    farmer_user = User(
        id=uuid.uuid4(),
        full_name="Farm Vendor",
        mobile_number="9988776644",
        password_hash="somehash",
    )
    db_session.add_all([customer, farmer_user])
    db_session.flush()

    farmer_profile = FarmerProfile(
        id=uuid.uuid4(),
        user_id=farmer_user.id
    )
    db_session.add(farmer_profile)
    db_session.flush()

    # Create Marketplace Order
    order = MarketplaceOrder(
        id=uuid.uuid4(),
        order_number="ORD-LS-2026-000088",
        customer_id=customer.id,
        farmer_profile_id=farmer_profile.id,
        total_items_count=1,
        subtotal_amount=Decimal("1500.00"),
        total_amount=Decimal("1500.00"),
        status=MarketplaceOrderStatus.PENDING.value,
        payment_status=MarketplacePaymentStatus.PENDING.value,
        delivery_type="FARM_PICKUP",
        delivery_contact_name="Marketplace Buyer",
        delivery_contact_phone="9988776655",
    )
    db_session.add(order)
    db_session.flush()

    payment = MarketplacePayment(
        id=uuid.uuid4(),
        payment_number="PAY-LS-2026-000088",
        order_id=order.id,
        customer_id=customer.id,
        amount=Decimal("1500.00"),
        payment_method="UPI",
        status="PENDING",
    )
    db_session.add(payment)
    db_session.commit()

    # 2. Dispatch Razorpay Webhook Event: payment.captured
    event_payload = {
        "id": f"evt_test_{uuid.uuid4().hex[:8]}",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_rzp_12345",
                    "order_id": "order_test_rzp_9999",
                    "amount": 150000,
                    "currency": "INR",
                    "status": "captured",
                    "notes": {
                        "order_id": str(order.id),
                        "order_number": order.order_number,
                    }
                }
            }
        }
    }

    raw_body = json.dumps(event_payload)
    secret = settings.RAZORPAY_WEBHOOK_SECRET or settings.RAZORPAY_KEY_SECRET or ""
    valid_signature = hmac.new(secret.encode("utf-8"), raw_body.encode("utf-8"), hashlib.sha256).hexdigest() if secret else "dev_test_sig"

    # Send webhook
    res = client.post(
        "/api/v1/payments/webhooks",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": valid_signature
        }
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "PROCESSED"

    # Verify order and payment updated in DB
    db_session.expire_all()
    updated_payment = db_session.get(MarketplacePayment, payment.id)
    assert updated_payment.status == MarketplacePaymentStatus.PAID.value
    assert updated_payment.transaction_reference == "pay_test_rzp_12345"

    # 3. Test duplicate delivery returns DUPLICATE status
    dup_res = client.post(
        "/api/v1/payments/webhooks",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": valid_signature
        }
    )
    assert dup_res.status_code == status.HTTP_200_OK
    assert dup_res.json()["status"] == "DUPLICATE"


def test_razorpay_webhook_subscription_activation(client, db_session):
    """Test Razorpay webhook auto-activating historical data subscription."""
    user = User(
        id=uuid.uuid4(),
        full_name="Subscriber User",
        mobile_number="9955443322",
        email="subscriber@example.com",
        password_hash="somehash",
    )
    db_session.add(user)
    db_session.commit()

    event_payload = {
        "id": f"evt_sub_{uuid.uuid4().hex[:8]}",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_sub_998877",
                    "order_id": "order_sub_112233",
                    "amount": 99900,
                    "currency": "INR",
                    "status": "captured",
                    "notes": {
                        "purpose": "historical_data_subscription",
                        "user_id": str(user.id),
                        "plan_type": "ANNUAL",
                    }
                }
            }
        }
    }

    raw_body = json.dumps(event_payload)
    secret = settings.RAZORPAY_WEBHOOK_SECRET or settings.RAZORPAY_KEY_SECRET or ""
    valid_signature = hmac.new(secret.encode("utf-8"), raw_body.encode("utf-8"), hashlib.sha256).hexdigest() if secret else "dev_test_sig"

    res = client.post(
        "/api/v1/payments/webhooks/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": valid_signature
        }
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "PROCESSED"

    # Check user subscription in DB
    sub = db_session.scalar(
        select(UserSubscription).where(UserSubscription.user_id == user.id)
    )
    assert sub is not None
    assert sub.status == "ACTIVE"
    assert sub.plan_type == "ANNUAL"
    assert sub.amount_paid == Decimal("999.00")
