from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch, MagicMock
from decimal import Decimal
from django.contrib.auth import get_user_model
from shop.models import DonationItem, Donation, Cart
from shop.views import finalize_donation, calculate_dashboard_metrics
from event.models import Event, OrganizationType, Fundraiser
from django.utils import timezone

User = get_user_model()

class DonationFeatureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="donor@example.com",
            phone="1234567890",
            password="testpassword123",
            full_name="Donor User"
        )
        self.item1 = DonationItem.objects.create(
            name="Bronze Support",
            description="Bronze support donation tier",
            price=Decimal("25.00"),
            is_active=True
        )
        self.item2 = DonationItem.objects.create(
            name="Gold Support",
            description="Gold support donation tier",
            price=Decimal("100.00"),
            is_active=True
        )
        self.inactive_item = DonationItem.objects.create(
            name="Old Tier",
            price=Decimal("5.00"),
            is_active=False
        )

        org_type = OrganizationType.objects.create(name="School", slug="school")
        self.event = Event.objects.create(
            name="Fall Fundraiser",
            type=org_type,
            start_date=timezone.now(),
            duration=7
        )
        self.fundraiser = Fundraiser.objects.create(
            user=self.user,
            event=self.event,
            name="Test Store"
        )

    def test_donation_items_list(self):
        url = reverse('donation-items')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        names = [d['name'] for d in data]
        self.assertIn("Bronze Support", names)
        self.assertIn("Gold Support", names)
        self.assertNotIn("Old Tier", names)

    def test_donation_item_detail(self):
        url = reverse('donation-item-detail', kwargs={'slug': self.item1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['name'], "Bronze Support")

    @patch('stripe.checkout.Session.create')
    def test_create_donation_checkout_session(self, mock_stripe_create):
        mock_session = MagicMock()
        mock_session.id = "cs_test_donation_123"
        mock_session.url = "https://checkout.stripe.com/pay/cs_test_donation_123"
        mock_stripe_create.return_value = mock_session

        url = reverse('donation-checkout')
        payload = {
            'donation_item_id': self.item1.id,
            'fundraiser_id': self.fundraiser.id,
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '9876543210'
            # Note: No address passed! No cart used!
        }
        response = self.client.post(url, data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['sessionId'], "cs_test_donation_123")
        self.assertEqual(response.json()['url'], mock_session.url)

        # Check Stripe line item had quantity 1 and amount $25.00 (2500 cents)
        call_kwargs = mock_stripe_create.call_args.kwargs
        self.assertEqual(call_kwargs['line_items'][0]['quantity'], 1)
        self.assertEqual(call_kwargs['line_items'][0]['price_data']['unit_amount'], 2500)
        self.assertEqual(call_kwargs['metadata']['type'], 'donation')

        # Check Donation record was created in DB
        donation = Donation.objects.filter(stripe_session_id="cs_test_donation_123").first()
        self.assertIsNotNone(donation)
        self.assertEqual(donation.amount, Decimal("25.00"))
        self.assertEqual(donation.quantity, 1)
        self.assertEqual(donation.name, "John Doe")
        self.assertEqual(donation.email, "john@example.com")
        self.assertEqual(donation.fundraiser, self.fundraiser)
        self.assertFalse(donation.is_paid)

        # Ensure Cart has 0 items
        self.assertEqual(Cart.objects.count(), 0)

    @patch('stripe.checkout.Session.create')
    def test_create_donation_checkout_custom_amount(self, mock_stripe_create):
        mock_session = MagicMock()
        mock_session.id = "cs_test_custom_456"
        mock_session.url = "https://checkout.stripe.com/pay/cs_test_custom_456"
        mock_stripe_create.return_value = mock_session

        url = reverse('donation-checkout')
        payload = {
            'amount': 75.50,
            'name': 'Generous Donor',
            'email': 'generous@example.com'
        }
        response = self.client.post(url, data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        call_kwargs = mock_stripe_create.call_args.kwargs
        self.assertEqual(call_kwargs['line_items'][0]['price_data']['unit_amount'], 7550)

        donation = Donation.objects.get(stripe_session_id="cs_test_custom_456")
        self.assertEqual(donation.amount, Decimal("75.50"))
        self.assertEqual(donation.quantity, 1)

    @patch('shop.shipstation.send_order_to_shipstation')
    def test_finalize_donation_does_not_call_shipstation(self, mock_shipstation):
        donation = Donation.objects.create(
            donation_item=self.item1,
            amount=Decimal("25.00"),
            quantity=1,
            name="Donor A",
            email="donorA@example.com",
            stripe_session_id="cs_test_finalize_789",
            is_paid=False
        )

        mock_session = MagicMock()
        mock_session.id = "cs_test_finalize_789"
        mock_session.payment_status = "paid"
        mock_session.metadata = {'type': 'donation', 'donation_item_id': str(self.item1.id)}
        mock_session.customer_details = MagicMock(name="Donor A", email="donorA@example.com", phone="1112223333")
        mock_session.client_reference_id = None

        finalized = finalize_donation(mock_session)
        self.assertIsNotNone(finalized)
        donation.refresh_from_db()
        self.assertTrue(donation.is_paid)

        # Assert ShipStation was never called!
        mock_shipstation.assert_not_called()

    def test_dashboard_metrics_calculates_total_donations(self):
        Donation.objects.create(
            donation_item=self.item1,
            amount=Decimal("50.00"),
            is_paid=True,
            stripe_session_id="paid_1"
        )
        Donation.objects.create(
            donation_item=self.item2,
            amount=Decimal("150.00"),
            is_paid=True,
            stripe_session_id="paid_2"
        )
        Donation.objects.create(
            donation_item=self.item1,
            amount=Decimal("25.00"),
            is_paid=False,  # Unpaid should not count
            stripe_session_id="unpaid_1"
        )

        metrics = calculate_dashboard_metrics({})
        self.assertEqual(metrics['total_donations'], 200.00)

    def test_donation_revenue_split_75_25(self):
        # Donation with fundraiser: 25% to Org, 75% to Treats Island
        donation = Donation.objects.create(
            donation_item=self.item1,
            fundraiser=self.fundraiser,
            amount=Decimal("100.00"),
            is_paid=True,
            stripe_session_id="split_test_1"
        )
        self.assertEqual(donation.organization_amount, 25.00)
        self.assertEqual(donation.treats_island_amount, 75.00)

        # Non-event donation: 0% to Org, 100% to Treats Island
        non_event_donation = Donation.objects.create(
            donation_item=self.item1,
            fundraiser=None,
            amount=Decimal("100.00"),
            is_paid=True,
            stripe_session_id="split_test_2"
        )
        self.assertEqual(non_event_donation.organization_amount, 0.0)
        self.assertEqual(non_event_donation.treats_island_amount, 100.00)

        # Verify dashboard metrics reflect the split
        metrics = calculate_dashboard_metrics({})
        # Event donation $100 -> org gets $25, treats gets $75
        # Non-event donation $100 -> treats gets $100
        self.assertEqual(metrics['owed_to_organizations'], 25.00)
        self.assertEqual(metrics['treats_island_revenue'], 175.00)

    def test_event_admin_revenue_split(self):
        from event.admin import EventAdmin
        from django.contrib.admin.sites import AdminSite

        Donation.objects.create(
            donation_item=self.item1,
            fundraiser=self.fundraiser,
            amount=Decimal("200.00"),
            is_paid=True,
            stripe_session_id="event_admin_1"
        )

        admin_instance = EventAdmin(Event, AdminSite())
        self.assertEqual(admin_instance.total_sales(self.event), "$200.00")
        self.assertEqual(admin_instance.amount_to_organizer(self.event), "$50.00") # 25% of 200
        self.assertEqual(admin_instance.to_treats_island(self.event), "$150.00") # 75% of 200
