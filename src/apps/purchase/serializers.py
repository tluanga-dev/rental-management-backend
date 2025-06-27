from rest_framework import serializers
from .models import PurchaseTransaction, PurchaseTransactionItem, WarrantyPeriodTypeChoices


class PurchaseTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for PurchaseTransaction model
    """
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    
    class Meta:
        model = PurchaseTransaction
        fields = [
            'id', 'transaction_date', 'transaction_id', 'vendor', 'vendor_name',
            'reference_number', 'invoice_number', 'total_amount', 'total_tax_amount',
            'total_discount', 'grand_total', 'remarks', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'transaction_id', 'created_at', 'updated_at']


class PurchaseTransactionItemSerializer(serializers.ModelSerializer):
    """
    Serializer for PurchaseTransactionItem model
    """
    transaction_id = serializers.CharField(source='transaction.transaction_id', read_only=True)
    inventory_item_name = serializers.CharField(source='inventory_item.inventory_item_master.name', read_only=True)
    inventory_item_sku = serializers.CharField(source='inventory_item.inventory_item_master.sku', read_only=True)
    
    class Meta:
        model = PurchaseTransactionItem
        fields = [
            'id', 'transaction', 'transaction_id', 'inventory_item', 
            'inventory_item_name', 'inventory_item_sku', 'serial_number',
            'quantity', 'unit_price', 'discount', 'tax_amount', 'amount',
            'total_price', 'reference_number', 'warranty_period_type',
            'warranty_period', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PurchaseItemInputSerializer(serializers.Serializer):
    """
    Serializer for individual purchase item input
    """
    item_master_id = serializers.UUIDField(required=True)
    warehouse_id = serializers.UUIDField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    tax_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    serial_number = serializers.CharField(max_length=255, required=False, allow_blank=True)
    reference_number = serializers.CharField(max_length=255, required=False, allow_blank=True)
    warranty_period_type = serializers.ChoiceField(
        choices=WarrantyPeriodTypeChoices.choices,
        required=False,
        allow_blank=True
    )
    warranty_period = serializers.IntegerField(required=False, min_value=1)
    
    # Inventory item fields
    rental_rate = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    replacement_cost = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    late_fee_rate = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    sell_tax_rate = serializers.IntegerField(required=False, default=0)
    rent_tax_rate = serializers.IntegerField(required=False, default=0)
    rentable = serializers.BooleanField(required=False, default=True)
    sellable = serializers.BooleanField(required=False, default=False)
    selling_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    
    def validate(self, data):
        if data.get('warranty_period') and not data.get('warranty_period_type'):
            raise serializers.ValidationError(
                "warranty_period_type is required when warranty_period is provided"
            )
        return data


class CreatePurchaseTransactionSerializer(serializers.Serializer):
    """
    Serializer for creating a complete purchase transaction with items
    """
    transaction_date = serializers.DateField(required=True)
    vendor = serializers.UUIDField(required=False, allow_null=True)
    reference_number = serializers.CharField(max_length=255, required=False, allow_blank=True)
    invoice_number = serializers.CharField(max_length=255, required=False, allow_blank=True)
    remarks = serializers.CharField(required=False, allow_blank=True)
    items = PurchaseItemInputSerializer(many=True, required=True)
    
    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("At least one item is required")
        return items
    
    def validate(self, data):
        # Check for forbidden fields
        forbidden_fields = ['transaction_id', 'id']
        request_data = self.context.get('request').data if self.context.get('request') else {}
        
        found_forbidden = [field for field in forbidden_fields if field in request_data]
        if found_forbidden:
            raise serializers.ValidationError(
                f"Request contains forbidden fields: {', '.join(found_forbidden)}. "
                "Transaction IDs are generated automatically by the system."
            )
        
        return data


class PurchaseTransactionDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for PurchaseTransaction with nested items
    """
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    transaction_items = PurchaseTransactionItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = PurchaseTransaction
        fields = [
            'id', 'transaction_date', 'transaction_id', 'vendor', 'vendor_name',
            'reference_number', 'invoice_number', 'total_amount', 'total_tax_amount',
            'total_discount', 'grand_total', 'remarks', 'created_at', 'updated_at',
            'transaction_items'
        ]
        read_only_fields = ['id', 'transaction_id', 'created_at', 'updated_at']