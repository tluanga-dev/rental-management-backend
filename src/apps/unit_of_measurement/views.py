from django.shortcuts import render
from rest_framework.routers import DefaultRouter
from apps.base.base_viewset import BaseModelViewSet, create_standard_schema_view
from .models import UnitOfMeasurement
from .serializers import UnitOfMeasurementSerializer

# Create your views here.

@create_standard_schema_view(
    "unit of measurement",
    "Unit of measurement management with search and filtering capabilities",
    ["Units"]
)
class UnitOfMeasurementViewSet(BaseModelViewSet):
    """
    ViewSet for managing units of measurement.
    
    Provides CRUD operations for units of measurement including:
    - Listing all units with pagination
    - Creating new measurement units
    - Retrieving, updating, and deleting specific units
    - Searching by name, abbreviation, and description
    - Ordering by various fields
    
    Authentication is conditional based on ENABLE_AUTHENTICATION environment variable:
    - When ENABLE_AUTHENTICATION=True: Requires JWT authentication
    - When ENABLE_AUTHENTICATION=False: Allows anonymous access (development mode)
    """
    queryset = UnitOfMeasurement.objects.all()
    serializer_class = UnitOfMeasurementSerializer
    search_fields = ['name', 'abbreviation', 'description']
    ordering_fields = ['name', 'abbreviation', 'created_at', 'updated_at']
    ordering = ['name']

# Router registration (for urls.py)
router = DefaultRouter()
router.register(r'', UnitOfMeasurementViewSet, basename='unitofmeasurement')
