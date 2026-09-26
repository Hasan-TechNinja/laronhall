from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock
from decimal import Decimal

from event.models import Event, Fundraiser, OrganizationType
from event.serializers import EventSerializer, EventDetailedSerializer, FundraiserSerializer
from shop.models import Product, Order
from shop.stripe_connect import (
    get_or_create_connect_account,
    create_onboarding_link,
    create_dashboard_login_link,
    sync_connect_account_status,
    transfer_order_payout,
    process_pending_creator_payouts,
)

User = get_user_model()


class StripeConnectTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Event Creator (Organizer)
        self.event_creator = User.objects.create_user(
            phone="+1234567890",
            password="testpassword123",
            email="organizer@example.com",
            full_name="Jane Organizer",
            is_active=True
        )

        # Shop Creator (Participant who runs a popup store)
        self.shop_creator = User.objects.create_user(
            phone="+1987654321",
            password="testpassword123",
            email="student@example.com",
            full_name="Bobby Student",
            is_active=True
        )

        self.client.force_authenticate(user=self.event_creator)

        self.org_type = OrganizationType.objects.create(name="School", slug="school")
        self.event = Event.objects.create(
            name="Spring School Fundraiser",
            type=self.org_type,
            start_date=timezone.now(),
            duration=5,
            creator=self.event_creator,
            is_active=True
        )
        self.fundraiser = Fundraiser.objects.create(
            user=self.shop_creator,
            event=self.event,
            name="Bobby's Candy Store",
            goal=Decimal("500.00")
        )
        self.product = Product.objects.create(
            name="Chocolate Truffle Box",
            price="30.00",
            stock="100",
            weight=12.0
        )

    def test_event_has_payout_properties_and_fundraiser_does_not(self):
        """Ensure payout properties are on Event (event creator) and removed from Fundraiser."""
        self.assertFalse(self.event.has_payout_setup)
        self.assertIsNone(self.event.stripe_connect_account_id)
        self.assertEqual(self.event.total_creator_earnings, 0.0)

        # Fundraiser should NOT have payout attributes/properties
        fundraiser_serializer = FundraiserSerializer(self.fundraiser)
        self.assertNotIn('has_payout_setup', fundraiser_serializer.data)
        self.assertNotIn('stripe_connect_account_id', fundraiser_serializer.data)
        self.assertNotIn('total_creator_earnings', fundraiser_serializer.data)

        # EventSerializer and EventDetailedSerializer SHOULD have payout attributes
        event_serializer = EventSerializer(self.event)
        self.assertIn('has_payout_setup', event_serializer.data)
        self.assertIn('stripe_connect_account_id', event_serializer.data)
        self.assertIn('total_creator_earnings', event_serializer.data)

        event_detailed_serializer = EventDetailedSerializer(self.event)
        self.assertIn('has_payout_setup', event_detailed_serializer.data)
        self.assertIn('stripe_connect_account_id', event_detailed_serializer.data)
        self.assertIn('total_creator_earnings', event_detailed_serializer.data)

    @patch('stripe.Account.create')
    def test_get_or_create_connect_account_creates_new(self, mock_account_create):
        mock_account = MagicMock()
        mock_account.id = "acct_test12345"
        mock_account_create.return_value = mock_account

        account = get_or_create_connect_account(self.event_creator)
        self.assertEqual(account.id, "acct_test12345")
        self.event_creator.refresh_from_db()
        self.assertEqual(self.event_creator.stripe_connect_account_id, "acct_test12345")
        mock_account_create.assert_called_once()
        # Verify card_payments is NOT requested
        args, kwargs = mock_account_create.call_args
        self.assertNotIn('card_payments', kwargs.get('capabilities', {}))
        self.assertTrue(kwargs.get('capabilities', {}).get('transfers', {}).get('requested'))

    @patch('stripe.Transfer.create')
    def test_transfer_order_payout_routes_to_event_creator(self, mock_transfer_create):
        """Payout must go to event_creator, NOT shop_creator."""
        self.event_creator.stripe_connect_account_id = "acct_organizer_999"
        self.event_creator.stripe_connect_onboarding_completed = True
        self.event_creator.stripe_connect_payouts_enabled = True
        self.event_creator.save()

        # Shop creator has NO stripe connect account
        self.shop_creator.stripe_connect_account_id = None
        self.shop_creator.stripe_connect_payouts_enabled = False
        self.shop_creator.save()

        # Order of 2 items @ $30.00 = $60.00 total.
        # 50% split: $30.00 event creator, $30.00 Treats Island
        order = Order.objects.create(
            user=None,
            fundraiser=self.fundraiser,
            product=self.product,
            quantity=2,
            is_paid=True,
            stripe_session_id="cs_test_event_creator_1"
        )

        mock_transfer = MagicMock()
        mock_transfer.id = "tr_event_creator_transfer"
        mock_transfer_create.return_value = mock_transfer

        transfer_order_payout(order)
        order.refresh_from_db()

        self.assertEqual(order.creator_payout_amount, Decimal("30.00"))
        self.assertEqual(order.treats_island_amount, Decimal("30.00"))
        self.assertEqual(order.payout_status, "transferred")
        self.assertEqual(order.stripe_transfer_id, "tr_event_creator_transfer")

        # Destination must be event_creator's account!
        mock_transfer_create.assert_called_once_with(
            amount=3000,
            currency="usd",
            destination="acct_organizer_999",
            description=f"50% Revenue Payout for Order #{order.id} (Chocolate Truffle Box)",
            metadata={
                "order_id": str(order.id),
                "fundraiser_id": str(self.fundraiser.id),
                "event_id": str(self.event.id),
                "product_name": "Chocolate Truffle Box",
                "event_creator_user_id": str(self.event_creator.id),
            }
        )

    def test_transfer_order_payout_pending_when_event_creator_not_onboarded(self):
        self.event_creator.stripe_connect_payouts_enabled = False
        self.event_creator.save()

        order = Order.objects.create(
            user=None,
            fundraiser=self.fundraiser,
            product=self.product,
            quantity=1,
            is_paid=True,
            stripe_session_id="cs_test_event_creator_2"
        )

        transfer_order_payout(order)
        order.refresh_from_db()

        self.assertEqual(order.creator_payout_amount, Decimal("15.00"))
        self.assertEqual(order.treats_island_amount, Decimal("15.00"))
        self.assertEqual(order.payout_status, "pending_onboarding")
        self.assertIsNone(order.stripe_transfer_id)

    @patch('stripe.Transfer.create')
    def test_process_pending_creator_payouts_for_event_creator(self, mock_transfer_create):
        order = Order.objects.create(
            user=None,
            fundraiser=self.fundraiser,
            product=self.product,
            quantity=1,
            is_paid=True,
            creator_payout_amount=Decimal("15.00"),
            treats_island_amount=Decimal("15.00"),
            payout_status="pending_onboarding"
        )

        self.event_creator.stripe_connect_account_id = "acct_organizer_999"
        self.event_creator.stripe_connect_onboarding_completed = True
        self.event_creator.stripe_connect_payouts_enabled = True
        self.event_creator.save()

        mock_transfer = MagicMock()
        mock_transfer.id = "tr_batch_event_creator"
        mock_transfer_create.return_value = mock_transfer

        result = process_pending_creator_payouts(self.event_creator)
        self.assertEqual(result['transferred_count'], 1)
        self.assertEqual(result['total_transferred'], 15.00)

        order.refresh_from_db()
        self.assertEqual(order.payout_status, "transferred")
        self.assertEqual(order.stripe_transfer_id, "tr_batch_event_creator")

    @patch('shop.stripe_connect.stripe.AccountLink.create')
    @patch('shop.stripe_connect.stripe.Account.create')
    def test_api_connect_banking_starts_hosted_event_creator_onboarding(
        self, mock_account_create, mock_account_link_create
    ):
        mock_account_create.return_value = MagicMock(id='acct_123')
        mock_account_link_create.return_value = MagicMock(url='https://connect.stripe.test/onboard')

        response = self.client.post('/event/connect/banking/', {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['onboarding_url'], 'https://connect.stripe.test/onboard')
        self.assertEqual(response.data['account_id'], 'acct_123')
        mock_account_create.assert_called_once()
        mock_account_link_create.assert_called_once()

        shop_response = self.client.post('/shop/connect/banking/', {}, format='json')
        self.assertEqual(shop_response.status_code, 404)

    def test_shop_creator_cannot_start_event_payout_onboarding(self):
        self.client.force_authenticate(user=self.shop_creator)
        response = self.client.post('/event/connect/onboard/', {}, format='json')
        self.assertEqual(response.status_code, 403)

    @patch('stripe.Account.retrieve')
    def test_api_connect_status_queries_event_creator_orders(self, mock_retrieve):
        self.event_creator.stripe_connect_account_id = "acct_organizer_999"
        self.event_creator.stripe_connect_onboarding_completed = True
        self.event_creator.stripe_connect_payouts_enabled = True
        self.event_creator.save()

        mock_account = MagicMock()
        mock_account.details_submitted = True
        mock_account.payouts_enabled = True
        mock_account.requirements.currently_due = []
        mock_account.capabilities = {'transfers': 'active'}
        mock_account.external_accounts.data = []
        mock_retrieve.return_value = mock_account

        # Create paid order under event
        Order.objects.create(
            fundraiser=self.fundraiser,
            product=self.product,
            quantity=1,
            is_paid=True,
            creator_payout_amount=Decimal("15.00"),
            treats_island_amount=Decimal("15.00"),
            payout_status="transferred"
        )

        response_event = self.client.get('/event/connect/status/')
        self.assertEqual(response_event.status_code, 200)
        self.assertTrue(response_event.data['payouts_enabled'])
        self.assertEqual(response_event.data['total_creator_earnings'], 15.00)

        shop_response = self.client.get('/shop/connect/status/')
        self.assertEqual(shop_response.status_code, 404)

    @patch('stripe.Transfer.create')
    def test_finalize_order_in_webhook_triggers_transfer_to_event_creator(self, mock_transfer):
        self.event_creator.stripe_connect_account_id = "acct_organizer_999"
        self.event_creator.stripe_connect_onboarding_completed = True
        self.event_creator.stripe_connect_payouts_enabled = True
        self.event_creator.save()

        mock_transfer.return_value = MagicMock(id="tr_webhook_test_event_creator")

        order = Order.objects.create(
            user=None,
            fundraiser=self.fundraiser,
            product=self.product,
            quantity=2,  # $60.00 total -> $30.00 event creator
            is_paid=False,
            stripe_session_id="cs_test_webhook_session_ec"
        )

        customer_details_mock = MagicMock()
        customer_details_mock.email = "buyer@example.com"
        customer_details_mock.phone = "+1987654321"
        customer_details_mock.name = "Buyer Bob"
        customer_details_mock.address = None

        session_mock = MagicMock()
        session_mock.id = "cs_test_webhook_session_ec"
        session_mock.payment_status = "paid"
        session_mock.client_reference_id = None
        session_mock.customer_details = customer_details_mock
        session_mock.shipping_details = None
        session_mock.metadata = {}

        from shop.views import finalize_order
        finalize_order(session_mock)

        order.refresh_from_db()
        self.assertTrue(order.is_paid)
        self.assertEqual(order.creator_payout_amount, Decimal("30.00"))
        self.assertEqual(order.treats_island_amount, Decimal("30.00"))
        self.assertEqual(order.payout_status, "transferred")
        self.assertEqual(order.stripe_transfer_id, "tr_webhook_test_event_creator")

        # Destination must be event_creator
        args, kwargs = mock_transfer.call_args
        self.assertEqual(kwargs['destination'], "acct_organizer_999")
