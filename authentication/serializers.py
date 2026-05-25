from rest_framework import serializers
from . models import User
from . models import Profile, PrivacyPolicy, TermsAndCondition

class ProfileSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Profile
        fields = "__all__"

        
class PrivacyPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacyPolicy
        fields = '__all__'

class TermsAndConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermsAndCondition
        fields = '__all__'
