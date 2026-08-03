import requests
import json
import uuid

url = "https://api.treatsislandgo.com/shop/checkout/guest/"
payload = {
    "cart": [
        {
            "slug": "chamoy-watermelon-rings-12-oz",
            "quantity": 1,
            "fundraiser_id": 11
        }
    ],
    "email": "hasantechninja@gmail.com",
    "name": "Olen Reichert",
    "phone": "(205) 940-1196",
    "address": {
        "street": "1600 Amphitheatre Parkway",
        "city": "Mountain Viev",
        "state": "CA",
        "zipcode": "94043"
    },
    "idempotency_key": str(uuid.uuid4())
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)
print("Status Code:", response.status_code)
print("Response:", response.text)
