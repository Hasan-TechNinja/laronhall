from django.test import TestCase
from django.contrib.auth import get_user_model
User = get_user_model()
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
from event.models import OrganizationType, Event, Fundraiser
from shop.models import Product, Order
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
        from unittest.mock import ANY
        mock_send_email.assert_called_once_with(email="organizer@example.com", organizer_name="Jane Doe", event=ANY)

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
        from unittest.mock import ANY
        mock_send_email.assert_called_once_with(
            email="organizer@example.com",
            organizer_name="Jane Doe",
            member_name="John Smith",
            popup_store_name="Johns Candy Corner",
            event=ANY
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


class EventSalesReportTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.creator = User.objects.create_user(phone="+10000000001", email="creator@example.com")
        self.creator.is_active = True
        self.creator.full_name = "Event Creator"
        self.creator.save()

        self.other_user = User.objects.create_user(phone="+10000000002", email="other@example.com")
        self.other_user.is_active = True
        self.other_user.full_name = "Other User"
        self.other_user.save()

        self.creator_token = str(RefreshToken.for_user(self.creator).access_token)
        self.other_token = str(RefreshToken.for_user(self.other_user).access_token)

        self.org_type = OrganizationType.objects.create(name="Youth Sports", slug="youth-sports")
        self.event = Event.objects.create(
            name="Youth Soccer Fundraiser",
            type=self.org_type,
            creator=self.creator,
            start_date=timezone.now(),
            duration=5,
            code="SOCCER1"
        )
        self.fundraiser = Fundraiser.objects.create(
            user=self.creator,
            event=self.event,
            name="Champions Store"
        )

        self.product1 = Product.objects.create(name="Sour Gummies", price="10.00", stock="50")
        self.product2 = Product.objects.create(name="Chocolate Bites", price="15.00", stock="50")

        # Session 1: Single order
        self.order1 = Order.objects.create(
            user=self.other_user,
            fundraiser=self.fundraiser,
            product=self.product1,
            quantity=2,
            stripe_session_id="cs_test_session_1",
            is_paid=True,
            name="Supporter One"
        )

        # Session 2: Multiple order items in same stripe_session_id
        self.order2a = Order.objects.create(
            user=self.other_user,
            fundraiser=self.fundraiser,
            product=self.product1,
            quantity=1,
            stripe_session_id="cs_test_session_2",
            is_paid=True,
            name="Supporter Two"
        )
        self.order2b = Order.objects.create(
            user=self.other_user,
            fundraiser=self.fundraiser,
            product=self.product2,
            quantity=2,
            stripe_session_id="cs_test_session_2",
            is_paid=True,
            name="Supporter Two"
        )

        # Unpaid order (should be excluded by default)
        self.unpaid_order = Order.objects.create(
            user=self.other_user,
            fundraiser=self.fundraiser,
            product=self.product1,
            quantity=1,
            stripe_session_id="cs_test_unpaid",
            is_paid=False,
            name="Unpaid Supporter"
        )

    def test_sales_report_unauthenticated_returns_401(self):
        url = reverse('event-sales-report', kwargs={'id': self.event.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_sales_report_non_creator_returns_403(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.other_token}')
        url = reverse('event-sales-report', kwargs={'id': self.event.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_sales_report_non_existent_event_returns_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.creator_token}')
        url = reverse('event-sales-report', kwargs={'id': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_sales_report_json_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.creator_token}')
        url = reverse('event-sales-report', kwargs={'id': self.event.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('event', data)
        self.assertIn('summary', data)
        self.assertIn('sales', data)
        self.assertIn('pdf_export_url', data)

        # Total transactions = 2 (session 1 + session 2, excluding unpaid)
        self.assertEqual(data['summary']['total_transactions'], 2)
        # Session 1: 2 * $10 = $20
        # Session 2: (1 * $10) + (2 * $15) = $10 + $30 = $40
        # Total sales = $60
        self.assertEqual(data['summary']['total_sales'], 60.0)
        # 50% due organizer = $30
        self.assertEqual(data['summary']['due_organizer_sales'], 30.0)
        # 50% due treats = $30
        self.assertEqual(data['summary']['due_treats_sales'], 30.0)

        # Check sales row fields
        sales = data['sales']
        self.assertEqual(len(sales), 2)
        row = sales[0]
        self.assertIn('number', row)
        self.assertIn('supporter_name', row)
        self.assertIn('purchase_date', row)
        self.assertIn('items_purchased', row)
        self.assertIn('candy_price', row)
        self.assertIn('due_organizer', row)
        self.assertIn('due_treats', row)
        self.assertIn('popup_name', row)

    def test_sales_report_pdf_export_via_param(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.creator_token}')
        url = reverse('event-sales-report', kwargs={'id': self.event.id}) + '?export=pdf'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment;', response['Content-Disposition'])
        self.assertTrue(len(response.content) > 0)
        # PDF signature check
        self.assertTrue(response.content.startswith(b'%PDF-'))

    def test_sales_report_pdf_export_view(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.creator_token}')
        url = reverse('event-sales-report-pdf', kwargs={'id': self.event.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment;', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF-'))

    def test_sales_report_pdf_export_with_token_param(self):
        # Without Authorization header, using ?token= query param
        self.client.credentials()  # clear credentials
        url = reverse('event-sales-report-pdf', kwargs={'id': self.event.id}) + f'?token={self.creator_token}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF-'))

