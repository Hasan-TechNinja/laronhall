from django.template.defaultfilters import default
from django.utils.html import MAX_URL_LENGTH
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class OrganizationType(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='organization_logo', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Event(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    type = models.ForeignKey(OrganizationType, on_delete=models.CASCADE, related_name="events")
    duration = models.CharField(max_length=255, default="5")
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    code = models.CharField(max_length=255, blank=True, null=True, unique=True)
    expected_sellers = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    min_estimated_earning = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    max_estimated_earning = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    estimated_participants = models.IntegerField(blank=True, null=True)
    participants = models.ManyToManyField(User, related_name='events', blank=True)

    def __str__(self):
        return self.name or f"Event {self.id}"