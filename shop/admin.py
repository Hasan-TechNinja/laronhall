from django.contrib import admin
from . models import Product, Cart, Order, Review, Report, FinanceSummary, DonationItem, Donation
from io import BytesIO
from datetime import datetime
import threading
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.db.models import Min, Q
from import_export import resources, fields
from import_export.admin import ExportActionModelAdmin
from import_export.formats import base_formats
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Register your models here.

class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'price', 'stock', 'is_active', 'image')
    list_filter = ('is_active', 'price', 'stock')
    list_editable = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('-created_at',)
    prepopulated_fields = {'slug': ('name',)}



# class CartAdmin(admin.ModelAdmin):
#     list_display = ('user', 'product', 'quantity', 'created_at')
#     list_filter = ('user', 'product', 'quantity')
#     search_fields = ('user', 'product', 'quantity')
#     ordering = ('-created_at',)
#     list_select_related = ('user', 'product')

#     def has_delete_permission(self, request, obj=None):
#         return False


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id','user', 'product', 'quantity', 'email','phone', 'name','address','city','state', 'country', 'tracking_number', 'carrier', 'shipment_status')
    list_filter = ('user', 'product', 'quantity', 'shipment_status', 'carrier')
    search_fields = ('user__phone', 'user__email', 'product__name', 'email', 'name', 'tracking_number')
    ordering = ('-created_at',)
    list_select_related = ('user', 'product', 'fundraiser')

    def lookup_allowed(self, lookup, value, request=None):
        if lookup in ('fundraiser__event__id__exact', 'fundraiser__event__id', 'fundraiser__id__exact', 'fundraiser__id'):
            return True
        return super().lookup_allowed(lookup, value, request)




class PDF(base_formats.Format):
    def get_title(self):
        return 'pdf'

    def get_extension(self):
        return 'pdf'

    def get_content_type(self):
        return 'application/pdf'

    def is_binary(self):
        return True

    def can_export(self):
        return True

    def export_data(self, dataset, **kwargs):
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=20,
            leftMargin=20,
            topMargin=25,
            bottomMargin=25
        )
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#1b4332'),
            alignment=0,
            spaceAfter=4
        )
        meta_style = ParagraphStyle(
            'ReportMeta',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#555555'),
            spaceAfter=12
        )

        elements.append(Paragraph("Treats Island - Export Report", title_style))
        date_str = datetime.now().strftime("%B %d, %Y - %I:%M %p")
        elements.append(Paragraph(f"Generated on: {date_str}", meta_style))

        headers = dataset.headers or []
        header_style = ParagraphStyle(
            'HeaderStyle',
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=colors.white,
            alignment=0
        )
        header_center_style = ParagraphStyle(
            'HeaderCenterStyle',
            parent=header_style,
            alignment=1
        )
        cell_style = ParagraphStyle(
            'CellStyle',
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#222222'),
            alignment=0
        )
        cell_center_style = ParagraphStyle(
            'CellCenterStyle',
            parent=cell_style,
            alignment=1
        )
        total_label_style = ParagraphStyle(
            'TotalLabelStyle',
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#1b4332'),
            alignment=2
        )
        total_val_style = ParagraphStyle(
            'TotalValStyle',
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#1b4332'),
            alignment=0
        )

        table_data = []
        if headers:
            header_cells = []
            for h in headers:
                style = header_center_style if str(h).strip() == '#' else header_style
                header_cells.append(Paragraph(str(h or ''), style))
            table_data.append(header_cells)

        due_org_total = 0.0
        due_treats_total = 0.0
        org_idx = headers.index('Due Organizer') if (headers and 'Due Organizer' in headers) else None
        treats_idx = headers.index('Due Treats') if (headers and 'Due Treats' in headers) else None

        for row in dataset:
            data_row = []
            for col_idx, cell in enumerate(row):
                cell_text = str(cell) if cell is not None else ''
                cell_text = cell_text.replace('\n', '<br/>')
                style = cell_center_style if (headers and col_idx < len(headers) and str(headers[col_idx]).strip() == '#') else cell_style
                data_row.append(Paragraph(cell_text, style))
            table_data.append(data_row)

            if org_idx is not None and org_idx < len(row):
                raw_org = str(row[org_idx] or '').replace('$', '').replace(',', '').strip()
                try:
                    due_org_total += float(raw_org)
                except (ValueError, TypeError):
                    pass
            if treats_idx is not None and treats_idx < len(row):
                raw_treats = str(row[treats_idx] or '').replace('$', '').replace(',', '').strip()
                try:
                    due_treats_total += float(raw_treats)
                except (ValueError, TypeError):
                    pass

        has_total_row = False
        if len(dataset) > 0 and headers and (org_idx is not None or treats_idx is not None):
            has_total_row = True
            total_row = []
            for col_idx, h in enumerate(headers):
                if col_idx == org_idx:
                    total_row.append(Paragraph(f"$ {due_org_total:.2f}", total_val_style))
                elif col_idx == treats_idx:
                    total_row.append(Paragraph(f"$ {due_treats_total:.2f}", total_val_style))
                elif org_idx is not None and col_idx == (org_idx - 1):
                    total_row.append(Paragraph("Total:", total_label_style))
                else:
                    total_row.append(Paragraph("", cell_style))
            table_data.append(total_row)

        col_widths = None
        if headers:
            col_map = {
                '#': 28,
                'Supporter name': 90,
                'Purchase date': 72,
                'Items purchased': 245,
                'Candy price': 55,
                'Due Organizer': 68,
                'Due Treats': 64,
                'Popup Name': 130,
            }
            if all(h in col_map for h in headers):
                col_widths = [col_map[h] for h in headers]
            elif '#' in headers and 'Items purchased' in headers:
                col_widths = [28 if h == '#' else (245 if h == 'Items purchased' else None) for h in headers]

        if table_data:
            t = Table(table_data, colWidths=col_widths, repeatRows=1)
            t_style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1b4332')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1b4332')),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            ]
            if headers and '#' in headers:
                num_idx = headers.index('#')
                t_style.append(('ALIGN', (num_idx, 0), (num_idx, -1), 'CENTER'))
            if has_total_row:
                t_style.extend([
                    ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#eef6f1')),
                    ('LINEABOVE', (0, -1), (-1, -1), 1.2, colors.HexColor('#1b4332')),
                    ('LINEBELOW', (0, -1), (-1, -1), 1.2, colors.HexColor('#1b4332')),
                    ('TOPPADDING', (0, -1), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, -1), (-1, -1), 6),
                ])
            t.setStyle(TableStyle(t_style))
            elements.append(t)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

