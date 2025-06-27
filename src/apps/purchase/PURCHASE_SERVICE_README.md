# Purchase Transaction Service Implementation

## Overview

The `PurchaseTransactionService` provides atomic transaction handling for purchase orders in the rental management system. It ensures data integrity by creating all related records within a single database transaction.

## Key Features

1. **Atomic Operations**: All operations (PurchaseTransaction, PurchaseTransactionItem, InventoryItem, InventoryItemStockMovement) are performed within a single database transaction
2. **Automatic ID Generation**: Transaction IDs are automatically generated using the ID Manager service
3. **Validation**: Comprehensive validation of input data with clear error messages
4. **Rollback on Failure**: If any operation fails, all changes are automatically rolled back
5. **Multi-Item Support**: Handle multiple items per purchase transaction
6. **Stock Movement Tracking**: Automatic creation of stock movement records

## Architecture

### Service Layer (`services/purchase_transaction_service.py`)

The service handles:
- Input validation (forbids user-provided transaction IDs)
- ID generation via ID Manager
- Transaction creation with all related records
- Stock quantity updates
- Error handling and rollback

### API Layer

#### Serializers (`serializers.py`)
- `CreatePurchaseTransactionSerializer`: Input validation for creating transactions
- `PurchaseTransactionDetailSerializer`: Detailed output with nested items
- `PurchaseItemInputSerializer`: Validation for individual items

#### Views (`views.py`)
- Custom `create()` method in `PurchaseTransactionViewSet` uses the service
- Returns detailed transaction data after creation
- Alternative endpoint: `/create-with-items/`

## Usage Example

### API Request
```json
POST /api/purchases/transactions/

{
  "transaction_date": "2024-01-15",
  "vendor": 1,
  "reference_number": "REF-001",
  "invoice_number": "INV-001",
  "remarks": "Initial purchase",
  "items": [
    {
      "item_master_id": 1,
      "warehouse_id": 1,
      "quantity": 10,
      "unit_price": "100.00",
      "discount": "10.00",
      "tax_amount": "90.00",
      "serial_number": "SN-12345",  // Optional, for individual items
      "warranty_period_type": "YEARS",
      "warranty_period": 2,
      "rental_rate": "50.00",
      "replacement_cost": "1000.00"
    }
  ]
}
```

### Response
```json
{
  "id": 1,
  "transaction_id": "PUR-AAA0001",  // Auto-generated
  "transaction_date": "2024-01-15",
  "vendor": 1,
  "vendor_name": "Vendor Name",
  "reference_number": "REF-001",
  "invoice_number": "INV-001",
  "total_amount": "990.00",
  "total_tax_amount": "90.00",
  "total_discount": "10.00",
  "grand_total": "1080.00",
  "remarks": "Initial purchase",
  "transaction_items": [
    {
      "id": 1,
      "inventory_item": 1,
      "inventory_item_name": "Item Name",
      "inventory_item_sku": "SKU-001",
      "quantity": 10,
      "unit_price": "100.00",
      "total_price": "1080.00"
    }
  ]
}
```

## Database Operations Flow

1. **Generate Transaction ID**: Uses `IdManager.generate_id('PUR')`
2. **Create PurchaseTransaction**: Main transaction record
3. **For each item**:
   - Get/Create InventoryItem
   - Create PurchaseTransactionItem
   - Create InventoryItemStockMovement
   - Update quantities
4. **Update transaction totals**: Calculate and save final amounts

## Error Handling

### Validation Errors
- Forbidden fields (transaction_id, id) → HTTP 400
- Missing required fields → HTTP 400
- Invalid references (vendor, warehouse, item) → HTTP 400
- Duplicate serial numbers → HTTP 400

### Rollback Scenarios
- ID generation failure
- Database constraint violations
- Any unexpected errors

## Testing

### Service Tests (`tests/test_purchase_transaction_service.py`)
- Atomic transaction creation
- Validation rules
- Rollback behavior
- Stock movement updates

### API Tests (`tests/test_purchase_api.py`)
- Endpoint functionality
- Authentication requirements
- Error responses
- Data integrity

## Security Considerations

1. **No Manual IDs**: Transaction IDs cannot be provided by users
2. **Authentication Required**: All endpoints require JWT authentication
3. **Data Validation**: Comprehensive input validation
4. **Atomic Operations**: Prevents partial data commits

## Future Enhancements

1. Batch purchase order processing
2. Inventory reservation system
3. Purchase order approval workflow
4. Integration with accounting systems
5. Enhanced reporting capabilities