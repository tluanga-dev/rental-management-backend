from django.shortcuts import render
from apps.base.base_viewset import BaseModelViewSet, create_standard_schema_view
from .models import ItemCategory, ItemSubCategory
from .serializers import ItemCategorySerializer, ItemSubCategorySerializer

# Create your views here.

@create_standard_schema_view(
    "item category",
    "Item category management with filtering by name and abbreviation",
    ["Item Categories"]
)
class ItemCategoryViewSet(BaseModelViewSet):
    """
    ViewSet for managing item categories.
    
    Provides CRUD operations for item categories including:
    - Listing all categories with pagination
    - Creating new categories
    - Retrieving, updating, and deleting specific categories
    - Filtering by name and abbreviation
    
    Authentication is conditionally applied based on ENABLE_AUTHENTICATION setting:
    - When enabled (production): Requires JWT authentication
    - When disabled (development): Allows anonymous access
    """
    queryset = ItemCategory.objects.all().order_by("name")
    serializer_class = ItemCategorySerializer
    filterset_fields = {
        "name": ["exact", "icontains"],
        "abbreviation": ["exact", "iexact"],
    }

@create_standard_schema_view(
    "item subcategory",
    "Item subcategory management with filtering by name, abbreviation, and parent category",
    ["Item Categories"]
)
class ItemSubCategoryViewSet(BaseModelViewSet):
    """
    ViewSet for managing item subcategories.
    
    Provides CRUD operations for item subcategories including:
    - Listing all subcategories with pagination
    - Creating new subcategories under parent categories
    - Retrieving, updating, and deleting specific subcategories
    - Filtering by name, abbreviation, and parent category
    
    Authentication is conditionally applied based on ENABLE_AUTHENTICATION setting:
    - When enabled (production): Requires JWT authentication
    - When disabled (development): Allows anonymous access
    """
    queryset = ItemSubCategory.objects.all().order_by("name")
    serializer_class = ItemSubCategorySerializer
    filterset_fields = {
        "name": ["exact", "icontains"],
        "abbreviation": ["exact", "iexact"],
        "item_category": ["exact"],
    }
