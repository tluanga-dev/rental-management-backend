from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import Customer
from apps.core.apps.contact_number.models import ContactNumber


class ContactNumberInline(GenericTabularInline):
    """Inline admin for contact numbers in customer admin."""
    model = ContactNumber
    extra = 1
    fields = ('number',)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Admin interface for Customer model."""
    list_display = ('name', 'email', 'city', 'created_at', 'updated_at')
    list_filter = ('city', 'created_at', 'updated_at')
    search_fields = ('name', 'email', 'city')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ContactNumberInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'email')
        }),
        ('Location & Contact', {
            'fields': ('address', 'city')
        }),
        ('Additional Information', {
            'fields': ('remarks',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
