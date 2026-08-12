import requests
from django.conf import settings


class AddressValidationError(Exception):
    pass


def validate_us_address(address):
    if not isinstance(address, dict):
        raise AddressValidationError("Address must be an object")

    street = str(address.get("street", "")).strip()
    if not street:
        raise AddressValidationError("Street address is required")

    auth_id = settings.SMARTY_AUTH_ID
    auth_token = settings.SMARTY_AUTH_TOKEN
    if not auth_id or not auth_token:
        raise AddressValidationError("Address verification is not configured")

    params = {
        "auth-id": auth_id,
        "auth-token": auth_token,
        "street": street,
        "candidates": 1,
        "match": "strict",
    }
    for field in ("street2", "city", "state", "zipcode"):
        value = str(address.get(field, "")).strip()
        if value:
            params[field] = value

    try:
        response = requests.get(
            "https://us-street.api.smarty.com/street-address",
            params=params,
            timeout=10,
        )
        if response.status_code == 401:
            raise AddressValidationError("Smarty credentials are invalid")
        if response.status_code == 402:
            raise AddressValidationError(
                "Smarty address verification is not active for this account"
            )
        response.raise_for_status()
        candidates = response.json()
    except AddressValidationError:
        raise
    except requests.RequestException as exc:
        raise AddressValidationError("Address verification service is unavailable") from exc
    except ValueError as exc:
        raise AddressValidationError("Address verification returned an invalid response") from exc

    if not candidates:
        raise AddressValidationError("No valid address was found")

    candidate = candidates[0]
    components = candidate.get("components", {})
    analysis = candidate.get("analysis", {})
    match_code = analysis.get("dpv_match_code", "")

    return {
        "street": candidate.get("delivery_line_1", street),
        "street2": candidate.get("delivery_line_2", ""),
        "city": components.get("city_name", address.get("city", "")),
        "state": components.get("state_abbreviation", address.get("state", "")),
        "zipcode": components.get("zipcode", address.get("zipcode", "")),
        "match_code": match_code,
    }
