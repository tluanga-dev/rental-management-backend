from apps.core.apps.contact_number.serializers import ContactNumberSerializer
from apps.core.apps.contact_number.models import ContactNumber
from rest_framework import serializers
from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    contact_numbers = ContactNumberSerializer(many=True, required=False)

    class Meta:
        model = Customer
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
        extra_kwargs = {"created_at": {"format": "%Y-%m-%dT%H:%M:%S.%fZ"}}

    def create(self, validated_data):
        contact_numbers_data = validated_data.pop("contact_numbers", [])
        try:
            customer = Customer.objects.create(**validated_data)

            # Create contact numbers with generic relation
            for number_data in contact_numbers_data:
                ContactNumber.objects.create(
                    content_object=customer, number=number_data["number"]
                )
            # Explicitly load the contact numbers to ensure they're included in the response
            customer.refresh_from_db()
            customer = Customer.objects.prefetch_related("contact_numbers").get(
                pk=customer.pk
            )
            return customer
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})

    def update(self, instance, validated_data):
        contact_numbers_data = validated_data.pop("contact_numbers", [])

        # Update Customer fields
        instance = super().update(instance, validated_data)

        # Get existing contact numbers
        existing_numbers = {str(n.id): n for n in instance.contact_numbers.all()}

        # Update or create contact numbers
        kept_numbers = []
        for number_data in contact_numbers_data:
            number_id = number_data.get("id", None)

            if number_id and str(number_id) in existing_numbers:
                # Update existing number
                number = existing_numbers[str(number_id)]
                number.number = number_data["number"]
                number.save()
                kept_numbers.append(str(number_id))
            else:
                # Create new number
                new_number = ContactNumber.objects.create(
                    content_object=instance, number=number_data["number"]
                )
                kept_numbers.append(str(new_number.id))

        # Delete numbers not included in the update
        for number_id, number in existing_numbers.items():
            if number_id not in kept_numbers:
                number.delete()

        return instance
