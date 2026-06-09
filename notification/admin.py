from django.contrib import admin
from . models import DeviceToken, Notification

# Register your models here.

@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'platform', 'is_active']
    list_filter = ['platform', 'is_active']
    search_fields = ['user__username', 'token']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['user__username', 'title', 'body']
