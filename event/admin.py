from django.contrib import admin
from .models import OrganizationType, Event, Fundraiser, Organization

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
from django.utils.safestring import mark_safe

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
        from django.core.mail import EmailMessage
        from django.conf import settings
        
        event = self.get_object(request, object_id)
        if request.method == 'POST' and event and event.creator and event.creator.email:
            message = request.POST.get('message', '').strip()
            subject = request.POST.get('subject', '').strip() or f"Message regarding event {event.name or event.code}"
            if message:
                try:
                    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@treatsislandgo.com')
                    email = EmailMessage(
                        subject=subject,
                        body=message,
                        from_email=from_email,
                        to=[event.creator.email],
                    )
                    attachments = request.FILES.getlist('attachment')
                    for f in attachments:
                        email.attach(f.name, f.read(), f.content_type)

                    email.send(fail_silently=False)
                    attach_note = f" with {len(attachments)} attachment(s)" if attachments else ""
                    messages.success(request, f"Email sent successfully to {event.creator.email}{attach_note}.")
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

    def get_total_donations(self, obj):
        if hasattr(obj, '_cached_total_donations'):
            return obj._cached_total_donations
            
        from shop.models import Donation
        total = 0.0
        donations = Donation.objects.filter(fundraiser__event=obj, is_paid=True)
        for donation in donations:
            try:
                total += float(donation.amount)
            except (ValueError, TypeError, AttributeError):
                pass
                
        obj._cached_total_donations = total
        return total

    def total_sales(self, obj):
        val = self.get_total_sales(obj) + self.get_total_donations(obj)
        return f"${val:.2f}"
    total_sales.short_description = "Total sales and donations"

    def amount_to_organizer(self, obj):
        sales = self.get_total_sales(obj)
        donations = self.get_total_donations(obj)
        val = (sales * 0.5) + (donations * 0.25)
        return f"${val:.2f}"
    amount_to_organizer.short_description = "Amount due to organization"

    def to_treats_island(self, obj):
        sales = self.get_total_sales(obj)
        donations = self.get_total_donations(obj)
        val = (sales * 0.5) + (donations * 0.75)
        return f"${val:.2f}"
    to_treats_island.short_description = "Amount due to Treats Island"

    def view_stores(self, obj):
        url = reverse('admin:event_fundraiser_changelist') + f'?event__id__exact={obj.id}'
        return format_html('<a class="button" href="{}">View Stores</a>', url)
    view_stores.short_description = "View Stores"

    def sales_report(self, obj):
        try:
            url = reverse('admin:shop_report_changelist') + f'?fundraiser__event__id__exact={obj.id}'
        except Exception:
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
    list_display = ('store_name', 'event_name', 'sales_and_goal', 'payout_status_display', 'actions_buttons')

    def payout_status_display(self, obj):
        if not obj or not obj.user:
            return "No User"
        if obj.user.stripe_connect_payouts_enabled:
            return format_html('<span style="color:green; font-weight:bold;">Active</span>')
        elif obj.user.stripe_connect_account_id:
            return format_html('<span style="color:orange; font-weight:bold;">Pending Onboarding</span>')
        return format_html('<span style="color:#888;">Not Connected</span>')
    payout_status_display.short_description = "Payout Setup"

    list_filter = ('event', 'event__type', 'created_at', 'is_active')
    search_fields = ('name', 'user__email', 'user__full_name', 'event__name', 'event__code')
    ordering = ('-created_at',)
    list_select_related = ('user', 'event', 'event__type')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            field = super().formfield_for_foreignkey(db_field, request, **kwargs)
            field.label = "Organizer"
            field.label_from_instance = lambda obj: (
                obj.full_name.strip() if (obj.full_name and obj.full_name.strip())
                else (obj.email if obj.email else (obj.phone if obj.phone else f"User {obj.id}"))
            )
            return field
        if db_field.name == "event":
            field = super().formfield_for_foreignkey(db_field, request, **kwargs)
            field.label = "Name of Organization"
            return field
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "event":
            field.label = "Name of Organization"
        elif db_field.name == "name":
            field.label = "Name of Popup Store"
        elif db_field.name == "description":
            field.label = "Add Message"
        return field

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
        if obj.name and obj.name.strip():
            return obj.name.strip()
        user_name = obj.user.full_name.strip() if (obj.user and obj.user.full_name and obj.user.full_name.strip()) else None
        if user_name:
            return f"{user_name}'s Store"
        if obj.user and obj.user.email:
            return f"{obj.user.email}'s Store"
        return f"Store {obj.id}"
    store_name.short_description = "Store Name"
    store_name.admin_order_field = 'name'

    def participant(self, obj):
        if not obj.user:
            return "-"
        name = obj.user.full_name.strip() if (obj.user.full_name and obj.user.full_name.strip()) else ""
        email = obj.user.email or ""
        phone = obj.user.phone or ""
        if name and email:
            return format_html(
                '<div style="font-weight: 600; color: #1e293b;">{}</div>'
                '<div style="font-size: 11px; color: #64748b;">{}</div>',
                name, email
            )
        elif name:
            return name
        elif email:
            return email
        return phone or f"User {obj.user.id}"
    participant.short_description = "Participant"
    participant.admin_order_field = 'user__full_name'

    def event_name(self, obj):
        if not obj.event:
            return "-"
        name = obj.event.name or f"Event {obj.event.id}"
        code = obj.event.code or ""
        type_name = obj.event.type.name if (obj.event and obj.event.type) else ""
        url = reverse('admin:event_event_change', args=[obj.event.id])

        type_badge = f'<div style="margin-top: 3px;"><span style="display: inline-block; background: #f1f5f9; color: #475569; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{type_name}</span></div>' if type_name else ""
        code_text = f'<div style="font-size: 11px; color: #64748b; margin-top: 2px;">Code: <strong>{code}</strong></div>' if code else ""

        return format_html(
            '<a href="{}" style="font-weight: 600; text-decoration: none; color: #ba215a;">{}</a>{}{}',
            url, name, mark_safe(code_text), mark_safe(type_badge)
        )
    event_name.short_description = "Event / Campaign"
    event_name.admin_order_field = 'event__name'


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
        
        try:
            supporters_url = reverse('admin:shop_report_changelist') + f'?fundraiser__id__exact={obj.id}'
        except Exception:
            supporters_url = reverse('admin:shop_order_changelist') + f'?fundraiser__id__exact={obj.id}'

        
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


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    change_form_template = 'admin/event/organization/change_form.html'
    list_display = (
        'organization_name',
        'organization_type',
        'contact_person',
        'organizer_email',
        'organizer_phone',
    )
    list_display_links = ('organization_name',)
    list_filter = ('type', 'is_active')
    search_fields = (
        'name',
        'code',
        'creator__email',
        'creator__phone',
        'creator__full_name',
        'type__name',
    )
    ordering = ('-id',)
    list_select_related = ('creator', 'type')
    readonly_fields = ('organizer_email', 'organizer_phone')
    fields = (
        'name',
        'type',
        'creator',
        'organizer_email',
        'organizer_phone',
    )

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/send-email/', self.admin_site.admin_view(self.send_email_view), name='event_organization_send_email'),
            path('quick-add-organizer/', self.admin_site.admin_view(self.quick_add_organizer_view), name='event_organization_quick_add_organizer'),
            path('organizer-info/<int:user_id>/', self.admin_site.admin_view(self.organizer_info_view), name='event_organization_user_info'),
        ]
        return custom_urls + urls

    def send_email_view(self, request, object_id, *args, **kwargs):
        from django.shortcuts import redirect
        from django.contrib import messages
        from django.core.mail import EmailMessage
        from django.conf import settings

        event = self.get_object(request, object_id)
        if request.method == 'POST' and event and event.creator and event.creator.email:
            message = request.POST.get('message', '').strip()
            subject = request.POST.get('subject', '').strip() or f"Message regarding organization {event.name or event.code}"
            if message:
                try:
                    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@treatsislandgo.com')
                    email = EmailMessage(
                        subject=subject,
                        body=message,
                        from_email=from_email,
                        to=[event.creator.email],
                    )
                    attachments = request.FILES.getlist('attachment')
                    for f in attachments:
                        email.attach(f.name, f.read(), f.content_type)

                    email.send(fail_silently=False)
                    attach_note = f" with {len(attachments)} attachment(s)" if attachments else ""
                    messages.success(request, f"Email sent successfully to {event.creator.email}{attach_note}.")
                except Exception as e:
                    messages.error(request, f"Failed to send email: {str(e)}")
            else:
                messages.warning(request, "Email message was empty.")
        elif request.method == 'POST':
            messages.error(request, "Cannot send email: Organizer has no email address.")

        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        return redirect(reverse('admin:event_organization_changelist'))

    def quick_add_organizer_view(self, request):
        from django.http import JsonResponse
        from authentication.models import User
        if request.method != 'POST':
            return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()

        if not phone:
            return JsonResponse({'status': 'error', 'message': 'Contact Number (Phone) is required.'}, status=400)

        try:
            from authentication.utils import normalize_phone_number
            norm_phone = normalize_phone_number(phone)
        except Exception:
            norm_phone = phone

        user = User.objects.filter(phone=norm_phone).first()
        if not user and email:
            user = User.objects.filter(email__iexact=email).first()

        if user:
            if full_name:
                user.full_name = full_name
            if email and not user.email:
                user.email = email
            user.is_active = True
            user.save()
        else:
            user = User.objects.create(
                phone=norm_phone,
                full_name=full_name or None,
                email=email or None,
                is_active=True,
            )
            user.set_unusable_password()
            user.save()

        display_name = user.full_name.strip() if (user.full_name and user.full_name.strip()) else (user.email or user.phone)
        return JsonResponse({
            'status': 'success',
            'id': user.id,
            'name': display_name,
            'email': user.email or '',
            'phone': user.phone or '',
        })

    def organizer_info_view(self, request, user_id):
        from django.http import JsonResponse
        from authentication.models import User
        user = User.objects.filter(id=user_id).first()
        if not user:
            return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)
        return JsonResponse({
            'status': 'success',
            'id': user.id,
            'name': user.full_name or user.phone,
            'email': user.email or '',
            'phone': user.phone or '',
        })

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'creator' and formfield:
            formfield.label_from_instance = lambda obj: obj.full_name.strip() if (obj.full_name and obj.full_name.strip()) else (obj.email or obj.phone or f"User {obj.id}")
        return formfield

    def save_model(self, request, obj, form, change):
        from django.utils import timezone
        import uuid
        is_new = not change
        if not obj.start_date:
            obj.start_date = timezone.now()
        if not obj.code:
            obj.code = uuid.uuid4().hex[:6].upper()
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

    def organization_name(self, obj):
        return obj.name or "-"
    organization_name.short_description = "Name of Organization"
    organization_name.admin_order_field = 'name'

    def organization_type(self, obj):
        return obj.type.name if obj and obj.type else "-"
    organization_type.short_description = "Type"
    organization_type.admin_order_field = 'type__name'

    def contact_person(self, obj):
        if obj.creator and obj.creator.full_name and obj.creator.full_name.strip():
            return obj.creator.full_name.strip()
        return "-"
    contact_person.short_description = "Organizer"
    contact_person.admin_order_field = 'creator__full_name'

    def organizer_email(self, obj):
        if not obj:
            return "-"
        email = obj.creator.email if obj.creator and obj.creator.email else ""
        send_button = ""
        if obj.id and email:
            send_url = reverse('admin:event_organization_send_email', args=[obj.id])
            clean_name = (obj.name or "").replace("'", "\\'").replace('"', '&quot;')
            onclick_action = (
                f"if(typeof openSendEmailInputBox==='function'){{ openSendEmailInputBox('{email}', '{send_url}', '{clean_name}'); }} "
                f"else {{ var m=prompt('Enter message to send to {email}:'); if(m && m.trim()){{ var f=document.createElement('form'); f.method='POST'; f.action='{send_url}'; var c=document.querySelector('[name=csrfmiddlewaretoken]'); if(c){{ var ci=document.createElement('input'); ci.type='hidden'; ci.name='csrfmiddlewaretoken'; ci.value=c.value; f.appendChild(ci); }} var mi=document.createElement('input'); mi.type='hidden'; mi.name='message'; mi.value=m.trim(); f.appendChild(mi); document.body.appendChild(f); f.submit(); }} }}"
            )
            send_button = (
                f'<button type="button" id="btn-send-organizer-email" data-url="{send_url}" class="button" style="'
                f'margin-left: 12px; background-color: #ba215a; color: #ffffff; border: none; '
                f'border-radius: 4px; padding: 5px 14px; font-size: 13px; font-weight: bold; '
                f'cursor: pointer; display: inline-flex; align-items: center; gap: 5px;" '
                f'onclick="{onclick_action}">'
                f'✉ Send Email</button>'
            )
        elif not email:
            return mark_safe('<div style="display:inline-flex; align-items:center;"><span id="organizer_email_text" style="color:#888;">(No email set)</span></div>')

        return mark_safe(
            f'<div style="display:inline-flex; align-items:center;">'
            f'<span id="organizer_email_text" style="font-weight: 500;">{email}</span>'
            f'{send_button}'
            f'</div>'
        )
    organizer_email.short_description = "Email"

    organizer_email.admin_order_field = 'creator__email'

    def organizer_phone(self, obj):
        phone = obj.creator.phone if obj and obj.creator and obj.creator.phone else ""
        if not phone:
            return mark_safe('<span id="organizer_phone_text" style="color:#888;">-</span>')
        return mark_safe(f'<span id="organizer_phone_text">{phone}</span>')
    organizer_phone.short_description = "Contact Number"
    organizer_phone.admin_order_field = 'creator__phone'