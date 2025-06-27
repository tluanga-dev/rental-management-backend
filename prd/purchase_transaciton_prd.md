# Product Requirements Document (PRD)

## Purchase Order Management System - Atomic Transaction Feature

### 1. Executive Summary

This PRD defines the requirements for implementing atomic transaction handling in the Purchase Order Management System, ensuring data integrity through proper transaction management and rollback mechanisms.

### 2. Objective

Implement a robust purchase order creation system that guarantees data consistency through atomic transactions, preventing partial data commits and maintaining inventory accuracy.

### 3. Scope

- Purchase order creation workflow
- Inventory management integration
- Stock movement tracking
- Transaction rollback mechanisms
- Data integrity constraints
- Automatic transaction ID generation

### 4. Functional Requirements

#### 4.1 Transaction ID Management

- **Automatic ID Generation**
  - Transaction IDs generated automatically by the ID Manager application
  - Users must NOT provide transaction IDs in request payload
  - System rejects any payload containing user-supplied transaction IDs
  - ID Manager ensures uniqueness and sequential ordering

#### 4.2 Purchase Order Creation Flow

1. **Input Validation**
   - Validate `PurchaseTransaction` data (excluding transaction_id)
   - Validate `PurchaseTransactionItem` entries
   - Verify `ItemMaster` references
   - Reject payload if transaction_id is present

2. **Atomic Transaction Operations**
   - Request transaction ID from ID Manager service
   - Create `PurchaseTransaction` record with system-generated ID
   - Create `PurchaseTransactionItem` record(s)
   - Generate `InventoryItem` record(s)
   - Establish foreign key relationships
   - Log `InventoryItemStockMovement` record(s)

#### 4.3 Inventory Management

- **InventoryItem Creation**
  - One record per unique `ItemMaster`
  - Link to `PurchaseTransactionItem` via foreign key
  - Track quantity received

- **Stock Movement Tracking**
  - Record initial stock levels (0 for new items)
  - Calculate post-transaction quantities
  - Maintain transaction history

#### 4.4 Multi-Item Support

- Handle multiple `ItemMaster` entries per purchase order
- Create corresponding inventory and movement records
- Maintain referential integrity across all records

### 5. Non-Functional Requirements

#### 5.1 Data Integrity

- **ACID Compliance**: All operations must be Atomic, Consistent, Isolated, and Durable
- **Rollback Capability**: Complete reversal on any operation failure
- **Constraint Enforcement**: Prevent deletion/modification of used purchase records
- **ID Uniqueness**: ID Manager guarantees no duplicate transaction IDs

#### 5.2 Performance

- Transaction completion within 3 seconds for orders up to 100 items
- ID generation latency < 100ms
- Efficient bulk record creation
- Optimized database queries

#### 5.3 Error Handling

- Clear error messages for validation failures
- Specific error for user-provided transaction IDs
- Detailed logging of rollback operations
- User-friendly error responses

### 6. Technical Specifications

#### 6.1 Database Schema Requirements

```
PurchaseTransaction
├── transaction_id (PK) - System Generated via ID Manager
├── PurchaseTransactionItem (1:N)
│   └── inventory_item (FK) → InventoryItem
├── InventoryItem (1:N per ItemMaster)
└── InventoryItemStockMovement (1:N)
```

#### 6.2 Transaction Boundaries

- Single database transaction for entire operation
- Isolation level: READ COMMITTED minimum
- Deadlock detection and retry logic
- ID Manager call happens within transaction boundary

#### 6.3 API Payload Validation

- **Forbidden Fields**: `transaction_id`, `id`, any system-generated identifiers
- **Required Fields**: All business data except IDs
- **Validation Response**: HTTP 400 if forbidden fields present

### 7. Business Rules

#### 7.1 ID Generation Rules

- Transaction IDs must be obtained from ID Manager service only
- No manual ID assignment allowed
- ID format follows organization's ID pattern standards
- Failed ID generation triggers complete transaction rollback

#### 7.2 Stock Calculation

- Initial purchase: `quantity_on_hand_before = 0`
- Post-purchase: `quantity_on_hand_after = purchased_quantity`
- Future purchases: Previous `quantity_on_hand_after` becomes new `quantity_on_hand_before`

#### 7.3 Data Immutability

- Purchase records become immutable once referenced
- No deletion if `InventoryItem` has dependent transactions
- No editing of quantity/price after transaction completion

### 8. Testing Requirements

#### 8.1 Backend Testing

- Unit tests for each transaction step
- Integration tests for complete flow
- ID Manager integration testing
- Payload validation testing (reject user-provided IDs)
- Rollback scenario testing
- Concurrent transaction testing

#### 8.2 Frontend E2E Testing (Puppeteer)

- Purchase order submission flow
- Verify no transaction_id in request payload
- Error handling validation
- UI state consistency
- Network failure handling

### 9. Success Criteria

- Zero partial commits in production
- 100% rollback success rate on failures
- < 0.1% transaction failure rate
- Complete audit trail for all operations
- 100% system-generated transaction IDs
- Zero user-provided IDs accepted

### 10. Integration Requirements

- **ID Manager Service**
  - Reliable connection required
  - Fallback mechanism for service unavailability
  - Timeout handling (max 5 seconds)
  - Retry logic with exponential backoff

### 11. Future Considerations

- Batch purchase order processing
- Inventory reservation system
- Advanced stock prediction
- Integration with accounting systems
- ID Manager caching for performance

### 12. Acceptance Criteria

- [ ] Transaction IDs generated exclusively by ID Manager
- [ ] User-provided transaction IDs rejected with clear error
- [ ] All 4 transaction steps execute atomically
- [ ] Rollback works at any failure point
- [ ] Multi-item purchases create correct records
- [ ] Purchase records cannot be deleted when referenced
- [ ] Stock movements accurately tracked
- [ ] All tests pass with 100% coverage
- [ ] Performance meets specified thresholds
- [ ] ID Manager integration fully functional
