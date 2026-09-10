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
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"

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
    start_reminder_sent = models.BooleanField(default=False)
    twenty_four_hour_reminder_sent = models.BooleanField(default=False)
    end_thank_you_sent = models.BooleanField(default=False)
    banking_details_reminder_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Campaign"
        verbose_name_plural = "Campaigns"

    def __str__(self):
        return self.name or f"Event {self.id}"


class Fundraiser(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='fundraisers')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='fundraisers')
    name = models.CharField(max_length=255, blank=True, null=True)
    video = models.FileField(upload_to='fundraisers_media/', blank=True, null=True)
    image = models.ImageField(upload_to='fundraisers_media/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    goal = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'event')
        verbose_name = "Popup Store"
        verbose_name_plural = "Popup Stores"

    def __str__(self):
        return f"{self.user.email} - {self.event.code}"