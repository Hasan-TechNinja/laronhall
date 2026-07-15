from django.contrib import admin
from .models import RegisterOTP, Profile, PrivacyPolicy, TermsAndCondition, User

# Register your models here.

# class ProfileAdmin(admin.ModelAdmin):
#     list_display = ('user', 'full_name', 'phone', 'created_at', 'updated_at')

# admin.site.register(Profile, ProfileAdmin)

class RegisterOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp', 'is_verified', 'created_at', 'updated_at')

admin.site.register(RegisterOTP, RegisterOTPAdmin)

class PrivacyPolicyAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_at', 'updated_at')

admin.site.register(PrivacyPolicy, PrivacyPolicyAdmin)

class TermsAndConditionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_at', 'updated_at')

admin.site.register(TermsAndCondition, TermsAndConditionAdmin)


from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class UserAdmin(BaseUserAdmin):
    list_display = ('phone', 'email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ('date_joined', 'last_login')
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'password'),
        }),
    )
    search_fields = ('phone', 'email')
    ordering = ('phone',)

admin.site.register(User, UserAdmin)
