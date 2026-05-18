from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('register-otp-verification/', views.RegisterOTPVerificationView.as_view(), name='register-otp-verification'),
    path('login/', views.LoginView.as_view(), name="login"),
    path('profile/', views.ProfileView.as_view(), name="profile"),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('forgot-password-otp-verification/', views.ForgotPasswordOTPVerificationView.as_view(), name='forgot-password-otp-verification'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
]