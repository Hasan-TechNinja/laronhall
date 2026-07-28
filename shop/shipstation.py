import requests
import base64
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def send_order_to_shipstation(order):
    """
    Sends a finalized paid order to the ShipStation API.
    Does not raise exceptions; instead logs failures to ensure e-commerce flows are not blocked.
    """
    api_key = getattr(settings, 'SHIPSTATION_API_KEY', None)
    api_secret = getattr(settings, 'SHIPSTATION_API_SECRET', None)
    
    if not api_key or not api_secret:
        logger.error("ShipStation API keys are not configured in settings.")
        return False

    url = "https://ssapi.shipstation.com/orders/createorder"
    
    # Encode credentials for HTTP Basic Authentication
    auth_str = f"{api_key}:{api_secret}"
    auth_bytes = auth_str.encode('ascii')
    base64_bytes = base64.b64encode(auth_bytes)
    base64_str = base64_bytes.decode('ascii')
    
    headers = {
        'Host': 'ssapi.shipstation.com',
        'Authorization': f'Basic {base64_str}',
        'Content-Type': 'application/json'
    }

    # Prepare Address fields safely (splitting address by newline or using as line1)
    address_lines = order.address.split('\n') if order.address else [""]
    street1 = address_lines[0]
    street2 = address_lines[1] if len(address_lines) > 1 else ""

    price_val = 0.0
    try:
        price_val = float(order.product.price)
    except (ValueError, TypeError, AttributeError):
        pass

    # Construct ShipStation payload
    payload = {
        "orderNumber": f"Order-{order.id}",
        "orderDate": order.created_at.isoformat() if order.created_at else "",
        "orderStatus": "awaiting_shipment",
        "customerEmail": order.email or "",
        "billTo": {
            "name": order.name or "Customer",
            "street1": street1,
            "street2": street2,
            "city": order.city or "",
            "state": order.state or "",
            "postalCode": order.postal_code or "",
            "country": order.country or "US",
            "phone": order.phone or ""
        },
        "shipTo": {
            "name": order.name or "Customer",
            "street1": street1,
            "street2": street2,
            "city": order.city or "",
            "state": order.state or "",
            "postalCode": order.postal_code or "",
            "country": order.country or "US",
            "phone": order.phone or ""
        },
        "items": [
            {
                "sku": order.product.slug or f"prod-{order.product.id}",
                "name": order.product.name,
                "quantity": order.quantity,
                "unitPrice": price_val
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code in (200, 201):
            logger.info(f"Successfully pushed Order {order.id} to ShipStation.")
            return True
        else:
            logger.error(f"Failed to push Order {order.id} to ShipStation. Response: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Exception raised while pushing Order {order.id} to ShipStation: {str(e)}")
        return False
