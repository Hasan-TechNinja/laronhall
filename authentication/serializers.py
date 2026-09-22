from rest_framework import serializers
from . models import User, PrivacyPolicy, TermsAndCondition

class ProfileSerializer(serializers.ModelSerializer):
    is_event_running = serializers.SerializerMethodField()

    class Meta: 
        model = User
        fields = [
            'id', 'phone', 'full_name', 'email', 'image', 'is_event_running',
            'stripe_connect_account_id', 'stripe_connect_onboarding_completed', 'stripe_connect_payouts_enabled'
        ]

    def get_is_event_running(self, obj):
        from event.models import Event
        from django.utils import timezone
        from django.db.models import Q
        
        now = timezone.now()
        return Event.objects.filter(
            participants=obj
        ).filter(
            Q(end_date__gte=now) | Q(end_date__isnull=True)
        ).exists()

        
class PrivacyPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacyPolicy
        fields = '__all__'

class TermsAndConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermsAndCondition
        fields = '__all__'
