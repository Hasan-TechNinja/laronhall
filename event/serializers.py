from rest_framework import serializers

from .models import OrganizationType, Event, Fundraiser
from shop.models import Order
from django.utils import timezone

class OrganizationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationType
        fields = "__all__"

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = "__all__"

class EventDetailedSerializer(serializers.ModelSerializer):
    organizer_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    starts_in = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = ['id', 'name', 'organizer_name', 'start_date', 'end_date', 'category_name', 'starts_in', 'code', 'duration', 'is_active', 'min_estimated_earning', 'max_estimated_earning', 'estimated_participants']

    def get_organizer_name(self, obj):
        if obj.creator:
            full_name = f"{obj.creator.first_name} {obj.creator.last_name}".strip()
            return full_name if full_name else obj.creator.username
        return "Unknown"

    def get_category_name(self, obj):
        return obj.type.name if obj.type else None

    def get_starts_in(self, obj):
        if not obj.start_date:
            return None
        now = timezone.now()
        if obj.start_date > now:
            diff = obj.start_date - now
            days = diff.days
            hours, remainder = divmod(diff.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            parts = []
            if days > 0:
                parts.append(f"{days} Days" if days != 1 else "1 Day")
            if hours > 0:
                parts.append(f"{hours} Hours" if hours != 1 else "1 Hour")
            if minutes > 0 or (days == 0 and hours == 0):
                parts.append(f"{minutes} Minutes" if minutes != 1 else "1 Minute")
                
            return " ".join(parts)
        return "Started"

class FundraiserSerializer(serializers.ModelSerializer):
    achieved = serializers.SerializerMethodField()

    class Meta:
        model = Fundraiser
        fields = "__all__"

    def get_achieved(self, obj):
        orders = Order.objects.filter(fundraiser=obj, is_paid=True)
        total_achieved = 0.0
        for order in orders:
            try:
                total_achieved += float(order.product.price) * order.quantity
            except (ValueError, TypeError):
                pass
        return total_achieved