from django.shortcuts import render
from apps.base.base_viewset import BaseModelViewSet, create_standard_schema_view
from .models import ItemPackaging
from .serializers import ItemPackagingSerializer

@create_standard_schema_view(
    "item packaging",
    "Item packaging management with filtering capabilities",
    ["Item Packaging"]
)
class ItemPackagingViewSet(BaseModelViewSet):
    """
    ViewSet for managing item packaging types.
    
    Provides CRUD operations for item packaging including:
    - Listing all packaging types with pagination
    - Creating new packaging types
    - Retrieving, updating, and deleting specific packaging types
    - Filtering by name and label
    
    Authentication is conditionally applied based on ENABLE_AUTHENTICATION setting:
    - When enabled (production): Requires JWT authentication
    - When disabled (development): Allows anonymous access
    """
    queryset = ItemPackaging.objects.all().order_by("-created_at")
    serializer_class = ItemPackagingSerializer
    filterset_fields = ["name", "label"]

# Create your views here.
