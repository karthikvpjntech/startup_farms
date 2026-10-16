"""
Phone number normalization, parsing, country-code validation, and search utility for FastAPI backend.
Supports international E.164 formats (+919876543210, +12025550123) and standard domestic mobile numbers.
"""

import re
from typing import Optional, Tuple, Dict, Any, List

# Comprehensive list of country metadata with dial codes and allowed national subscriber digit lengths
COUNTRY_CONFIGS: List[Dict[str, Any]] = [
    {"name": "India", "iso": "IN", "dial_code": "+91", "min_digits": 10, "max_digits": 10},
    {"name": "United States", "iso": "US", "dial_code": "+1", "min_digits": 10, "max_digits": 10},
    {"name": "United Kingdom", "iso": "GB", "dial_code": "+44", "min_digits": 10, "max_digits": 10},
    {"name": "United Arab Emirates", "iso": "AE", "dial_code": "+971", "min_digits": 9, "max_digits": 9},
    {"name": "Saudi Arabia", "iso": "SA", "dial_code": "+966", "min_digits": 9, "max_digits": 9},
    {"name": "Australia", "iso": "AU", "dial_code": "+61", "min_digits": 9, "max_digits": 9},
    {"name": "Canada", "iso": "CA", "dial_code": "+1", "min_digits": 10, "max_digits": 10},
    {"name": "Singapore", "iso": "SG", "dial_code": "+65", "min_digits": 8, "max_digits": 8},
    {"name": "Malaysia", "iso": "MY", "dial_code": "+60", "min_digits": 9, "max_digits": 10},
    {"name": "Germany", "iso": "DE", "dial_code": "+49", "min_digits": 10, "max_digits": 11},
    {"name": "France", "iso": "FR", "dial_code": "+33", "min_digits": 9, "max_digits": 9},
    {"name": "Bangladesh", "iso": "BD", "dial_code": "+880", "min_digits": 10, "max_digits": 10},
    {"name": "Pakistan", "iso": "PK", "dial_code": "+92", "min_digits": 10, "max_digits": 10},
    {"name": "Sri Lanka", "iso": "LK", "dial_code": "+94", "min_digits": 9, "max_digits": 9},
    {"name": "Nepal", "iso": "NP", "dial_code": "+977", "min_digits": 10, "max_digits": 10},
    {"name": "Japan", "iso": "JP", "dial_code": "+81", "min_digits": 10, "max_digits": 10},
    {"name": "South Africa", "iso": "ZA", "dial_code": "+27", "min_digits": 9, "max_digits": 9},
    {"name": "Nigeria", "iso": "NG", "dial_code": "+234", "min_digits": 10, "max_digits": 10},
    {"name": "Kenya", "iso": "KE", "dial_code": "+254", "min_digits": 9, "max_digits": 9},
    {"name": "Brazil", "iso": "BR", "dial_code": "+55", "min_digits": 10, "max_digits": 11},
    {"name": "Mexico", "iso": "MX", "dial_code": "+52", "min_digits": 10, "max_digits": 10},
    {"name": "Philippines", "iso": "PH", "dial_code": "+63", "min_digits": 10, "max_digits": 10},
    {"name": "Indonesia", "iso": "ID", "dial_code": "+62", "min_digits": 9, "max_digits": 12},
    {"name": "Qatar", "iso": "QA", "dial_code": "+974", "min_digits": 8, "max_digits": 8},
    {"name": "Kuwait", "iso": "KW", "dial_code": "+965", "min_digits": 8, "max_digits": 8},
    {"name": "Oman", "iso": "OM", "dial_code": "+968", "min_digits": 8, "max_digits": 8},
    {"name": "Bahrain", "iso": "BH", "dial_code": "+973", "min_digits": 8, "max_digits": 8},
    {"name": "New Zealand", "iso": "NZ", "dial_code": "+64", "min_digits": 8, "max_digits": 10},
]

# Quick lookup by dial_code (sorted longest dial_code first to avoid prefix collisions, e.g. +880 vs +88)
SORTED_COUNTRY_CONFIGS = sorted(COUNTRY_CONFIGS, key=lambda c: len(c["dial_code"]), reverse=True)
DEFAULT_COUNTRY = COUNTRY_CONFIGS[0]  # India (+91)


def sanitize_phone_number(raw_phone: str) -> str:
    """
    Strips non-digit characters except leading '+'.
    Example: '+91 98765-43210' -> '+919876543210'
    """
    if not raw_phone:
        return ""
    trimmed = str(raw_phone).strip()
    if trimmed.startswith("+"):
        return "+" + re.sub(r"\D", "", trimmed[1:])
    return re.sub(r"\D", "", trimmed)


