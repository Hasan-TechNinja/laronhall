from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock
from decimal import Decimal

from event.models import Event, Fundraiser, OrganizationType
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
        self.user = User.objects.create_user(
            phone="+1234567890",
            password="testpassword123",
            email="creator@example.com",
            full_name="Jane Creator",
            is_active=True
        )
        self.client.force_authenticate(user=self.user)

        self.org_type = OrganizationType.objects.create(name="School", slug="school")
        self.event = Event.objects.create(
            name="Spring School Fundraiser",
            type=self.org_type,
            start_date=timezone.now(),
            duration=5,
            creator=self.user,
            is_active=True
        )
        self.fundraiser = Fundraiser.objects.create(
            user=self.user,
            event=self.event,
            name="Jane's Candy Store",
            goal=Decimal("500.00")
        )
        self.product = Product.objects.create(
            name="Chocolate Truffle Box",
            price="30.00",
            stock="100",
            weight=12.0
        )

    @patch('stripe.Account.create')
    def test_get_or_create_connect_account_creates_new(self, mock_account_create):
        mock_account = MagicMock()
        mock_account.id = "acct_test12345"
        mock_account_create.return_value = mock_account

        account = get_or_create_connect_account(self.user)
        self.assertEqual(account.id, "acct_test12345")
        self.user.refresh_from_db()
        self.assertEqual(self.user.stripe_connect_account_id, "acct_test12345")
        mock_account_create.assert_called_once()

    @patch('stripe.Account.retrieve')
    @patch('stripe.AccountLink.create')
    def test_create_onboarding_link(self, mock_link_create, mock_account_retrieve):
        self.user.stripe_connect_account_id = "acct_test12345"
        self.user.save()

        mock_account = MagicMock()
        mock_account.id = "acct_test12345"
        mock_account_retrieve.return_value = mock_account

        mock_link = MagicMock()
        mock_link.url = "https://connect.stripe.com/setup/s/test_link"
        mock_link_create.return_value = mock_link

        url = create_onboarding_link(self.user)
        self.assertEqual(url, "https://connect.stripe.com/setup/s/test_link")
        mock_link_create.assert_called_once_with(
            account="acct_test12345",
            refresh_url="https://treatsislandgo.com/payout/refresh",
            return_url="https://treatsislandgo.com/payout/return",
            type="account_onboarding"
        )

    @patch('stripe.Account.create_login_link')
    def test_create_dashboard_login_link(self, mock_login_link):
        self.user.stripe_connect_account_id = "acct_test12345"
        self.user.save()

        mock_link = MagicMock()
        mock_link.url = "https://connect.stripe.com/express/login_test"
        mock_login_link.return_value = mock_link

        url = create_dashboard_login_link(self.user)
        self.assertEqual(url, "https://connect.stripe.com/express/login_test")

    @patch('stripe.Account.retrieve')
    def test_sync_connect_account_status(self, mock_account_retrieve):
        self.user.stripe_connect_account_id = "acct_test12345"
        self.user.save()

        mock_account = MagicMock()
        mock_account.details_submitted = True
        mock_account.payouts_enabled = True
        mock_account_retrieve.return_value = mock_account

        status = sync_connect_account_status(self.user)
        self.assertTrue(status['onboarding_completed'])
        self.assertTrue(status['payouts_enabled'])

        self.user.refresh_from_db()
        self.assertTrue(self.user.stripe_connect_onboarding_completed)
        self.assertTrue(self.user.stripe_connect_payouts_enabled)

    @patch('stripe.Transfer.create')
    def test_transfer_order_payout_with_onboarded_creator(self, mock_transfer_create):
        # Setup creator as onboarded
        self.user.stripe_connect_account_id = "acct_test12345"
        self.user.stripe_connect_onboarding_completed = True
        self.user.stripe_connect_payouts_enabled = True
        self.user.save()

        # Order of 2 items @ $30.00 = $60.00 total.
        # 50% split: $30.00 creator, $30.00 Treats Island
        order = Order.objects.create(
            user=None,
            fundraiser=self.fundraiser,
            product=self.product,
            quantity=2,
            is_paid=True,
            stripe_session_id="cs_test_split_1"
        )

        mock_transfer = MagicMock()
        mock_transfer.id = "tr_test_split_999"
        mock_transfer_create.return_value = mock_transfer

        transfer_order_payout(order)
        order.refresh_from_db()

        self.assertEqual(order.creator_payout_amount, Decimal("30.00"))
        self.assertEqual(order.treats_island_amount, Decimal("30.00"))
        self.assertEqual(order.payout_status, "transferred")
        self.assertEqual(order.stripe_transfer_id, "tr_test_split_999")

        mock_transfer_create.assert_called_once_with(
            amount=3000,  # $30.00 in cents
            currency="usd",
            destination="acct_test12345",
            description=f"50% Shop Revenue Payout for Order #{order.id} (Chocolate Truffle Box)",
            metadata={
                "order_id": str(order.id),
                "fundraiser_id": str(self.fundraiser.id),
                "event_id": str(self.event.id),
                "product_name": "Chocolate Truffle Box",
                "creator_user_id": str(self.user.id),
            }
        )

    def test_transfer_order_payout_pending_onboarding_when_not_onboarded(self):
        # Creator has not completed onboarding
        self.user.stripe_connect_payouts_enabled = False
        self.user.save()

        order = Order.objects.create(
            user=None,
            fundraiser=self.fundraiser,
            product=self.product,
            quantity=1,
            is_paid=True,
            stripe_session_id="cs_test_split_2"
        )

        transfer_order_payout(order)
        order.refresh_from_db()

        self.assertEqual(order.creator_payout_amount, Decimal("15.00"))
        self.assertEqual(order.treats_island_amount, Decimal("15.00"))
        self.assertEqual(order.payout_status, "pending_onboarding")
        self.assertIsNone(order.stripe_transfer_id)

    @patch('stripe.Transfer.create')
    def test_process_pending_creator_payouts_after_onboarding(self, mock_transfer_create):
        # Create pending order
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

        # Now creator onboards
        self.user.stripe_connect_account_id = "acct_test12345"
        self.user.stripe_connect_onboarding_completed = True
        self.user.stripe_connect_payouts_enabled = True
        self.user.save()

        mock_transfer = MagicMock()
        mock_transfer.id = "tr_batch_123"
        mock_transfer_create.return_value = mock_transfer

        result = process_pending_creator_payouts(self.user)
        self.assertEqual(result['transferred_count'], 1)
        self.assertEqual(result['total_transferred'], 15.00)

        order.refresh_from_db()
        self.assertEqual(order.payout_status, "transferred")
        self.assertEqual(order.stripe_transfer_id, "tr_batch_123")

    @patch('shop.stripe_connect.create_onboarding_link')
    def test_api_connect_onboard(self, mock_create_link):
        mock_create_link.return_value = "https://connect.stripe.com/onboard/abc"
        response = self.client.post('/shop/connect/onboard/', {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['onboarding_url'], "https://connect.stripe.com/onboard/abc")

    @patch('stripe.Account.retrieve')
    def test_api_connect_status(self, mock_retrieve):
        self.user.stripe_connect_account_id = "acct_test12345"
        self.user.save()

        mock_account = MagicMock()
        mock_account.details_submitted = True
        mock_account.payouts_enabled = True
        mock_retrieve.return_value = mock_account

        # Create paid order for summary calculation
        Order.objects.create(
            fundraiser=self.fundraiser,
            product=self.product,
            quantity=1,
            is_paid=True,
            creator_payout_amount=Decimal("15.00"),
            treats_island_amount=Decimal("15.00"),
            payout_status="transferred"
        )

        response = self.client.get('/shop/connect/status/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['onboarding_completed'])
        self.assertTrue(response.data['payouts_enabled'])
        self.assertEqual(response.data['total_creator_earnings'], 15.00)
        self.assertEqual(response.data['transferred_amount'], 15.00)

    @patch('stripe.Account.create_login_link')
    def test_api_connect_dashboard(self, mock_login_link):
        self.user.stripe_connect_account_id = "acct_test12345"
        self.user.save()

        mock_link = MagicMock()
        mock_link.url = "https://connect.stripe.com/express/dash_123"
        mock_login_link.return_value = mock_link

        response = self.client.post('/shop/connect/dashboard/', {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['dashboard_url'], "https://connect.stripe.com/express/dash_123")

    @patch('stripe.Transfer.create')
    def test_finalize_order_in_webhook_triggers_50_50_split(self, mock_transfer):
        self.user.stripe_connect_account_id = "acct_test12345"
        self.user.stripe_connect_onboarding_completed = True
        self.user.stripe_connect_payouts_enabled = True
        self.user.save()

        mock_transfer.return_value = MagicMock(id="tr_webhook_test_1")

        order = Order.objects.create(
            user=None,
            fundraiser=self.fundraiser,
            product=self.product,
            quantity=2,  # $60.00 total -> $30.00 creator
            is_paid=False,
            stripe_session_id="cs_test_webhook_session_99"
        )

        customer_details_mock = MagicMock()
        customer_details_mock.email = "buyer@example.com"
        customer_details_mock.phone = "+1987654321"
        customer_details_mock.name = "Buyer Bob"
        customer_details_mock.address = None

        session_mock = MagicMock()
        session_mock.id = "cs_test_webhook_session_99"
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
        self.assertEqual(order.stripe_transfer_id, "tr_webhook_test_1")
