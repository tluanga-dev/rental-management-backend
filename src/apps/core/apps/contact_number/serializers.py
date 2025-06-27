from .models import ContactNumber
from rest_framework import serializers


class ContactNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactNumber
        fields = ["id", "number"]
        extra_kwargs = {
            "id": {"read_only": False, "required": False}  # For update operations
        }
