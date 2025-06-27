from django.contrib import admin
from .models import PurchaseTransaction, PurchaseTransactionItem


class PurchaseTransactionItemInline(admin.TabularInline):
    model = PurchaseTransactionItem
    extra = 1
    fields = ['inventory_item', 'serial_number', 'quantity', 'unit_price', 'discount', 'tax_amount', 'total_price']


@admin.register(PurchaseTransaction)
class PurchaseTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'transaction_date', 'vendor', 'grand_total', 'created_at']
    list_filter = ['transaction_date', 'vendor', 'created_at']
    search_fields = ['transaction_id', 'reference_number', 'invoice_number', 'vendor__name']
    ordering = ['-transaction_date', '-created_at']
    readonly_fields = ['transaction_id', 'created_at', 'updated_at']
    inlines = [PurchaseTransactionItemInline]
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('transaction_date', 'transaction_id', 'vendor', 'reference_number', 'invoice_number')
        }),
        ('Financial Information', {
            'fields': ('total_amount', 'total_tax_amount', 'total_discount', 'grand_total')
        }),
        ('Additional Information', {
            'fields': ('remarks',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PurchaseTransactionItem)
class PurchaseTransactionItemAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'inventory_item', 'serial_number', 'quantity', 'unit_price', 'total_price']
    list_filter = ['transaction__transaction_date', 'warranty_period_type', 'created_at']
    search_fields = [
        'serial_number', 'reference_number', 'transaction__transaction_id',
        'inventory_item__inventory_item_master__name'
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('transaction', 'inventory_item', 'serial_number', 'reference_number')
        }),
        ('Quantity & Pricing', {
            'fields': ('quantity', 'unit_price', 'discount', 'tax_amount', 'amount', 'total_price')
        }),
        ('Warranty Information', {
            'fields': ('warranty_period_type', 'warranty_period')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
