from django.contrib import admin
from .models import OrganizationType, Event, Fundraiser

# Register your models here.

@admin.register(OrganizationType)
class OrganizationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at', 'updated_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('-created_at',)
    

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'creator', 'name', 'type', 'start_date', 'end_date', 'code', 'is_active')
    list_filter = ('is_active', 'type', 'start_date', 'end_date')
    search_fields = ('name', 'code', 'creator__email', 'creator__username')
    ordering = ('id',)


@admin.register(Fundraiser)
class FundraiserAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'event', 'goal', 'created_at', 'updated_at')
    list_filter = ('user', 'event', 'created_at', 'updated_at')
    search_fields = ('user__email', 'event__code')
    ordering = ('id',)