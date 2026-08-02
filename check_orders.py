import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laronhall.settings')
django.setup()

from shop.models import Order

print("Recent Orders:")
for order in Order.objects.all().order_by('-id')[:5]:
    print(f"ID: {order.id}, Paid: {order.is_paid}, Session: {order.stripe_session_id}")
