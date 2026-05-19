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
from django.contrib.auth.models import User

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
        return Response(serializer.data)


class AddToCart(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        slug = request.data.get('slug') 
        quantity = request.data.get('quantity')

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

        if Cart.objects.filter(user=request.user, product=product).exists():
            cart = Cart.objects.get(user=request.user, product=product)
            cart.quantity += quantity
            cart.save()
            return Response({"message": "Product added to cart"}, status=status.HTTP_200_OK)
            
        cart = Cart.objects.create(user=request.user, product=product, quantity=quantity)
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
                
        return Response({
            "items": serializer.data,
            "cart_total": cart_total
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
            
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=request.build_absolute_uri('/success/'),
                cancel_url=request.build_absolute_uri('/cancel/'),
                client_reference_id=str(request.user.id)
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

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            user_id = session.get('client_reference_id')
            
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    cart_items = Cart.objects.filter(user=user)
                    
                    for item in cart_items:
                        Order.objects.create(
                            user=user,
                            product=item.product,
                            quantity=item.quantity
                        )
                    
                    # Clear the cart after placing order
                    cart_items.delete()
                except User.DoesNotExist:
                    pass

        return Response({'status': 'success'}, status=status.HTTP_200_OK)
