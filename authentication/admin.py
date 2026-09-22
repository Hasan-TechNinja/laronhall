from django.contrib import admin
from .models import RegisterOTP, PrivacyPolicy, TermsAndCondition, User

# Register your models here.

# class RegisterOTPAdmin(admin.ModelAdmin):
#     list_display = ('user', 'otp', 'is_verified', 'created_at', 'updated_at')

# admin.site.register(RegisterOTP, RegisterOTPAdmin)

class PrivacyPolicyAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_at', 'updated_at')

admin.site.register(PrivacyPolicy, PrivacyPolicyAdmin)

class TermsAndConditionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_at', 'updated_at')

admin.site.register(TermsAndCondition, TermsAndConditionAdmin)


from django import forms
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminUserCreationForm


class CustomUserCreationForm(AdminUserCreationForm):
    full_name = forms.CharField(max_length=255, required=False, label="Full Name")
    email = forms.EmailField(required=False, label="Email")

    class Meta(AdminUserCreationForm.Meta):
        model = User
        fields = ('phone', 'full_name', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.full_name = self.cleaned_data.get('full_name')
        user.email = self.cleaned_data.get('email')
        user.is_active = True
        if commit:
            user.save()
        return user


class UserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    list_display = ('phone', 'email', 'full_name', 'stripe_connect_account_id', 'stripe_connect_payouts_enabled', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'stripe_connect_payouts_enabled')
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'email', 'image')}),
        ('Stripe Connect Payouts', {'fields': ('stripe_connect_account_id', 'stripe_connect_onboarding_completed', 'stripe_connect_payouts_enabled')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ('date_joined', 'last_login')
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'full_name', 'email', 'password1', 'password2'),
        }),
    )
    search_fields = ('phone', 'email', 'full_name')
    ordering = ('phone',)

admin.site.register(User, UserAdmin)

