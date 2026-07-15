from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render
from django.contrib.auth import get_user_model
User = get_user_model()
from rest_framework import status, permissions
from django.core.mail import send_mail
from django.conf import settings
import random
from . models import RegisterOTP, Profile, ForgotPasswordOTP, PrivacyPolicy, TermsAndCondition
from . serializers import ProfileSerializer, PrivacyPolicySerializer, TermsAndConditionSerializer
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from .emails import send_register_otp_email, send_forgot_password_otp_email
from . utils import send_otp_phone, verify_otp, normalize_phone_number

# Create your views here.

class RegisterView(APIView):
    def post(self, request):
        phone = request.data.get('phone')
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')

        if not phone:
            return Response({'error': 'phone is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not password or not confirm_password:
            return Response({'error': 'Password and confirm password is required'}, status=status.HTTP_400_BAD_REQUEST)

        if password != confirm_password:
            return Response({'error': 'Password and confirm password does not match'}, status=status.HTTP_400_BAD_REQUEST)

        phone = normalize_phone_number(phone)

        if User.objects.filter(phone=phone).exists():
            user = User.objects.filter(phone=phone).first()
            if user.is_active:
                return Response({'error': 'User is already registered.'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                send_otp_phone(phone)
            except Exception as e:
                return Response({'error': f'Failed to send OTP: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(password)
            user.save()
            return Response({'message': 'OTP sent successfully.'}, status=status.HTTP_200_OK)

        user = User.objects.create_user(phone=phone)
        user.is_active = False
        user.set_password(password)
        user.save()

        profile = getattr(user, 'profile', None)
        if profile:
            profile.phone = phone
            profile.save()

        try:
            send_otp_phone(phone)
        except Exception as e:
            return Response({'error': f'Failed to send OTP: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'OTP sent successfully.'}, status=status.HTTP_200_OK)


class RegisterOTPVerificationView(APIView):
    def post(self, request):
        phone = request.data.get('phone')
        otp = request.data.get('otp')

        if not phone:
            return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not otp:
            return Response({'error': 'OTP is required'}, status=status.HTTP_400_BAD_REQUEST)

        phone = normalize_phone_number(phone)

        if not User.objects.filter(phone=phone).exists():
            return Response({'error': 'User is not registered.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(phone=phone).first()

        try:
            is_valid = verify_otp(phone, otp)
        except Exception as e:
            return Response({'error': f'Verification failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        if not is_valid:
            return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.save()
        
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return Response({'access': str(access), 'refresh': str(refresh)}, status=status.HTTP_200_OK)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        phone = request.data.get('phone')
        password = request.data.get('password')

        if not phone:
            return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not password:
            return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)

        phone = normalize_phone_number(phone)

        if not User.objects.filter(phone=phone).exists():
            return Response({'error': 'User is not registered.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(phone=phone).first()
        if not user.is_active:
            return Response({'error': 'User is not activated.'}, status=status.HTTP_400_BAD_REQUEST)
        if not user.check_password(password):
            return Response({'error': 'Invalid password.'}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return Response({'access': str(access), 'refresh': str(refresh)}, status=status.HTTP_200_OK)


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        profile = Profile.objects.filter(user=request.user).first()

        serializer = ProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)


    def put(self, request):
        profile = Profile.objects.filter(user=request.user).first()

        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    def post(self, request):
        phone = request.data.get('phone')
        if not phone:
            return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        phone = normalize_phone_number(phone)
        if not User.objects.filter(phone=phone).exists():
            return Response({'error': 'User is not registered.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            send_otp_phone(phone)
        except Exception as e:
            return Response({'error': f'Failed to send OTP: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'OTP sent successfully.'}, status=status.HTTP_200_OK)


class ForgotPasswordOTPVerificationView(APIView):
    def post(self, request):
        phone = request.data.get('phone')
        otp = request.data.get('otp')

        if not phone:
            return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not otp:
            return Response({'error': 'OTP is required'}, status=status.HTTP_400_BAD_REQUEST)

        phone = normalize_phone_number(phone)
        if not User.objects.filter(phone=phone).exists():
            return Response({'error': 'User is not registered.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(phone=phone).first()

        try:
            is_valid = verify_otp(phone, otp)
        except Exception as e:
            return Response({'error': f'Verification failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        if not is_valid:
            return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        forgot_password_otp, created = ForgotPasswordOTP.objects.get_or_create(user=user)
        forgot_password_otp.otp = str(otp)
        forgot_password_otp.is_verified = True
        forgot_password_otp.save()
        return Response({'message': 'OTP verified successfully.'}, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    def post(self, request):
        phone = request.data.get('phone')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not phone:
            return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not new_password or not confirm_password:
            return Response({'error': 'New password and confirm password are required'}, status=status.HTTP_400_BAD_REQUEST)
        if new_password != confirm_password:
            return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

        phone = normalize_phone_number(phone)
        if not User.objects.filter(phone=phone).exists():
            return Response({'error': 'User is not registered.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(phone=phone).first()
        forgot_password_otp = ForgotPasswordOTP.objects.filter(user=user).first()

        if not forgot_password_otp or not forgot_password_otp.is_verified:
            return Response({'error': 'OTP not verified.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        forgot_password_otp.delete()

        return Response({'message': 'Password reset successfully.'}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not old_password or not new_password or not confirm_password:
            return Response({'error': 'Old password, new password, and confirm password are required'}, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.check_password(old_password):
            return Response({'error': 'Incorrect old password'}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({'error': 'New passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(new_password)
        request.user.save()

        return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)


class PrivacyPolicyView(APIView):
    def get(self, request):
        privacy_policy = PrivacyPolicy.objects.filter().first()
        serializer = PrivacyPolicySerializer(privacy_policy)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TermsAndConditionView(APIView):
    def get(self, request):
        terms_and_condition = TermsAndCondition.objects.filter().first()
        serializer = TermsAndConditionSerializer(terms_and_condition)
        return Response(serializer.data, status=status.HTTP_200_OK)