import threading
import time
from datetime import date
from django.test import TransactionTestCase
from django.db import transaction, connections

from apps.purchase.services.purchase_transaction_service_v2 import PurchaseTransactionServiceV2
from apps.purchase.models import PurchaseTransaction
from apps.inventory_item.models import InventoryItemMaster, LineItem
from apps.warehouse.models import Warehouse
from apps.vendor.models import Vendor
from apps.item_category.models import ItemCategory, ItemSubCategory
from apps.unit_of_measurement.models import UnitOfMeasurement
from apps.id_manager.models import IdManager


class ConcurrentPurchaseTransactionTest(TransactionTestCase):
    """
    Test suite for concurrent purchase transaction handling.
    Verifies that the system correctly handles multiple simultaneous transactions.
    """
    
    def setUp(self):
        """Set up test data."""
        self.service = PurchaseTransactionServiceV2()
        
        # Create test data
        self.category = ItemCategory.objects.create(name="Test Category")
        self.subcategory = ItemSubCategory.objects.create(
            name="Test Subcategory",
            category=self.category
        )
        self.unit = UnitOfMeasurement.objects.create(
            name="Piece",
            abbreviation="pc"
        )
        self.warehouse = Warehouse.objects.create(name="Main Warehouse")
        self.vendor = Vendor.objects.create(name="Test Vendor")
        
        # Create item master for testing
        self.item_master = InventoryItemMaster.objects.create(
            name="Concurrent Test Item",
            sku="CONC001",
            item_sub_category=self.subcategory,
            unit_of_measurement=self.unit,
            tracking_type="BULK"
        )
        
        # Results storage for threads
        self.results = []
        self.errors = []
    
    def _create_transaction_in_thread(self, thread_id, quantity):
        """Helper method to create a transaction in a thread."""
        try:
            # Close existing database connection to force new one per thread
            connections.close_all()
            
            data = {
                'transaction_date': date.today().isoformat(),
                'vendor': self.vendor.id,
                'reference_number': f'THREAD-{thread_id}',
                'items': [{
                    'item_master_id': self.item_master.id,
                    'warehouse_id': self.warehouse.id,
                    'quantity': quantity,
                    'unit_price': '100.00'
                }]
            }
            
            transaction, items = self.service.create_purchase_transaction(data)
            self.results.append({
                'thread_id': thread_id,
                'transaction_id': transaction.transaction_id,
                'quantity': quantity
            })
        except Exception as e:
            self.errors.append({
                'thread_id': thread_id,
                'error': str(e)
            })
    
    def test_concurrent_id_generation(self):
        """Test that concurrent transactions get unique IDs."""
        threads = []
        num_threads = 5
        
        # Create and start threads
        for i in range(num_threads):
            thread = threading.Thread(
                target=self._create_transaction_in_thread,
                args=(i, 10)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no errors
        self.assertEqual(len(self.errors), 0, f"Errors occurred: {self.errors}")
        
        # Verify all transactions created
        self.assertEqual(len(self.results), num_threads)
        
        # Verify all IDs are unique
        transaction_ids = [r['transaction_id'] for r in self.results]
        self.assertEqual(len(set(transaction_ids)), num_threads)
        
        # Verify all IDs follow correct format
        for tid in transaction_ids:
            self.assertTrue(tid.startswith('PUR-'))
    
    def test_concurrent_stock_updates(self):
        """Test that concurrent stock updates are handled correctly."""
        threads = []
        quantities = [10, 20, 30, 40, 50]
        
        # Create threads with different quantities
        for i, qty in enumerate(quantities):
            thread = threading.Thread(
                target=self._create_transaction_in_thread,
                args=(i, qty)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify no errors
        self.assertEqual(len(self.errors), 0)
        
        # Verify total stock is correct
        self.item_master.refresh_from_db()
        expected_total = sum(quantities)
        self.assertEqual(self.item_master.quantity, expected_total)
        
        # Verify individual line items
        line_items = LineItem.objects.filter(
            inventory_item_master=self.item_master
        )
        total_line_item_qty = sum(li.quantity for li in line_items)
        self.assertEqual(total_line_item_qty, expected_total)
    
    def test_concurrent_serial_number_conflict(self):
        """Test handling of concurrent serial number conflicts."""
        # Create individual tracking item
        individual_item = InventoryItemMaster.objects.create(
            name="Serial Item",
            sku="SERIAL001",
            item_sub_category=self.subcategory,
            unit_of_measurement=self.unit,
            tracking_type="INDIVIDUAL"
        )
        
        def create_with_serial(thread_id):
            """Create transaction with same serial number."""
            try:
                connections.close_all()
                
                data = {
                    'transaction_date': date.today().isoformat(),
                    'items': [{
                        'item_master_id': individual_item.id,
                        'warehouse_id': self.warehouse.id,
                        'quantity': 1,
                        'serial_number': 'DUPLICATE-001'  # Same for all threads
                    }]
                }
                
                transaction, _ = self.service.create_purchase_transaction(data)
                self.results.append({
                    'thread_id': thread_id,
                    'transaction_id': transaction.transaction_id
                })
            except Exception as e:
                self.errors.append({
                    'thread_id': thread_id,
                    'error': str(e)
                })
        
        # Start multiple threads trying to use same serial number
        threads = []
        for i in range(3):
            thread = threading.Thread(target=create_with_serial, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Only one should succeed
        self.assertEqual(len(self.results), 1)
        self.assertEqual(len(self.errors), 2)
        
        # Verify errors are about duplicate serial
        for error in self.errors:
            self.assertIn('already exists', error['error'])
    
    def test_id_manager_concurrency(self):
        """Test ID Manager handles concurrent requests correctly."""
        prefix = 'TEST'
        num_ids = 20
        generated_ids = []
        
        def generate_id(index):
            """Generate ID in thread."""
            connections.close_all()
            generated_id = IdManager.generate_id(prefix)
            generated_ids.append(generated_id)
        
        # Generate IDs concurrently
        threads = []
        for i in range(num_ids):
            thread = threading.Thread(target=generate_id, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify all IDs generated
        self.assertEqual(len(generated_ids), num_ids)
        
        # Verify all IDs are unique
        self.assertEqual(len(set(generated_ids)), num_ids)
        
        # Verify sequential pattern
        numbers = []
        for id_val in generated_ids:
            # Extract number part (e.g., TEST-AAA0001 -> 1)
            parts = id_val.split('-')
            if len(parts) == 2:
                num_str = ''.join(filter(str.isdigit, parts[1]))
                if num_str:
                    numbers.append(int(num_str))
        
        # Numbers should be 1 through num_ids (not necessarily in order due to concurrency)
        self.assertEqual(sorted(numbers), list(range(1, num_ids + 1)))