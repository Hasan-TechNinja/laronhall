import requests
import base64
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def get_shipping_rate(address, total_weight_ounces):
    """
    Fetches the lowest available shipping rate from ShipStation.
    Falls back to a default rate if the API call fails or is unconfigured.
    """
    default_rate = 5.00
    api_key = getattr(settings, 'SHIPSTATION_API_KEY', None)
    api_secret = getattr(settings, 'SHIPSTATION_API_SECRET', None)
    
    if not api_key or not api_secret:
        return default_rate
        
    url = "https://ssapi.shipstation.com/shipments/getrates"
    
    auth_str = f"{api_key}:{api_secret}"
    auth_bytes = auth_str.encode('ascii')
    base64_bytes = base64.b64encode(auth_bytes)
    base64_str = base64_bytes.decode('ascii')
    
    headers = {
        'Authorization': f'Basic {base64_str}',
        'Content-Type': 'application/json'
    }
    
    carrier_code = getattr(settings, 'SHIPSTATION_CARRIER_CODE', 'stamps_com')
    from_postal_code = getattr(settings, 'SHIPSTATION_ORIGIN_ZIP', '91739')
    
    payload = {
        "carrierCode": carrier_code,
        "fromPostalCode": from_postal_code,
        "toState": address.get("state", ""),
        "toCountry": address.get("country", "US"),
        "toPostalCode": address.get("zipcode", ""),
        "weight": {
            "value": total_weight_ounces,
            "units": "ounces"
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            rates = response.json()
            if rates and isinstance(rates, list):
                # Return the cheapest rate
                cheapest = min(rates, key=lambda x: x.get('shipmentCost', float('inf')))
                return float(cheapest.get('shipmentCost', default_rate))
        else:
            logger.error(f"ShipStation getrates failed: {response.text}")
    except Exception as e:
        logger.error(f"ShipStation getrates exception: {str(e)}")
        
    return default_rate


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

    shipping_val = 0.0
    try:
        if order.delivery_charge:
            shipping_val = float(order.delivery_charge)
    except (ValueError, TypeError, AttributeError):
        pass
        
    order_total = (price_val * order.quantity) + shipping_val

    item_weight = 12.00
    try:
        if hasattr(order.product, 'weight') and order.product.weight is not None:
            item_weight = float(order.product.weight)
    except (ValueError, TypeError, AttributeError):
        pass

    total_weight = item_weight * order.quantity

    # Construct ShipStation payload
    payload = {
        "orderNumber": f"Order-{order.id}",
        "orderDate": order.created_at.isoformat() if order.created_at else "",
        "orderStatus": "awaiting_shipment",
        "customerEmail": order.email or "",
        "amountPaid": order_total,
        "shippingAmount": shipping_val,
        "orderTotal": order_total,
        "weight": {
            "value": total_weight,
            "units": "ounces"
        },
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
                "unitPrice": price_val,
                "weight": {
                    "value": item_weight,
                    "units": "ounces"
                }
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code in (200, 201):
            logger.info(f"Successfully pushed Order {order.id} to ShipStation.")
            return True
        else:
            error_msg = f"Failed to push Order {order.id} to ShipStation. Response: {response.status_code} - {response.text}"
            logger.error(error_msg)
            try:
                from django.core.mail import send_mail
                send_mail(
                    "ShipStation Debug Error", 
                    f"ShipStation rejected the order!\n\nStatus: {response.status_code}\nResponse: {response.text}\n\nPayload sent:\n{payload}", 
                    settings.DEFAULT_FROM_EMAIL, 
                    ["hasantechninja@hotmail.com"]
                )
            except:
                pass
            return False
    except Exception as e:
        logger.error(f"Exception raised while pushing Order {order.id} to ShipStation: {str(e)}")
        try:
            from django.core.mail import send_mail
            send_mail(
                "ShipStation Debug Crash", 
                f"Crash: {str(e)}\n\nPayload sent:\n{payload}", 
                settings.DEFAULT_FROM_EMAIL, 
                ["hasantechninja@hotmail.com"]
            )
        except:
            pass
        return False
