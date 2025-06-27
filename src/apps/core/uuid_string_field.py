import uuid
from rest_framework import serializers
class UUIDStringField(serializers.Field):
    """Converts UUID objects to strings"""
    def to_representation(self, value):
        return str(value)
    
    def to_internal_value(self, data):
        try:
            return uuid.UUID(data)
        except ValueError:
            raise serializers.ValidationError("Invalid UUID format")