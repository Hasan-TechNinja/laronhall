from django.template.defaultfilters import default
from django.db import models
from django.conf import settings
from django.utils.text import slugify

# Create your models here.

class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    price = models.CharField(max_length=50)
    stock = models.CharField(max_length=255)
    weight = models.DecimalField(max_digits=8, decimal_places=2, default=12)
    image = models.ImageField(upload_to='product_images')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Product, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    fundraiser = models.ForeignKey('event.Fundraiser', on_delete=models.SET_NULL, null=True, blank=True, related_name='carts')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart')
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.phone} - {self.product.name}"


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='order', null=True, blank=True)
    fundraiser = models.ForeignKey('event.Fundraiser', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order')
    quantity = models.IntegerField(default=1)
    
    # Guest and Shipping Details
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    
    # Payment status
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    delivery_charge = models.CharField(max_length=50, default="0.00")

    # Stripe Connect 50/50 Payout Tracking
    PAYOUT_STATUS_CHOICES = (
        ('pending', 'Pending Payment'),
        ('pending_onboarding', 'Pending Shop Creator Onboarding'),
        ('transferred', 'Transferred to Creator'),
        ('not_applicable', 'Not Applicable (No Fundraiser Shop)'),
        ('failed', 'Payout Transfer Failed'),
    )
    creator_payout_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="50% of product subtotal to shop creator")
    treats_island_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="50% of product subtotal to Treats Island")
    stripe_transfer_id = models.CharField(max_length=255, blank=True, null=True)
    payout_status = models.CharField(max_length=50, default='pending', choices=PAYOUT_STATUS_CHOICES)
    
    # Shipping Tracking Details
    tracking_number = models.CharField(max_length=255, blank=True, null=True)
    carrier = models.CharField(max_length=100, blank=True, null=True)
    shipment_status = models.CharField(max_length=100, default='unshipped')
    
    invoice_id = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def product_subtotal(self):
        try:
            return round(float(self.product.price) * self.quantity, 2)
        except (ValueError, TypeError, AttributeError):
            return 0.00

    def calculate_split_amounts(self):
        """Calculates 50% split for shop creator and 50% for Treats Island"""
        subtotal = self.product_subtotal
        if self.fundraiser:
            creator_share = round(subtotal * 0.50, 2)
            treats_share = round(subtotal - creator_share, 2)
            return creator_share, treats_share
        return 0.00, subtotal
                        
    def __str__(self):
        if self.user:
            return f"{self.user.phone} - {self.product.name}"
        return f"Guest ({self.email}) - {self.product.name}"

class Review(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='review_images', blank=True, null=True)
    rating = models.IntegerField(default=5)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.rating} stars"


class Report(Order):
    class Meta:
        proxy = True
        verbose_name = "Report"
        verbose_name_plural = "Reports"

class FinanceSummary(Order):
    class Meta:
        proxy = True
        verbose_name = "Finance Summary"
        verbose_name_plural = "Finance Summaries"


class DonationItem(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=10.00, help_text="Donation amount")
    image = models.ImageField(upload_to='donation_images', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "donation-item"
            slug = base_slug
            counter = 1
            while DonationItem.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (${self.price})"


class Donation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='donations', null=True, blank=True)
    donation_item = models.ForeignKey(DonationItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='donations')
    fundraiser = models.ForeignKey('event.Fundraiser', on_delete=models.SET_NULL, null=True, blank=True, related_name='donations')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)  # Always 1 as per requirements

    # Donor details (no shipping address required)
    name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)

    # Payment status
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    is_paid = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def organization_amount(self):
        """Organization receives 25% of donation if attributed to a fundraiser/campaign"""
        if self.fundraiser:
            return round(float(self.amount) * 0.25, 2)
        return 0.0

    @property
    def treats_island_amount(self):
        """Treats Island receives 75% of donation (or 100% if non-event donation)"""
        if self.fundraiser:
            return round(float(self.amount) * 0.75, 2)
        return round(float(self.amount), 2)

    def __str__(self):
        donor = self.name or self.email or (self.user.phone if self.user else "Anonymous")
        item_name = self.donation_item.name if self.donation_item else "Direct Donation"
        return f"Donation: {donor} - ${self.amount} ({item_name})"
