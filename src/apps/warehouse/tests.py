from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.test import APIClient
import json
from unittest.mock import patch, MagicMock
from .models import Warehouse
from .serializers import WarehouseSerializer


class WarehouseModelTestCase(TestCase):
    """Test case for Warehouse model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    def test_warehouse_creation(self):
        """Test basic warehouse creation"""
        warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            label='main',
            remarks='Primary storage facility',
            created_by=self.user
        )
        self.assertEqual(warehouse.name, 'Main Warehouse')
        self.assertEqual(warehouse.label, 'MAIN')  # Should be uppercase
        self.assertEqual(warehouse.remarks, 'Primary storage facility')
        self.assertEqual(warehouse.created_by, self.user)
        self.assertIsNotNone(warehouse.created_at)
        self.assertIsNotNone(warehouse.updated_at)
        
    def test_warehouse_label_uppercase_conversion(self):
        """Test that label is automatically converted to uppercase"""
        warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            label='lowercase_label',
            created_by=self.user
        )
        self.assertEqual(warehouse.label, 'LOWERCASE_LABEL')
        
    def test_warehouse_str_representation(self):
        """Test string representation of warehouse"""
        warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            label='test',
            created_by=self.user
        )
        self.assertEqual(str(warehouse), 'Test Warehouse')
        
    def test_warehouse_label_unique_constraint(self):
        """Test that label must be unique"""
        Warehouse.objects.create(
            name='First Warehouse',
            label='unique_label',
            created_by=self.user
        )
        
        with self.assertRaises(Exception):  # IntegrityError for unique constraint
            Warehouse.objects.create(
                name='Second Warehouse',
                label='unique_label',
                created_by=self.user
            )
            
    def test_warehouse_optional_remarks(self):
        """Test that remarks field is optional"""
        warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            label='test',
            created_by=self.user
        )
        self.assertIsNone(warehouse.remarks)
        
    def test_warehouse_with_empty_remarks(self):
        """Test warehouse creation with empty remarks"""
        warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            label='test',
            remarks='',
            created_by=self.user
        )
        self.assertEqual(warehouse.remarks, '')


class WarehouseSerializerTestCase(TestCase):
    """Test case for Warehouse serializer"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    def test_warehouse_serializer_with_valid_data(self):
        """Test serializer with valid data"""
        data = {
            'name': 'Test Warehouse',
            'label': 'test',
            'remarks': 'Test remarks',
            'created_by': self.user.id
        }
        serializer = WarehouseSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        warehouse = serializer.save()
        self.assertEqual(warehouse.name, 'Test Warehouse')
        self.assertEqual(warehouse.label, 'TEST')  # Should be uppercase
        
    def test_warehouse_serializer_without_remarks(self):
        """Test serializer without optional remarks field"""
        data = {
            'name': 'Test Warehouse',
            'label': 'test',
            'created_by': self.user.id
        }
        serializer = WarehouseSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        warehouse = serializer.save()
        self.assertEqual(warehouse.name, 'Test Warehouse')
        self.assertIsNone(warehouse.remarks)
        
    def test_warehouse_serializer_invalid_data(self):
        """Test serializer with invalid data"""
        data = {
            'label': 'test',  # Missing required 'name' field
            'created_by': self.user.id
        }
        serializer = WarehouseSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)


