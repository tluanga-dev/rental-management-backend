from rest_framework.routers import DefaultRouter
from apps.base.base_viewset import BaseModelViewSet, create_standard_schema_view
from .models import LineItem, InventoryItemMaster, InventoryItemStockMovement
from .serializers import (
    LineItemSerializer, 
    InventoryItemMasterSerializer, 
    InventoryItemStockMovementSerializer
)


@create_standard_schema_view(
    "inventory_item_master",
    "Inventory item master management with search and filtering capabilities",
    ["Inventory Management"]
)
class InventoryItemMasterViewSet(BaseModelViewSet):
    """
    ViewSet for managing inventory item masters.
    
    Provides CRUD operations for inventory item masters including:
    - Listing all master items with pagination
    - Creating new master item definitions
    - Retrieving, updating, and deleting specific master items
    - Searching by name, SKU, and brand
    - Filtering by tracking type, category, and other fields
    """
    queryset = InventoryItemMaster.objects.select_related(
        'item_sub_category', 'unit_of_measurement', 'packaging'
    ).all()
    serializer_class = InventoryItemMasterSerializer
    search_fields = ['name', 'sku', 'brand', 'description']
    filterset_fields = ['tracking_type', 'is_consumable', 'item_sub_category', 'unit_of_measurement']
    ordering_fields = ['name', 'sku', 'created_at', 'quantity']
    ordering = ['name']


@create_standard_schema_view(
    "inventory_item",
    "Inventory item instance management with search and filtering capabilities",
    ["Inventory Management"]
)
class LineItemViewSet(BaseModelViewSet):
    """
    ViewSet for managing inventory item instances.
    
    Provides CRUD operations for inventory items including:
    - Listing all inventory items with pagination
    - Creating new inventory item instances
    - Retrieving, updating, and deleting specific inventory items
    - Searching by serial number and master item details
    - Filtering by status, warehouse, rentable/sellable flags
    """
    queryset = LineItem.objects.select_related(
        'inventory_item_master', 'warehouse'
    ).all()
    serializer_class = LineItemSerializer
    search_fields = ['serial_number', 'inventory_item_master__name', 'inventory_item_master__sku']
    filterset_fields = ['status', 'warehouse', 'rentable', 'sellable', 'inventory_item_master']
    ordering_fields = ['created_at', 'serial_number', 'rental_rate', 'status']
    ordering = ['-created_at']


@create_standard_schema_view(
    "inventory_stock_movement",
    "Inventory stock movement tracking with search and filtering capabilities",
    ["Inventory Management"]
)
class InventoryItemStockMovementViewSet(BaseModelViewSet):
    """
    ViewSet for managing inventory stock movements.
    
    Provides CRUD operations for stock movements including:
    - Listing all stock movements with pagination
    - Creating new movement records
    - Retrieving, updating, and deleting specific movements
    - Searching by transaction ID and movement details
    - Filtering by movement type, warehouses, and dates
    """
    queryset = InventoryItemStockMovement.objects.select_related(
        'inventory_item__inventory_item_master', 'warehouse_from', 'warehouse_to'
    ).all()
    serializer_class = InventoryItemStockMovementSerializer
    search_fields = ['inventory_transaction_id', 'notes', 'inventory_item__inventory_item_master__name']
    filterset_fields = ['movement_type', 'warehouse_from', 'warehouse_to', 'inventory_item']
    ordering_fields = ['created_at', 'movement_type', 'quantity']
    ordering = ['-created_at']


# Router registration
router = DefaultRouter()
router.register(r'inventory-masters', InventoryItemMasterViewSet, basename='inventory_item_master')
router.register(r'line-items', LineItemViewSet, basename='line_item')
router.register(r'inventory-movements', InventoryItemStockMovementViewSet, basename='inventory_stock_movement')