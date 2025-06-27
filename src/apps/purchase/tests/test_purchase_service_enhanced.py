import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import patch, MagicMock, Mock
from django.test import TestCase, TransactionTestCase
from django.db import transaction
from rest_framework.exceptions import ValidationError as DRFValidationError

from apps.purchase.services.purchase_transaction_service_v2 import PurchaseTransactionServiceV2
from apps.purchase.exceptions import (
    ForbiddenFieldException,
    IDGenerationException,
    IDGenerationTimeoutException,
    InvalidItemMasterException,
    InvalidWarehouseException,
    DuplicateSerialNumberException
)
from apps.purchase.models import PurchaseTransaction, PurchaseTransactionItem
from apps.inventory_item.models import LineItem, InventoryItemMaster, InventoryItemStockMovement
from apps.warehouse.models import Warehouse
from apps.vendor.models import Vendor
from apps.item_category.models import ItemCategory, ItemSubCategory
from apps.unit_of_measurement.models import UnitOfMeasurement
from apps.id_manager.models import IdManager


class PurchaseTransactionServiceEnhancedTest(TransactionTestCase):
    """
    Comprehensive test suite for enhanced purchase transaction service.
    Tests bulk operations, error handling, retries, and performance.
    """
    
    def setUp(self):
        """Set up test data."""
        self.service = PurchaseTransactionServiceV2()
        
        # Create test category and subcategory
        self.category = ItemCategory.objects.create(name="Test Category")
        self.subcategory = ItemSubCategory.objects.create(
            name="Test Subcategory",
            category=self.category
        )
        
        # Create test unit of measurement
        self.unit = UnitOfMeasurement.objects.create(
            name="Piece",
            abbreviation="pc"
        )
        
        # Create test warehouse
        self.warehouse = Warehouse.objects.create(name="Main Warehouse")
        
        # Create test vendor
        self.vendor = Vendor.objects.create(name="Test Vendor")
        
        # Create test item masters
        self.item_master_bulk = InventoryItemMaster.objects.create(
            name="Bulk Item",
            sku="BULK001",
            item_sub_category=self.subcategory,
            unit_of_measurement=self.unit,
            tracking_type="BULK"
        )
        
        self.item_master_individual = InventoryItemMaster.objects.create(
            name="Individual Item",
            sku="IND001",
            item_sub_category=self.subcategory,
            unit_of_measurement=self.unit,
            tracking_type="INDIVIDUAL"
        )
    
    def test_forbidden_fields_validation(self):
        """Test that forbidden fields are rejected."""
        data = {
            'transaction_date': date.today().isoformat(),
            'transaction_id': 'USER-PROVIDED-ID',  # Forbidden field
            'items': []
        }
        
        with self.assertRaises(ForbiddenFieldException) as context:
            self.service.create_purchase_transaction(data)
        
        self.assertIn('forbidden fields', str(context.exception))
        self.assertIn('transaction_id', str(context.exception))
    
    def test_missing_required_fields(self):
        """Test validation of required fields."""
        data = {
            'vendor': self.vendor.id,
            'items': []
        }
        
        with self.assertRaises(DRFValidationError) as context:
            self.service.create_purchase_transaction(data)
        
        self.assertIn('Missing required fields', str(context.exception))
    
    def test_empty_items_validation(self):
        """Test that at least one item is required."""
        data = {
            'transaction_date': date.today().isoformat(),
            'vendor': self.vendor.id,
            'items': []
        }
        
        with self.assertRaises(DRFValidationError) as context:
            self.service.create_purchase_transaction(data)
        
        self.assertIn('At least one item is required', str(context.exception))
    
    def test_bulk_create_multiple_items(self):
        """Test bulk creation of multiple items."""
        data = {
            'transaction_date': date.today().isoformat(),
            'vendor': self.vendor.id,
            'items': [
                {
                    'item_master_id': self.item_master_bulk.id,
                    'warehouse_id': self.warehouse.id,
                    'quantity': 10,
                    'unit_price': '100.00',
                    'tax_amount': '10.00'
                },
                {
                    'item_master_id': self.item_master_individual.id,
                    'warehouse_id': self.warehouse.id,
                    'quantity': 1,
                    'serial_number': 'SN001',
                    'unit_price': '500.00',
                    'tax_amount': '50.00'
                }
            ]
        }
        
        transaction, created_items = self.service.create_purchase_transaction(data)
        
        # Verify transaction created
        self.assertIsNotNone(transaction.transaction_id)
        self.assertTrue(transaction.transaction_id.startswith('PUR-'))
        
        # Verify items created
        self.assertEqual(len(created_items), 2)
        
        # Verify line items created
        self.assertEqual(LineItem.objects.count(), 2)
        
        # Verify transaction items created
        self.assertEqual(PurchaseTransactionItem.objects.count(), 2)
        
        # Verify stock movements created
        self.assertEqual(InventoryItemStockMovement.objects.count(), 2)
        
        # Verify totals
        self.assertEqual(transaction.total_amount, Decimal('1500.00'))
        self.assertEqual(transaction.total_tax_amount, Decimal('60.00'))
        self.assertEqual(transaction.grand_total, Decimal('1560.00'))
    
    def test_invalid_item_master_id(self):
        """Test handling of invalid item master ID."""
        data = {
            'transaction_date': date.today().isoformat(),
            'items': [{
                'item_master_id': 99999,  # Non-existent
                'warehouse_id': self.warehouse.id,
                'quantity': 10
            }]
        }
        
        with self.assertRaises(DRFValidationError) as context:
            self.service.create_purchase_transaction(data)
        
        self.assertIn('Invalid item_master_id', str(context.exception))
    
    def test_invalid_warehouse_id(self):
        """Test handling of invalid warehouse ID."""
        data = {
            'transaction_date': date.today().isoformat(),
            'items': [{
                'item_master_id': self.item_master_bulk.id,
                'warehouse_id': 99999,  # Non-existent
                'quantity': 10
            }]
        }
        
        with self.assertRaises(DRFValidationError) as context:
            self.service.create_purchase_transaction(data)
        
        self.assertIn('Invalid warehouse_id', str(context.exception))
    
    def test_duplicate_serial_number(self):
        """Test handling of duplicate serial numbers."""
        # Create existing item with serial number
        LineItem.objects.create(
            inventory_item_master=self.item_master_individual,
            warehouse=self.warehouse,
            serial_number='EXISTING001'
        )
        
        data = {
            'transaction_date': date.today().isoformat(),
            'items': [{
                'item_master_id': self.item_master_individual.id,
                'warehouse_id': self.warehouse.id,
                'quantity': 1,
                'serial_number': 'EXISTING001'  # Duplicate
            }]
        }
        
        with self.assertRaises(DRFValidationError) as context:
            self.service.create_purchase_transaction(data)
        
        self.assertIn('already exists', str(context.exception))
    
    @patch('apps.id_manager.models.IdManager.generate_id')
    def test_id_generation_retry_logic(self, mock_generate_id):
        """Test retry logic for ID generation failures."""
        # First two calls fail, third succeeds
        mock_generate_id.side_effect = [
            Exception("Connection failed"),
            Exception("Timeout"),
            "PUR-AAA0001"
        ]
        
        data = {
            'transaction_date': date.today().isoformat(),
            'items': [{
                'item_master_id': self.item_master_bulk.id,
                'warehouse_id': self.warehouse.id,
                'quantity': 10
            }]
        }
        
        transaction, _ = self.service.create_purchase_transaction(data)
        
        # Verify retry happened (3 calls)
        self.assertEqual(mock_generate_id.call_count, 3)
        self.assertEqual(transaction.transaction_id, "PUR-AAA0001")
    
    @patch('apps.id_manager.models.IdManager.generate_id')
    def test_id_generation_all_retries_fail(self, mock_generate_id):
        """Test when all ID generation retries fail."""
        mock_generate_id.side_effect = Exception("Persistent failure")
        
        data = {
            'transaction_date': date.today().isoformat(),
            'items': [{
                'item_master_id': self.item_master_bulk.id,
                'warehouse_id': self.warehouse.id,
                'quantity': 10
            }]
        }
        
        with self.assertRaises(DRFValidationError) as context:
            self.service.create_purchase_transaction(data)
        
        # Verify all retries attempted
        self.assertEqual(mock_generate_id.call_count, 3)
        self.assertIn("Failed to generate transaction ID", str(context.exception))
    
    def test_transaction_rollback_on_failure(self):
        """Test that all changes are rolled back on failure."""
        initial_transaction_count = PurchaseTransaction.objects.count()
        initial_line_item_count = LineItem.objects.count()
        
        data = {
            'transaction_date': date.today().isoformat(),
            'items': [
                {
                    'item_master_id': self.item_master_bulk.id,
                    'warehouse_id': self.warehouse.id,
                    'quantity': 10
                },
                {
                    'item_master_id': 99999,  # This will cause failure
                    'warehouse_id': self.warehouse.id,
                    'quantity': 5
                }
            ]
        }
        
        with self.assertRaises(DRFValidationError):
            self.service.create_purchase_transaction(data)
        
        # Verify nothing was created
        self.assertEqual(PurchaseTransaction.objects.count(), initial_transaction_count)
        self.assertEqual(LineItem.objects.count(), initial_line_item_count)
    
    def test_stock_quantity_updates(self):
        """Test that stock quantities are updated correctly."""
        data = {
            'transaction_date': date.today().isoformat(),
            'items': [{
                'item_master_id': self.item_master_bulk.id,
                'warehouse_id': self.warehouse.id,
                'quantity': 25
            }]
        }
        
        transaction, created_items = self.service.create_purchase_transaction(data)
        
        # Verify line item quantity
        line_item = created_items[0]['inventory_item']
        self.assertEqual(line_item.quantity, 25)
        
        # Verify master item quantity updated
        self.item_master_bulk.refresh_from_db()
        self.assertEqual(self.item_master_bulk.quantity, 25)
        
        # Verify stock movement
        movement = created_items[0]['stock_movement']
        self.assertEqual(movement.quantity_on_hand_before, 0)
        self.assertEqual(movement.quantity_on_hand_after, 25)
    
    def test_performance_logging(self):
        """Test that performance metrics are logged."""
        with self.assertLogs('apps.purchase.services.purchase_transaction_service_v2', level='INFO') as cm:
            data = {
                'transaction_date': date.today().isoformat(),
                'items': [{
                    'item_master_id': self.item_master_bulk.id,
                    'warehouse_id': self.warehouse.id,
                    'quantity': 10
                }]
            }
            
            self.service.create_purchase_transaction(data)
        
        # Verify performance log
        self.assertTrue(any('Successfully created purchase transaction' in msg for msg in cm.output))
        self.assertTrue(any('seconds' in msg for msg in cm.output))


class IDManagerHealthCheckTest(TestCase):
    """Test suite for ID Manager health check functionality."""
    
    def test_health_check_healthy(self):
        """Test health check when service is healthy."""
        health_status = IdManager.health_check()
        
        self.assertEqual(health_status['status'], 'healthy')
        self.assertIn('message', health_status)
        self.assertIn('test_id_generated', health_status)
        self.assertTrue(health_status['test_id_generated'].startswith('_HEALTH_CHECK_-'))
        
        # Verify test entry was cleaned up
        self.assertFalse(IdManager.objects.filter(prefix='_HEALTH_CHECK_').exists())
    
    @patch('apps.id_manager.models.IdManager.objects.count')
    def test_health_check_unhealthy(self, mock_count):
        """Test health check when service is unhealthy."""
        mock_count.side_effect = Exception("Database connection failed")
        
        health_status = IdManager.health_check()
        
        self.assertEqual(health_status['status'], 'unhealthy')
        self.assertIn('error_type', health_status)
        self.assertIn('Database connection failed', health_status['message'])