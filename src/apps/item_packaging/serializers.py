from rest_framework import serializers
from .models import ItemPackaging

class ItemPackagingSerializer(serializers.ModelSerializer):
    """
    Serializer for ItemPackaging model.
    
    Handles item packaging data including name, label, unit, and remarks.
    """
    
    class Meta:
        model = ItemPackaging
        fields = [
            "id",
            "name",
            "label",
            "unit",
            "remarks",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = ("id", "created_at", "updated_at", "is_active")
        extra_kwargs = {
            "name": {
                "help_text": "Descriptive name of the packaging type"
            },
            "label": {
                "help_text": "Short label or code for the packaging (automatically converted to uppercase)"
            },
            "unit": {
                "help_text": "Unit of measurement for this packaging type"
            },
            "remarks": {
                "help_text": "Additional notes or comments about this packaging type"
            },
            "created_at": {
                "help_text": "Timestamp when packaging type was created"
            },
            "updated_at": {
                "help_text": "Timestamp when packaging type was last updated"
            },
            "is_active": {
                "help_text": "Whether this packaging type is currently active"
            }
        }
