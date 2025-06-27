from decimal import Decimal
from typing import Dict, List, Any, Tuple
from django.db import transaction, models
from rest_framework.exceptions import ValidationError as DRFValidationError
import logging

from apps.purchase.models import PurchaseTransaction, PurchaseTransactionItem
from apps.inventory_item.models import (
    LineItem, 
    InventoryItemMaster, 
    InventoryItemStockMovement,
    MovementType
)
from apps.id_manager.models import IdManager
from apps.warehouse.models import Warehouse
from apps.vendor.models import Vendor

logger = logging.getLogger(__name__)


class PurchaseTransactionService:
    """
    Service class for handling purchase transactions with atomic operations.
    
    This service ensures data integrity by using database transactions to create
    all related records atomically. If any operation fails, all changes are rolled back.
    """
    
    PURCHASE_TRANSACTION_PREFIX = 'PUR'
    
    def __init__(self):
        self.errors = []
        
    def create_purchase_transaction(self, data: Dict[str, Any]) -> Tuple[PurchaseTransaction, List[Dict[str, Any]]]:
        """
        Create a purchase transaction with all related records in an atomic transaction.
        
        Args:
            data: Dictionary containing purchase transaction data and items
            
        Returns:
            Tuple of (created PurchaseTransaction, list of created items with details)
            
        Raises:
            DRFValidationError: If validation fails or transaction cannot be completed
        """
        try:
            with transaction.atomic():
                # Validate input data
                self._validate_input_data(data)
                
                # Extract transaction data and items
                transaction_data = self._extract_transaction_data(data)
                items_data = data.get('items', [])
                
                if not items_data:
                    raise DRFValidationError({"items": "At least one item is required"})
                
                # Generate transaction ID
                transaction_id = self._generate_transaction_id()
                transaction_data['transaction_id'] = transaction_id
                
                # Create purchase transaction
                purchase_transaction = self._create_purchase_transaction(transaction_data)
                
                # Process each item - prepare for bulk operations
                created_items = []
                line_items_to_create = []
                stock_movements_to_create = []
                
                for item_data in items_data:
                    created_item_info = self._process_purchase_item(
                        purchase_transaction, 
                        item_data
                    )
                    created_items.append(created_item_info)
                
                # Update transaction totals
                self._update_transaction_totals(purchase_transaction, created_items)
                
                logger.info(f"Successfully created purchase transaction {transaction_id}")
                return purchase_transaction, created_items
                
        except DRFValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating purchase transaction: {str(e)}")
            raise DRFValidationError({"error": f"Failed to create purchase transaction: {str(e)}"})
    
    def _validate_input_data(self, data: Dict[str, Any]) -> None:
        """
        Validate that input data doesn't contain forbidden fields like transaction_id.
        """
        forbidden_fields = ['transaction_id', 'id']
        found_forbidden = [field for field in forbidden_fields if field in data]
        
        if found_forbidden:
            raise DRFValidationError({
                "error": f"Request contains forbidden fields: {', '.join(found_forbidden)}. "
                        "Transaction IDs are generated automatically by the system."
            })
        
        # Validate required fields
        required_fields = ['transaction_date']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            raise DRFValidationError({
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            })
    
    def _extract_transaction_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and validate transaction-level data.
        """
        transaction_fields = [
            'transaction_date', 'vendor', 'reference_number', 'invoice_number',
            'total_amount', 'total_tax_amount', 'total_discount', 'grand_total', 'remarks'
        ]
        
        transaction_data = {
            field: data.get(field) 
            for field in transaction_fields 
            if field in data
        }
        
        # Validate vendor if provided
        if 'vendor' in transaction_data and transaction_data['vendor']:
            try:
                vendor = Vendor.objects.get(id=transaction_data['vendor'])
                transaction_data['vendor'] = vendor
            except Vendor.DoesNotExist:
                raise DRFValidationError({"vendor": "Invalid vendor ID"})
        
        return transaction_data
    
    def _generate_transaction_id(self) -> str:
        """
        Generate a unique transaction ID using the ID Manager service.
        """
        try:
            return IdManager.generate_id(self.PURCHASE_TRANSACTION_PREFIX)
        except Exception as e:
            logger.error(f"Failed to generate transaction ID: {str(e)}")
            raise DRFValidationError({"error": "Failed to generate transaction ID"})
    
    def _create_purchase_transaction(self, transaction_data: Dict[str, Any]) -> PurchaseTransaction:
        """
        Create the purchase transaction record.
        """
        try:
            purchase_transaction = PurchaseTransaction.objects.create(**transaction_data)
            return purchase_transaction
        except Exception as e:
            logger.error(f"Failed to create purchase transaction: {str(e)}")
            raise DRFValidationError({"error": f"Failed to create purchase transaction: {str(e)}"})
    
    def _process_purchase_item(
        self, 
        purchase_transaction: PurchaseTransaction, 
        item_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a single purchase item, creating all necessary records.
        """
        # Validate item data
        self._validate_item_data(item_data)
        
        # Get the item master
        item_master = self._get_item_master(item_data['item_master_id'])
        
        # Get or create inventory item
        inventory_item = self._get_or_create_inventory_item(
            item_master,
            item_data,
            purchase_transaction.transaction_id
        )
        
        # Create purchase transaction item
        transaction_item = self._create_transaction_item(
            purchase_transaction,
            inventory_item,
            item_data
        )
        
        # Create stock movement record
        stock_movement = self._create_stock_movement(
            inventory_item,
            transaction_item.quantity,
            purchase_transaction.transaction_id
        )
        
        return {
            'transaction_item': transaction_item,
            'inventory_item': inventory_item,
            'stock_movement': stock_movement,
            'item_master': item_master
        }
    
    def _validate_item_data(self, item_data: Dict[str, Any]) -> None:
        """
        Validate individual item data.
        """
        required_fields = ['item_master_id', 'quantity', 'warehouse_id']
        missing_fields = [field for field in required_fields if field not in item_data]
        
        if missing_fields:
            raise DRFValidationError({
                "items": f"Item missing required fields: {', '.join(missing_fields)}"
            })
        
        if item_data['quantity'] <= 0:
            raise DRFValidationError({"items": "Quantity must be greater than 0"})
    
    def _get_item_master(self, item_master_id: Any) -> InventoryItemMaster:
        """
        Retrieve the item master record.
        """
        try:
            return InventoryItemMaster.objects.get(id=item_master_id)
        except InventoryItemMaster.DoesNotExist:
            raise DRFValidationError({"items": f"Invalid item_master_id: {item_master_id}"})
    
    def _get_or_create_inventory_item(
        self, 
        item_master: InventoryItemMaster,
        item_data: Dict[str, Any],
        transaction_id: str
    ) -> LineItem:
        """
        Get existing inventory item or create a new one.
        """
        try:
            warehouse = Warehouse.objects.get(id=item_data['warehouse_id'])
        except Warehouse.DoesNotExist:
            raise DRFValidationError({"items": f"Invalid warehouse_id: {item_data['warehouse_id']}"})
        
        # For individually tracked items with serial numbers
        if item_master.tracking_type == 'INDIVIDUAL' and item_data.get('serial_number'):
            # Check if serial number already exists
            existing_item = LineItem.objects.filter(
                serial_number=item_data['serial_number']
            ).first()
            
            if existing_item:
                raise DRFValidationError({
                    "items": f"Serial number {item_data['serial_number']} already exists"
                })
            
            # Create new individual item
            inventory_item = LineItem.objects.create(
                inventory_item_master=item_master,
                warehouse=warehouse,
                serial_number=item_data['serial_number'],
                quantity=0,  # Will be updated by stock movement
                rental_rate=item_data.get('rental_rate', 0),
                replacement_cost=item_data.get('replacement_cost', 0),
                late_fee_rate=item_data.get('late_fee_rate', 0),
                sell_tax_rate=item_data.get('sell_tax_rate', 0),
                rent_tax_rate=item_data.get('rent_tax_rate', 0),
                rentable=item_data.get('rentable', True),
                sellable=item_data.get('sellable', False),
                selling_price=item_data.get('selling_price', 0),
                warranty_period_type=item_data.get('warranty_period_type'),
                warranty_period=item_data.get('warranty_period')
            )
        else:
            # For bulk items, try to find existing inventory item
            inventory_item = LineItem.objects.filter(
                inventory_item_master=item_master,
                warehouse=warehouse,
                serial_number__isnull=True  # Bulk items don't have serial numbers
            ).first()
            
            if not inventory_item:
                # Create new bulk inventory item
                inventory_item = LineItem.objects.create(
                    inventory_item_master=item_master,
                    warehouse=warehouse,
                    quantity=0,  # Will be updated by stock movement
                    rental_rate=item_data.get('rental_rate', 0),
                    replacement_cost=item_data.get('replacement_cost', 0),
                    late_fee_rate=item_data.get('late_fee_rate', 0),
                    sell_tax_rate=item_data.get('sell_tax_rate', 0),
                    rent_tax_rate=item_data.get('rent_tax_rate', 0),
                    rentable=item_data.get('rentable', True),
                    sellable=item_data.get('sellable', False),
                    selling_price=item_data.get('selling_price', 0)
                )
        
        return inventory_item
    
    def _create_transaction_item(
        self,
        purchase_transaction: PurchaseTransaction,
        inventory_item: LineItem,
        item_data: Dict[str, Any]
    ) -> PurchaseTransactionItem:
        """
        Create a purchase transaction item record.
        """
        unit_price = Decimal(str(item_data.get('unit_price', 0)))
        quantity = item_data['quantity']
        discount = Decimal(str(item_data.get('discount', 0)))
        tax_amount = Decimal(str(item_data.get('tax_amount', 0)))
        
        # Calculate amounts
        amount = (unit_price * quantity) - discount
        total_price = amount + tax_amount
        
        transaction_item = PurchaseTransactionItem.objects.create(
            transaction=purchase_transaction,
            inventory_item=inventory_item,
            serial_number=item_data.get('serial_number'),
            quantity=quantity,
            unit_price=unit_price,
            discount=discount,
            tax_amount=tax_amount,
            amount=amount,
            total_price=total_price,
            reference_number=item_data.get('reference_number'),
            warranty_period_type=item_data.get('warranty_period_type'),
            warranty_period=item_data.get('warranty_period')
        )
        
        return transaction_item
    
    def _create_stock_movement(
        self,
        inventory_item: LineItem,
        quantity: int,
        transaction_id: str
    ) -> InventoryItemStockMovement:
        """
        Create a stock movement record for the purchase.
        """
        # Get current quantity
        quantity_before = inventory_item.quantity
        quantity_after = quantity_before + quantity
        
        # Update inventory item quantity
        inventory_item.quantity = quantity_after
        inventory_item.save()
        
        # Update master item quantity
        master_item = inventory_item.inventory_item_master
        master_item.quantity = models.F('quantity') + quantity
        master_item.save()
        
        # Create stock movement record
        stock_movement = InventoryItemStockMovement.objects.create(
            inventory_item=inventory_item,
            movement_type=MovementType.PURCHASE,
            inventory_transaction_id=transaction_id,
            quantity=quantity,
            quantity_on_hand_before=quantity_before,
            quantity_on_hand_after=quantity_after,
            warehouse_to=inventory_item.warehouse
        )
        
        return stock_movement
    
    def _update_transaction_totals(
        self, 
        purchase_transaction: PurchaseTransaction,
        created_items: List[Dict[str, Any]]
    ) -> None:
        """
        Update transaction totals based on created items.
        """
        total_amount = Decimal('0')
        total_tax_amount = Decimal('0')
        total_discount = Decimal('0')
        
        for item_info in created_items:
            transaction_item = item_info['transaction_item']
            total_amount += transaction_item.amount
            total_tax_amount += transaction_item.tax_amount or Decimal('0')
            total_discount += transaction_item.discount or Decimal('0')
        
        grand_total = total_amount + total_tax_amount
        
        purchase_transaction.total_amount = total_amount
        purchase_transaction.total_tax_amount = total_tax_amount
        purchase_transaction.total_discount = total_discount
        purchase_transaction.grand_total = grand_total
        purchase_transaction.save()