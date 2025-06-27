"""
Custom exception classes for purchase transaction handling.
"""
from rest_framework.exceptions import APIException
from rest_framework import status


class PurchaseTransactionException(APIException):
    """Base exception class for purchase transaction errors."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'A purchase transaction error occurred.'
    default_code = 'purchase_error'


class InvalidTransactionDataException(PurchaseTransactionException):
    """Raised when transaction data is invalid."""
    default_detail = 'Invalid transaction data provided.'
    default_code = 'invalid_transaction_data'


class ForbiddenFieldException(PurchaseTransactionException):
    """Raised when forbidden fields are present in the request."""
    default_detail = 'Request contains forbidden fields that are auto-generated.'
    default_code = 'forbidden_fields'


class IDGenerationException(PurchaseTransactionException):
    """Raised when ID generation fails."""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Failed to generate transaction ID.'
    default_code = 'id_generation_failed'


class IDGenerationTimeoutException(IDGenerationException):
    """Raised when ID generation times out."""
    default_detail = 'ID generation service timed out.'
    default_code = 'id_generation_timeout'


class ItemValidationException(PurchaseTransactionException):
    """Raised when item validation fails."""
    default_detail = 'Item validation failed.'
    default_code = 'item_validation_failed'


class InvalidItemMasterException(ItemValidationException):
    """Raised when an invalid item master ID is provided."""
    default_detail = 'Invalid item master ID provided.'
    default_code = 'invalid_item_master'


class InvalidWarehouseException(ItemValidationException):
    """Raised when an invalid warehouse ID is provided."""
    default_detail = 'Invalid warehouse ID provided.'
    default_code = 'invalid_warehouse'


class DuplicateSerialNumberException(ItemValidationException):
    """Raised when a duplicate serial number is detected."""
    default_detail = 'Serial number already exists.'
    default_code = 'duplicate_serial_number'


class StockUpdateException(PurchaseTransactionException):
    """Raised when stock update fails."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Failed to update stock levels.'
    default_code = 'stock_update_failed'


class TransactionRollbackException(PurchaseTransactionException):
    """Raised when transaction rollback is needed."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Transaction was rolled back due to an error.'
    default_code = 'transaction_rollback'


class ConcurrentTransactionException(PurchaseTransactionException):
    """Raised when concurrent transaction conflicts occur."""
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Concurrent transaction conflict detected.'
    default_code = 'concurrent_transaction_conflict'