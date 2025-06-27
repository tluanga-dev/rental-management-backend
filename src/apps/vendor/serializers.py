from rest_framework import serializers
from .models import Vendor
from apps.core.apps.contact_number.serializers import ContactNumberSerializer


class VendorSerializer(serializers.ModelSerializer):
    """
    Serializer for Vendor model with contact number management.
    
    Handles vendor creation and updates including nested contact numbers.
    """
    contact_numbers = ContactNumberSerializer(
        many=True, 
        required=True,
        help_text="List of contact numbers for the vendor (at least one required)"
    )

    class Meta:
        model = Vendor
        fields = [
            "id",
            "name",
            "email",
            "address",
            "remarks",
            "city",
            "contact_numbers",
            "is_active",
            "updated_at",
            "created_at",
        ]
        extra_kwargs = {
            "name": {
                "required": True,
                "help_text": "Vendor company or individual name"
            },
            "email": {
                "allow_blank": True,
                "help_text": "Primary email address for vendor communications"
            },
            "address": {
                "help_text": "Physical address of the vendor"
            },
            "city": {
                "help_text": "City where vendor is located"
            },
            "remarks": {
                "help_text": "Additional notes or comments about the vendor"
            },
            "is_active": {
                "help_text": "Whether this vendor is currently active"
            },
            "created_at": {
                "read_only": True, 
                "format": "%Y-%m-%dT%H:%M:%S.%fZ",
                "help_text": "Timestamp when vendor was created"
            },
            "updated_at": {
                "help_text": "Timestamp when vendor was last updated"
            }
        }

    def validate(self, data):
        # Custom validation for contact numbers
        contact_numbers = data.get("contact_numbers", [])
        if not contact_numbers:
            raise serializers.ValidationError(
                {"contact_numbers": "At least one contact number is required."}
            )
        return data

    def create(self, validated_data):
        contact_numbers_data = validated_data.pop("contact_numbers")
        vendor = Vendor.objects.create(**validated_data)

        for number_data in contact_numbers_data:
            vendor.contact_numbers.create(**number_data)

        return vendor

    def update(self, instance, validated_data):
        contact_numbers_data = validated_data.pop("contact_numbers", [])

        # Update vendor fields
        instance = super().update(instance, validated_data)

        # Update contact numbers
        existing_numbers = {str(n.id): n for n in instance.contact_numbers.all()}
        kept_numbers = []

        for number_data in contact_numbers_data:
            number_id = str(number_data.get("id"))  # Ensure id is treated as a string
            if number_id and number_id in existing_numbers:
                number = existing_numbers[number_id]
                number.number = number_data["number"]
                number.save()
                kept_numbers.append(number_id)
            else:
                new_number = instance.contact_numbers.create(**number_data)
                kept_numbers.append(str(new_number.id))

        # Delete removed numbers
        for number_id in existing_numbers:
            if number_id not in kept_numbers:
                existing_numbers[number_id].delete()

        return instance
