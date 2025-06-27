from rest_framework import serializers
from .models import Warehouse

class WarehouseSerializer(serializers.ModelSerializer):
    """
    Serializer for Warehouse model.
    
    Handles warehouse location data including name, label, and remarks.
    """
    
    class Meta:
        model = Warehouse
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
        extra_kwargs = {
            "name": {
                "help_text": "Descriptive name of the warehouse"
            },
            "label": {
                "help_text": "Short label or code for the warehouse"
            },
            "remarks": {
                "help_text": "Additional notes or comments about the warehouse"
            },
            "is_active": {
                "help_text": "Whether this warehouse is currently active"
            },
            "created_at": {
                "help_text": "Timestamp when warehouse was created"
            },
            "updated_at": {
                "help_text": "Timestamp when warehouse was last updated"
            }
        }
