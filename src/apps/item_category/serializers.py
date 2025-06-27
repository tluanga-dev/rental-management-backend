from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from apps.base.time_stamped_abstract_serializer import TimeStampedModelSerializer
from .models import ItemCategory, ItemSubCategory

class ItemCategorySerializer(TimeStampedModelSerializer):
    """
    Serializer for ItemCategory model.
    
    Provides serialization for item categories including timestamps,
    name, abbreviation, and description fields.
    """
    
    name = serializers.CharField(
        max_length=100,
        help_text="Name of the item category (e.g., 'Electronics', 'Furniture')"
    )
    abbreviation = serializers.CharField(
        max_length=10,
        help_text="Short abbreviation for the category (e.g., 'ELEC', 'FURN')"
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional detailed description of the category"
    )
    
    class Meta(TimeStampedModelSerializer.Meta):
        model = ItemCategory
        fields = TimeStampedModelSerializer.Meta.fields + [
            "name", "abbreviation", "description"
        ]

class ItemSubCategorySerializer(TimeStampedModelSerializer):
    """
    Serializer for ItemSubCategory model.
    
    Provides serialization for item subcategories including timestamps,
    name, abbreviation, description, and parent category relationship.
    """
    
    item_category = serializers.PrimaryKeyRelatedField(
        queryset=ItemCategory.objects.all(),
        help_text="ID of the parent item category"
    )
    item_category_name = serializers.CharField(
        source='item_category.name', 
        read_only=True,
        help_text="Name of the parent item category (read-only)"
    )
    name = serializers.CharField(
        max_length=100,
        help_text="Name of the item subcategory (e.g., 'Laptops', 'Chairs')"
    )
    abbreviation = serializers.CharField(
        max_length=10,
        help_text="Short abbreviation for the subcategory (e.g., 'LAP', 'CHR')"
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional detailed description of the subcategory"
    )

    class Meta(TimeStampedModelSerializer.Meta):
        model = ItemSubCategory
        fields = TimeStampedModelSerializer.Meta.fields + [
            "name", "abbreviation", "description", "item_category", "item_category_name"
        ]
