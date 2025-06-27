from rest_framework import serializers
from .models import LineItem, InventoryItemMaster, InventoryItemStockMovement


class InventoryItemMasterSerializer(serializers.ModelSerializer):
    """
    Serializer for InventoryItemMaster model
    """
    item_sub_category_name = serializers.CharField(source='item_sub_category.name', read_only=True)
    unit_of_measurement_name = serializers.CharField(source='unit_of_measurement.name', read_only=True)
    packaging_name = serializers.CharField(source='packaging.name', read_only=True)
    
    class Meta:
        model = InventoryItemMaster
        fields = [
            'id', 'name', 'sku', 'description', 'contents',
            'item_sub_category', 'item_sub_category_name',
            'unit_of_measurement', 'unit_of_measurement_name',
            'packaging', 'packaging_name',
            'tracking_type', 'is_consumable', 'brand',
            'manufacturer_part_number', 'product_id',
            'weight', 'length', 'width', 'height',
            'renting_period', 'quantity',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LineItemSerializer(serializers.ModelSerializer):
    """
    Serializer for LineItem model
    """
    inventory_item_master_name = serializers.CharField(source='inventory_item_master.name', read_only=True)
    inventory_item_master_sku = serializers.CharField(source='inventory_item_master.sku', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    
    class Meta:
        model = LineItem
        fields = [
            'id', 'inventory_item_master', 'inventory_item_master_name', 'inventory_item_master_sku',
            'warehouse', 'warehouse_name', 'status', 'serial_number', 'quantity',
            'rental_rate', 'replacement_cost', 'late_fee_rate',
            'sell_tax_rate', 'rent_tax_rate', 'rentable', 'sellable',
            'selling_price', 'warranty_period_type', 'warranty_period',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def validate(self, data):
        """
        Validate inventory item data
        """
        # Check if individual tracking items have serial numbers
        if (data.get('inventory_item_master') and 
            data['inventory_item_master'].tracking_type == 'INDIVIDUAL' and 
            not data.get('serial_number')):
            raise serializers.ValidationError(
                "Serial number is required for individually tracked items"
            )
        
        # Check if individual tracking items have quantity of 1
        if (data.get('inventory_item_master') and 
            data['inventory_item_master'].tracking_type == 'INDIVIDUAL' and 
            data.get('quantity', 1) != 1):
            raise serializers.ValidationError(
                "Quantity must be 1 for individually tracked items"
            )
        
        return data


class InventoryItemStockMovementSerializer(serializers.ModelSerializer):
    """
    Serializer for InventoryItemStockMovement model
    """
    inventory_item_name = serializers.CharField(source='inventory_item.inventory_item_master.name', read_only=True)
    warehouse_from_name = serializers.CharField(source='warehouse_from.name', read_only=True)
    warehouse_to_name = serializers.CharField(source='warehouse_to.name', read_only=True)
    
    class Meta:
        model = InventoryItemStockMovement
        fields = [
            'id', 'inventory_item', 'inventory_item_name',
            'movement_type', 'inventory_transaction_id', 'quantity',
            'quantity_on_hand_before', 'quantity_on_hand_after',
            'warehouse_from', 'warehouse_from_name',
            'warehouse_to', 'warehouse_to_name',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']