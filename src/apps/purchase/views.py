from rest_framework.routers import DefaultRouter
from rest_framework.response import Response
from rest_framework import status
from apps.base.base_viewset import BaseModelViewSet, create_standard_schema_view
from .models import PurchaseTransaction, PurchaseTransactionItem
from .serializers import (
    PurchaseTransactionSerializer, 
    PurchaseTransactionItemSerializer,
    CreatePurchaseTransactionSerializer,
    PurchaseTransactionDetailSerializer
)
from .services.purchase_transaction_service_v2 import PurchaseTransactionServiceV2


@create_standard_schema_view(
    "purchase_transaction",
    "Purchase transaction management with search and filtering capabilities",
    ["Purchase Management"]
)
class PurchaseTransactionViewSet(BaseModelViewSet):
    """
    ViewSet for managing purchase transactions.
    
    Provides CRUD operations for purchase transactions including:
    - Listing all transactions with pagination
    - Creating new purchase transactions
    - Retrieving, updating, and deleting specific transactions
    - Searching by transaction ID, reference number, and invoice number
    - Filtering by vendor, transaction date, and amounts
    """
    queryset = PurchaseTransaction.objects.select_related(
        'vendor'
    ).prefetch_related(
        'transaction_items__inventory_item__inventory_item_master',
        'transaction_items__inventory_item__warehouse'
    ).all()
    serializer_class = PurchaseTransactionSerializer
    search_fields = ['transaction_id', 'reference_number', 'invoice_number', 'vendor__name']
    filterset_fields = ['vendor', 'transaction_date']
    ordering_fields = ['transaction_date', 'created_at', 'grand_total']
    ordering = ['-transaction_date', '-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePurchaseTransactionSerializer
        elif self.action == 'retrieve':
            return PurchaseTransactionDetailSerializer
        return super().get_serializer_class()
    
    def create(self, request, *args, **kwargs):
        """
        Create a new purchase transaction with atomic operations.
        
        This endpoint creates a complete purchase transaction including:
        - Purchase transaction record with auto-generated ID
        - Purchase transaction items
        - Inventory items (if new)
        - Stock movement records
        
        All operations are performed atomically - if any step fails, all changes are rolled back.
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Use the enhanced service to create the purchase transaction
        service = PurchaseTransactionServiceV2()
        purchase_transaction, created_items = service.create_purchase_transaction(
            serializer.validated_data
        )
        
        # Return the created transaction with details
        detail_serializer = PurchaseTransactionDetailSerializer(
            purchase_transaction,
            context={'request': request}
        )
        
        return Response(
            detail_serializer.data,
            status=status.HTTP_201_CREATED
        )
    


@create_standard_schema_view(
    "purchase_transaction_item",
    "Purchase transaction item management with search and filtering capabilities",
    ["Purchase Management"]
)
class PurchaseTransactionItemViewSet(BaseModelViewSet):
    """
    ViewSet for managing purchase transaction items.
    
    Provides CRUD operations for transaction items including:
    - Listing all transaction items with pagination
    - Creating new transaction item records
    - Retrieving, updating, and deleting specific items
    - Searching by serial number and inventory item details
    - Filtering by transaction, inventory item, and warranty details
    """
    queryset = PurchaseTransactionItem.objects.select_related(
        'transaction__vendor',
        'inventory_item__inventory_item_master__item_sub_category',
        'inventory_item__inventory_item_master__unit_of_measurement',
        'inventory_item__warehouse'
    ).all()
    serializer_class = PurchaseTransactionItemSerializer
    search_fields = [
        'serial_number', 'reference_number', 'transaction__transaction_id',
        'inventory_item__inventory_item_master__name', 'inventory_item__inventory_item_master__sku'
    ]
    filterset_fields = ['transaction', 'inventory_item', 'warranty_period_type']
    ordering_fields = ['created_at', 'quantity', 'unit_price', 'total_price']
    ordering = ['-created_at']


# Router registration
router = DefaultRouter()
router.register(r'transactions', PurchaseTransactionViewSet, basename='purchase_transaction')
router.register(r'transaction-items', PurchaseTransactionItemViewSet, basename='purchase_transaction_item')
