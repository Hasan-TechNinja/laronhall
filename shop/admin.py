from django.contrib import admin
from . models import Product, Cart, Order, Review

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



class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'created_at')
    list_filter = ('user', 'product', 'quantity')
    search_fields = ('user', 'product', 'quantity')
    ordering = ('-created_at',)
    list_select_related = ('user', 'product')

    def has_delete_permission(self, request, obj=None):
        return False


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




admin.site.register(Product, ProductAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Order, OrderAdmin)

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('name', 'comment')

admin.site.register(Review, ReviewAdmin)