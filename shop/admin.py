from django.contrib import admin
from . models import Product, Cart, Order, Review, Report, FinanceSummary

# Register your models here.

class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'price', 'stock', 'is_active', 'image')
    list_filter = ('is_active', 'price', 'stock')
    list_editable = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('-created_at',)
    prepopulated_fields = {'slug': ('name',)}
    
    def has_delete_permission(self, request, obj=None):
        return False



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

    def has_delete_permission(self, request, obj=None):
        return False

    def lookup_allowed(self, lookup, value, request=None):
        if lookup in ('fundraiser__event__id__exact', 'fundraiser__event__id'):
            return True
        return super().lookup_allowed(lookup, value, request)




from import_export import resources, fields
from import_export.admin import ExportActionModelAdmin

class ReportResource(resources.ModelResource):
    order_number = fields.Field(attribute='id', column_name='Order Number')
    supporter = fields.Field(column_name='Supporter')
    purchase_date = fields.Field(column_name='Purchase Date')
    popup_store = fields.Field(column_name='Popup Store')
    order_total = fields.Field(column_name='Order Total')
    items_qty = fields.Field(column_name='Items / Qty')
    item_price = fields.Field(column_name='Item Price')
    org_share = fields.Field(column_name='Org Share')
    treats_share = fields.Field(column_name='Treats Share')
    status = fields.Field(column_name='Status')

    class Meta:
        model = Report
        fields = ('order_number', 'supporter', 'purchase_date', 'popup_store', 'order_total', 'items_qty', 'item_price', 'org_share', 'treats_share', 'status')
        export_order = fields

    def dehydrate_supporter(self, obj):
        name = obj.name or (getattr(obj.user, 'full_name', '') if obj.user else '')
        email = obj.email or (getattr(obj.user, 'email', '') if obj.user else '')
        return f"{name} ({email})"

    def dehydrate_purchase_date(self, obj):
        return obj.created_at.strftime("%b %d, %Y") if obj.created_at else ""

    def dehydrate_popup_store(self, obj):
        return obj.fundraiser.name if obj.fundraiser else (f"{obj.fundraiser.user.email}'s Store" if obj.fundraiser and obj.fundraiser.user else "-")

    def dehydrate_order_total(self, obj):
        try:
            return float(obj.product.price) * obj.quantity + float(obj.delivery_charge)
        except Exception:
            return 0.00

    def dehydrate_items_qty(self, obj):
        return f"{obj.product.name} x{obj.quantity}" if obj.product else ""

    def dehydrate_item_price(self, obj):
        return obj.product.price if obj.product else 0.00

    def dehydrate_org_share(self, obj):
        return self.dehydrate_order_total(obj) * 0.5

    def dehydrate_treats_share(self, obj):
        return self.dehydrate_order_total(obj) * 0.5

    def dehydrate_status(self, obj):
        paid = "Paid" if obj.is_paid else "Unpaid"
        status = obj.shipment_status.title() if obj.shipment_status else "Unshipped"
        return f"{paid} / {status}"

class ReportAdmin(ExportActionModelAdmin, admin.ModelAdmin):
    resource_class = ReportResource
    list_display = ('id', 'supporter_display', 'purchase_date_display', 'popup_store_display', 'order_total_display', 'items_qty_display', 'item_price_display', 'org_share_display', 'treats_share_display', 'status_display')
    list_filter = ('fundraiser__event','created_at', 'is_paid', 'shipment_status')
    search_fields = ('user__email', 'user__phone', 'email', 'name', 'fundraiser__name', 'fundraiser__event__name')
    list_select_related = ('user', 'product', 'fundraiser', 'fundraiser__event')
    ordering = ('-created_at',)

    def has_delete_permission(self, request, obj=None):
        return False

    def lookup_allowed(self, lookup, value, request=None):
        if lookup in ('fundraiser__id__exact', 'fundraiser__id'):
            return True
        return super().lookup_allowed(lookup, value, request)

    def supporter_display(self, obj):
        name = obj.name or (getattr(obj.user, 'full_name', '') if obj.user else '')
        email = obj.email or (getattr(obj.user, 'email', '') if obj.user else '')
        return f"{name} ({email})"
    supporter_display.short_description = "Supporter"

    def purchase_date_display(self, obj):
        return obj.created_at.strftime("%b %d, %Y") if obj.created_at else ""
    purchase_date_display.short_description = "Purchase Date"
    purchase_date_display.admin_order_field = 'created_at'

    def popup_store_display(self, obj):
        return obj.fundraiser.name if obj.fundraiser and obj.fundraiser.name else (f"{obj.fundraiser.user.email}'s Store" if obj.fundraiser and obj.fundraiser.user else "-")
    popup_store_display.short_description = "Popup Store"

    def get_order_total(self, obj):
        try:
            return float(obj.product.price) * obj.quantity + float(obj.delivery_charge)
        except Exception:
            return 0.00

    def order_total_display(self, obj):
        return f"${self.get_order_total(obj):.2f}"
    order_total_display.short_description = "Order Total"

    def items_qty_display(self, obj):
        return f"{obj.product.name} x{obj.quantity}" if obj.product else ""
    items_qty_display.short_description = "Items / Qty"

    def item_price_display(self, obj):
        return f"${float(obj.product.price):.2f}" if obj.product else "$0.00"
    item_price_display.short_description = "Item Price"

    def org_share_display(self, obj):
        return f"${self.get_order_total(obj) * 0.5:.2f}"
    org_share_display.short_description = "Org Share"

    def treats_share_display(self, obj):
        return f"${self.get_order_total(obj) * 0.5:.2f}"
    treats_share_display.short_description = "Treats Share"

    def status_display(self, obj):
        paid = "Paid" if obj.is_paid else "Unpaid"
        status = obj.shipment_status.title() if obj.shipment_status else "Unshipped"
        return f"{paid} / {status}"
    status_display.short_description = "Status"


admin.site.register(Product, ProductAdmin)
# admin.site.register(Cart, CartAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(FinanceSummary, ReportAdmin)

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('name', 'comment')

# admin.site.register(Review, ReviewAdmin)