from rest_framework import serializers
from .models import UnitOfMeasurement

class UnitOfMeasurementSerializer(serializers.ModelSerializer):
    """
    Serializer for UnitOfMeasurement model.
    
    Handles unit of measurement data including name, abbreviation, and description.
    """
    
    class Meta:
        model = UnitOfMeasurement
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
        extra_kwargs = {
            "name": {
                "help_text": "Full name of the unit of measurement (e.g., 'Kilogram', 'Meter')"
            },
            "abbreviation": {
                "help_text": "Short abbreviation for the unit (e.g., 'kg', 'm')"
            },
            "description": {
                "help_text": "Detailed description of the unit of measurement"
            },
            "is_active": {
                "help_text": "Whether this unit of measurement is currently active"
            },
            "created_at": {
                "help_text": "Timestamp when unit was created"
            },
            "updated_at": {
                "help_text": "Timestamp when unit was last updated"
            }
        }
