from django.template.defaultfilters import default
from django.utils.html import MAX_URL_LENGTH
from django.db import models
from django.conf import settings
# Create your models here.
class OrganizationType(models.Model):
    name = models.CharField(max_length=255, verbose_name="Name of Organization")
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='organization_logo', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Organization Type"
        verbose_name_plural = "Organization Types"

    def __str__(self):
        return self.name


class Event(models.Model):
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_events', null=True, blank=True, verbose_name="Organizer")
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Name of Organization")
    type = models.ForeignKey(OrganizationType, on_delete=models.CASCADE, related_name="events")
    duration = models.IntegerField(default=5)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    code = models.CharField(max_length=255, blank=True, null=True, unique=True)
    expected_sellers = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    min_estimated_earning = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Min estimated earnings")
    max_estimated_earning = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Max estimated earnings")
    estimated_participants = models.IntegerField(blank=True, null=True)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='events', blank=True)
    payout_manager = models.CharField(max_length=255, blank=True, null=True)
    event_created = models.BooleanField(default=False, verbose_name="Event created")
    popup_store_created = models.BooleanField(default=False, verbose_name="Popup store created")
    start_reminder_sent = models.BooleanField(default=False)
    twenty_four_hour_reminder_sent = models.BooleanField(default=False)
    end_thank_you_sent = models.BooleanField(default=False)
    banking_details_reminder_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Campaign"
        verbose_name_plural = "Campaigns"

    def __str__(self):
        return self.name or f"Event {self.id}"


class Organization(Event):
    class Meta:
        proxy = True
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"


class Fundraiser(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='fundraisers', verbose_name="Organizer")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='fundraisers', verbose_name="Name of Organization")
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Name of Popup Store")
    video = models.FileField(upload_to='fundraisers_media/', blank=True, null=True)
    image = models.ImageField(upload_to='fundraisers_media/', blank=True, null=True)
    description = models.TextField(blank=True, null=True, verbose_name="Add Message")
    goal = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'event')
        verbose_name = "Popup Store"
        verbose_name_plural = "Popup Stores"

    @property
    def has_payout_setup(self):
        return bool(self.user and self.user.stripe_connect_payouts_enabled)

    @property
    def stripe_connect_account_id(self):
        return self.user.stripe_connect_account_id if self.user else None

    @property
    def total_creator_earnings(self):
        from django.db.models import Sum
        orders = self.orders.filter(is_paid=True)
        res = orders.aggregate(total=Sum('creator_payout_amount'))['total']
        return float(res) if res is not None else 0.0

    def __str__(self):
        user_name = self.user.full_name.strip() if (self.user and self.user.full_name and self.user.full_name.strip()) else (self.user.email if self.user else f"User {self.user_id}")
        store_display = self.name.strip() if (self.name and self.name.strip()) else f"{user_name}'s Store"
        event_code = self.event.code if self.event else ""
        return f"{store_display} - {event_code}" if event_code else store_display