from django.test import TestCase
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
User = get_user_model()
from django.urls import reverse
from unittest.mock import patch

class AuthenticationTests(APITestCase):
    @patch('authentication.views.send_otp_phone')
    def test_send_otp_new_user(self, mock_send_otp):
        mock_send_otp.return_value = 'mock_sid'
        url = reverse('send-otp')
        data = {
            'phone': '01580625257'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'OTP sent successfully.')
        
        # Verify user is created but inactive
        user = User.objects.get(phone='+8801580625257')
        self.assertFalse(user.is_active)

    @patch('authentication.views.send_otp_phone')
    def test_send_otp_existing_user(self, mock_send_otp):
        # Create active user
        user = User.objects.create_user(phone='+8801580625257')
        user.is_active = True
        user.save()

        mock_send_otp.return_value = 'mock_sid'
        url = reverse('send-otp')
        data = {
            'phone': '01580625257'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'OTP sent successfully.')
        
        # Check user count remains 1
        self.assertEqual(User.objects.filter(phone='+8801580625257').count(), 1)

    @patch('authentication.views.verify_otp')
    def test_verify_otp_valid(self, mock_verify_otp):
        # Create user
        user = User.objects.create_user(phone='+8801580625257')
        user.is_active = False
        user.save()
        
        mock_verify_otp.return_value = True
        url = reverse('verify-otp')
        data = {
            'phone': '01580625257',
            'otp': '123456'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['message'], 'Verification successful.')
        
        # Verify user is active now
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    @patch('authentication.views.verify_otp')
    def test_verify_otp_invalid(self, mock_verify_otp):
        # Create user
        user = User.objects.create_user(phone='+8801580625257')
        user.is_active = False
        user.save()
        
        mock_verify_otp.return_value = False
        url = reverse('verify-otp')
        data = {
            'phone': '01580625257',
            'otp': '000000'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'Invalid OTP.')
        
        # Verify user remains inactive
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_delete_account_authenticated_delete_method(self):
        user = User.objects.create_user(phone='+8801580625257')
        user.is_active = True
        user.save()
        self.client.force_authenticate(user=user)

        url = reverse('delete-account')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Account deleted successfully.')
        self.assertFalse(User.objects.filter(phone='+8801580625257').exists())

    def test_delete_account_authenticated_post_method(self):
        user = User.objects.create_user(phone='+8801580625257')
        user.is_active = True
        user.save()
        self.client.force_authenticate(user=user)

        url = reverse('delete-account')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Account deleted successfully.')
        self.assertFalse(User.objects.filter(phone='+8801580625257').exists())

    def test_profile_delete_authenticated(self):
        user = User.objects.create_user(phone='+8801580625257')
        user.is_active = True
        user.save()
        self.client.force_authenticate(user=user)

        url = reverse('profile')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Account deleted successfully.')
        self.assertFalse(User.objects.filter(phone='+8801580625257').exists())

    def test_delete_account_unauthenticated(self):
        url = reverse('delete-account')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 401)


