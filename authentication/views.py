from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import status, permissions
from django.core.mail import send_mail
from django.conf import settings
import random
from . models import RegisterOTP
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


# Create your views here.

class RegisterView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')

        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not password or not confirm_password:
            return Response({'error': 'Password and confirm password is required'}, status=status.HTTP_400_BAD_REQUEST)

        if password != confirm_password:
            return Response({'error': 'Password and confirm password does not match'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            if User.objects.filter(email=email).first().is_active:
                return Response({'error': 'User is already registered.'}, status=status.HTTP_400_BAD_REQUEST)

            RegisterOTP.objects.filter(user=email).delete()
            
            return Response({'error': 'User is already registered.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(email=email, username=email)
        user.is_active = False
        user.set_password(password)
        user.save()

        otp = random.randint(100000, 999999)
        RegisterOTP.objects.create(user=user, otp=otp)
        send_mail(
            'Register verification for Treats Island',
            f'Your OTP is {otp}',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return Response({'message': 'Email sent successfully.'}, status=status.HTTP_200_OK)


class RegisterOTPVerificationView(APIView):
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not otp:
            return Response({'error': 'OTP is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not User.objects.filter(email=email).exists():
            return Response({'error': 'User is not registered.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        register_otp = RegisterOTP.objects.filter(user=user).first()
        if not register_otp:
            return Response({'error': 'OTP is not found.'}, status=status.HTTP_400_BAD_REQUEST)

        if register_otp.otp != otp:
            return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.save()
        register_otp.is_verified = True
        register_otp.save()
        return Response({'error': 'Email verified successfully.'}, status=status.HTTP_200_OK)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_100_CONTINUE)

        if not password:
            return Response({'error': 'Password is required'}, status=status.HTTP_100_CONTINUE)

        if not User.objects.filter(email=email).exists():
            return Response({'error': 'User is not registered.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user.is_active:
            return Response({'error': 'User is not activated.'}, status=status.HTTP_400_BAD_REQUEST)
        if not user.check_password(password):
            return Response({'error': 'Invalid password.'}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return Response({'access': str(access), 'refresh': str(refresh)}, status=status.HTTP_200_OK)