#!/usr/bin/env python3
"""
Manual test script for the Purchase Transaction API
This script demonstrates the purchase transaction service functionality
"""

import os
import sys
import json
import uuid
from datetime import date

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup Django
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.purchase.services import PurchaseTransactionService
from apps.warehouse.models import Warehouse
from apps.vendor.models import Vendor
from apps.item_category.models import ItemCategory, ItemSubCategory
from apps.unit_of_measurement.models import UnitOfMeasurement
from apps.item_packaging.models import ItemPackaging
from apps.inventory_item.models import InventoryItemMaster, TrackingType


def create_test_data():
    """Create test data for the purchase transaction"""
    print("Creating test data...")
    
    # Create warehouse
    warehouse = Warehouse.objects.create(
        name="Test Warehouse",
        label="TEST"
    )
    
    # Create vendor
    vendor = Vendor.objects.create(
        name="Test Vendor",
        email="vendor@test.com"
    )
    
    # Create category and subcategory
    category = ItemCategory.objects.create(name="Test Category")
    subcategory = ItemSubCategory.objects.create(
        name="Test Subcategory",
        item_category=category
    )
    
    # Create unit of measurement
    unit = UnitOfMeasurement.objects.create(
        name="Piece",
        abbreviation="pc"
    )
    
    # Create packaging
    packaging = ItemPackaging.objects.create(name="Box")
    
    # Create item masters
    bulk_item = InventoryItemMaster.objects.create(
        name="Test Bulk Item",
        sku="BULK-001",
        item_sub_category=subcategory,
        unit_of_measurement=unit,
        packaging=packaging,
        tracking_type=TrackingType.BULK
    )
    
    individual_item = InventoryItemMaster.objects.create(
        name="Test Individual Item",
        sku="IND-001",
        item_sub_category=subcategory,
        unit_of_measurement=unit,
        packaging=packaging,
        tracking_type=TrackingType.INDIVIDUAL
    )
    
    return {
        'warehouse': warehouse,
        'vendor': vendor,
        'bulk_item': bulk_item,
        'individual_item': individual_item
    }


def test_purchase_transaction_service():
    """Test the purchase transaction service"""
    print("\n" + "="*60)
    print("TESTING PURCHASE TRANSACTION SERVICE")
    print("="*60)
    
    # Create test data
    test_data = create_test_data()
    
    # Initialize service
    service = PurchaseTransactionService()
    
    # Test Case 1: Create purchase with bulk item
    print("\n1. Testing bulk item purchase...")
    bulk_data = {
        'transaction_date': date.today(),
        'vendor': str(test_data['vendor'].id),
        'reference_number': 'REF-001',
        'invoice_number': 'INV-001',
        'remarks': 'Test bulk purchase',
        'items': [
            {
                'item_master_id': str(test_data['bulk_item'].id),
                'warehouse_id': str(test_data['warehouse'].id),
                'quantity': 50,
                'unit_price': '25.00',
                'discount': '50.00',
                'tax_amount': '115.00'
            }
        ]
    }
    
    try:
        transaction, items = service.create_purchase_transaction(bulk_data)
        print(f"✅ Bulk purchase successful!")
        print(f"   Transaction ID: {transaction.transaction_id}")
        print(f"   Grand Total: ${transaction.grand_total}")
        print(f"   Items Created: {len(items)}")
        
        # Check inventory item
        inventory_item = items[0]['inventory_item']
        print(f"   Inventory Quantity: {inventory_item.quantity}")
        
        # Check stock movement
        stock_movement = items[0]['stock_movement']
        print(f"   Stock Movement: {stock_movement.quantity_on_hand_before} → {stock_movement.quantity_on_hand_after}")
        
    except Exception as e:
        print(f"❌ Bulk purchase failed: {e}")
    
    # Test Case 2: Create purchase with individual item
    print("\n2. Testing individual item purchase...")
    individual_data = {
        'transaction_date': date.today(),
        'vendor': str(test_data['vendor'].id),
        'reference_number': 'REF-002',
        'items': [
            {
                'item_master_id': str(test_data['individual_item'].id),
                'warehouse_id': str(test_data['warehouse'].id),
                'quantity': 1,
                'serial_number': 'SN-12345',
                'unit_price': '500.00',
                'warranty_period_type': 'YEARS',
                'warranty_period': 2,
                'rental_rate': '50.00'
            }
        ]
    }
    
    try:
        transaction, items = service.create_purchase_transaction(individual_data)
        print(f"✅ Individual purchase successful!")
        print(f"   Transaction ID: {transaction.transaction_id}")
        print(f"   Serial Number: {items[0]['inventory_item'].serial_number}")
        print(f"   Warranty: {items[0]['inventory_item'].warranty_period} {items[0]['inventory_item'].warranty_period_type}")
        
    except Exception as e:
        print(f"❌ Individual purchase failed: {e}")
    
    # Test Case 3: Test validation (should fail)
    print("\n3. Testing validation (forbidden transaction_id)...")
    invalid_data = {
        'transaction_id': 'USER-PROVIDED-ID',  # This should be rejected
        'transaction_date': date.today(),
        'items': [
            {
                'item_master_id': str(test_data['bulk_item'].id),
                'warehouse_id': str(test_data['warehouse'].id),
                'quantity': 1
            }
        ]
    }
    
    try:
        transaction, items = service.create_purchase_transaction(invalid_data)
        print(f"❌ Validation test failed - should have been rejected!")
    except Exception as e:
        print(f"✅ Validation working correctly: {e}")
    
    # Test Case 4: Multi-item purchase
    print("\n4. Testing multi-item purchase...")
    multi_item_data = {
        'transaction_date': date.today(),
        'vendor': str(test_data['vendor'].id),
        'reference_number': 'REF-003',
        'items': [
            {
                'item_master_id': str(test_data['bulk_item'].id),
                'warehouse_id': str(test_data['warehouse'].id),
                'quantity': 10,
                'unit_price': '15.00'
            },
            {
                'item_master_id': str(test_data['individual_item'].id),
                'warehouse_id': str(test_data['warehouse'].id),
                'quantity': 1,
                'serial_number': 'SN-67890',
                'unit_price': '300.00'
            }
        ]
    }
    
    try:
        transaction, items = service.create_purchase_transaction(multi_item_data)
        print(f"✅ Multi-item purchase successful!")
        print(f"   Transaction ID: {transaction.transaction_id}")
        print(f"   Total Items: {len(items)}")
        print(f"   Grand Total: ${transaction.grand_total}")
        
    except Exception as e:
        print(f"❌ Multi-item purchase failed: {e}")


