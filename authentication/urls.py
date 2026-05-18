from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('register-otp-verification/', views.RegisterOTPVerificationView.as_view(), name='register-otp-verification'),
    path('login/', views.LoginView.as_view(), name="login"),
    path('profile/', views.ProfileView.as_view(), name="profile"),
]