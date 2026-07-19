from django.test import TestCase
from django.contrib.auth import get_user_model
User = get_user_model()
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
from event.models import OrganizationType, Event
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.management import call_command

class EventEmailTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(phone="+8801580625257", email="organizer@example.com")
        self.user.is_active = True
        self.user.full_name = "Jane Doe"
        self.user.save()
        
        # Get JWT tokens
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Create OrganizationType
        self.org_type = OrganizationType.objects.create(name="School", slug="school")

    @patch('authentication.emails.send_welcome_organizer_email')
    def test_create_event_sends_welcome_email(self, mock_send_email):
        url = reverse('event-create')
        data = {
            'type': 'school',
            'start_date': '2026-07-20T10:00:00Z',
            'team_name': 'My Charity Event',
            'estimated_participants': 50,
            'min_estimated_earning': '100.00',
            'max_estimated_earning': '500.00'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        
        # Verify welcome email was sent
        mock_send_email.assert_called_once_with(email="organizer@example.com", organizer_name="Jane Doe")

    @patch('event.management.commands.send_event_start_reminders.send_event_start_soon_email')
    def test_send_event_start_reminders_command(self, mock_send_email):
        # Create an event starting 45 minutes from now
        start_date = timezone.now() + timedelta(minutes=45)
        event = Event.objects.create(
            name="Upcoming Event",
            type=self.org_type,
            start_date=start_date,
            creator=self.user,
            start_reminder_sent=False
        )
        
        # Run command
        call_command('send_event_start_reminders')
        
        # Verify email was sent
        mock_send_email.assert_called_once_with("organizer@example.com", "Jane Doe")
        
        # Verify flag is set to True
        event.refresh_from_db()
        self.assertTrue(event.start_reminder_sent)

    @patch('event.management.commands.send_event_twenty_four_hour_reminders.send_event_twenty_four_hour_reminder_email')
    def test_send_event_twenty_four_hour_reminders_command(self, mock_send_email):
        # Create an event that started 24 hours ago
        start_date = timezone.now() - timedelta(hours=24, minutes=5)
        event = Event.objects.create(
            name="Started Event",
            type=self.org_type,
            start_date=start_date,
            creator=self.user,
            twenty_four_hour_reminder_sent=False
        )
        
        # Run command
        call_command('send_event_twenty_four_hour_reminders')
        
        # Verify email was sent
        mock_send_email.assert_called_once_with("organizer@example.com", "Jane Doe")
        
        # Verify flag is set to True
        event.refresh_from_db()
        self.assertTrue(event.twenty_four_hour_reminder_sent)

    @patch('event.management.commands.send_event_end_thank_you_emails.send_event_end_thank_you_email')
    def test_send_event_end_thank_you_emails_command(self, mock_send_email):
        # Create an event that ended 5 minutes ago
        end_date = timezone.now() - timedelta(minutes=5)
        event = Event.objects.create(
            name="Ended Event",
            type=self.org_type,
            start_date=timezone.now() - timedelta(days=5),
            end_date=end_date,
            creator=self.user,
            end_thank_you_sent=False
        )
        
        # Run command
        call_command('send_event_end_thank_you_emails')
        
        # Verify email was sent
        mock_send_email.assert_called_once_with("organizer@example.com", "Jane Doe", "Ended Event")
        
        # Verify flag is set to True
        event.refresh_from_db()
        self.assertTrue(event.end_thank_you_sent)

    @patch('authentication.emails.send_new_popup_alert_email')
    def test_update_fundraiser_name_sends_alert_email(self, mock_send_email):
        # Create an event created by self.user
        event = Event.objects.create(
            name="My Charity Event",
            type=self.org_type,
            start_date=timezone.now(),
            creator=self.user
        )
        from event.models import Fundraiser
        # Create another user (member)
        member = User.objects.create_user(phone="+8801711111111", email="member@example.com")
        member.is_active = True
        member.full_name = "John Smith"
        member.save()
        
        # Create fundraiser record for the member
        fundraiser = Fundraiser.objects.create(user=member, event=event)
        
        # Authenticate as member
        refresh = RefreshToken.for_user(member)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('fundraiser-update-name', kwargs={'id': fundraiser.id})
        data = {'name': 'Johns Candy Corner'}
        
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        
        # Verify alert email was sent to organizer
        mock_send_email.assert_called_once_with(
            email="organizer@example.com",
            organizer_name="Jane Doe",
            member_name="John Smith",
            popup_store_name="Johns Candy Corner"
        )

    @patch('event.management.commands.send_event_banking_details_reminders.send_event_banking_details_reminder_email')
    def test_send_event_banking_details_reminders_command(self, mock_send_email):
        # Create an event that started 2 days ago (48 hours + 5 minutes)
        start_date = timezone.now() - timedelta(days=2, minutes=5)
        event = Event.objects.create(
            name="Ongoing Event",
            type=self.org_type,
            start_date=start_date,
            creator=self.user,
            banking_details_reminder_sent=False
        )
        
        # Run command
        call_command('send_event_banking_details_reminders')
        
        # Verify email was sent
        mock_send_email.assert_called_once_with("organizer@example.com", "Jane Doe")
        
        # Verify flag is set to True
        event.refresh_from_db()
        self.assertTrue(event.banking_details_reminder_sent)
