from rest_framework.views import APIView
from django.shortcuts import render
from . models import Product, Cart, Order
from . serializers import ProductSerializer, CartSerializer, OrderSerializer
from rest_framework import permissions, status
from rest_framework.response import Response
import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.contrib.auth import get_user_model
User = get_user_model()
from notification.utils import send_push_notification
from .models import Review
from .serializers import ReviewSerializer
from django.db import transaction
import uuid
from .utils import AddressValidationError, validate_us_address

stripe.api_key = settings.STRIPE_SECRET_KEY


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

    @method_decorator(cache_page(60 * 15))
    def get(self, request):
        products = Product.objects.filter(is_active=True)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
        

class ProductDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    @method_decorator(cache_page(60 * 15))
    def get(self, request, slug):
        try:
            product = Product.objects.get(slug=slug, is_active=True)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product)
        
        # from .models import Review
        # from .serializers import ReviewSerializer
        # reviews = Review.objects.all().order_by('-created_at')
        # review_serializer = ReviewSerializer(reviews, many=True, context={'request': request})
        
        data = serializer.data
        # data['reviews'] = review_serializer.data
        
        return Response(data)


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
                
        delivery_charge = 5.00 if cart.exists() else 0.00

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
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        payload_cart = request.data.get('cart')
        if payload_cart and isinstance(payload_cart, list):
            # Sync payload cart to database cart for this user
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
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            address = validate_us_address(request.data.get("address"))
        except AddressValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        name = request.data.get("name") or request.user.full_name
        email = request.data.get("email") or request.user.email
        phone = request.data.get("phone") or request.user.phone
            
        line_items = []
        for item in cart_items:
            try:
                # Stripe expects amount in cents
                unit_amount = int(float(item.product.price) * 100)
            except (ValueError, TypeError):
                unit_amount = 0
                
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item.product.name,
                    },
                    'unit_amount': unit_amount,
                },
                'quantity': item.quantity,
            })
            
        delivery_charge_dollars = 5.00  # $5.00 delivery charge
            
        customer = None
        idempotency_key = request.data.get('idempotency_key', str(uuid.uuid4()))
        try:
            customer = create_stripe_customer(address, name, email, phone)
            checkout_session = stripe.checkout.Session.create(
                idempotency_key=idempotency_key,
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url='https://treatsislandgo.com/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url='https://treatsislandgo.com/cancel',
                client_reference_id=str(request.user.id),
                customer=customer.id,
                metadata=address_session_metadata(address, name, email, phone),
                payment_intent_data={
                    "metadata": address_session_metadata(address, name, email, phone),
                },
                shipping_options=[
                    {
                        'shipping_rate_data': {
                            'type': 'fixed_amount',
                            'fixed_amount': {
                                'amount': int(delivery_charge_dollars * 100),
                                'currency': 'usd',
                            },
                            'display_name': 'Delivery Charge',
                        },
                    },
                ],
                phone_number_collection={
                    'enabled': True
                },
            )
            
            # Pre-create unpaid orders atomically
            with transaction.atomic():
                for item in cart_items:
                    Order.objects.create(
                        user=request.user,
                        product=item.product,
                        quantity=item.quantity,
                        fundraiser=item.fundraiser,
                        stripe_session_id=checkout_session.id,
                        invoice_id=idempotency_key,
                        is_paid=False,
                        delivery_charge="5.00"
                    )

            return Response({'sessionId': checkout_session.id, 'url': checkout_session.url})
        except Exception as e:
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
        
    address = (
        f"{address_obj.line1} {address_obj.line2 or ''}".strip()
        if address_obj
        else metadata.get("shipping_line1")
    )
    city = address_obj.city if address_obj else metadata.get("shipping_city")
    state = address_obj.state if address_obj else metadata.get("shipping_state")
    postal_code = address_obj.postal_code if address_obj else metadata.get("shipping_postal_code")
    country = address_obj.country if address_obj else metadata.get("shipping_country")

    # Handle Guest/Pre-created Orders
    unpaid_orders = Order.objects.filter(stripe_session_id=session.id, is_paid=False)
    if unpaid_orders.exists():
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
            order.delivery_charge = "5.00"
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
                    delivery_charge="5.00"
                )
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
            cart_items.delete()
        except (User.DoesNotExist, ValueError, TypeError):
            pass


class PaymentSuccessView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        session_id = request.data.get('session_id')
        if not session_id:
            return Response({'error': 'Session ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                finalize_order(session)
                return Response({'message': 'Payment successful, order created.'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Payment not successful'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GuestCheckoutSessionView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        cart = request.data.get('cart', [])
        if not cart or not isinstance(cart, list):
            return Response({"error": "Cart is empty or invalid format. Expecting a list of items under 'cart' key."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            address = validate_us_address(request.data.get("address"))
        except AddressValidationError as exc:
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
            return Response({"error": "No valid products found"}, status=status.HTTP_400_BAD_REQUEST)

        delivery_charge_dollars = 5.00  # $5.00 delivery charge

        customer = None
        idempotency_key = request.data.get('idempotency_key', str(uuid.uuid4()))
        try:
            customer = create_stripe_customer(address, name, email, phone)
            checkout_session = stripe.checkout.Session.create(
                idempotency_key=idempotency_key,
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url='https://treatsislandgo.com/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url='https://treatsislandgo.com/cancel',
                customer=customer.id,
                metadata=address_session_metadata(address, name, email, phone),
                payment_intent_data={
                    "metadata": address_session_metadata(address, name, email, phone),
                },
                shipping_options=[
                    {
                        'shipping_rate_data': {
                            'type': 'fixed_amount',
                            'fixed_amount': {
                                'amount': int(delivery_charge_dollars * 100),
                                'currency': 'usd',
                            },
                            'display_name': 'Delivery Charge',
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
                        delivery_charge="5.00"
                    )
                
            return Response({'sessionId': checkout_session.id, 'url': checkout_session.url})
        except Exception as e:
            if customer:
                try:
                    stripe.Customer.delete(customer.id)
                except Exception:
                    pass
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

    total_donations = 0.0

    event_sales = sum_sales(paid_orders.filter(fundraiser__isnull=False))
    non_event_sales = sum_sales(paid_orders.filter(fundraiser__isnull=True))

    owed_to_organizations = event_sales * 0.5
    treats_island_revenue = (event_sales * 0.5) + non_event_sales

    # Campaigns (Events) counts
    events_filtered = Event.objects.all()
    if selected_org:
        events_filtered = events_filtered.filter(type_id=selected_org)
    if selected_campaign:
        events_filtered = events_filtered.filter(id=selected_campaign)

    active_campaigns_count = events_filtered.filter(start_date__lte=now, end_date__gte=now, is_active=True).count()
    upcoming_campaigns_count = events_filtered.filter(start_date__gt=now).count()
    ending_soon_campaigns_count = events_filtered.filter(end_date__gt=now, end_date__lte=now + datetime.timedelta(days=3)).count()

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

    top_participants = sorted(part_performance.items(), key=lambda x: x[1], reverse=True)[:5]

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

