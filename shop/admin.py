from django.contrib import admin
from . models import Product, Cart, Order

# Register your models here.

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'price', 'stock', 'image')
    list_filter = ('price', 'stock')
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

    def has_delete_permission(self, request, obj=None):
        return False


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id','user', 'product', 'quantity', 'email','phone', 'name','address','city','state', 'country')
    list_filter = ('user', 'product', 'quantity')
    search_fields = ('user', 'product', 'quantity')
    ordering = ('-created_at',)

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Product, ProductAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Order, OrderAdmin)