from django.contrib import admin
from .models import OrganizationType, Event, Fundraiser

# Register your models here.

@admin.register(OrganizationType)
class OrganizationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at', 'updated_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('-created_at',)
    

from django.urls import reverse
from django.utils.html import format_html

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'creator', 
        'code', 
        'start_date', 
        'end_date', 
        'current_status', 
        'total_sales', 
        'amount_to_organizer', 
        'to_treats_island', 
        'view_stores', 
        'sales_report', 
        'edit_event',
        'delete_event',
        'relaunch_event',
        'is_active'
    )
    list_filter = ('is_active', 'type', 'start_date', 'end_date')
    search_fields = ('name', 'code', 'creator__email', 'creator__username', 'creator__full_name')
    ordering = ('id',)
    list_select_related = ('creator', 'type')

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/relaunch/', self.admin_site.admin_view(self.relaunch_view), name='event_event_relaunch'),
        ]
        return custom_urls + urls

    def relaunch_view(self, request, object_id, *args, **kwargs):
        from django.shortcuts import redirect
        from django.contrib import messages
        event = self.get_object(request, object_id)
        if event:
            event.is_active = True
            event.save()
            messages.success(request, f"Event {event.name or event.code} has been relaunched (set to active).")
        return redirect(reverse('admin:event_event_changelist'))

    def creator_name(self, obj):
        if obj.creator:
            return obj.creator.full_name or obj.creator.phone or obj.creator.email
        return "-"
    creator_name.short_description = "Creator Name"

    def current_status(self, obj):
        from django.utils import timezone
        now = timezone.now()
        if obj.start_date and obj.end_date:
            if obj.start_date > now:
                return "Upcoming"
            elif obj.start_date <= now <= obj.end_date:
                return "Ongoing"
            else:
                return "Completed"
        elif obj.start_date:
            if obj.start_date > now:
                return "Upcoming"
            else:
                return "Ongoing"
        return "Unknown"
    current_status.short_description = "Status"

    def get_total_sales(self, obj):
        if hasattr(obj, '_cached_total_sales'):
            return obj._cached_total_sales
            
        from shop.models import Order
        total = 0.0
        orders = Order.objects.filter(fundraiser__event=obj, is_paid=True).select_related('product')
        for order in orders:
            try:
                total += float(order.product.price) * order.quantity
            except (ValueError, TypeError, AttributeError):
                pass
                
        obj._cached_total_sales = total
        return total

    def total_sales(self, obj):
        val = self.get_total_sales(obj)
        return f"${val:.2f}"
    total_sales.short_description = "Total sales and donations"

    def amount_to_organizer(self, obj):
        val = self.get_total_sales(obj) * 0.5
        return f"${val:.2f}"
    amount_to_organizer.short_description = "Amount due to organization"

    def to_treats_island(self, obj):
        val = self.get_total_sales(obj) * 0.5
        return f"${val:.2f}"
    to_treats_island.short_description = "Amount due to Treats Island"

    def view_stores(self, obj):
        url = reverse('admin:event_fundraiser_changelist') + f'?event__id__exact={obj.id}'
        return format_html('<a class="button" href="{}">View Stores</a>', url)
    view_stores.short_description = "View Stores"

    def sales_report(self, obj):
        url = reverse('admin:shop_order_changelist') + f'?fundraiser__event__id__exact={obj.id}'
        return format_html('<a class="button" href="{}">Sales Report</a>', url)
    sales_report.short_description = "Sales Report"

    def edit_event(self, obj):
        url = reverse('admin:event_event_change', args=[obj.id])
        return format_html('<a class="button" href="{}">Edit</a>', url)
    edit_event.short_description = "Edit"

    def delete_event(self, obj):
        url = reverse('admin:event_event_delete', args=[obj.id])
        return format_html('<a class="button" href="{}">Delete</a>', url)
    delete_event.short_description = "Delete"

    def relaunch_event(self, obj):
        url = reverse('admin:event_event_relaunch', args=[obj.id])
        return format_html('<a class="button" href="{}">Relaunch</a>', url)
    relaunch_event.short_description = "Relaunch"



@admin.register(Fundraiser)
class FundraiserAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'event', 'goal', 'created_at', 'updated_at')
    list_filter = ('user', 'event', 'created_at', 'updated_at')
    search_fields = ('user__email', 'event__code')
    ordering = ('id',)
    list_select_related = ('user', 'event')