if PDF not in base_formats.DEFAULT_FORMATS:
    base_formats.DEFAULT_FORMATS.append(PDF)

class ReportResource(resources.ModelResource):
    report_number = fields.Field(column_name='#')
    supporter_name = fields.Field(column_name='Supporter name')
    purchase_date = fields.Field(column_name='Purchase date')
    items_purchased = fields.Field(column_name='Items purchased')
    candy_price = fields.Field(column_name='Candy price')
    due_organizer = fields.Field(column_name='Due Organizer')
    due_treats = fields.Field(column_name='Due Treats')
    popup_name = fields.Field(column_name='Popup Name')

    class Meta:
        model = Report
        fields = (
            'report_number',
            'supporter_name',
            'purchase_date',
            'items_purchased',
            'candy_price',
            'due_organizer',
            'due_treats',
            'popup_name',
        )
        export_order = fields

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._counter = 0

    def before_export(self, queryset, *args, **kwargs):
        self._counter = 0
        return super().before_export(queryset, *args, **kwargs)

    def get_items(self, obj):
        if hasattr(obj, '_cached_items'):
            return obj._cached_items
        if obj.stripe_session_id:
            from shop.models import Order
            items = list(Order.objects.filter(stripe_session_id=obj.stripe_session_id).select_related('product', 'fundraiser', 'fundraiser__user', 'user'))
        else:
            items = [obj]
        obj._cached_items = items
        return items

    def dehydrate_report_number(self, obj):
        if not hasattr(self, '_counter'):
            self._counter = 0
        self._counter += 1
        return self._counter

    def dehydrate_supporter_name(self, obj):
        name = (obj.name or '').strip()
        if not name and obj.user:
            name = (obj.user.full_name or '').strip()
        if not name:
            name = (obj.email or '').strip()
        return name or "-"

    def dehydrate_purchase_date(self, obj):
        if not obj.created_at:
            return ""
        dt = timezone.localtime(obj.created_at) if timezone.is_aware(obj.created_at) else obj.created_at
        return f"{dt.month}/{dt.day}/{dt.strftime('%y')} {dt.hour}:{dt.strftime('%M')}"

    def dehydrate_items_purchased(self, obj):
        items = self.get_items(obj)
        lines = []
        for item in items:
            if item.product:
                lines.append(f"{item.product.name} x {item.quantity}")
        return "\n".join(lines)

    def dehydrate_candy_price(self, obj):
        items = self.get_items(obj)
        total = sum(float(item.product.price) * item.quantity for item in items if item.product)
        if float(total).is_integer():
            return f"{int(total)}"
        return f"{total:.2f}"

    def dehydrate_due_organizer(self, obj):
        items = self.get_items(obj)
        total = sum(float(item.product.price) * item.quantity for item in items if item.product)
        due_org = total * 0.5
        return f"$ {due_org:.2f}"

    def dehydrate_due_treats(self, obj):
        items = self.get_items(obj)
        total = sum(float(item.product.price) * item.quantity for item in items if item.product)
        due = total * 0.5
        return f"$ {due:.2f}"

    def dehydrate_popup_name(self, obj):
        if not obj.fundraiser:
            return "-"
        if obj.fundraiser.name and obj.fundraiser.name.strip():
            return obj.fundraiser.name.strip()
        if obj.fundraiser.user:
            u_name = obj.fundraiser.user.full_name.strip() if obj.fundraiser.user.full_name else ""
            if u_name:
                return f"{u_name}'s Store"
            if obj.fundraiser.user.email:
                return f"{obj.fundraiser.user.email}'s Store"
        return f"Store {obj.fundraiser.id}"


