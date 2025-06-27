from django.contrib import admin
from .models import ItemCategory, ItemSubCategory


class ItemSubCategoryInline(admin.TabularInline):
    """Inline admin for subcategories in category admin."""
    model = ItemSubCategory
    extra = 1
    fields = ('name', 'abbreviation', 'description')


@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    """Admin interface for Item Category model."""
    list_display = ('name', 'abbreviation', 'subcategory_count', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'abbreviation', 'description')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ItemSubCategoryInline]
    
    def subcategory_count(self, obj):
        """Display count of subcategories."""
        return obj.subcategories.count()
    subcategory_count.short_description = 'Subcategories'
    
    fieldsets = (
        (None, {
            'fields': ('name', 'abbreviation', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ItemSubCategory)
class ItemSubCategoryAdmin(admin.ModelAdmin):
    """Admin interface for Item SubCategory model."""
    list_display = ('name', 'abbreviation', 'item_category', 'created_at', 'updated_at')
    list_filter = ('item_category', 'created_at', 'updated_at')
    search_fields = ('name', 'abbreviation', 'description', 'item_category__name')
    ordering = ('item_category__name', 'name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'abbreviation', 'item_category', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
