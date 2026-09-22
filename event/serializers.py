from rest_framework import serializers
from .models import OrganizationType, Event, Fundraiser
from shop.models import Order
from django.utils import timezone
from django.contrib.auth import get_user_model
User = get_user_model()

class UserProfileMinSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'image']

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

class OrganizationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationType
        fields = "__all__"

class EventSerializer(serializers.ModelSerializer):
    creator = UserProfileMinSerializer(read_only=True)
    participants = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    total_achieved = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()
    type_slug = serializers.CharField(source='type.slug', read_only=True)

    class Meta:
        model = Event
        fields = "__all__"

    def get_is_mine(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.creator == request.user
        return False

    def get_total_achieved(self, obj):
        from shop.models import Order, Donation
        total = 0.0
        orders = Order.objects.filter(fundraiser__event=obj, is_paid=True)
        for order in orders:
            try:
                total += float(order.product.price) * order.quantity
            except (ValueError, TypeError):
                pass
        donations = Donation.objects.filter(fundraiser__event=obj, is_paid=True)
        for donation in donations:
            try:
                total += float(donation.amount)
            except (ValueError, TypeError):
                pass
        return total

    def get_status(self, obj):
        now = timezone.now()
        if obj.start_date and obj.end_date:
            if obj.start_date > now:
                return "Upcoming"
            elif obj.start_date <= now <= obj.end_date:
                return "Ongoing"
            else:
                return "Completed"
        elif obj.start_date:
            if obj.start_date > now:
                return "Upcoming"
            else:
                return "Ongoing"
        return "Unknown"

    def get_participants(self, obj):
        participants = obj.participants.all()
        request = self.context.get('request')
        result = []
        
        # We also need Fundraiser and Order to calculate shop data
        from shop.models import Order, Donation
        
        for user in participants:
            full_name = user.full_name
            image_url = None
            if user.image:
                image_url = user.image.url
                if request:
                    image_url = request.build_absolute_uri(image_url)
            
            shop_goal = 0.0
            shop_achieved = 0.0
            total_supporters = 0
            fundraiser = Fundraiser.objects.filter(user=user, event=obj).first()
            
            if fundraiser:
                from django.db.models.functions import Coalesce
                shop_goal = float(fundraiser.goal) if fundraiser.goal else 0.0
                orders = Order.objects.filter(fundraiser=fundraiser, is_paid=True)
                for order in orders:
                    try:
                        shop_achieved += float(order.product.price) * order.quantity
                    except (ValueError, TypeError):
                        pass

                donations = Donation.objects.filter(fundraiser=fundraiser, is_paid=True)
                for donation in donations:
                    try:
                        shop_achieved += float(donation.amount)
                    except (ValueError, TypeError):
                        pass
                
                order_emails = set(orders.annotate(supporter_email=Coalesce('user__email', 'email')).values_list('supporter_email', flat=True))
                donation_emails = set(donations.annotate(supporter_email=Coalesce('user__email', 'email')).values_list('supporter_email', flat=True))
                total_supporters = len(order_emails.union(donation_emails))

            result.append({
                'id': user.id,
                'email': user.email,
                'full_name': full_name,
                'image': image_url,
                'shop_goal': shop_goal,
                'shop_achieved': shop_achieved,
                'total_supporters': total_supporters
            })
        return result

class EventDetailedSerializer(serializers.ModelSerializer):
    organizer_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    starts_in = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    total_achieved = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = ['id', 'name', 'organizer_name', 'start_date', 'end_date', 'category_name', 'starts_in', 'code', 'duration', 'is_active', 'min_estimated_earning', 'max_estimated_earning', 'estimated_participants', 'status', 'total_achieved', 'is_mine', 'payout_manager']

    def get_is_mine(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.creator == request.user
        return False

    def get_total_achieved(self, obj):
        from shop.models import Order, Donation
        total = 0.0
        orders = Order.objects.filter(fundraiser__event=obj, is_paid=True)
        for order in orders:
            try:
                total += float(order.product.price) * order.quantity
            except (ValueError, TypeError):
                pass
        donations = Donation.objects.filter(fundraiser__event=obj, is_paid=True)
        for donation in donations:
            try:
                total += float(donation.amount)
            except (ValueError, TypeError):
                pass
        return total

    def get_organizer_name(self, obj):
        if obj.creator:
            return obj.creator.full_name or obj.creator.phone
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

    def get_status(self, obj):
        now = timezone.now()
        if obj.start_date and obj.end_date:
            if obj.start_date > now:
                return "Upcoming"
            elif obj.start_date <= now <= obj.end_date:
                return "Ongoing"
            else:
                return "Completed"
        elif obj.start_date:
            if obj.start_date > now:
                return "Upcoming"
            else:
                return "Ongoing"
        return "Unknown"

class FundraiserSerializer(serializers.ModelSerializer):
    achieved = serializers.SerializerMethodField()
    user_profile = UserProfileMinSerializer(source='user', read_only=True)
    share_link = serializers.SerializerMethodField()
    has_payout_setup = serializers.BooleanField(read_only=True)
    stripe_connect_account_id = serializers.CharField(read_only=True)
    total_creator_earnings = serializers.FloatField(read_only=True)

    class Meta:
        model = Fundraiser
        fields = "__all__"

    def get_share_link(self, obj):
        return f"https://treatsislandgo.com/shop/{obj.id}"

    def get_achieved(self, obj):
        from shop.models import Order, Donation
        orders = Order.objects.filter(fundraiser=obj, is_paid=True)
        total_achieved = 0.0
        for order in orders:
            try:
                total_achieved += float(order.product.price) * order.quantity
            except (ValueError, TypeError):
                pass
        donations = Donation.objects.filter(fundraiser=obj, is_paid=True)
        for donation in donations:
            try:
                total_achieved += float(donation.amount)
            except (ValueError, TypeError):
                pass
        return total_achieved