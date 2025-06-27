from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.purchase.models import PurchaseTransaction
from apps.inventory_item.models import (
    InventoryItemMaster, 
    InventoryItemStockMovement,
    TrackingType
)
from apps.warehouse.models import Warehouse
from apps.vendor.models import Vendor
from apps.item_category.models import ItemCategory, ItemSubCategory
from apps.unit_of_measurement.models import UnitOfMeasurement
from apps.item_packaging.models import ItemPackaging

User = get_user_model()


class PurchaseTransactionAPITestCase(TestCase):
    """
    Test cases for Purchase Transaction API endpoints
    """
    
    def setUp(self):
        """
        Set up test data and client
        """
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create warehouse
        self.warehouse = Warehouse.objects.create(
            name="Test Warehouse",
            label="TEST"
        )
        
        # Create vendor
        self.vendor = Vendor.objects.create(
            name="API Test Vendor",
            email="apivendor@test.com"
        )
        
        # Create category and subcategory
        self.category = ItemCategory.objects.create(
            name="API Test Category"
        )
        self.subcategory = ItemSubCategory.objects.create(
            name="API Test Subcategory",
            item_category=self.category
        )
        
        # Create unit of measurement
        self.unit = UnitOfMeasurement.objects.create(
            name="Unit",
            abbreviation="u"
        )
        
        # Create packaging
        self.packaging = ItemPackaging.objects.create(
            name="Package"
        )
        
        # Create item master
        self.item_master = InventoryItemMaster.objects.create(
            name="API Test Item",
            sku="API-001",
            item_sub_category=self.subcategory,
            unit_of_measurement=self.unit,
            packaging=self.packaging,
            tracking_type=TrackingType.BULK
        )
    
    def test_create_purchase_transaction_success(self):
        """
        Test successful creation of purchase transaction via API
        """
        data = {
            'transaction_date': str(date.today()),
            'vendor': str(self.vendor.id),
            'reference_number': 'API-REF-001',
            'invoice_number': 'API-INV-001',
            'remarks': 'API test purchase',
            'items': [
                {
                    'item_master_id': str(self.item_master.id),
                    'warehouse_id': str(self.warehouse.id),
                    'quantity': 20,
                    'unit_price': '50.00',
                    'discount': '5.00',
                    'tax_amount': '47.50'
                }
            ]
        }
        
        response = self.client.post('/api/purchases/transactions/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify response data
        response_data = response.json()
        self.assertIn('transaction_id', response_data)
        self.assertTrue(response_data['transaction_id'].startswith('PUR-'))
        self.assertEqual(response_data['vendor'], str(self.vendor.id))
        self.assertEqual(response_data['reference_number'], 'API-REF-001')
        
        # Verify transaction items
        self.assertIn('transaction_items', response_data)
        self.assertEqual(len(response_data['transaction_items']), 1)
        
        # Verify totals
        self.assertEqual(Decimal(response_data['total_amount']), Decimal('995.00'))
        self.assertEqual(Decimal(response_data['total_tax_amount']), Decimal('47.50'))
        self.assertEqual(Decimal(response_data['grand_total']), Decimal('1042.50'))
        
        # Verify database records
        transaction = PurchaseTransaction.objects.get(transaction_id=response_data['transaction_id'])
        self.assertEqual(transaction.transaction_items.count(), 1)
        
        # Verify stock movement was created
        movements = InventoryItemStockMovement.objects.filter(
            inventory_transaction_id=response_data['transaction_id']
        )
        self.assertEqual(movements.count(), 1)
    
    def test_create_purchase_transaction_with_forbidden_fields(self):
        """
        Test that forbidden fields are rejected
        """
        data = {
            'transaction_id': 'USER-123',  # Forbidden field
            'transaction_date': str(date.today()),
            'items': [{
                'item_master_id': str(self.item_master.id),
                'warehouse_id': str(self.warehouse.id),
                'quantity': 1
            }]
        }
        
        response = self.client.post('/api/purchases/transactions/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # The error is nested in the response
        error_msg = str(response.json())
        self.assertIn('forbidden fields', error_msg.lower())
    
    def test_create_purchase_transaction_without_items(self):
        """
        Test that transaction without items is rejected
        """
        data = {
            'transaction_date': str(date.today()),
            'vendor': self.vendor.id,
            'items': []
        }
        
        response = self.client.post('/api/purchases/transactions/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('at least one item', response.json()['items'][0].lower())
    
    def test_create_purchase_transaction_invalid_item_master(self):
        """
        Test that invalid item master is rejected
        """
        data = {
            'transaction_date': str(date.today()),
            'items': [{
                'item_master_id': '00000000-0000-0000-0000-000000000099',  # Non-existent UUID
                'warehouse_id': str(self.warehouse.id),
                'quantity': 1
            }]
        }
        
        response = self.client.post('/api/purchases/transactions/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # The error is a DRF validation error in the format {"items": "error message"}
        error_msg = str(response.json())
        self.assertIn('invalid item_master_id', error_msg.lower())
    
    
    def test_list_purchase_transactions(self):
        """
        Test listing purchase transactions
        """
        # Create a transaction using the service
        from apps.purchase.services import PurchaseTransactionService
        service = PurchaseTransactionService()
        
        data = {
            'transaction_date': date.today(),
            'vendor': str(self.vendor.id),
            'items': [{
                'item_master_id': str(self.item_master.id),
                'warehouse_id': str(self.warehouse.id),
                'quantity': 10,
                'unit_price': '25.00'
            }]
        }
        
        service.create_purchase_transaction(data)
        
        # List transactions
        response = self.client.get('/api/purchases/transactions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.json())
        self.assertGreater(len(response.json()['results']), 0)
    
    def test_retrieve_purchase_transaction_detail(self):
        """
        Test retrieving detailed purchase transaction
        """
        # Create a transaction
        from apps.purchase.services import PurchaseTransactionService
        service = PurchaseTransactionService()
        
        data = {
            'transaction_date': date.today(),
            'items': [{
                'item_master_id': str(self.item_master.id),
                'warehouse_id': str(self.warehouse.id),
                'quantity': 15,
                'unit_price': '30.00'
            }]
        }
        
        transaction, _ = service.create_purchase_transaction(data)
        
        # Retrieve transaction detail
        response = self.client.get(f'/api/purchases/transactions/{transaction.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        # Should include transaction items
        self.assertIn('transaction_items', response_data)
        self.assertEqual(len(response_data['transaction_items']), 1)
        self.assertEqual(response_data['transaction_items'][0]['quantity'], 15)
    
    def test_unauthenticated_access_denied(self):
        """
        Test that unauthenticated access is denied
        """
        self.client.force_authenticate(user=None)
        
        response = self.client.get('/api/purchases/transactions/')
        
        # JWT returns 403 for unauthenticated requests to protected endpoints
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])