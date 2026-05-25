from django.contrib import admin
from .models import RegisterOTP, Profile, PrivacyPolicy, TermsAndCondition

# Register your models here.

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'phone', 'created_at', 'updated_at')

admin.site.register(Profile, ProfileAdmin)

class RegisterOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp', 'is_verified', 'created_at', 'updated_at')

admin.site.register(RegisterOTP, RegisterOTPAdmin)

class PrivacyPolicyAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_at', 'updated_at')

admin.site.register(PrivacyPolicy, PrivacyPolicyAdmin)

class TermsAndConditionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_at', 'updated_at')

admin.site.register(TermsAndCondition, TermsAndConditionAdmin)