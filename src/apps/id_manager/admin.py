from django.contrib import admin
from django.utils.html import format_html
from .models import IdManager


@admin.register(IdManager)
class IdManagerAdmin(admin.ModelAdmin):
    """Admin interface for IdManager model."""
    list_display = ('prefix', 'latest_id', 'get_sequence_info', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('prefix', 'latest_id')
    ordering = ('prefix',)
    readonly_fields = ('created_at', 'updated_at', 'get_sequence_info', 'get_format_info')
    
    fieldsets = (
        (None, {
            'fields': ('prefix', 'latest_id')
        }),
        ('Sequence Information', {
            'fields': ('get_sequence_info', 'get_format_info'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_sequence_info(self, obj):
        """Display information about the current sequence."""
        if not obj.latest_id:
            return "No ID generated yet"
        
        try:
            prefix_part, sequence_part = obj.latest_id.split("-", 1)
            import re
            match = re.match(r"^([A-Za-z]*)(\d+)$", sequence_part)
            if match:
                letters = match.group(1)
                numbers = match.group(2)
                return format_html(
                    "<strong>Letters:</strong> {} <br><strong>Numbers:</strong> {} <br><strong>Next will be:</strong> {}",
                    letters,
                    numbers,
                    self._get_next_id_preview(obj)
                )
        except:
            pass
        return "Invalid format"
    get_sequence_info.short_description = 'Sequence Details'

    def get_format_info(self, obj):
        """Display format information."""
        return format_html(
            "<strong>Format:</strong> PREFIX-LETTERS+NUMBERS<br>"
            "<strong>Example:</strong> PO-AAA0001<br>"
            "<strong>Range:</strong> AAA0001 to ZZZ9999, then AAAA0001..."
        )
    get_format_info.short_description = 'Format Information'

    def _get_next_id_preview(self, obj):
        """Get a preview of what the next ID would be."""
        try:
            next_id = IdManager._increment_id(obj.latest_id, obj.prefix)
            return next_id
        except:
            return f"{obj.prefix}-AAA0001 (reset)"

    def has_add_permission(self, request):
        """Allow adding new ID managers."""
        return True

    def has_delete_permission(self, request, obj=None):
        """Allow deletion but warn about consequences."""
        return True

    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request)

    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