_report_state = threading.local()


class ReportAdmin(ExportActionModelAdmin, admin.ModelAdmin):
    resource_class = ReportResource
    export_formats = (base_formats.CSV, base_formats.XLSX, base_formats.TSV, base_formats.JSON, base_formats.HTML, PDF)
    formats = export_formats
    list_display = (
        'report_number',
        'supporter_name',
        'purchase_date',
        'items_purchased',
        'candy_price',
        'due_organizer',
        'due_treats',
        'popup_name',
    )
    list_display_links = ('report_number', 'supporter_name')
    list_filter = ('fundraiser__event', 'created_at', 'is_paid')
    search_fields = ('user__email', 'user__phone', 'email', 'name', 'fundraiser__name', 'fundraiser__event__name')
    list_select_related = ('user', 'product', 'fundraiser', 'fundraiser__event', 'fundraiser__user')
    ordering = ('-created_at',)

    def has_module_permission(self, request):
        return False

    def lookup_allowed(self, lookup, value, request=None):
        if lookup in ('fundraiser__event__id__exact', 'fundraiser__event__id', 'fundraiser__id__exact', 'fundraiser__id'):
            return True
        return super().lookup_allowed(lookup, value, request)

    def changelist_view(self, request, extra_context=None):
        try:
            page = int(request.GET.get('p', 0))
        except (ValueError, TypeError):
            page = 0
        _report_state.row_counter = page * self.list_per_page
        return super().changelist_view(request, extra_context=extra_context)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        session_rep_ids = (
            qs.filter(stripe_session_id__isnull=False)
            .exclude(stripe_session_id='')
            .order_by()
            .values('stripe_session_id')
            .annotate(rep_id=Min('id'))
            .values_list('rep_id', flat=True)
        )
        no_session_ids = (
            qs.filter(Q(stripe_session_id__isnull=True) | Q(stripe_session_id=''))
            .order_by()
            .values_list('id', flat=True)
        )
        all_rep_ids = list(session_rep_ids) + list(no_session_ids)
        return qs.filter(id__in=all_rep_ids)

    def get_items(self, obj):
        if hasattr(obj, '_cached_items'):
            return obj._cached_items
        if obj.stripe_session_id:
            from shop.models import Order
            items = list(Order.objects.filter(stripe_session_id=obj.stripe_session_id).select_related('product', 'fundraiser', 'fundraiser__user', 'user'))
        else:
            items = [obj]
        obj._cached_items = items
        return items

    def report_number(self, obj):
        counter = getattr(_report_state, 'row_counter', None)
        if counter is not None:
            _report_state.row_counter = counter + 1
            return counter + 1
        return obj.id
    report_number.short_description = "#"
    report_number.admin_order_field = 'id'

    def supporter_name(self, obj):
        name = (obj.name or '').strip()
        if not name and obj.user:
            name = (obj.user.full_name or '').strip()
        if not name:
            name = (obj.email or '').strip()
        return name or "-"
    supporter_name.short_description = "Supporter name"
    supporter_name.admin_order_field = 'name'

    def purchase_date(self, obj):
        if not obj.created_at:
            return ""
        dt = timezone.localtime(obj.created_at) if timezone.is_aware(obj.created_at) else obj.created_at
        return f"{dt.month}/{dt.day}/{dt.strftime('%y')} {dt.hour}:{dt.strftime('%M')}"
    purchase_date.short_description = "Purchase date"
    purchase_date.admin_order_field = 'created_at'

    def items_purchased(self, obj):
        items = self.get_items(obj)
        lines = []
        for item in items:
            if item.product:
                lines.append(f"{escape(item.product.name)} x {item.quantity}")
        return mark_safe("<br>".join(lines))
    items_purchased.short_description = "Items purchased"

    def candy_price(self, obj):
        items = self.get_items(obj)
        total = sum(float(item.product.price) * item.quantity for item in items if item.product)
        if float(total).is_integer():
            return f"{int(total)}"
        return f"{total:.2f}"
    candy_price.short_description = "Candy price"

    def due_organizer(self, obj):
        items = self.get_items(obj)
        total = sum(float(item.product.price) * item.quantity for item in items if item.product)
        due_org = total * 0.5
        return f"$ {due_org:.2f}"
    due_organizer.short_description = "Due Organizer"

    def due_treats(self, obj):
        items = self.get_items(obj)
        total = sum(float(item.product.price) * item.quantity for item in items if item.product)
        due = total * 0.5
        return f"$ {due:.2f}"
    due_treats.short_description = "Due Treats"

    def popup_name(self, obj):
        if not obj.fundraiser:
            return "-"
        if obj.fundraiser.name and obj.fundraiser.name.strip():
            return obj.fundraiser.name.strip()
        if obj.fundraiser.user:
            u_name = obj.fundraiser.user.full_name.strip() if obj.fundraiser.user.full_name else ""
            if u_name:
                return f"{u_name}'s Store"
            if obj.fundraiser.user.email:
                return f"{obj.fundraiser.user.email}'s Store"
        return f"Store {obj.fundraiser.id}"
    popup_name.short_description = "Popup Name"
    popup_name.admin_order_field = 'fundraiser__name'


