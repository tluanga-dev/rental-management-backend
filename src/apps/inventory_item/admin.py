from django.contrib import admin
from .models import InventoryItemMaster, InventoryItem, InventoryItemStockMovement


@admin.register(InventoryItemMaster)
class InventoryItemMasterAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'tracking_type', 'is_consumable', 'brand', 'created_at']
    list_filter = ['tracking_type', 'is_consumable', 'item_sub_category', 'created_at']
    search_fields = ['name', 'sku', 'brand', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'sku', 'description', 'contents')
        }),
        ('Categorization', {
            'fields': ('item_sub_category', 'unit_of_measurement', 'packaging', 'tracking_type', 'is_consumable')
        }),
        ('Product Details', {
            'fields': ('brand', 'manufacturer_part_number', 'product_id')
        }),
        ('Physical Properties', {
            'fields': ('weight', 'length', 'width', 'height')
        }),
        ('Inventory Management', {
            'fields': ('renting_period', 'quantity')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'status', 'warehouse', 'rentable', 'sellable', 'created_at']
    list_filter = ['status', 'warehouse', 'rentable', 'sellable', 'created_at']
    search_fields = ['serial_number', 'inventory_item_master__name', 'inventory_item_master__sku']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('inventory_item_master', 'warehouse', 'status', 'serial_number', 'quantity')
        }),
        ('Pricing', {
            'fields': ('rental_rate', 'replacement_cost', 'late_fee_rate', 'selling_price')
        }),
        ('Tax & Availability', {
            'fields': ('sell_tax_rate', 'rent_tax_rate', 'rentable', 'sellable')
        }),
        ('Warranty', {
            'fields': ('warranty_period_type', 'warranty_period')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(InventoryItemStockMovement)
class InventoryItemStockMovementAdmin(admin.ModelAdmin):
    list_display = ['inventory_item', 'movement_type', 'quantity', 'inventory_transaction_id', 'created_at']
    list_filter = ['movement_type', 'created_at']
    search_fields = ['inventory_transaction_id', 'inventory_item__inventory_item_master__name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Movement Details', {
            'fields': ('inventory_item', 'movement_type', 'inventory_transaction_id', 'quantity')
        }),
        ('Stock Tracking', {
            'fields': ('quantity_on_hand_before', 'quantity_on_hand_after')
        }),
        ('Warehouse Transfer', {
            'fields': ('warehouse_from', 'warehouse_to')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