def parse_country_and_digits(phone_str: str) -> Tuple[Optional[Dict[str, Any]], str, str]:
    """
    Parses a phone string into (matched_country_config, dial_code, national_digits).
    If no leading '+' is provided, returns (None, '', clean_digits).
    """
    sanitized = sanitize_phone_number(phone_str)
    if not sanitized:
        return None, "", ""

    if sanitized.startswith("+"):
        for country in SORTED_COUNTRY_CONFIGS:
            dc = country["dial_code"]
            if sanitized.startswith(dc):
                national = sanitized[len(dc):]
                return country, dc, national
        # Unknown '+' prefix country
        return None, "+", sanitized[1:]

    return None, "", sanitized


def validate_phone_with_country(
    phone_str: str,
    default_dial_code: str = "+91"
) -> Tuple[bool, str, Optional[str]]:
    """
    Validates mobile/phone number format and country-based allowable digit count.
    
    Returns:
        (is_valid, normalized_e164_or_sanitized, error_message)
    """
    if not phone_str or not str(phone_str).strip():
        return False, "", "Mobile number is required."

    sanitized = sanitize_phone_number(phone_str)
    if not sanitized:
        return False, "", "Mobile number cannot be empty."

    country, dial_code, national_digits = parse_country_and_digits(sanitized)

    # 1. If country dial code matched
    if country:
        min_d = country["min_digits"]
        max_d = country["max_digits"]
        n_len = len(national_digits)

        if min_d == max_d and n_len != min_d:
            return (
                False,
                sanitized,
                f"Mobile number for {country['name']} ({dial_code}) must be exactly {min_d} digits (got {n_len}).",
            )
        elif n_len < min_d:
            return (
                False,
                sanitized,
                f"Mobile number for {country['name']} ({dial_code}) requires at least {min_d} digits (got {n_len}).",
            )
        elif n_len > max_d:
            return (
                False,
                sanitized,
                f"Mobile number for {country['name']} ({dial_code}) cannot exceed {max_d} digits (got {n_len}).",
            )

        # Valid formatted E.164
        return True, f"{dial_code}{national_digits}", None

    # 2. No country code supplied: check default country fallback or general length
    if not sanitized.startswith("+"):
        # If user entered 10 digits starting with Indian mobile standard
        if len(sanitized) == 10:
            return True, f"+91{sanitized}", None
        elif 7 <= len(sanitized) <= 15:
            return True, sanitized, None
        else:
            return False, sanitized, "Mobile number must be between 7 and 15 digits."

    # 3. Unrecognized international dial code
    national_len = len(sanitized[1:])
    if 7 <= national_len <= 15:
        return True, sanitized, None

    return False, sanitized, "Invalid international mobile number length."


def validate_and_format_phone(phone_str: Optional[str]) -> Optional[str]:
    """
    Pydantic helper validator. Returns normalized phone or raises ValueError.
    """
    if phone_str is None:
        return None

    trimmed = str(phone_str).strip()
    if not trimmed:
        return None

    is_valid, normalized, err = validate_phone_with_country(trimmed)
    if not is_valid:
        raise ValueError(err or "Invalid mobile number format.")
    return normalized


def extract_search_variants(query: str) -> List[str]:
    """
    Generates potential variations for database lookup to ensure backward compatibility.
    E.g., for '9999999999', returns ['9999999999', '+919999999999', '919999999999'].
    For '+919999999999', returns ['+919999999999', '9999999999', '919999999999'].
    """
    clean = sanitize_phone_number(query)
    if not clean:
        return [str(query).strip()]

    variants = {clean}

    # Match country prefixes
    if clean.startswith("+"):
        for country in SORTED_COUNTRY_CONFIGS:
            dc = country["dial_code"]
            if clean.startswith(dc):
                nat = clean[len(dc):]
                if nat:
                    variants.add(nat)
                    variants.add(f"{dc[1:]}{nat}")  # e.g., '919876543210' without '+'
                break
        # Also include without leading '+'
        variants.add(clean[1:])
    else:
        # Check standard 10-digit mobile
        if len(clean) == 10:
            variants.add(f"+91{clean}")
            variants.add(f"91{clean}")
            variants.add(f"+1{clean}")
        elif len(clean) == 12 and clean.startswith("91"):
            variants.add(f"+{clean}")
            variants.add(clean[2:])

    return list(variants)


def is_valid_phone(phone_str: str) -> bool:
    """
    Validates phone number length and format.
    """
    is_valid, _, _ = validate_phone_with_country(phone_str)
    return is_valid