admin.site.register(Product, ProductAdmin)
# admin.site.register(Cart, CartAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Report, ReportAdmin)
# admin.site.register(FinanceSummary, ReportAdmin)


class DonationItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'price', 'is_active', 'image', 'created_at')
    list_filter = ('is_active', 'created_at')
    list_editable = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('-created_at',)
    prepopulated_fields = {'slug': ('name',)}


class DonationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'donor_display',
        'donation_item',
        'amount',
        'organization_share',
        'treats_share',
        'fundraiser',
        'is_paid',
        'stripe_session_id',
        'created_at'
    )
    list_filter = ('is_paid', 'created_at', 'donation_item')
    search_fields = ('name', 'email', 'phone', 'stripe_session_id', 'user__phone', 'user__email', 'fundraiser__name')
    ordering = ('-created_at',)
    list_select_related = ('user', 'donation_item', 'fundraiser')
    readonly_fields = ('stripe_session_id', 'created_at', 'organization_share', 'treats_share')

    def organization_share(self, obj):
        if obj.fundraiser:
            return f"${obj.organization_amount:.2f} (25%)"
        return "$0.00 (No Org)"
    organization_share.short_description = "Org Share (25%)"

    def treats_share(self, obj):
        pct = "75%" if obj.fundraiser else "100%"
        return f"${obj.treats_island_amount:.2f} ({pct})"
    treats_share.short_description = "Treats Island (75%)"

    def donor_display(self, obj):
        donor = (obj.name or '').strip()
        if not donor and obj.user:
            donor = (obj.user.full_name or obj.user.phone or '').strip()
        if not donor:
            donor = (obj.email or '').strip()
        return donor or "Anonymous"
    donor_display.short_description = "Donor"
    donor_display.admin_order_field = 'name'


admin.site.register(DonationItem, DonationItemAdmin)
admin.site.register(Donation, DonationAdmin)


class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('name', 'comment')

# admin.site.register(Review, ReviewAdmin)