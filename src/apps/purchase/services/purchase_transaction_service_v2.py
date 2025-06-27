from decimal import Decimal
from typing import Dict, List, Any, Tuple, Optional
from django.db import transaction, models
from django.db.models import Prefetch, F
from rest_framework.exceptions import ValidationError as DRFValidationError
import logging
import time
from functools import wraps

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
from apps.purchase.exceptions import (
    PurchaseTransactionException,
    ForbiddenFieldException,
    IDGenerationException,
    IDGenerationTimeoutException,
    InvalidItemMasterException,
    InvalidWarehouseException,
    DuplicateSerialNumberException,
    ItemValidationException,
    InvalidTransactionDataException
)

logger = logging.getLogger(__name__)


def with_retry(max_attempts: int = 3, backoff_factor: float = 2.0):
    """
    Decorator for implementing retry logic with exponential backoff.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = backoff_factor ** attempt
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {wait_time} seconds..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}: {str(e)}")
            raise last_exception
        return wrapper
    return decorator


class PurchaseTransactionServiceV2:
    """
    Enhanced service class for handling purchase transactions with:
    - Bulk operations for better performance
    - Optimized database queries
    - Retry logic with exponential backoff
    - Comprehensive error logging
    - Timeout handling for external services
    """
    
    PURCHASE_TRANSACTION_PREFIX = 'PUR'
    ID_MANAGER_TIMEOUT = 5.0  # seconds
    
    def __init__(self):
        self.errors = []
        
    def create_purchase_transaction(self, data: Dict[str, Any]) -> Tuple[PurchaseTransaction, List[Dict[str, Any]]]:
        """
        Create a purchase transaction with all related records in an atomic transaction.
        Uses bulk operations for improved performance.
        
        Args:
            data: Dictionary containing purchase transaction data and items
            
        Returns:
            Tuple of (created PurchaseTransaction, list of created items with details)
            
        Raises:
            DRFValidationError: If validation fails or transaction cannot be completed
        """
        start_time = time.time()
        
        try:
            with transaction.atomic():
                # Validate input data
                self._validate_input_data(data)
                
                # Extract transaction data and items
                transaction_data = self._extract_transaction_data(data)
                items_data = data.get('items', [])
                
                if not items_data:
                    raise DRFValidationError({"items": "At least one item is required"})
                
                # Generate transaction ID with timeout
                transaction_id = self._generate_transaction_id_with_timeout()
                transaction_data['transaction_id'] = transaction_id
                
                # Create purchase transaction
                purchase_transaction = self._create_purchase_transaction(transaction_data)
                
                # Bulk process items
                created_items = self._bulk_process_items(purchase_transaction, items_data)
                
                # Update transaction totals
                self._update_transaction_totals(purchase_transaction, created_items)
                
                # Log performance metrics
                duration = time.time() - start_time
                logger.info(
                    f"Successfully created purchase transaction {transaction_id} "
                    f"with {len(created_items)} items in {duration:.2f} seconds",
                    extra={
                        'transaction_id': transaction_id,
                        'item_count': len(created_items),
                        'duration': duration,
                        'vendor_id': getattr(purchase_transaction.vendor, 'id', None),
                        'total_amount': str(purchase_transaction.grand_total)
                    }
                )
                
                return purchase_transaction, created_items
                
        except DRFValidationError:
            raise
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Failed to create purchase transaction after {duration:.2f} seconds: {str(e)}",
                extra={
                    'duration': duration,
                    'error_type': type(e).__name__,
                    'items_count': len(data.get('items', []))
                },
                exc_info=True
            )
            raise DRFValidationError({"error": f"Failed to create purchase transaction: {str(e)}"})
    
    def _validate_input_data(self, data: Dict[str, Any]) -> None:
        """
        Validate that input data doesn't contain forbidden fields like transaction_id.
        """
        forbidden_fields = ['transaction_id', 'id']
        found_forbidden = [field for field in forbidden_fields if field in data]
        
        if found_forbidden:
            raise ForbiddenFieldException(
                detail=f"Request contains forbidden fields: {', '.join(found_forbidden)}. "
                       "Transaction IDs are generated automatically by the system."
            )
        
        # Validate required fields
        required_fields = ['transaction_date']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            raise DRFValidationError({
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            })
    
    def _extract_transaction_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and validate transaction-level data with optimized queries.
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
        
        # Validate vendor if provided with optimized query
        if 'vendor' in transaction_data and transaction_data['vendor']:
            try:
                vendor = Vendor.objects.only('id', 'name').get(id=transaction_data['vendor'])
                transaction_data['vendor'] = vendor
            except Vendor.DoesNotExist:
                raise DRFValidationError({"vendor": "Invalid vendor ID"})
        
        return transaction_data
    
    @with_retry(max_attempts=3, backoff_factor=2.0)
    def _generate_transaction_id_with_timeout(self) -> str:
        """
        Generate a unique transaction ID using the ID Manager service with timeout.
        Includes retry logic with exponential backoff.
        """
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("ID Manager request timed out")
        
        # Set up timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(self.ID_MANAGER_TIMEOUT))
        
        try:
            transaction_id = IdManager.generate_id(self.PURCHASE_TRANSACTION_PREFIX)
            signal.alarm(0)  # Cancel the alarm
            return transaction_id
        except TimeoutError:
            signal.alarm(0)  # Cancel the alarm
            logger.error("ID Manager timeout after 5 seconds")
            raise DRFValidationError({"error": "ID generation service timeout"})
        except Exception as e:
            signal.alarm(0)  # Cancel the alarm
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
    
    def _bulk_process_items(
        self, 
        purchase_transaction: PurchaseTransaction, 
        items_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process multiple items using bulk operations for better performance.
        """
        # Validate all items first
        for item_data in items_data:
            self._validate_item_data(item_data)
        
        # Collect all item master IDs and warehouse IDs for bulk fetch
        item_master_ids = [item['item_master_id'] for item in items_data]
        warehouse_ids = [item['warehouse_id'] for item in items_data]
        
        # Bulk fetch item masters with optimized query
        item_masters = {
            im.id: im 
            for im in InventoryItemMaster.objects.filter(
                id__in=item_master_ids
            ).select_related('item_sub_category', 'unit_of_measurement')
        }
        
        # Bulk fetch warehouses
        warehouses = {
            w.id: w 
            for w in Warehouse.objects.filter(id__in=warehouse_ids).only('id', 'name')
        }
        
        # Validate all IDs exist
        for item_data in items_data:
            if item_data['item_master_id'] not in item_masters:
                raise DRFValidationError({"items": f"Invalid item_master_id: {item_data['item_master_id']}"})
            if item_data['warehouse_id'] not in warehouses:
                raise DRFValidationError({"items": f"Invalid warehouse_id: {item_data['warehouse_id']}"})
        
        # Prepare bulk create lists
        line_items_to_create = []
        transaction_items_to_create = []
        stock_movements_to_create = []
        created_items_info = []
        
        # Process each item
        for item_data in items_data:
            item_master = item_masters[item_data['item_master_id']]
            warehouse = warehouses[item_data['warehouse_id']]
            
            # Prepare line item
            line_item_data = self._prepare_line_item_data(
                item_master, warehouse, item_data
            )
            
            # For individually tracked items, check serial number uniqueness
            if item_master.tracking_type == 'INDIVIDUAL' and item_data.get('serial_number'):
                existing = LineItem.objects.filter(
                    serial_number=item_data['serial_number']
                ).exists()
                if existing:
                    raise DRFValidationError({
                        "items": f"Serial number {item_data['serial_number']} already exists"
                    })
            
            line_items_to_create.append(line_item_data)
        
        # Bulk create line items
        if line_items_to_create:
            created_line_items = LineItem.objects.bulk_create(
                [LineItem(**data) for data in line_items_to_create]
            )
        else:
            created_line_items = []
        
        # Now create transaction items and stock movements
        for i, (line_item, item_data) in enumerate(zip(created_line_items, items_data)):
            item_master = item_masters[item_data['item_master_id']]
            
            # Prepare transaction item
            transaction_item_data = self._prepare_transaction_item_data(
                purchase_transaction, line_item, item_data
            )
            transaction_items_to_create.append(
                PurchaseTransactionItem(**transaction_item_data)
            )
            
            # Prepare stock movement
            stock_movement_data = self._prepare_stock_movement_data(
                line_item, item_data['quantity'], purchase_transaction.transaction_id
            )
            stock_movements_to_create.append(
                InventoryItemStockMovement(**stock_movement_data)
            )
        
        # Bulk create transaction items and stock movements
        created_transaction_items = PurchaseTransactionItem.objects.bulk_create(
            transaction_items_to_create
        )
        created_stock_movements = InventoryItemStockMovement.objects.bulk_create(
            stock_movements_to_create
        )
        
        # Update line item quantities and master item quantities
        self._bulk_update_quantities(created_line_items, items_data, item_masters)
        
        # Prepare return data
        for i in range(len(created_line_items)):
            created_items_info.append({
                'transaction_item': created_transaction_items[i],
                'inventory_item': created_line_items[i],
                'stock_movement': created_stock_movements[i],
                'item_master': item_masters[items_data[i]['item_master_id']]
            })
        
        return created_items_info
    
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
    
    def _prepare_line_item_data(
        self,
        item_master: InventoryItemMaster,
        warehouse: Warehouse,
        item_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare data for creating a line item.
        """
        return {
            'inventory_item_master': item_master,
            'warehouse': warehouse,
            'serial_number': item_data.get('serial_number') if item_master.tracking_type == 'INDIVIDUAL' else None,
            'quantity': 0,  # Will be updated later
            'rental_rate': item_data.get('rental_rate', 0),
            'replacement_cost': item_data.get('replacement_cost', 0),
            'late_fee_rate': item_data.get('late_fee_rate', 0),
            'sell_tax_rate': item_data.get('sell_tax_rate', 0),
            'rent_tax_rate': item_data.get('rent_tax_rate', 0),
            'rentable': item_data.get('rentable', True),
            'sellable': item_data.get('sellable', False),
            'selling_price': item_data.get('selling_price', 0),
            'warranty_period_type': item_data.get('warranty_period_type'),
            'warranty_period': item_data.get('warranty_period')
        }
    
    def _prepare_transaction_item_data(
        self,
        purchase_transaction: PurchaseTransaction,
        line_item: LineItem,
        item_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare data for creating a transaction item.
        """
        unit_price = Decimal(str(item_data.get('unit_price', 0)))
        quantity = item_data['quantity']
        discount = Decimal(str(item_data.get('discount', 0)))
        tax_amount = Decimal(str(item_data.get('tax_amount', 0)))
        
        # Calculate amounts
        amount = (unit_price * quantity) - discount
        total_price = amount + tax_amount
        
        return {
            'transaction': purchase_transaction,
            'inventory_item': line_item,
            'serial_number': item_data.get('serial_number'),
            'quantity': quantity,
            'unit_price': unit_price,
            'discount': discount,
            'tax_amount': tax_amount,
            'amount': amount,
            'total_price': total_price,
            'reference_number': item_data.get('reference_number'),
            'warranty_period_type': item_data.get('warranty_period_type'),
            'warranty_period': item_data.get('warranty_period')
        }
    
    def _prepare_stock_movement_data(
        self,
        line_item: LineItem,
        quantity: int,
        transaction_id: str
    ) -> Dict[str, Any]:
        """
        Prepare data for creating a stock movement.
        """
        return {
            'inventory_item': line_item,
            'movement_type': MovementType.PURCHASE,
            'inventory_transaction_id': transaction_id,
            'quantity': quantity,
            'quantity_on_hand_before': 0,  # For new items
            'quantity_on_hand_after': quantity,
            'warehouse_to': line_item.warehouse
        }
    
    def _bulk_update_quantities(
        self,
        line_items: List[LineItem],
        items_data: List[Dict[str, Any]],
        item_masters: Dict[int, InventoryItemMaster]
    ) -> None:
        """
        Bulk update quantities for line items and master items.
        """
        # Update line item quantities
        for line_item, item_data in zip(line_items, items_data):
            line_item.quantity = item_data['quantity']
        
        LineItem.objects.bulk_update(line_items, ['quantity'])
        
        # Update master item quantities
        master_updates = {}
        for item_data in items_data:
            master_id = item_data['item_master_id']
            if master_id not in master_updates:
                master_updates[master_id] = 0
            master_updates[master_id] += item_data['quantity']
        
        # Use F() expressions for atomic updates
        for master_id, quantity_increase in master_updates.items():
            InventoryItemMaster.objects.filter(id=master_id).update(
                quantity=F('quantity') + quantity_increase
            )
    
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