from rest_framework.views import APIView
from django.shortcuts import render
from . models import Product, Cart, Order, Review, DonationItem, Donation
from . serializers import ProductSerializer, CartSerializer, OrderSerializer, ReviewSerializer, DonationItemSerializer, DonationSerializer
from rest_framework import permissions, status
from rest_framework.response import Response
import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.cache import cache
from django.contrib.auth import get_user_model
User = get_user_model()
from notification.utils import send_push_notification
from .models import Review
from .serializers import ReviewSerializer
from django.db import transaction
import uuid
import os
import datetime
from urllib.parse import urlparse
from .utils import AddressValidationError, validate_us_address

def write_checkout_log(view_name, request, error=None):
    try:
        logs_dir = os.path.join(settings.BASE_DIR, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        log_file_path = os.path.join(logs_dir, 'checkout_debug.log')
        with open(log_file_path, "a") as f:
            f.write(f"[{datetime.datetime.now().isoformat()}] [{view_name}]\n")
            if error:
                f.write(f"ERROR: {error}\n")
            f.write(f"USER AGENT: {request.META.get('HTTP_USER_AGENT', 'Unknown')}\n")
            f.write(f"PAYLOAD: {request.data}\n")
            f.write("-" * 50 + "\n")
    except Exception:
        pass

stripe.api_key = settings.STRIPE_SECRET_KEY


def get_payment_success_url(extra_params=None):
    raw_url = getattr(settings, 'PAYMENT_SUCCESS_URL', 'https://treatsislandgo.com/success').strip()
    if raw_url.endswith('/'):
        raw_url = raw_url[:-1]

    parsed = urlparse(raw_url)
    if not parsed.path or parsed.path == '':
        raw_url = f"{raw_url}/success"

    separator = '&' if '?' in raw_url else '?'
    success_url = f"{raw_url}{separator}session_id={{CHECKOUT_SESSION_ID}}"
    if extra_params:
        for k, v in extra_params.items():
            if v is not None and v != '':
                success_url += f"&{k}={v}"
    return success_url


def get_payment_cancel_url():
    return getattr(settings, 'PAYMENT_CANCEL_URL', 'https://treatsislandgo.com/cancel')



def create_stripe_customer(address, name=None, email=None, phone=None):
    customer_address = {
        "line1": address["street"],
        "city": address["city"],
        "state": address["state"],
        "postal_code": address["zipcode"],
        "country": "US",
    }
    if address.get("street2"):
        customer_address["line2"] = address["street2"]

    customer_data = {
        "address": customer_address,
        "metadata": {
            "address_verified": "true",
            "address_match_code": address.get("match_code", ""),
        },
    }
    if name:
        customer_data["name"] = name
    if email:
        customer_data["email"] = email
    if phone:
        customer_data["phone"] = phone

    return stripe.Customer.create(**customer_data)


def address_session_metadata(address, name=None, email=None, phone=None):
    metadata = {
        "shipping_line1": address["street"],
        "shipping_line2": address.get("street2", ""),
        "shipping_city": address["city"],
        "shipping_state": address["state"],
        "shipping_postal_code": address["zipcode"],
        "shipping_country": "US",
    }
    if name:
        metadata["shipping_name"] = name
    if email:
        metadata["shipping_email"] = email
    if phone:
        metadata["shipping_phone"] = phone
    return metadata

# Create your views here.

class ProductsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        cache_key = "all_products"
        data = cache.get(cache_key)
        
        if not data:
            products = Product.objects.filter(is_active=True)
            serializer = ProductSerializer(products, many=True)
            data = serializer.data
            cache.set(cache_key, data, 60 * 60 * 24) # 24 hours
            
        return Response(data)
        

class ProductDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        cache_key = f"product_detail_{slug}"
        data = cache.get(cache_key)
        
        if not data:
            try:
                product = Product.objects.get(slug=slug, is_active=True)
            except Product.DoesNotExist:
                return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = ProductSerializer(product)
            data = serializer.data
            cache.set(cache_key, data, 60 * 60 * 24) # 24 hours
            
        return Response(data)


class DonationItemListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        items = DonationItem.objects.filter(is_active=True).order_by('price')
        serializer = DonationItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class DonationItemDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        try:
            item = DonationItem.objects.get(slug=slug, is_active=True)
        except DonationItem.DoesNotExist:
            return Response({"error": "Donation item not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = DonationItemSerializer(item, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class AddToCart(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        slug = request.data.get('slug') 
        quantity = request.data.get('quantity')
        fundraiser_id = request.data.get('fundraiser_id')

        if not slug:
            return Response({"error": "Please provide product slug"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantity = int(quantity) if quantity else 1
        except ValueError:
            return Response({"error": "Quantity must be an integer"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            product = Product.objects.get(slug=slug, is_active=True)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        fundraiser = None
        if fundraiser_id:
            from event.models import Fundraiser
            try:
                fundraiser = Fundraiser.objects.get(id=fundraiser_id)
            except Fundraiser.DoesNotExist:
                return Response({"error": "Fundraiser not found"}, status=status.HTTP_404_NOT_FOUND)

        if Cart.objects.filter(user=request.user, product=product, fundraiser=fundraiser).exists():
            cart = Cart.objects.get(user=request.user, product=product, fundraiser=fundraiser)
            cart.quantity += quantity
            cart.save()
            return Response({"message": "Product added to cart"}, status=status.HTTP_200_OK)
            
        cart = Cart.objects.create(user=request.user, product=product, quantity=quantity, fundraiser=fundraiser)
        return Response({"message": "Product added to cart"}, status=status.HTTP_201_CREATED)


class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart = Cart.objects.filter(user=request.user)
        serializer = CartSerializer(cart, many=True)
        
        cart_total = 0
        for item in cart:
            try:
                cart_total += float(item.product.price) * item.quantity
            except (ValueError, TypeError):
                pass
                
        delivery_charge = 0.00

        return Response({
            "items": serializer.data,
            "subtotal": cart_total,
            "delivery_charge": delivery_charge,
            "cart_total": cart_total + delivery_charge
        })


class CartUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, id):
        action = request.data.get('action')
        
        if not action or action not in ['increase', 'decrease']:
            return Response({"error": "Valid action ('increase' or 'decrease') is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = Cart.objects.get(id=id, user=request.user)
        except Cart.DoesNotExist:
            return Response({"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)

        if action == 'increase':
            cart_item.quantity += 1
        elif action == 'decrease':
            cart_item.quantity -= 1
            if cart_item.quantity <= 0:
                cart_item.delete()
                return Response({"message": "Item removed from cart"}, status=status.HTTP_200_OK)
        
        cart_item.save()
        serializer = CartSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CartDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, id):
        try:
            cart_item = Cart.objects.get(id=id, user=request.user)
        except Cart.DoesNotExist:
            return Response({"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)
        
        cart_item.delete()
        return Response({"message": "Item removed from cart"}, status=status.HTTP_200_OK)


class AddressValidationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            address = validate_us_address(request.data.get("address", request.data))
        except AddressValidationError as exc:
            return Response({"valid": False, "error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"valid": True, "address": address}, status=status.HTTP_200_OK)


class CreateCheckoutSessionView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        write_checkout_log("CreateCheckoutSessionView", request)
        
        is_guest = not request.user.is_authenticated
        payload_cart = request.data.get('cart')
        
        order_items_to_create = [] # List of tuples: (product, quantity, fundraiser)
        line_items = []
        total_weight_ounces = 0.0

        if not is_guest:
            # Authenticated User: Sync payload cart to database cart
            if payload_cart and isinstance(payload_cart, list):
                Cart.objects.filter(user=request.user).delete()
                for item in payload_cart:
                    slug = item.get('slug')
                    quantity = item.get('quantity', 1)
                    fundraiser_id = item.get('fundraiser_id')
                    try:
                        product = Product.objects.get(slug=slug, is_active=True)
                        fundraiser = None
                        if fundraiser_id:
                            from event.models import Fundraiser
                            try:
                                fundraiser = Fundraiser.objects.get(id=fundraiser_id)
                            except Fundraiser.DoesNotExist:
                                pass
                        Cart.objects.create(user=request.user, product=product, quantity=quantity, fundraiser=fundraiser)
                    except Product.DoesNotExist:
                        pass
            
            cart_items = Cart.objects.filter(user=request.user)
            if not cart_items.exists():
                write_checkout_log("CreateCheckoutSessionView", request, error="Cart is empty")
                return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
                
            for item in cart_items:
                try:
                    unit_amount = int(float(item.product.price) * 100)
                except (ValueError, TypeError):
                    unit_amount = 0
                    
                line_items.append({
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': item.product.name},
                        'unit_amount': unit_amount,
                    },
                    'quantity': item.quantity,
                })
                
                try:
                    weight = float(item.product.weight)
                except (ValueError, TypeError, AttributeError):
                    weight = 12.0
                total_weight_ounces += (weight * item.quantity)
                order_items_to_create.append((item.product, item.quantity, item.fundraiser))
                
        else:
            # Guest User logic
            if not payload_cart or not isinstance(payload_cart, list):
                write_checkout_log("CreateCheckoutSessionView", request, error="Cart is empty or invalid format")
                return Response({"error": "Cart is empty or invalid format. Expecting a list of items under 'cart' key."}, status=status.HTTP_400_BAD_REQUEST)
                
            for item in payload_cart:
                slug = item.get('slug')
                quantity = item.get('quantity', 1)
                fundraiser_id = item.get('fundraiser_id')
                try:
                    product = Product.objects.get(slug=slug, is_active=True)
                    unit_amount = int(float(product.price) * 100)
                    
                    line_items.append({
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {'name': product.name},
                            'unit_amount': unit_amount,
                        },
                        'quantity': quantity,
                    })
                    
                    fundraiser = None
                    if fundraiser_id:
                        from event.models import Fundraiser
                        fundraiser = Fundraiser.objects.filter(id=fundraiser_id).first()
                    order_items_to_create.append((product, quantity, fundraiser))
                    
                    try:
                        weight = float(product.weight)
                    except (ValueError, TypeError, AttributeError):
                        weight = 12.0
                    total_weight_ounces += (weight * quantity)
                except (Product.DoesNotExist, ValueError, TypeError):
                    continue
                    
            if not line_items:
                write_checkout_log("CreateCheckoutSessionView", request, error="No valid products found")
                return Response({"error": "No valid products found"}, status=status.HTTP_400_BAD_REQUEST)

        # Common Address Validation
        try:
            address = validate_us_address(request.data.get("address"))
        except AddressValidationError as exc:
            write_checkout_log("CreateCheckoutSessionView", request, error=f"Address Validation Failed: {str(exc)}")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if not is_guest:
            name = request.data.get("name") or request.user.full_name
            email = request.data.get("email") or request.user.email
            phone = request.data.get("phone") or request.user.phone
        else:
            name = request.data.get("name")
            email = request.data.get("email")
            phone = request.data.get("phone")
            
        try:
            from .shipstation import get_shipping_rate
            delivery_charge_dollars = get_shipping_rate(address, total_weight_ounces)
        except Exception:
            delivery_charge_dollars = 5.00
            
        customer = None
        idempotency_key = request.data.get('idempotency_key', str(uuid.uuid4()))
        try:
            customer = create_stripe_customer(address, name, email, phone)
            
            shop_id = next((f.id for _, _, f in order_items_to_create if f), None)
            params = {}
            if shop_id:
                params['shop_id'] = shop_id
            success_url = get_payment_success_url(params)

            checkout_kwargs = {
                'idempotency_key': idempotency_key,
                'payment_method_types': ['card'],
                'line_items': line_items,
                'mode': 'payment',
                'success_url': success_url,
                'cancel_url': get_payment_cancel_url(),
                'customer': customer.id,
                'metadata': address_session_metadata(address, name, email, phone),
                'payment_intent_data': {
                    "metadata": address_session_metadata(address, name, email, phone),
                },
                'shipping_options': [
                    {
                        "shipping_rate_data": {
                            "type": "fixed_amount",
                            "fixed_amount": {"amount": int(delivery_charge_dollars * 100), "currency": "usd"},
                            "display_name": "Standard Shipping",
                            "delivery_estimate": {
                                "minimum": {"unit": "business_day", "value": 3},
                                "maximum": {"unit": "business_day", "value": 5},
                            },
                        },
                    },
                ],
                'phone_number_collection': {
                    'enabled': True
                },
            }
            
            if not is_guest:
                checkout_kwargs['client_reference_id'] = str(request.user.id)

            checkout_session = stripe.checkout.Session.create(**checkout_kwargs)
            
            # Pre-create unpaid orders atomically
            with transaction.atomic():
                for product, quantity, fundraiser in order_items_to_create:
                    Order.objects.create(
                        user=request.user if not is_guest else None,
                        product=product,
                        quantity=quantity,
                        fundraiser=fundraiser,
                        stripe_session_id=checkout_session.id,
                        invoice_id=idempotency_key,
                        is_paid=False,
                        delivery_charge="0.00"
                    )

            return Response({'sessionId': checkout_session.id, 'url': checkout_session.url})
        except Exception as e:
            write_checkout_log("CreateCheckoutSessionView", request, error=f"Exception: {str(e)}")
            if customer:
                try:
                    stripe.Customer.delete(customer.id)
                except Exception:
                    pass
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            if event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                metadata_obj = getattr(session, 'metadata', {}) or {}
                metadata = metadata_obj._data if hasattr(metadata_obj, '_data') else metadata_obj
                if metadata.get('type') == 'donation' or Donation.objects.filter(stripe_session_id=session.id).exists():
                    finalize_donation(session)
                else:
                    finalize_order(session)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'status': 'success'}, status=status.HTTP_200_OK)

class OrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user, is_paid=True).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@transaction.atomic
def finalize_order(session):
    if session.payment_status != 'paid':
        return

    user_id = getattr(session, 'client_reference_id', None)
    
    customer_details = getattr(session, 'customer_details', None)
    shipping_details = getattr(session, 'shipping_details', None)
    metadata_obj = getattr(session, 'metadata', {}) or {}
    metadata = metadata_obj._data if hasattr(metadata_obj, '_data') else metadata_obj
    
    email = (customer_details.email if customer_details else None) or metadata.get("shipping_email")
    phone = (customer_details.phone if customer_details else None) or metadata.get("shipping_phone")
    
    address_obj = None
    name = metadata.get("shipping_name")
    if shipping_details:
        address_obj = shipping_details.address
        name = shipping_details.name or name
    elif customer_details:
        address_obj = customer_details.address
        name = customer_details.name or name
        
    if address_obj:
        if address_obj.line2:
            address = f"{address_obj.line1}\n{address_obj.line2}".strip()
        else:
            address = address_obj.line1
    else:
        address = metadata.get("shipping_line1")
    city = address_obj.city if address_obj else metadata.get("shipping_city")
    state = address_obj.state if address_obj else metadata.get("shipping_state")
    postal_code = address_obj.postal_code if address_obj else metadata.get("shipping_postal_code")
    country = address_obj.country if address_obj else metadata.get("shipping_country")

    shipping_cost = 0.00
    if hasattr(session, 'total_details') and session.total_details and hasattr(session.total_details, 'amount_shipping'):
        if session.total_details.amount_shipping:
            shipping_cost = session.total_details.amount_shipping / 100.0

    # Handle Guest/Pre-created Orders
    unpaid_orders = Order.objects.filter(stripe_session_id=session.id, is_paid=False)
    if unpaid_orders.exists():
        first_order = True
        for order in unpaid_orders:
            order.is_paid = True
            order.email = email
            order.phone = phone
            order.name = name
            order.address = address
            order.city = city
            order.state = state
            order.postal_code = postal_code
            order.country = country
            if first_order:
                order.delivery_charge = str(shipping_cost)
                first_order = False
            else:
                order.delivery_charge = "0.00"
            if user_id:
                try:
                    order.user = User.objects.get(id=int(user_id))
                except (User.DoesNotExist, ValueError, TypeError):
                    pass
            order.save()
            try:
                from .shipstation import send_order_to_shipstation
                send_order_to_shipstation(order)
            except Exception:
                pass
            
            if order.fundraiser and order.fundraiser.user:
                send_push_notification(
                    user=order.fundraiser.user,
                    title="New Order Received",
                    body=f"Someone purchased '{order.product.name}' from your shop.",
                    data={"fundraiser_id": str(order.fundraiser.id), "order_id": str(order.id), "type": "new_order"}
                )
                
        # Send confirmation email to customer
        try:
            from authentication.emails import send_order_confirmation_email
            send_order_confirmation_email(email, name, list(unpaid_orders))
        except Exception:
            pass
            
        # Clear cart for user if user exists
        if user_id:
            try:
                user = User.objects.get(id=int(user_id))
                Cart.objects.filter(user=user).delete()
            except (User.DoesNotExist, ValueError, TypeError):
                pass

    # Handle Legacy Authenticated Flow (if orders weren't created beforehand)
    elif user_id:
        try:
            user = User.objects.get(id=int(user_id))
            cart_items = Cart.objects.filter(user=user)
            created_orders = []
            first_order = True
            for item in cart_items:
                order = Order.objects.create(
                    user=user,
                    fundraiser=item.fundraiser,
                    product=item.product,
                    quantity=item.quantity,
                    is_paid=True,
                    stripe_session_id=session.id,
                    email=email,
                    phone=phone,
                    name=name,
                    address=address,
                    city=city,
                    state=state,
                    postal_code=postal_code,
                    country=country,
                    delivery_charge=str(shipping_cost) if first_order else "0.00"
                )
                first_order = False
                created_orders.append(order)
                try:
                    from .shipstation import send_order_to_shipstation
                    send_order_to_shipstation(order)
                except Exception:
                    pass
                
                if order.fundraiser and order.fundraiser.user:
                    send_push_notification(
                        user=order.fundraiser.user,
                        title="New Order Received",
                        body=f"Someone purchased '{order.product.name}' from your shop.",
                        data={"fundraiser_id": str(order.fundraiser.id), "order_id": str(order.id), "type": "new_order"}
                    )
            
            # Send confirmation email to customer
            try:
                from authentication.emails import send_order_confirmation_email
                send_order_confirmation_email(email, name, created_orders)
            except Exception:
                pass
                
            cart_items.delete()
        except (User.DoesNotExist, ValueError, TypeError):
            pass


@transaction.atomic
def finalize_donation(session):
    if getattr(session, 'payment_status', None) != 'paid':
        return None

    donation = Donation.objects.filter(stripe_session_id=session.id).first()
    metadata_obj = getattr(session, 'metadata', {}) or {}
    metadata = metadata_obj._data if hasattr(metadata_obj, '_data') else metadata_obj

    if not donation:
        donation_item_id = metadata.get('donation_item_id')
        fundraiser_id = metadata.get('fundraiser_id')
        amount_val = metadata.get('amount')
        if not amount_val and hasattr(session, 'amount_total') and session.amount_total:
            amount_val = round(session.amount_total / 100.0, 2)
        else:
            amount_val = round(float(amount_val or 0.0), 2)

        donation_item = DonationItem.objects.filter(id=donation_item_id).first() if donation_item_id else None
        fundraiser = None
        if fundraiser_id:
            from event.models import Fundraiser
            try:
                fundraiser = Fundraiser.objects.filter(id=fundraiser_id).first()
            except (ValueError, TypeError):
                fundraiser = None

        donation = Donation.objects.create(
            donation_item=donation_item,
            fundraiser=fundraiser,
            amount=amount_val,
            quantity=1,
            stripe_session_id=session.id,
            is_paid=True,
        )

    customer_details = getattr(session, 'customer_details', None)
    name = metadata.get('donor_name')
    email = metadata.get('donor_email')
    phone = metadata.get('donor_phone')

    if customer_details:
        c_name = getattr(customer_details, 'name', None)
        c_email = getattr(customer_details, 'email', None)
        c_phone = getattr(customer_details, 'phone', None)
        if isinstance(c_name, str) and c_name:
            name = c_name
        if isinstance(c_email, str) and c_email:
            email = c_email
        if isinstance(c_phone, str) and c_phone:
            phone = c_phone

    if name and not donation.name:
        donation.name = name
    if email and not donation.email:
        donation.email = email
    if phone and not donation.phone:
        donation.phone = phone

    user_id = getattr(session, 'client_reference_id', None) or metadata.get('user_id')
    if user_id and not donation.user:
        try:
            donation.user = User.objects.get(id=int(user_id))
        except (User.DoesNotExist, ValueError, TypeError):
            pass

    donation.is_paid = True
    donation.save()

    # If linked to a fundraiser organizer, send push notification
    if donation.fundraiser and donation.fundraiser.user:
        try:
            donor_display = donation.name or "Someone"
            send_push_notification(
                user=donation.fundraiser.user,
                title="New Donation Received",
                body=f"{donor_display} donated ${donation.amount} to your campaign.",
                data={"fundraiser_id": str(donation.fundraiser.id), "donation_id": str(donation.id), "type": "new_donation"}
            )
        except Exception:
            pass

    return donation


class PaymentSuccessView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        session_id = request.data.get('session_id')
        if not session_id:
            return Response({'error': 'Session ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                metadata_obj = getattr(session, 'metadata', {}) or {}
                metadata = metadata_obj._data if hasattr(metadata_obj, '_data') else metadata_obj
                if metadata.get('type') == 'donation' or Donation.objects.filter(stripe_session_id=session.id).exists():
                    donation = finalize_donation(session)
                    shop_id = donation.fundraiser_id if donation else (metadata.get('fundraiser_id') or None)
                    return Response({
                        'message': 'Payment successful, donation recorded.',
                        'type': 'donation',
                        'shop_id': shop_id,
                        'fundraiser_id': shop_id
                    }, status=status.HTTP_200_OK)
                else:
                    finalize_order(session)
                    first_order = Order.objects.filter(stripe_session_id=session.id).first()
                    shop_id = first_order.fundraiser_id if first_order else None
                    return Response({
                        'message': 'Payment successful, order created.',
                        'type': 'order',
                        'shop_id': shop_id,
                        'fundraiser_id': shop_id
                    }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Payment not successful'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GuestCheckoutSessionView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        write_checkout_log("GuestCheckoutSessionView", request)
        cart = request.data.get('cart', [])
        if not cart or not isinstance(cart, list):
            write_checkout_log("GuestCheckoutSessionView", request, error="Cart is empty or invalid format")
            return Response({"error": "Cart is empty or invalid format. Expecting a list of items under 'cart' key."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            address = validate_us_address(request.data.get("address"))
        except AddressValidationError as exc:
            write_checkout_log("GuestCheckoutSessionView", request, error=f"Address Validation Failed: {str(exc)}")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        name = request.data.get("name")
        email = request.data.get("email")
        phone = request.data.get("phone")
            
        line_items = []
        order_items_to_create = []

        for item in cart:
            slug = item.get('slug')
            quantity = item.get('quantity', 1)
            fundraiser_id = item.get('fundraiser_id')
            try:
                product = Product.objects.get(slug=slug, is_active=True)
                unit_amount = int(float(product.price) * 100)
                
                line_items.append({
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': product.name,
                        },
                        'unit_amount': unit_amount,
                    },
                    'quantity': quantity,
                })
                order_items_to_create.append((product, quantity, fundraiser_id))
            except (Product.DoesNotExist, ValueError, TypeError):
                continue
                
        if not line_items:
            write_checkout_log("GuestCheckoutSessionView", request, error="No valid products found")
            return Response({"error": "No valid products found"}, status=status.HTTP_400_BAD_REQUEST)

        total_weight_ounces = 0.0
        for product, quantity, fundraiser_id in order_items_to_create:
            try:
                weight = float(product.weight)
            except (ValueError, TypeError, AttributeError):
                weight = 12.0
            total_weight_ounces += (weight * quantity)

        try:
            from .shipstation import get_shipping_rate
            delivery_charge_dollars = get_shipping_rate(address, total_weight_ounces)
        except Exception:
            delivery_charge_dollars = 5.00

        customer = None
        idempotency_key = request.data.get('idempotency_key', str(uuid.uuid4()))
        try:
            shop_id = next((fid for _, _, fid in order_items_to_create if fid), None)
            params = {}
            if shop_id:
                params['shop_id'] = shop_id
            success_url = get_payment_success_url(params)

            checkout_session = stripe.checkout.Session.create(
                idempotency_key=idempotency_key,
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=success_url,
                cancel_url=get_payment_cancel_url(),
                customer=customer.id,
                metadata=address_session_metadata(address, name, email, phone),
                payment_intent_data={
                    "metadata": address_session_metadata(address, name, email, phone),
                },
                shipping_options=[
                    {
                        "shipping_rate_data": {
                            "type": "fixed_amount",
                            "fixed_amount": {"amount": int(delivery_charge_dollars * 100), "currency": "usd"},
                            "display_name": "Standard Shipping",
                            "delivery_estimate": {
                                "minimum": {"unit": "business_day", "value": 3},
                                "maximum": {"unit": "business_day", "value": 5},
                            },
                        },
                    },
                ],
                phone_number_collection={
                    'enabled': True
                },
            )
            
            # Create unpaid orders beforehand to link them with session_id atomically
            with transaction.atomic():
                for product, quantity, fundraiser_id in order_items_to_create:
                    fundraiser = None
                    if fundraiser_id:
                        from event.models import Fundraiser
                        fundraiser = Fundraiser.objects.filter(id=fundraiser_id).first()
                        
                    Order.objects.create(
                        product=product,
                        quantity=quantity,
                        fundraiser=fundraiser,
                        stripe_session_id=checkout_session.id,
                        invoice_id=idempotency_key,
                        is_paid=False,
                        delivery_charge="0.00"
                    )
                
            return Response({'sessionId': checkout_session.id, 'url': checkout_session.url})
        except Exception as e:
            write_checkout_log("GuestCheckoutSessionView", request, error=f"Exception: {str(e)}")
            if customer:
                try:
                    stripe.Customer.delete(customer.id)
                except Exception:
                    pass
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateDonationCheckoutSessionView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        write_checkout_log("CreateDonationCheckoutSessionView", request)

        donation_item_id = request.data.get('donation_item_id')
        slug = request.data.get('slug')
        fundraiser_id = request.data.get('fundraiser_id') or request.data.get('shop_id')
        custom_amount = request.data.get('amount')

        donation_item = None
        if donation_item_id:
            donation_item = DonationItem.objects.filter(id=donation_item_id, is_active=True).first()
        elif slug:
            donation_item = DonationItem.objects.filter(slug=slug, is_active=True).first()

        if not donation_item and not custom_amount:
            return Response({"error": "Please provide a valid donation item or donation amount."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if custom_amount is not None:
                amount = round(float(custom_amount), 2)
            else:
                amount = round(float(donation_item.price), 2)
            if amount <= 0:
                raise ValueError("Amount must be greater than zero")
        except (ValueError, TypeError):
            return Response({"error": "Invalid donation amount."}, status=status.HTTP_400_BAD_REQUEST)

        fundraiser = None
        if fundraiser_id:
            from event.models import Fundraiser
            try:
                fundraiser = Fundraiser.objects.filter(id=fundraiser_id).first()
            except (ValueError, TypeError):
                fundraiser = None
            if not fundraiser:
                return Response(
                    {"error": f"Shop / Fundraiser with ID '{fundraiser_id}' does not exist."},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Donor details (NO shipping address required, NO address validation)
        is_guest = not request.user.is_authenticated
        if not is_guest:
            name = request.data.get("name") or request.user.full_name
            email = request.data.get("email") or request.user.email
            phone = request.data.get("phone") or request.user.phone
        else:
            name = request.data.get("name")
            email = request.data.get("email")
            phone = request.data.get("phone")

        item_title = donation_item.name if donation_item else "Direct Donation"
        description = (donation_item.description if donation_item and donation_item.description else "Donation")

        line_items = [{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f"Donation: {item_title}",
                    'description': description,
                },
                'unit_amount': int(amount * 100),
            },
            'quantity': 1,  # Always 1, no increase or decrease
        }]

        idempotency_key = request.data.get('idempotency_key', str(uuid.uuid4()))

        try:
            params = {'type': 'donation'}
            if fundraiser:
                params['shop_id'] = fundraiser.id
            success_url = get_payment_success_url(params)

            checkout_kwargs = {
                'idempotency_key': idempotency_key,
                'payment_method_types': ['card'],
                'line_items': line_items,
                'mode': 'payment',
                'success_url': success_url,
                'cancel_url': get_payment_cancel_url(),
                'metadata': {
                    'type': 'donation',
                    'donation_item_id': str(donation_item.id) if donation_item else '',
                    'fundraiser_id': str(fundraiser.id) if fundraiser else '',
                    'donor_name': name or '',
                    'donor_email': email or '',
                    'donor_phone': phone or '',
                    'amount': str(amount),
                    'user_id': str(request.user.id) if not is_guest else '',
                },
                'payment_intent_data': {
                    'metadata': {
                        'type': 'donation',
                        'donation_item_id': str(donation_item.id) if donation_item else '',
                        'fundraiser_id': str(fundraiser.id) if fundraiser else '',
                    },
                },
            }

            if email:
                checkout_kwargs['customer_email'] = email
            if not is_guest:
                checkout_kwargs['client_reference_id'] = str(request.user.id)

            checkout_session = stripe.checkout.Session.create(**checkout_kwargs)

            # Pre-create unpaid donation record (NO cart, NO ShipStation)
            Donation.objects.create(
                user=request.user if not is_guest else None,
                donation_item=donation_item,
                fundraiser=fundraiser,
                amount=amount,
                quantity=1,
                name=name,
                email=email,
                phone=phone,
                stripe_session_id=checkout_session.id,
                is_paid=False,
            )

            return Response({'sessionId': checkout_session.id, 'url': checkout_session.url}, status=status.HTTP_200_OK)
        except Exception as e:
            write_checkout_log("CreateDonationCheckoutSessionView", request, error=f"Exception: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductReviewListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        try:
            product = Product.objects.get(slug=slug)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        
        from .models import Review
        from .serializers import ReviewSerializer
        reviews = Review.objects.all().order_by('-created_at')
        serializer = ReviewSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class LatestReview(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        from .models import Review
        from .serializers import ReviewSerializer
        reviews = Review.objects.filter().order_by('-created_at')[:10]
        serializer = ReviewSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class ShipStationWebhookView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        import logging
        import requests
        import base64
        from django.conf import settings
        from .models import Order

        logger = logging.getLogger(__name__)
        payload = request.data
        logger.info(f"Incoming ShipStation Webhook: {payload}")

        resource_url = payload.get('resource_url')
        resource_type = payload.get('resource_type')

        if resource_type == "shipnotify" and resource_url:
            api_key = getattr(settings, 'SHIPSTATION_API_KEY', None)
            api_secret = getattr(settings, 'SHIPSTATION_API_SECRET', None)
            
            if not api_key or not api_secret:
                logger.error("ShipStation keys are not configured. Cannot retrieve shipment details.")
                return Response({'error': 'Credentials not configured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            auth_str = f"{api_key}:{api_secret}"
            auth_bytes = auth_str.encode('ascii')
            base64_bytes = base64.b64encode(auth_bytes)
            base64_str = base64_bytes.decode('ascii')
            
            headers = {
                'Authorization': f'Basic {base64_str}',
                'Accept': 'application/json'
            }

            try:
                resp = requests.get(resource_url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    shipment_data = resp.json()
                    shipments = shipment_data.get('shipments', [])
                    for shipment in shipments:
                        order_number_str = shipment.get('orderNumber', '')
                        tracking_number = shipment.get('trackingNumber')
                        carrier = shipment.get('carrierCode')
                        
                        if order_number_str.startswith("Order-"):
                            try:
                                order_id = int(order_number_str.replace("Order-", ""))
                                order = Order.objects.filter(id=order_id).first()
                                if order:
                                    order.tracking_number = tracking_number
                                    order.carrier = carrier
                                    order.shipment_status = "shipped"
                                    order.save()
                                    logger.info(f"Updated Order {order_id} tracking to {tracking_number} ({carrier}).")
                            except ValueError:
                                logger.error(f"Invalid order number format: {order_number_str}")
                else:
                    logger.error(f"ShipStation API request failed with status: {resp.status_code}")
            except Exception as e:
                logger.error(f"Error handling ShipStation shipment fetch: {str(e)}")

        return Response({'status': 'success'}, status=status.HTTP_200_OK)


# Helper to fetch dashboard metrics
def calculate_dashboard_metrics(filters_dict):
    import datetime
    from django.utils import timezone
    from django.db.models import Q
    from event.models import Event, OrganizationType
    from shop.models import Order

    # 1. Gather choices
    organizations = OrganizationType.objects.all()
    campaigns = Event.objects.all()
    states_list = sorted(list(set(Order.objects.filter(is_paid=True).exclude(state__isnull=True).exclude(state='').values_list('state', flat=True))))

    # Extract filter parameters
    selected_org = filters_dict.get('organization', '')
    selected_campaign = filters_dict.get('campaign', '')
    selected_state = filters_dict.get('state', '')
    selected_status = filters_dict.get('status', '')
    start_date_str = filters_dict.get('start_date', '')
    end_date_str = filters_dict.get('end_date', '')

    # 2. Filter orders base query
    orders_qs = Order.objects.select_related('product', 'fundraiser', 'fundraiser__event', 'fundraiser__event__type', 'fundraiser__user').all()

    if start_date_str:
        try:
            start_date = timezone.make_aware(datetime.datetime.strptime(start_date_str, '%Y-%m-%d'))
            orders_qs = orders_qs.filter(created_at__gte=start_date)
        except Exception:
            pass
    if end_date_str:
        try:
            end_date = timezone.make_aware(datetime.datetime.strptime(end_date_str, '%Y-%m-%d') + datetime.timedelta(days=1))
            orders_qs = orders_qs.filter(created_at__lt=end_date)
        except Exception:
            pass

    if selected_org:
        orders_qs = orders_qs.filter(fundraiser__event__type_id=selected_org)

    if selected_campaign:
        orders_qs = orders_qs.filter(fundraiser__event_id=selected_campaign)

    if selected_state:
        orders_qs = orders_qs.filter(state__iexact=selected_state)

    if selected_status:
        if selected_status == 'paid':
            orders_qs = orders_qs.filter(is_paid=True)
        elif selected_status == 'unpaid':
            orders_qs = orders_qs.filter(is_paid=False)
        elif selected_status == 'shipped':
            orders_qs = orders_qs.filter(is_paid=True, shipment_status='shipped')
        elif selected_status == 'unshipped':
            orders_qs = orders_qs.filter(is_paid=True, shipment_status='unshipped')

    paid_orders = orders_qs.filter(is_paid=True)
    unpaid_orders = orders_qs.filter(is_paid=False)

    def sum_sales(qs):
        total = 0.0
        for o in qs:
            try:
                total += float(o.product.price) * o.quantity
            except Exception:
                pass
        return total

    # Time-based sales (among paid orders matching other filters)
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    this_week_start = today_start - datetime.timedelta(days=7)
    this_month_start = today_start.replace(day=1)
    this_year_start = today_start.replace(month=1, day=1)

    sales_today = sum_sales(paid_orders.filter(created_at__gte=today_start))
    sales_week = sum_sales(paid_orders.filter(created_at__gte=this_week_start))
    sales_month = sum_sales(paid_orders.filter(created_at__gte=this_month_start))
    sales_ytd = sum_sales(paid_orders.filter(created_at__gte=this_year_start))
    total_sales = sum_sales(paid_orders)

    # Chart Data (Last 7 days)
    chart_labels = []
    chart_values = []
    for i in range(6, -1, -1):
        day = today_start - datetime.timedelta(days=i)
        next_day = day + datetime.timedelta(days=1)
        day_sales = sum_sales(paid_orders.filter(created_at__gte=day, created_at__lt=next_day))
        chart_labels.append(day.strftime('%b %d'))
        chart_values.append(day_sales)

    donations_qs = Donation.objects.filter(is_paid=True)
    if start_date_str:
        try:
            donations_qs = donations_qs.filter(created_at__gte=start_date)
        except Exception:
            pass
    if end_date_str:
        try:
            donations_qs = donations_qs.filter(created_at__lt=end_date)
        except Exception:
            pass
    if selected_campaign:
        donations_qs = donations_qs.filter(fundraiser__event_id=selected_campaign)
    if selected_org:
        donations_qs = donations_qs.filter(fundraiser__event__type_id=selected_org)

    total_donations = sum(float(d.amount) for d in donations_qs)

    event_sales = sum_sales(paid_orders.filter(fundraiser__isnull=False))
    non_event_sales = sum_sales(paid_orders.filter(fundraiser__isnull=True))

    event_donations = sum(float(d.amount) for d in donations_qs.filter(fundraiser__isnull=False))
    non_event_donations = sum(float(d.amount) for d in donations_qs.filter(fundraiser__isnull=True))

    # Product sales split 50/50, donations split 75% Treats Island and 25% Organization
    owed_to_organizations = (event_sales * 0.5) + (event_donations * 0.25)
    treats_island_revenue = (event_sales * 0.5) + non_event_sales + (event_donations * 0.75) + non_event_donations

    # Campaigns (Events) counts
    events_filtered = Event.objects.all()
    if selected_org:
        events_filtered = events_filtered.filter(type_id=selected_org)
    if selected_campaign:
        events_filtered = events_filtered.filter(id=selected_campaign)

    active_campaigns_count = events_filtered.filter(start_date__lte=now, end_date__gte=now, is_active=True).count()
    upcoming_campaigns_count = events_filtered.filter(start_date__gt=now).count()
    
    ending_soon_qs = events_filtered.filter(end_date__gt=now, end_date__lte=now + datetime.timedelta(days=3))
    ending_soon_campaigns_count = ending_soon_qs.count()
    ending_soon_campaigns = list(ending_soon_qs[:5])

    # Orders counts
    total_orders_count = orders_qs.count()

    five_days_ago = now - datetime.timedelta(days=5)
    orders_needing_attention = paid_orders.filter(
        Q(shipment_status='unshipped', created_at__lt=five_days_ago) |
        Q(address__isnull=True) | Q(address='') |
        Q(city__isnull=True) | Q(city='')
    )
    orders_needing_attention_count = orders_needing_attention.count()

    failed_payments_count = unpaid_orders.exclude(stripe_session_id__isnull=True).exclude(stripe_session_id='').count()

    address_problems_count = paid_orders.filter(
        Q(address__isnull=True) | Q(address='') |
        Q(city__isnull=True) | Q(city='') |
        Q(state__isnull=True) | Q(state='') |
        Q(postal_code__isnull=True) | Q(postal_code='')
    ).count()

    unshipped_orders_count = paid_orders.filter(shipment_status='unshipped').count()
    refund_requests_count = 0
    new_orgs_count = OrganizationType.objects.all().count()

    org_performance = {}
    for o in paid_orders:
        if o.fundraiser and o.fundraiser.event and o.fundraiser.event.type:
            org_name = o.fundraiser.event.type.name
            try:
                val = float(o.product.price) * o.quantity
            except Exception:
                val = 0.0
            org_performance[org_name] = org_performance.get(org_name, 0.0) + val
    for d in donations_qs:
        if d.fundraiser and d.fundraiser.event and d.fundraiser.event.type:
            org_name = d.fundraiser.event.type.name
            try:
                val = float(d.amount)
            except Exception:
                val = 0.0
            org_performance[org_name] = org_performance.get(org_name, 0.0) + val

    top_orgs = sorted(org_performance.items(), key=lambda x: x[1], reverse=True)[:5]

    part_performance = {}
    for o in paid_orders:
        if o.fundraiser and o.fundraiser.user:
            part_name = o.fundraiser.user.full_name or o.fundraiser.user.phone
            try:
                val = float(o.product.price) * o.quantity
            except Exception:
                val = 0.0
            part_performance[part_name] = part_performance.get(part_name, 0.0) + val
    for d in donations_qs:
        if d.fundraiser and d.fundraiser.user:
            part_name = d.fundraiser.user.full_name or d.fundraiser.user.phone
            try:
                val = float(d.amount)
            except Exception:
                val = 0.0
            part_performance[part_name] = part_performance.get(part_name, 0.0) + val

    top_participants = sorted(part_performance.items(), key=lambda x: x[1], reverse=True)[:5]

    # Recent Activity Mockup
    recent_activity = []
    for e in Event.objects.order_by('-id')[:3]:
        recent_activity.append(f"New campaign created: {e.name or 'Event ' + str(e.id)}")
    for o in Order.objects.order_by('-id')[:2]:
        recent_activity.append(f"New order placed for {o.product.name}")
    for d in Donation.objects.filter(is_paid=True).order_by('-id')[:2]:
        donor_name = d.name or "A supporter"
        recent_activity.append(f"{donor_name} donated ${d.amount}")

    return {
        'organizations': organizations,
        'campaigns': campaigns,
        'states': states_list,

        'selected_org': selected_org,
        'selected_campaign': selected_campaign,
        'selected_state': selected_state,
        'selected_status': selected_status,
        'start_date': start_date_str,
        'end_date': end_date_str,

        'sales_today': sales_today,
        'sales_week': sales_week,
        'sales_month': sales_month,
        'sales_ytd': sales_ytd,
        'total_sales': total_sales,
        'total_donations': total_donations,
        'owed_to_organizations': owed_to_organizations,
        'treats_island_revenue': treats_island_revenue,

        'active_campaigns_count': active_campaigns_count,
        'upcoming_campaigns_count': upcoming_campaigns_count,
        'ending_soon_campaigns_count': ending_soon_campaigns_count,

        'total_orders_count': total_orders_count,
        'orders_needing_attention_count': orders_needing_attention_count,
        'failed_payments_count': failed_payments_count,
        'address_problems_count': address_problems_count,
        'unshipped_orders_count': unshipped_orders_count,
        'refund_requests_count': refund_requests_count,
        'new_orgs_count': new_orgs_count,

        'top_orgs': top_orgs,
        'top_participants': top_participants,
        'ending_soon_campaigns': ending_soon_campaigns,
        'recent_activity': recent_activity,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
    }


from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

@staff_member_required
def admin_dashboard_html_view(request):
    metrics = calculate_dashboard_metrics(request.GET)
    return render(request, 'admin/dashboard.html', metrics)


class AdminDashboardAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        metrics = calculate_dashboard_metrics(request.GET)
        serialized_metrics = {
            'selected_org': metrics['selected_org'],
            'selected_campaign': metrics['selected_campaign'],
            'selected_state': metrics['selected_state'],
            'selected_status': metrics['selected_status'],
            'start_date': metrics['start_date'],
            'end_date': metrics['end_date'],

            'sales_today': metrics['sales_today'],
            'sales_week': metrics['sales_week'],
            'sales_month': metrics['sales_month'],
            'sales_ytd': metrics['sales_ytd'],
            'total_sales': metrics['total_sales'],
            'total_donations': metrics['total_donations'],
            'owed_to_organizations': metrics['owed_to_organizations'],
            'treats_island_revenue': metrics['treats_island_revenue'],

            'active_campaigns_count': metrics['active_campaigns_count'],
            'upcoming_campaigns_count': metrics['upcoming_campaigns_count'],
            'ending_soon_campaigns_count': metrics['ending_soon_campaigns_count'],

            'total_orders_count': metrics['total_orders_count'],
            'orders_needing_attention_count': metrics['orders_needing_attention_count'],
            'failed_payments_count': metrics['failed_payments_count'],
            'address_problems_count': metrics['address_problems_count'],
            'unshipped_orders_count': metrics['unshipped_orders_count'],
            'refund_requests_count': metrics['refund_requests_count'],
            'new_orgs_count': metrics['new_orgs_count'],

            'top_orgs': metrics['top_orgs'],
            'top_participants': metrics['top_participants'],
        }
        return Response(serialized_metrics, status=status.HTTP_200_OK)

