from django.contrib import admin
from .models import OrganizationType, Event, Fundraiser

# Register your models here.
#code update from server

# @admin.register(OrganizationType)
# class OrganizationTypeAdmin(admin.ModelAdmin):
#     list_display = ('name', 'created_at', 'updated_at')
#     search_fields = ('name',)
#     prepopulated_fields = {'slug': ('name',)}
#     ordering = ('-created_at',)
    
#     def type_display(self, obj):
#         return obj.slug
#     type_display.short_description = 'Type'
#     type_display.admin_order_field = 'slug'
    

from django.urls import reverse
from django.utils.html import format_html

class FundraiserInline(admin.TabularInline):
    model = Fundraiser
    extra = 0
    fields = ('user', 'name', 'raised_amount', 'goal', 'total_orders', 'is_active')
    readonly_fields = ('raised_amount', 'total_orders')
    show_change_link = True

    def raised_amount(self, obj):
        if not obj or not obj.id:
            return "$0.00"
        total = 0.0
        orders = obj.orders.filter(is_paid=True).select_related('product')
        for order in orders:
            try:
                total += float(order.product.price) * order.quantity
            except (ValueError, TypeError, AttributeError):
                pass
        return f"${total:.2f}"
    raised_amount.short_description = "Raised"

    def total_orders(self, obj):
        if not obj or not obj.id:
            return 0
        return obj.orders.filter(is_paid=True).count()
    total_orders.short_description = "Total Orders"

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'organizer_name', 
        'organizer_email',
        'organizer_phone',
        'name',
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
        'send_email_action',
        # 'is_active'
    )
    # list_filter = ('is_active', 'type', 'start_date', 'end_date')
    search_fields = ('name', 'code', 'creator__email', 'creator__username', 'creator__full_name')
    ordering = ('id',)
    list_select_related = ('creator', 'type')
    readonly_fields = ('organizer_email', 'organizer_phone')
    fields = (
        'creator',
        'organizer_email',
        'organizer_phone',
        'name',
        'type',
        'duration',
        'start_date',
        'end_date',
        'code',
        'estimated_participants',
        # 'is_active',
        'min_estimated_earning',
        'max_estimated_earning',
        # 'participants',
        # 'payout_manager',
        'event_created',
        'popup_store_created',
        'start_reminder_sent',
        'twenty_four_hour_reminder_sent',
        'end_thank_you_sent',
        'banking_details_reminder_sent',
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'creator' and formfield:
            formfield.label_from_instance = lambda obj: obj.full_name.strip() if (obj.full_name and obj.full_name.strip()) else (obj.email or obj.phone or f"User {obj.id}")
        return formfield

    def save_model(self, request, obj, form, change):
        is_new = not change
        super().save_model(request, obj, form, change)
        if is_new and not obj.event_created:
            obj.event_created = True
            obj.save(update_fields=['event_created'])
            if obj.creator and obj.creator.email:
                from authentication.emails import send_welcome_organizer_email
                send_welcome_organizer_email(
                    email=obj.creator.email,
                    organizer_name=obj.creator.full_name or obj.creator.phone
                )
            from authentication.emails import send_event_created_admin_email
            send_event_created_admin_email(obj)

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/send-email/', self.admin_site.admin_view(self.send_email_view), name='event_event_send_email'),
        ]
        return custom_urls + urls

    def send_email_view(self, request, object_id, *args, **kwargs):
        from django.shortcuts import redirect
        from django.contrib import messages
        from django.core.mail import send_mail
        from django.conf import settings
        
        event = self.get_object(request, object_id)
        if request.method == 'POST' and event and event.creator and event.creator.email:
            message = request.POST.get('message', '')
            if message:
                try:
                    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@treatsislandgo.com')
                    send_mail(
                        subject=f"Message regarding event {event.name or event.code}",
                        message=message,
                        from_email=from_email,
                        recipient_list=[event.creator.email],
                        fail_silently=False,
                    )
                    messages.success(request, f"Email sent successfully to {event.creator.email}.")
                except Exception as e:
                    messages.error(request, f"Failed to send email: {str(e)}")
            else:
                messages.warning(request, "Email message was empty.")
        return redirect(reverse('admin:event_event_changelist'))


    def organizer_name(self, obj):
        if obj.creator and obj.creator.full_name and obj.creator.full_name.strip():
            return obj.creator.full_name.strip()
        return "-"
    organizer_name.short_description = "Organizer"
    organizer_name.admin_order_field = 'creator__full_name'

    creator_name = organizer_name

    def organizer_email(self, obj):
        return obj.creator.email if obj and obj.creator and obj.creator.email else "-"
    organizer_email.short_description = "Organizer Email"
    organizer_email.admin_order_field = 'creator__email'

    def organizer_phone(self, obj):
        return obj.creator.phone if obj and obj.creator and obj.creator.phone else "-"
    organizer_phone.short_description = "Organizer Phone"
    organizer_phone.admin_order_field = 'creator__phone'

    def current_status(self, obj):
        from django.utils import timezone
        now = timezone.now()
        if obj.start_date and obj.end_date:
            if obj.start_date > now:
                return "Upcoming"
            elif obj.start_date <= now <= obj.end_date:
                return "Ongoing"
            else:
                return "Ended"
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
        url = reverse('admin:shop_report_changelist') + f'?fundraiser__event__id__exact={obj.id}'
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


    def send_email_action(self, obj):
        if not obj.creator or not obj.creator.email:
            return "-"
        url = reverse('admin:event_event_send_email', args=[obj.id])
        return format_html(
            '''<button type="button" class="button" onclick="
            var msg = prompt('Enter message to send to {}');
            if(msg) {{
                var form = document.createElement('form');
                form.method = 'POST';
                form.action = '{}';
                var csrf = document.createElement('input');
                csrf.type = 'hidden';
                csrf.name = 'csrfmiddlewaretoken';
                var csrfNode = document.querySelector('[name=csrfmiddlewaretoken]');
                if (csrfNode) {{
                    csrf.value = csrfNode.value;
                }}
                form.appendChild(csrf);
                var input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'message';
                input.value = msg;
                form.appendChild(input);
                document.body.appendChild(form);
                form.submit();
            }}
            ">Send Email</button>''',
            obj.creator.email, url
        )
    send_email_action.short_description = "Send Email"


