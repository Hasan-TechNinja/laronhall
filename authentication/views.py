from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
User = get_user_model()
from rest_framework import status, permissions
from . models import Profile, PrivacyPolicy, TermsAndCondition
from . serializers import ProfileSerializer, PrivacyPolicySerializer, TermsAndConditionSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from . utils import send_otp_phone, verify_otp, normalize_phone_number

# Create your views here.

class SendOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get('phone')

        if not phone:
            return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)

        phone = normalize_phone_number(phone)

        # Check if the user exists
        user_exists = User.objects.filter(phone=phone).exists()

        if not user_exists:
            # Create user as inactive since it's passwordless registration
            user = User.objects.create_user(phone=phone)
            user.is_active = False
            user.save()

            # Profile is automatically created by the post_save signal.
            # Set the phone number on the profile if needed
            profile = getattr(user, 'profile', None)
            if profile:
                profile.phone = phone
                profile.save()

        try:
            send_otp_phone(phone)
        except Exception as e:
            return Response({'error': f'Failed to send OTP: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'OTP sent successfully.'}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

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

        # Activate the user
        user.is_active = True
        user.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return Response({
            'access': str(access),
            'refresh': str(refresh),
            'message': 'Verification successful.'
        }, status=status.HTTP_200_OK)


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