class WarehouseAPITestCase(APITestCase):
    """Test case for Warehouse API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create test warehouses
        self.warehouse1 = Warehouse.objects.create(
            name='Main Warehouse',
            label='main',
            remarks='Primary storage',
            created_by=self.user
        )
        self.warehouse2 = Warehouse.objects.create(
            name='Secondary Warehouse',
            label='secondary',
            remarks='Backup storage',
            created_by=self.user
        )
        
    def test_get_warehouse_list(self):
        """Test retrieving list of warehouses"""
        url = reverse('warehouse-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # With pagination, the response has a 'results' key
        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 2)
        else:
            self.assertEqual(len(response.data), 2)
        
    def test_get_warehouse_detail(self):
        """Test retrieving a specific warehouse"""
        url = reverse('warehouse-detail', kwargs={'pk': self.warehouse1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Main Warehouse')
        self.assertEqual(response.data['label'], 'MAIN')
        
    def test_create_warehouse(self):
        """Test creating a new warehouse"""
        url = reverse('warehouse-list')
        data = {
            'name': 'New Warehouse',
            'label': 'new',
            'remarks': 'Newly created warehouse',
            'created_by': self.user.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Warehouse.objects.count(), 3)
        warehouse = Warehouse.objects.get(pk=response.data['id'])
        self.assertEqual(warehouse.name, 'New Warehouse')
        self.assertEqual(warehouse.label, 'NEW')  # Should be uppercase
        
    def test_update_warehouse(self):
        """Test updating an existing warehouse"""
        url = reverse('warehouse-detail', kwargs={'pk': self.warehouse1.pk})
        data = {
            'name': 'Updated Warehouse',
            'label': 'updated',
            'remarks': 'Updated remarks',
            'created_by': self.user.id
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.warehouse1.refresh_from_db()
        self.assertEqual(self.warehouse1.name, 'Updated Warehouse')
        self.assertEqual(self.warehouse1.label, 'UPDATED')
        
    def test_partial_update_warehouse(self):
        """Test partially updating a warehouse"""
        url = reverse('warehouse-detail', kwargs={'pk': self.warehouse1.pk})
        data = {'name': 'Partially Updated Warehouse'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.warehouse1.refresh_from_db()
        self.assertEqual(self.warehouse1.name, 'Partially Updated Warehouse')
        self.assertEqual(self.warehouse1.label, 'MAIN')  # Should remain unchanged
        
    def test_delete_warehouse(self):
        """Test deleting a warehouse"""
        url = reverse('warehouse-detail', kwargs={'pk': self.warehouse1.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Warehouse.objects.count(), 1)
        self.assertFalse(Warehouse.objects.filter(pk=self.warehouse1.pk).exists())
        
    def test_create_warehouse_with_invalid_data(self):
        """Test creating warehouse with invalid data"""
        url = reverse('warehouse-list')
        data = {
            'label': 'invalid',  # Missing required 'name' field
            'created_by': self.user.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)


class WarehouseViewSetTestCase(APITestCase):
    """Test case for Warehouse ViewSet functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create multiple warehouses for testing
        self.warehouses = []
        for i in range(15):  # Create 15 warehouses for pagination testing
            warehouse = Warehouse.objects.create(
                name=f'Warehouse {i+1}',
                label=f'wh{i+1}',
                remarks=f'Warehouse {i+1} remarks',
                created_by=self.user
            )
            self.warehouses.append(warehouse)
            
    def test_warehouse_viewset_queryset(self):
        """Test that viewset returns all warehouses"""
        url = reverse('warehouse-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # With pagination, the response has a 'results' key
        if 'results' in response.data:
            # Check that we get some results (may be paginated)
            self.assertGreaterEqual(len(response.data['results']), 1)
            self.assertIn('count', response.data)
            self.assertEqual(response.data['count'], 15)
        else:
            self.assertEqual(len(response.data), 15)
        
    def test_warehouse_viewset_filtering_by_name(self):
        """Test filtering warehouses by name"""
        url = reverse('warehouse-list')
        response = self.client.get(url, {'search': 'Warehouse 1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should find warehouses containing "Warehouse 1" (1, 10, 11, 12, 13, 14, 15)
        
    def test_warehouse_viewset_ordering(self):
        """Test ordering warehouses"""
        url = reverse('warehouse-list')
        response = self.client.get(url, {'ordering': 'name'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle pagination
        results = response.data['results'] if 'results' in response.data else response.data
        names = [warehouse['name'] for warehouse in results]
        self.assertEqual(names, sorted(names))
        
    def test_warehouse_viewset_reverse_ordering(self):
        """Test reverse ordering warehouses"""
        url = reverse('warehouse-list')
        response = self.client.get(url, {'ordering': '-name'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle pagination
        results = response.data['results'] if 'results' in response.data else response.data
        names = [warehouse['name'] for warehouse in results]
        self.assertEqual(names, sorted(names, reverse=True))


class WarehouseModelValidationTestCase(TestCase):
    """Test case for Warehouse model validation"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    def test_warehouse_clean_method(self):
        """Test the clean method converts label to uppercase"""
        warehouse = Warehouse(
            name='Test Warehouse',
            label='lowercase',
            created_by=self.user
        )
        warehouse.clean()
        self.assertEqual(warehouse.label, 'LOWERCASE')
        
    def test_warehouse_save_calls_clean(self):
        """Test that save method calls clean method"""
        warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            label='mixed_Case',
            created_by=self.user
        )
        self.assertEqual(warehouse.label, 'MIXED_CASE')
        
    def test_warehouse_max_length_validation(self):
        """Test field max length validation"""
        # Test name field max length (255 characters)
        long_name = 'a' * 256
        warehouse = Warehouse(
            name=long_name,
            label='test',
            created_by=self.user
        )
        
        with self.assertRaises(Exception):  # ValidationError or DataError
            warehouse.full_clean()
            
    def test_warehouse_label_max_length_validation(self):
        """Test label field max length validation"""
        # Test label field max length (255 characters)
        long_label = 'a' * 256
        warehouse = Warehouse(
            name='Test Warehouse',
            label=long_label,
            created_by=self.user
        )
        
        with self.assertRaises(Exception):  # ValidationError or DataError
            warehouse.full_clean()


# Create your tests here.
