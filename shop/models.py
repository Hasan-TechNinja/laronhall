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
    
    # Shipping Tracking Details
    tracking_number = models.CharField(max_length=255, blank=True, null=True)
    carrier = models.CharField(max_length=100, blank=True, null=True)
    shipment_status = models.CharField(max_length=100, default='unshipped')
    
    invoice_id = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

                        
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
