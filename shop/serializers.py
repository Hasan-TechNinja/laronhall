from rest_framework import serializers
from . models import Product, Cart, Order, Review, DonationItem, Donation
from event.serializers import UserProfileMinSerializer

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class CartSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = '__all__'
        
    def get_subtotal(self, obj):
        try:
            return float(obj.product.price) * obj.quantity
        except (ValueError, TypeError):
            return 0.0


class OrderSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()
    grand_total = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = '__all__'
        
    def get_subtotal(self, obj):
        try:
            return float(obj.product.price) * obj.quantity
        except (ValueError, TypeError):
            return 0.0

    def get_grand_total(self, obj):
        subtotal = self.get_subtotal(obj)
        try:
            return subtotal + float(obj.delivery_charge)
        except (ValueError, TypeError, AttributeError):
            return subtotal


class DonationItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonationItem
        fields = '__all__'


class DonationSerializer(serializers.ModelSerializer):
    donation_item = DonationItemSerializer(read_only=True)
    organization_amount = serializers.ReadOnlyField()
    treats_island_amount = serializers.ReadOnlyField()

    class Meta:
        model = Donation
        fields = '__all__'