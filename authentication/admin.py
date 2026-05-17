from django.contrib import admin
from .models import RegisterOTP, Profile

# Register your models here.

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'phone', 'created_at', 'updated_at')

admin.site.register(Profile, ProfileAdmin)

class RegisterOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp', 'is_verified', 'created_at', 'updated_at')

admin.site.register(RegisterOTP, RegisterOTPAdmin)