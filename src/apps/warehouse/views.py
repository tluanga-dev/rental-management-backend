from django.shortcuts import render
from rest_framework.routers import DefaultRouter
from apps.base.base_viewset import BaseModelViewSet, create_standard_schema_view
from .models import Warehouse
from .serializers import WarehouseSerializer

@create_standard_schema_view(
    "warehouse",
    "Warehouse management with search and filtering capabilities",
    ["Warehouses"]
)
class WarehouseViewSet(BaseModelViewSet):
    """
    ViewSet for managing warehouse locations.
    
    Provides CRUD operations for warehouses including:
    - Listing all warehouses with pagination
    - Creating new warehouse locations
    - Retrieving, updating, and deleting specific warehouses
    - Searching by name and label
    - Ordering by various fields
    
    Authentication is conditional based on ENABLE_AUTHENTICATION environment variable:
    - When ENABLE_AUTHENTICATION=True: Requires JWT authentication
    - When ENABLE_AUTHENTICATION=False: Allows anonymous access (development mode)
    """
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    search_fields = ['name', 'label']
    ordering_fields = ['name', 'label']
    ordering = ['name']

# Router registration (for urls.py)
router = DefaultRouter()
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')

# Create your views here.
