import pytest
from pydantic import ValidationError
from app.core.phone_utils import (
    validate_phone_with_country,
    validate_and_format_phone,
    parse_country_and_digits,
    extract_search_variants,
)
from app.schemas.auth import RegisterRequest
from app.schemas.admin_user import AdminUserCreateRequest, AdminUserUpdateRequest
from app.schemas.farmer_crm import WorkerCreate, WorkerUpdate, SMSSendRequest
from app.schemas.supplier import SupplierCreate, SupplierUpdate
from app.schemas.marketplace_order import OrderCheckoutRequest


def test_country_parsing_and_allowed_digits():
    # India (+91) -> exactly 10 digits
    is_valid, formatted, err = validate_phone_with_country("+919876543210")
    assert is_valid is True
    assert formatted == "+919876543210"
    assert err is None

    # India with 9 digits -> invalid
    is_valid, _, err = validate_phone_with_country("+91987654321")
    assert is_valid is False
    assert "must be exactly 10 digits" in err

    # India with 11 digits -> invalid
    is_valid, _, err = validate_phone_with_country("+9198765432100")
    assert is_valid is False
    assert "must be exactly 10 digits" in err

    # United States (+1) -> exactly 10 digits
    is_valid, formatted, err = validate_phone_with_country("+12025550123")
    assert is_valid is True
    assert formatted == "+12025550123"

    # United Arab Emirates (+971) -> exactly 9 digits
    is_valid, formatted, err = validate_phone_with_country("+971501234567")
    assert is_valid is True
    assert formatted == "+971501234567"

    # UAE with 10 digits -> invalid
    is_valid, _, err = validate_phone_with_country("+9715012345678")
    assert is_valid is False
    assert "must be exactly 9 digits" in err

    # Singapore (+65) -> exactly 8 digits
    is_valid, formatted, err = validate_phone_with_country("+6581234567")
    assert is_valid is True
    assert formatted == "+6581234567"

    # Singapore with 9 digits -> invalid
    is_valid, _, err = validate_phone_with_country("+65812345678")
    assert is_valid is False
    assert "must be exactly 8 digits" in err

    # Germany (+49) -> between 10 and 11 digits
    is_valid, formatted, err = validate_phone_with_country("+491512345678")
    assert is_valid is True
    assert formatted == "+491512345678"

    # Domestic 10-digit number defaults to +91
    is_valid, formatted, _ = validate_phone_with_country("9876543210")
    assert is_valid is True
    assert formatted == "+919876543210"


def test_schema_validations_with_country_codes():
    # 1. RegisterRequest with international numbers
    reg_in = RegisterRequest(
        full_name="Indian User",
        mobile_number="+919876543210",
        password="ValidPassword123!",
    )
    assert reg_in.mobile_number == "+919876543210"

    reg_uae = RegisterRequest(
        full_name="UAE User",
        mobile_number="+971501234567",
        password="ValidPassword123!",
    )
    assert reg_uae.mobile_number == "+971501234567"

    with pytest.raises(ValidationError):
        RegisterRequest(
            full_name="Invalid User",
            mobile_number="+97150123456",  # 8 digits for UAE (requires 9)
            password="ValidPassword123!",
        )

    # 2. AdminUserCreateRequest
    admin_user = AdminUserCreateRequest(
        full_name="Admin John",
        mobile_number="+12025550199",
        password="AdminSecurePassword123!",
        roles=["SUPER_ADMIN"],
    )
    assert admin_user.mobile_number == "+12025550199"

    with pytest.raises(ValidationError):
        AdminUserCreateRequest(
            full_name="Bad Admin",
            mobile_number="+1202555",  # Too short for US
            password="AdminSecurePassword123!",
            roles=["SUPER_ADMIN"],
        )

    # 3. WorkerCreate
    worker = WorkerCreate(
        full_name="Farm Laborer",
        mobile_number="+919876543210",
    )
    assert worker.mobile_number == "+919876543210"

    # 4. SupplierCreate
    supplier = SupplierCreate(
        supplier_name="Agri Seeds Ltd",
        phone_number="+919876543210",
        address_line1="123 Farm Road",
        village_city="Nashik",
        district="Nashik",
        state="Maharashtra",
        pincode="422001",
    )
    assert supplier.phone_number == "+919876543210"

    with pytest.raises(ValidationError):
        SupplierCreate(
            supplier_name="Agri Seeds Ltd",
            phone_number="+91123",  # Invalid digit length
            address_line1="123 Farm Road",
            village_city="Nashik",
            district="Nashik",
            state="Maharashtra",
            pincode="422001",
        )


def test_search_variants_compatibility():
    # Searching with domestic or E.164 generates appropriate query variants
    variants_domestic = extract_search_variants("9876543210")
    assert "+919876543210" in variants_domestic
    assert "9876543210" in variants_domestic

    variants_e164 = extract_search_variants("+919876543210")
    assert "+919876543210" in variants_e164
    assert "9876543210" in variants_e164
