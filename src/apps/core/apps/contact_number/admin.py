from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from .models import ContactNumber


@admin.register(ContactNumber)
class ContactNumberAdmin(admin.ModelAdmin):
    """Admin interface for ContactNumber model."""
    list_display = ('number', 'get_content_object', 'content_type', 'created_date')
    list_filter = ('content_type',)
    search_fields = ('number', 'object_id')
    ordering = ('content_type', 'number')
    autocomplete_fields = []
    
    fieldsets = (
        (None, {
            'fields': ('number',)
        }),
        ('Associated Object', {
            'fields': ('content_type', 'object_id', 'content_object'),
            'description': 'This contact number is associated with the following object:'
        }),
    )
    
    readonly_fields = ('content_object',)

    def get_content_object(self, obj):
        """Display the associated object."""
        if obj.content_object:
            return str(obj.content_object)
        return "No associated object"
    get_content_object.short_description = 'Associated With'

    def created_date(self, obj):
        """Display creation date if the associated object has it."""
        if hasattr(obj.content_object, 'created_at'):
            return obj.content_object.created_at
        return "N/A"
    created_date.short_description = 'Created'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('content_type')
