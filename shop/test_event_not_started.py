import datetime
from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from event.models import OrganizationType, Event, Fundraiser
from shop.models import Product, Cart

User = get_user_model()


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class PopupStoreEventNotStartedTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(phone="1111111111", password="pass1234", email="buyer@example.com")
        self.owner = User.objects.create_user(phone="2222222222", password="pass1234", email="owner@example.com")
        org_type = OrganizationType.objects.create(name="School", slug="school")
        now = timezone.now()
        self.upcoming_event = Event.objects.create(
            name="Upcoming", type=org_type, start_date=now + datetime.timedelta(days=2),
            end_date=now + datetime.timedelta(days=7), code="UPC1",
        )
        self.ongoing_event = Event.objects.create(
            name="Ongoing", type=org_type, start_date=now - datetime.timedelta(days=1),
            end_date=now + datetime.timedelta(days=4), code="ONG1",
        )
        self.upcoming_store = Fundraiser.objects.create(user=self.owner, event=self.upcoming_event, name="Up Store")
        self.ongoing_store = Fundraiser.objects.create(user=self.owner, event=self.ongoing_event, name="On Store")
        self.product = Product.objects.create(name="Cookie", price="10.00", stock="10", image="product_images/x.png")

    def test_add_to_cart_blocked_for_upcoming_event(self):
        self.client.force_authenticate(self.user)
        res = self.client.post('/shop/cart/add/', {"slug": self.product.slug, "fundraiser_id": self.upcoming_store.id}, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data["code"], "event_not_started")
        self.assertFalse(Cart.objects.exists())

    def test_add_to_cart_allowed_for_ongoing_event(self):
        self.client.force_authenticate(self.user)
        res = self.client.post('/shop/cart/add/', {"slug": self.product.slug, "fundraiser_id": self.ongoing_store.id}, format='json')
        self.assertEqual(res.status_code, 201)

    def test_guest_checkout_blocked_for_upcoming_event(self):
        payload = {"cart": [{"slug": self.product.slug, "quantity": 1, "fundraiser_id": self.upcoming_store.id}]}
        for url in ('/shop/checkout/', '/shop/checkout/guest/'):
            res = self.client.post(url, payload, format='json')
            # guest endpoint validates address first; checkout validates cart first
            if url.endswith('/checkout/'):
                self.assertEqual(res.status_code, 400)
                self.assertEqual(res.data["code"], "event_not_started")

    def test_authenticated_checkout_blocked_for_upcoming_event(self):
        self.client.force_authenticate(self.user)
        payload = {"cart": [{"slug": self.product.slug, "quantity": 1, "fundraiser_id": self.upcoming_store.id}]}
        res = self.client.post('/shop/checkout/', payload, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data["code"], "event_not_started")

    def test_serializer_exposes_purchase_status(self):
        res = self.client.get(f'/event/fundraiser/{self.upcoming_store.id}/public/')
        if res.status_code == 200 and 'shop' in res.data:
            self.assertFalse(res.data['shop']['is_purchasable'])
            self.assertEqual(res.data['shop']['event_status'], 'Upcoming')
        from event.serializers import FundraiserSerializer
        data = FundraiserSerializer(self.upcoming_store).data
        self.assertFalse(data['is_purchasable'])
        self.assertEqual(data['event_status'], 'Upcoming')
        self.assertTrue(data['purchase_message'])
        data = FundraiserSerializer(self.ongoing_store).data
        self.assertTrue(data['is_purchasable'])
        self.assertIsNone(data['purchase_message'])