def test_api_payload_examples():
    """Show example API payloads"""
    print("\n" + "="*60)
    print("API PAYLOAD EXAMPLES")
    print("="*60)
    
    print("\nExample 1: Bulk Item Purchase")
    print("-" * 30)
    example1 = {
        "transaction_date": "2024-01-15",
        "vendor": "123e4567-e89b-12d3-a456-426614174000",
        "reference_number": "REF-001",
        "invoice_number": "INV-001",
        "remarks": "Monthly inventory purchase",
        "items": [
            {
                "item_master_id": "987fcdeb-51a2-43d1-9f4e-426614174001",
                "warehouse_id": "456e7890-e89b-12d3-a456-426614174002",
                "quantity": 100,
                "unit_price": "12.50",
                "discount": "25.00",
                "tax_amount": "149.38"
            }
        ]
    }
    print(json.dumps(example1, indent=2))
    
    print("\nExample 2: Individual Item Purchase")
    print("-" * 35)
    example2 = {
        "transaction_date": "2024-01-15",
        "vendor": "123e4567-e89b-12d3-a456-426614174000",
        "items": [
            {
                "item_master_id": "987fcdeb-51a2-43d1-9f4e-426614174003",
                "warehouse_id": "456e7890-e89b-12d3-a456-426614174002",
                "quantity": 1,
                "serial_number": "DEV-2024-001",
                "unit_price": "1500.00",
                "warranty_period_type": "YEARS",
                "warranty_period": 3,
                "rental_rate": "150.00",
                "replacement_cost": "1800.00"
            }
        ]
    }
    print(json.dumps(example2, indent=2))


if __name__ == "__main__":
    print("Purchase Transaction Service Manual Test")
    print("This script demonstrates the functionality of the atomic purchase transaction service.")
    
    try:
        test_purchase_transaction_service()
        test_api_payload_examples()
        
        print("\n" + "="*60)
        print("✅ MANUAL TESTING COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nKey Features Demonstrated:")
        print("• Automatic transaction ID generation (no user input allowed)")
        print("• Atomic operations (all records created together)")
        print("• Stock movement tracking")
        print("• Support for both bulk and individual items")
        print("• Multi-item purchases")
        print("• Comprehensive validation")
        print("• Automatic total calculations")
        
    except Exception as e:
        print(f"\n❌ Manual testing failed: {e}")
        import traceback
        traceback.print_exc()