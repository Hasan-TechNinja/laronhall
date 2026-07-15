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
from django.contrib.auth import get_user_model
User = get_user_model()
from notification.utils import send_push_notification
from .models import Review
from .serializers import ReviewSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY

# Create your views here.

class ProductsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
        

class ProductDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        try:
            product = Product.objects.get(slug=slug)
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
            product = Product.objects.get(slug=slug)
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


class CreateCheckoutSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        cart_items = Cart.objects.filter(user=request.user)
        
        if not cart_items.exists():
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
            
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
            
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url='http://localhost:5173/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url='http://localhost:5173/cancel',
                client_reference_id=str(request.user.id),
                shipping_address_collection={
                    'allowed_countries': ['US', 'CA', 'GB', 'AU', 'NZ', 'DE', 'FR', 'IT', 'ES', 'NL'],
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
            return Response({'sessionId': checkout_session.id, 'url': checkout_session.url})
        except Exception as e:
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

def finalize_order(session):
    if session.payment_status != 'paid':
        return

    user_id = getattr(session, 'client_reference_id', None)
    
    customer_details = getattr(session, 'customer_details', None)
    shipping_details = getattr(session, 'shipping_details', None)
    
    email = customer_details.email if customer_details else None
    phone = customer_details.phone if customer_details else None
    
    address_obj = None
    name = None
    if shipping_details:
        address_obj = shipping_details.address
        name = shipping_details.name
    elif customer_details:
        address_obj = customer_details.address
        name = customer_details.name
        
    address = f"{address_obj.line1} {address_obj.line2 or ''}".strip() if address_obj else None
    city = address_obj.city if address_obj else None
    state = address_obj.state if address_obj else None
    postal_code = address_obj.postal_code if address_obj else None
    country = address_obj.country if address_obj else None

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
                Order.objects.create(
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
            
        line_items = []
        order_items_to_create = []

        for item in cart:
            slug = item.get('slug')
            quantity = item.get('quantity', 1)
            fundraiser_id = item.get('fundraiser_id')
            try:
                product = Product.objects.get(slug=slug)
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

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url='http://localhost:5173/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url='http://localhost:5173/cancel',
                shipping_address_collection={
                    'allowed_countries': ['US', 'CA', 'GB', 'AU', 'NZ', 'DE', 'FR', 'IT', 'ES', 'NL'],
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
            
            # Create unpaid orders beforehand to link them with session_id
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
                    is_paid=False,
                    delivery_charge="5.00"
                )
                
            return Response({'sessionId': checkout_session.id, 'url': checkout_session.url})
        except Exception as e:
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