@admin.register(Fundraiser)
class FundraiserAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'participant', 'sales_and_goal', 'actions_buttons')
    list_filter = ('event', 'event__type', 'created_at', 'is_active')
    search_fields = ('name', 'user__email', 'user__full_name', 'event__name')
    ordering = ('-created_at',)
    list_select_related = ('user', 'event')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        from django.db.models import Sum, F, FloatField, Value, Q
        from django.db.models.functions import Cast, Coalesce
        qs = qs.annotate(
            total_sales_annotated=Coalesce(
                Sum(
                    Cast(F('orders__product__price'), FloatField()) * F('orders__quantity'),
                    filter=Q(orders__is_paid=True)
                ),
                Value(0.0),
                output_field=FloatField()
            )
        )
        return qs

    def store_name(self, obj):
        return obj.name or f"{obj.user.email}'s Store"
    store_name.short_description = "Store Name"
    store_name.admin_order_field = 'name'

    def participant(self, obj):
        return getattr(obj.user, 'full_name', obj.user.email) or obj.user.email
    participant.short_description = "Participant"
    participant.admin_order_field = 'user__email'

    def sales_and_goal(self, obj):
        sales = getattr(obj, 'total_sales_annotated', 0.0)
        goal = obj.goal or 0
        if goal > 0:
            percentage = (sales / float(goal)) * 100
            return f"${sales:,.2f} / ${goal:,.2f} ({percentage:.0f}%)"
        return f"${sales:,.2f} / None"
    sales_and_goal.short_description = "Sales / Goal"
    sales_and_goal.admin_order_field = 'total_sales_annotated'

    def actions_buttons(self, obj):
        from django.conf import settings
        domain = getattr(settings, 'FRONTEND_URL', 'https://treatsislandgo.com').rstrip('/')
        full_url = f"{domain}/store/{obj.id}" 
        
        copy_js = f"navigator.clipboard.writeText('{full_url}'); alert('Copied link!');"
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={full_url}"
        
        toggle_label = "Disable" if getattr(obj, 'is_active', True) else "Enable"
        toggle_url = reverse('admin:fundraiser_toggle_active', args=[obj.id])
        
        supporters_url = reverse('admin:shop_report_changelist') + f'?fundraiser__id__exact={obj.id}'
        
        return format_html(
            '<a class="button" href="{}" style="margin:2px;">View Supporters</a> '
            '<button class="button" onclick="{}" type="button" style="margin:2px;">Copy Link</button> '
            '<a class="button" href="{}" target="_blank" style="margin:2px;">QR</a> '
            '<a class="button" href="{}" style="margin:2px;">{}</a>',
            supporters_url, copy_js, qr_url, toggle_url, toggle_label
        )
    actions_buttons.short_description = "Actions"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/toggle-active/', self.admin_site.admin_view(self.toggle_active_view), name='fundraiser_toggle_active'),
        ]
        return custom_urls + urls

    def toggle_active_view(self, request, object_id, *args, **kwargs):
        from django.shortcuts import redirect
        from django.contrib import messages
        fundraiser = self.get_object(request, object_id)
        if fundraiser:
            fundraiser.is_active = not getattr(fundraiser, 'is_active', True)
            fundraiser.save()
            status = "enabled" if fundraiser.is_active else "disabled"
            messages.success(request, f"Popup store for {fundraiser.user.email} has been {status}.")
        return redirect(reverse('admin:event_fundraiser_changelist'))

    def save_model(self, request, obj, form, change):
        is_new = not change
        super().save_model(request, obj, form, change)
        if is_new and obj.event and not obj.event.popup_store_created:
            obj.event.popup_store_created = True
            obj.event.save(update_fields=['popup_store_created'])
            from authentication.emails import (
                send_new_popup_alert_email,
                send_popup_store_created_member_email,
                send_popup_store_created_admin_email,
            )
            store_url = f"https://treatsislandgo.com/store/{obj.id}"
            member_name = (obj.user.full_name or obj.user.phone) if obj.user else "Supporter"
            org_name = (obj.event.creator.full_name or obj.event.creator.phone) if obj.event.creator else "Organizer"
            if obj.event.creator and obj.event.creator.email:
                send_new_popup_alert_email(
                    email=obj.event.creator.email,
                    organizer_name=org_name,
                    member_name=member_name,
                    popup_store_name=obj.name or "Pop-Up Store"
                )
            if obj.user and obj.user.email:
                send_popup_store_created_member_email(
                    email=obj.user.email,
                    member_name=member_name,
                    popup_store_name=obj.name or "Pop-Up Store",
                    event_name=obj.event.name or obj.event.code,
                    store_url=store_url
                )
            send_popup_store_created_admin_email(obj)