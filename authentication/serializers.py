from rest_framework import serializers
from . models import User
from . models import Profile, PrivacyPolicy, TermsAndCondition

class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    is_event_running = serializers.SerializerMethodField()

    class Meta: 
        model = Profile
        fields = "__all__"

    def get_is_event_running(self, obj):
        from event.models import Event
        from django.utils import timezone
        from django.db.models import Q
        
        now = timezone.now()
        return Event.objects.filter(
            participants=obj.user,
            start_date__lte=now
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
