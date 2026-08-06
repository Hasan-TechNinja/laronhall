import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laronhall.settings')
django.setup()

from shop.utils import validate_us_address, AddressValidationError

def test_address(address_dict):
    print(f"Testing {address_dict}")
    try:
        result = validate_us_address(address_dict)
        print("Success:", result)
    except AddressValidationError as e:
        print("Error:", str(e))
    print("-" * 40)

test_address({
    "street": "1600 Amphitheatre Pkwy",
    "city": "Mountain View",
    "state": "CA",
    "zipcode": "94043"
})

test_address({
    "street": "Fake Street 123",
    "city": "Nowhere",
    "state": "CA",
    "zipcode": "99999"
})
