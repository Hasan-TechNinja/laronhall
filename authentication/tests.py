from django.test import TestCase
from django.contrib.auth import get_user_model
User = get_user_model()
from django.urls import reverse
from unittest.mock import patch
from authentication.models import Profile, ForgotPasswordOTP

class AuthenticationTests(TestCase):
    @patch('authentication.views.send_otp_phone')
    def test_register_user(self, mock_send_otp):
        mock_send_otp.return_value = 'mock_sid'
        url = reverse('register')
        data = {
            'phone': '01580625257',
            'password': 'testpassword123',
            'confirm_password': 'testpassword123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'OTP sent successfully.')
        
        # Verify user is created but inactive
        user = User.objects.get(phone='+8801580625257')
        self.assertFalse(user.is_active)
        
        # Verify profile is created
        self.assertEqual(user.profile.phone, '+8801580625257')

    @patch('authentication.views.verify_otp')
    def test_register_otp_verification(self, mock_verify_otp):
        # Create user
        user = User.objects.create_user(phone='+8801580625257')
        user.is_active = False
        user.save()
        
        mock_verify_otp.return_value = True
        url = reverse('register-otp-verification')
        data = {
            'phone': '01580625257',
            'otp': '123456'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        
        # Verify user is active now
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_login(self):
        user = User.objects.create_user(phone='+8801580625257', password='testpassword123')
        user.is_active = True
        user.save()
        
        url = reverse('login')
        data = {
            'phone': '01580625257',
            'password': 'testpassword123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)

    @patch('authentication.views.send_otp_phone')
    def test_forgot_password(self, mock_send_otp):
        user = User.objects.create_user(phone='+8801580625257')
        mock_send_otp.return_value = 'mock_sid'
        
        url = reverse('forgot-password')
        data = {'phone': '01580625257'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'OTP sent successfully.')

    @patch('authentication.views.verify_otp')
    def test_forgot_password_verification_and_reset(self, mock_verify_otp):
        user = User.objects.create_user(phone='+8801580625257')
        mock_verify_otp.return_value = True
        
        # Verify OTP
        url_verify = reverse('forgot-password-otp-verification')
        data_verify = {'phone': '01580625257', 'otp': '123456'}
        response_verify = self.client.post(url_verify, data_verify)
        self.assertEqual(response_verify.status_code, 200)
        
        # Reset Password
        url_reset = reverse('reset-password')
        data_reset = {
            'phone': '01580625257',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        response_reset = self.client.post(url_reset, data_reset)
        self.assertEqual(response_reset.status_code, 200)
        
        # Check password updated
        user.refresh_from_db()
        self.assertTrue(user.check_password('newpassword123'))
