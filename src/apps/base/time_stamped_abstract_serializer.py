import uuid

from rest_framework import serializers


class TimeStampedModelSerializer(serializers.ModelSerializer):
    """
    Base serializer for models inheriting from TimeStampedAbstractModelClass
    """

    id = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    is_active = serializers.BooleanField(required=False, default=True)

    class Meta:
        abstract = True
        fields = ["id", "created_at", "updated_at", "is_active"]
        read_only_fields = ["id", "created_at", "updated_at"]


# Usage example

# class ConcreteModel(TimeStampedAbstractModelClass):
#     name = models.CharField(max_length=255)
#     description = models.TextField()

# class ConcreteModelSerializer(TimeStampedModelSerializer):
#     class Meta(TimeStampedModelSerializer.Meta):
#         model = ConcreteModel
#         fields = TimeStampedModelSerializer.Meta.fields + ['name', 'description']
