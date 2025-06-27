from decimal import Decimal
from datetime import date
from django.test import TestCase
from rest_framework.exceptions import ValidationError as DRFValidationError

from apps.purchase.models import PurchaseTransaction, PurchaseTransactionItem
from apps.purchase.services import PurchaseTransactionService
from apps.inventory_item.models import (
    LineItemMaster, 
    LineItem, 
    LineItemStockMovement,
    TrackingType,
    MovementType
)
from apps.warehouse.models import Warehouse
from apps.vendor.models import Vendor
from apps.item_category.models import ItemCategory, ItemSubCategory
from apps.unit_of_measurement.models import UnitOfMeasurement
from apps.item_packaging.models import ItemPackaging


class PurchaseTransactionServiceTestCase(TestCase):
    """
    Test cases for PurchaseTransactionService
    """
    
    def setUp(self):
        """
        Set up test data
        """
        # Create warehouse
        self.warehouse = Warehouse.objects.create(
            name="Main Warehouse",
            label="MAIN"
        )
        
        # Create vendor
        self.vendor = Vendor.objects.create(
            name="Test Vendor",
            email="vendor@test.com"
        )
        
        # Create category and subcategory
        self.category = ItemCategory.objects.create(
            name="Test Category"
        )
        self.subcategory = ItemSubCategory.objects.create(
            name="Test Subcategory",
            item_category=self.category
        )
        
        # Create unit of measurement
        self.unit = UnitOfMeasurement.objects.create(
            name="Piece",
            abbreviation="pc"
        )
        
        # Create packaging
        self.packaging = ItemPackaging.objects.create(
            name="Box"
        )
        
        # Create item masters
        self.bulk_item_master = LineItemMaster.objects.create(
            name="Bulk Test Item",
            sku="BULK-001",
            item_sub_category=self.subcategory,
            unit_of_measurement=self.unit,
            packaging=self.packaging,
            tracking_type=TrackingType.BULK
        )
        
        self.individual_item_master = LineItemMaster.objects.create(
            name="Individual Test Item",
            sku="IND-001",
            item_sub_category=self.subcategory,
            unit_of_measurement=self.unit,
            packaging=self.packaging,
            tracking_type=TrackingType.INDIVIDUAL
        )
        
        self.service = PurchaseTransactionService()
    
    def test_create_purchase_transaction_with_bulk_item(self):
        """
        Test creating a purchase transaction with a bulk item
        """
        data = {
            'transaction_date': date.today(),
            'vendor': self.vendor.id,
            'reference_number': 'REF-001',
            'invoice_number': 'INV-001',
            'remarks': 'Test purchase',
            'items': [
                {
                    'item_master_id': self.bulk_item_master.id,
                    'warehouse_id': self.warehouse.id,
                    'quantity': 10,
                    'unit_price': '100.00',
                    'discount': '10.00',
                    'tax_amount': '90.00'
                }
            ]
        }
        
        transaction, items = self.service.create_purchase_transaction(data)
        
        # Verify transaction was created
        self.assertIsNotNone(transaction)
        self.assertTrue(transaction.transaction_id.startswith('PUR-'))
        self.assertEqual(transaction.vendor, self.vendor)
        self.assertEqual(transaction.reference_number, 'REF-001')
        
        # Verify totals
        self.assertEqual(transaction.total_amount, Decimal('990.00'))  # (100 * 10) - 10
        self.assertEqual(transaction.total_tax_amount, Decimal('90.00'))
        self.assertEqual(transaction.total_discount, Decimal('10.00'))
        self.assertEqual(transaction.grand_total, Decimal('1080.00'))  # 990 + 90
        
        # Verify items were created
        self.assertEqual(len(items), 1)
        item_info = items[0]
        
        # Verify transaction item
        transaction_item = item_info['transaction_item']
        self.assertEqual(transaction_item.quantity, 10)
        self.assertEqual(transaction_item.unit_price, Decimal('100.00'))
        
        # Verify line item
        line_item = item_info['line_item']
        self.assertEqual(line_item.quantity, 10)
        self.assertEqual(line_item.warehouse, self.warehouse)
        
        # Verify stock movement
        stock_movement = item_info['stock_movement']
        self.assertEqual(stock_movement.movement_type, MovementType.PURCHASE)
        self.assertEqual(stock_movement.quantity, 10)
        self.assertEqual(stock_movement.quantity_on_hand_before, 0)
        self.assertEqual(stock_movement.quantity_on_hand_after, 10)
    
    def test_create_purchase_transaction_with_individual_item(self):
        """
        Test creating a purchase transaction with an individual item
        """
        data = {
            'transaction_date': date.today(),
            'vendor': self.vendor.id,
            'items': [
                {
                    'item_master_id': self.individual_item_master.id,
                    'warehouse_id': self.warehouse.id,
                    'quantity': 1,
                    'serial_number': 'SN-12345',
                    'unit_price': '500.00',
                    'warranty_period_type': 'YEARS',
                    'warranty_period': 2,
                    'rental_rate': '50.00'
                }
            ]
        }
        
        transaction, items = self.service.create_purchase_transaction(data)
        
        # Verify transaction was created
        self.assertIsNotNone(transaction)
        self.assertTrue(transaction.transaction_id.startswith('PUR-'))
        
        # Verify line item
        line_item = items[0]['line_item']
        self.assertEqual(line_item.serial_number, 'SN-12345')
        self.assertEqual(line_item.quantity, 1)
        self.assertEqual(Decimal(str(line_item.rental_rate)), Decimal('50.00'))
        self.assertEqual(line_item.warranty_period_type, 'YEARS')
        self.assertEqual(line_item.warranty_period, 2)
    
    def test_create_purchase_transaction_multiple_items(self):
        """
        Test creating a purchase transaction with multiple items
        """
        data = {
            'transaction_date': date.today(),
            'items': [
                {
                    'item_master_id': self.bulk_item_master.id,
                    'warehouse_id': self.warehouse.id,
                    'quantity': 5,
                    'unit_price': '100.00'
                },
                {
                    'item_master_id': self.individual_item_master.id,
                    'warehouse_id': self.warehouse.id,
                    'quantity': 1,
                    'serial_number': 'SN-99999',
                    'unit_price': '200.00'
                }
            ]
        }
        
        transaction, items = self.service.create_purchase_transaction(data)
        
        # Verify transaction was created
        self.assertIsNotNone(transaction)
        self.assertEqual(len(items), 2)
        
        # Verify total
        self.assertEqual(transaction.grand_total, Decimal('700.00'))  # (5 * 100) + (1 * 200)
        
        # Verify both items were created
        self.assertEqual(PurchaseTransactionItem.objects.filter(transaction=transaction).count(), 2)
    
    def test_reject_user_provided_transaction_id(self):
        """
        Test that user-provided transaction IDs are rejected
        """
        data = {
            'transaction_id': 'USER-PROVIDED-ID',
            'transaction_date': date.today(),
            'items': [{
                'item_master_id': self.bulk_item_master.id,
                'warehouse_id': self.warehouse.id,
                'quantity': 1
            }]
        }
        
        with self.assertRaises(DRFValidationError) as context:
            self.service.create_purchase_transaction(data)
        
        self.assertIn('forbidden fields', str(context.exception.detail['error']))
    
    def test_duplicate_serial_number_rejected(self):
        """
        Test that duplicate serial numbers are rejected
        """
        # Create an existing item with serial number
        LineItem.objects.create(
            line_item_master=self.individual_item_master,
            warehouse=self.warehouse,
            serial_number='SN-EXISTING',
            quantity=1
        )
        
        data = {
            'transaction_date': date.today(),
            'items': [{
                'item_master_id': self.individual_item_master.id,
                'warehouse_id': self.warehouse.id,
                'quantity': 1,
                'serial_number': 'SN-EXISTING'
            }]
        }
        
        with self.assertRaises(DRFValidationError) as context:
            self.service.create_purchase_transaction(data)
        
        self.assertIn('already exists', str(context.exception.detail['items']))
    
    def test_invalid_item_master_rejected(self):
        """
        Test that invalid item master IDs are rejected
        """
        data = {
            'transaction_date': date.today(),
            'items': [{
                'item_master_id': 99999,  # Non-existent ID
                'warehouse_id': self.warehouse.id,
                'quantity': 1
            }]
        }
        
        with self.assertRaises(DRFValidationError) as context:
            self.service.create_purchase_transaction(data)
        
        self.assertIn('Invalid item_master_id', str(context.exception.detail['items']))
    
    def test_missing_required_fields_rejected(self):
        """
        Test that missing required fields are rejected
        """
        # Missing transaction_date
        data = {
            'items': [{
                'item_master_id': self.bulk_item_master.id,
                'warehouse_id': self.warehouse.id,
                'quantity': 1
            }]
        }
        
        with self.assertRaises(DRFValidationError) as context:
            self.service.create_purchase_transaction(data)
        
        self.assertIn('Missing required fields', str(context.exception.detail['error']))
    
    def test_empty_items_list_rejected(self):
        """
        Test that empty items list is rejected
        """
        data = {
            'transaction_date': date.today(),
            'items': []
        }
        
        with self.assertRaises(DRFValidationError) as context:
            self.service.create_purchase_transaction(data)
        
        self.assertIn('At least one item is required', str(context.exception.detail['items']))
    
    def test_atomic_rollback_on_failure(self):
        """
        Test that all changes are rolled back on failure
        """
        initial_transaction_count = PurchaseTransaction.objects.count()
        initial_item_count = PurchaseTransactionItem.objects.count()
        initial_inventory_count = LineItem.objects.count()
        initial_movement_count = LineItemStockMovement.objects.count()
        
        # Create data with invalid warehouse ID for second item
        data = {
            'transaction_date': date.today(),
            'items': [
                {
                    'item_master_id': self.bulk_item_master.id,
                    'warehouse_id': self.warehouse.id,
                    'quantity': 5
                },
                {
                    'item_master_id': self.bulk_item_master.id,
                    'warehouse_id': 99999,  # Invalid warehouse
                    'quantity': 10
                }
            ]
        }
        
        with self.assertRaises(DRFValidationError):
            self.service.create_purchase_transaction(data)
        
        # Verify nothing was created
        self.assertEqual(PurchaseTransaction.objects.count(), initial_transaction_count)
        self.assertEqual(PurchaseTransactionItem.objects.count(), initial_item_count)
        self.assertEqual(LineItem.objects.count(), initial_inventory_count)
        self.assertEqual(LineItemStockMovement.objects.count(), initial_movement_count)
    
    def test_stock_movement_updates_master_quantity(self):
        """
        Test that stock movements update the master item quantity
        """
        initial_master_quantity = self.bulk_item_master.quantity
        
        data = {
            'transaction_date': date.today(),
            'items': [{
                'item_master_id': self.bulk_item_master.id,
                'warehouse_id': self.warehouse.id,
                'quantity': 15
            }]
        }
        
        self.service.create_purchase_transaction(data)
        
        # Refresh from database
        self.bulk_item_master.refresh_from_db()
        
        # Verify master quantity was updated
        self.assertEqual(self.bulk_item_master.quantity, initial_master_quantity + 15)