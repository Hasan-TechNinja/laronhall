from rest_framework import serializers
from . models import Product, Cart, Order

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

    class Meta:
        model = Order
        fields = '__all__'
        
    def get_subtotal(self, obj):
        try:
            return float(obj.product.price) * obj.quantity
        except (ValueError, TypeError):
            return 0.0