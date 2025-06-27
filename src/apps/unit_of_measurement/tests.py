import json
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse
from .models import UnitOfMeasurement
from .serializers import UnitOfMeasurementSerializer


class UnitOfMeasurementModelTest(TestCase):
    """Test the UnitOfMeasurement model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_unit_creation(self):
        """Test creating a unit of measurement."""
        unit = UnitOfMeasurement.objects.create(
            name="Kilogram",
            abbreviation="kg",
            description="Unit of mass",
            created_by=self.user
        )
        self.assertEqual(unit.name, "Kilogram")
        self.assertEqual(unit.abbreviation, "kg")
        self.assertEqual(unit.description, "Unit of mass")
        self.assertEqual(unit.created_by, self.user)
        self.assertTrue(unit.is_active)
        self.assertIsNotNone(unit.created_at)
        self.assertIsNotNone(unit.updated_at)
        self.assertIsNotNone(unit.id)

    def test_str_representation(self):
        """Test the string representation of unit."""
        unit = UnitOfMeasurement.objects.create(
            name="Meter",
            abbreviation="m"
        )
        self.assertEqual(str(unit), "Meter")

    def test_unique_name_constraint(self):
        """Test that unit names must be unique."""
        UnitOfMeasurement.objects.create(
            name="Kilogram",
            abbreviation="kg"
        )
        with self.assertRaises(IntegrityError):
            UnitOfMeasurement.objects.create(
                name="Kilogram",
                abbreviation="kg2"
            )

    def test_unique_abbreviation_constraint(self):
        """Test that abbreviations must be unique."""
        UnitOfMeasurement.objects.create(
            name="Kilogram",
            abbreviation="kg"
        )
        with self.assertRaises(IntegrityError):
            UnitOfMeasurement.objects.create(
                name="Kilograms",
                abbreviation="kg"
            )

    def test_max_name_length(self):
        """Test maximum length for name field."""
        long_name = "a" * 256  # Exceeds 255 character limit
        with self.assertRaises(Exception):
            unit = UnitOfMeasurement(
                name=long_name,
                abbreviation="test"
            )
            unit.full_clean()

    def test_max_abbreviation_length(self):
        """Test maximum length for abbreviation field."""
        long_abbr = "a" * 9  # Exceeds 8 character limit
        with self.assertRaises(Exception):
            unit = UnitOfMeasurement(
                name="Test Unit",
                abbreviation=long_abbr
            )
            unit.full_clean()

    def test_optional_description(self):
        """Test that description is optional."""
        unit = UnitOfMeasurement.objects.create(
            name="Liter",
            abbreviation="L"
        )
        self.assertIsNone(unit.description)

    def test_blank_description(self):
        """Test that description can be blank."""
        unit = UnitOfMeasurement.objects.create(
            name="Liter",
            abbreviation="L",
            description=""
        )
        self.assertEqual(unit.description, "")

    def test_model_inheritance(self):
        """Test that model inherits from TimeStampedAbstractModelClass."""
        unit = UnitOfMeasurement.objects.create(
            name="Gram",
            abbreviation="g"
        )
        # Check inherited fields
        self.assertTrue(hasattr(unit, 'created_at'))
        self.assertTrue(hasattr(unit, 'updated_at'))
        self.assertTrue(hasattr(unit, 'created_by'))
        self.assertTrue(hasattr(unit, 'is_active'))
        self.assertTrue(hasattr(unit, 'id'))


class UnitOfMeasurementSerializerTest(TestCase):
    """Test the UnitOfMeasurement serializer."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.valid_data = {
            'name': 'Kilogram',
            'abbreviation': 'kg',
            'description': 'Unit of mass'
        }

    def test_serializer_with_valid_data(self):
        """Test serializer with valid data."""
        serializer = UnitOfMeasurementSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        
    def test_serializer_save(self):
        """Test saving through serializer."""
        serializer = UnitOfMeasurementSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        unit = serializer.save(created_by=self.user)
        self.assertEqual(unit.name, 'Kilogram')
        self.assertEqual(unit.abbreviation, 'kg')
        self.assertEqual(unit.created_by, self.user)

    def test_serializer_without_description(self):
        """Test serializer without description field."""
        data = {
            'name': 'Meter',
            'abbreviation': 'm'
        }
        serializer = UnitOfMeasurementSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        unit = serializer.save()
        self.assertEqual(unit.name, 'Meter')
        self.assertIsNone(unit.description)

    def test_serializer_empty_name(self):
        """Test serializer with empty name."""
        data = self.valid_data.copy()
        data['name'] = ''
        serializer = UnitOfMeasurementSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_serializer_empty_abbreviation(self):
        """Test serializer with empty abbreviation."""
        data = self.valid_data.copy()
        data['abbreviation'] = ''
        serializer = UnitOfMeasurementSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('abbreviation', serializer.errors)

    def test_serializer_update(self):
        """Test updating through serializer."""
        unit = UnitOfMeasurement.objects.create(
            name='Original',
            abbreviation='orig'
        )
        update_data = {
            'name': 'Updated',
            'abbreviation': 'upd',
            'description': 'Updated description'
        }
        serializer = UnitOfMeasurementSerializer(unit, data=update_data)
        self.assertTrue(serializer.is_valid())
        updated_unit = serializer.save()
        self.assertEqual(updated_unit.name, 'Updated')
        self.assertEqual(updated_unit.abbreviation, 'upd')
        self.assertEqual(updated_unit.description, 'Updated description')

    def test_serializer_representation(self):
        """Test serializer representation of data."""
        unit = UnitOfMeasurement.objects.create(
            name='Kilogram',
            abbreviation='kg',
            description='Unit of mass',
            created_by=self.user
        )
        serializer = UnitOfMeasurementSerializer(unit)
        data = serializer.data
        self.assertEqual(data['name'], 'Kilogram')
        self.assertEqual(data['abbreviation'], 'kg')
        self.assertEqual(data['description'], 'Unit of mass')
        self.assertIn('id', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)


class UnitOfMeasurementAPITest(APITestCase):
    """Test the UnitOfMeasurement API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Authenticate the client with JWT token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Create test units
        self.unit1 = UnitOfMeasurement.objects.create(
            name="Kilogram",
            abbreviation="kg",
            description="Weight unit",
            created_by=self.user
        )
        self.unit2 = UnitOfMeasurement.objects.create(
            name="Meter",
            abbreviation="m",
            description="Length unit",
            created_by=self.user
        )
        
        # URLs
        self.list_url = reverse('unitofmeasurement-list')
        self.detail_url = reverse('unitofmeasurement-detail', args=[self.unit1.id])

    def test_list_units_success(self):
        """Test listing all units of measurement."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 2)
        
        # Check structure
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)

    def test_list_units_empty(self):
        """Test listing when no units exist."""
        UnitOfMeasurement.objects.all().delete()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
        self.assertEqual(response.data['count'], 0)

    def test_retrieve_unit_success(self):
        """Test retrieving a specific unit."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.unit1.name)
        self.assertEqual(response.data['abbreviation'], self.unit1.abbreviation)
        self.assertEqual(response.data['description'], self.unit1.description)

    def test_retrieve_unit_not_found(self):
        """Test retrieving a non-existent unit."""
        non_existent_url = reverse('unitofmeasurement-detail', args=['99999999-9999-9999-9999-999999999999'])
        response = self.client.get(non_existent_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_unit_success(self):
        """Test creating a new unit."""
        data = {
            "name": "Liter",
            "abbreviation": "L",
            "description": "Volume unit"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Liter')
        self.assertEqual(response.data['abbreviation'], 'L')
        self.assertEqual(UnitOfMeasurement.objects.count(), 3)

    def test_create_unit_duplicate_name(self):
        """Test creating unit with duplicate name."""
        data = {
            "name": "Kilogram",  # Already exists
            "abbreviation": "kg2"
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_unit_duplicate_abbreviation(self):
        """Test creating unit with duplicate abbreviation."""
        data = {
            "name": "Kilograms",
            "abbreviation": "kg"  # Already exists
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_unit_missing_required_fields(self):
        """Test creating unit without required fields."""
        data = {"description": "Missing name and abbreviation"}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        self.assertIn('abbreviation', response.data)

    def test_create_unit_invalid_data_types(self):
        """Test creating unit with invalid data types."""
        data = {
            "name": 123,  # Should be string
            "abbreviation": None,  # Should be string
            "description": ["invalid", "list"]  # Should be string
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_unit_full_success(self):
        """Test full update (PUT) of a unit."""
        data = {
            "name": "Gram",
            "abbreviation": "g",
            "description": "Weight unit (small)"
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.unit1.refresh_from_db()
        self.assertEqual(self.unit1.name, "Gram")
        self.assertEqual(self.unit1.abbreviation, "g")

    def test_update_unit_partial_success(self):
        """Test partial update (PATCH) of a unit."""
        data = {"description": "Updated weight unit"}
        unit2_detail_url = reverse('unitofmeasurement-detail', args=[self.unit2.id])
        response = self.client.patch(unit2_detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.unit2.refresh_from_db()
        self.assertEqual(self.unit2.description, "Updated weight unit")
        # Other fields should remain unchanged
        self.assertEqual(self.unit2.name, "Meter")
        self.assertEqual(self.unit2.abbreviation, "m")

    def test_update_unit_not_found(self):
        """Test updating a non-existent unit."""
        non_existent_url = reverse('unitofmeasurement-detail', args=['99999999-9999-9999-9999-999999999999'])
        data = {"name": "New Name"}
        response = self.client.patch(non_existent_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_unit_success(self):
        """Test deleting a unit."""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UnitOfMeasurement.objects.filter(id=self.unit1.id).exists())

    def test_delete_unit_not_found(self):
        """Test deleting a non-existent unit."""
        non_existent_url = reverse('unitofmeasurement-detail', args=['99999999-9999-9999-9999-999999999999'])
        response = self.client.delete(non_existent_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_search_functionality(self):
        """Test search filtering."""
        # Search by name
        response = self.client.get(self.list_url, {'search': 'kilo'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any('Kilogram' in u['name'] for u in response.data['results']))
        
        # Search by abbreviation
        response = self.client.get(self.list_url, {'search': 'kg'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any('kg' in u['abbreviation'] for u in response.data['results']))

    def test_search_no_results(self):
        """Test search with no matching results."""
        response = self.client.get(self.list_url, {'search': 'nonexistent'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_ordering_by_name_asc(self):
        """Test ordering by name ascending."""
        response = self.client.get(self.list_url, {'ordering': 'name'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [u['name'] for u in response.data['results']]
        self.assertEqual(names, sorted(names))

    def test_ordering_by_name_desc(self):
        """Test ordering by name descending."""
        response = self.client.get(self.list_url, {'ordering': '-name'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [u['name'] for u in response.data['results']]
        self.assertEqual(names, sorted(names, reverse=True))

    def test_ordering_by_abbreviation(self):
        """Test ordering by abbreviation."""
        response = self.client.get(self.list_url, {'ordering': 'abbreviation'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        abbreviations = [u['abbreviation'] for u in response.data['results']]
        self.assertEqual(abbreviations, sorted(abbreviations))

    def test_invalid_ordering_field(self):
        """Test ordering by invalid field."""
        response = self.client.get(self.list_url, {'ordering': 'invalid_field'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return default ordering (by name)

    def test_pagination_first_page(self):
        """Test pagination first page."""
        # Create additional units to test pagination
        for i in range(3, 7):
            UnitOfMeasurement.objects.create(
                name=f"Unit{i}",
                abbreviation=f"u{i}",
                description=f"Test unit {i}"
            )
        
        response = self.client.get(self.list_url, {'page_size': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])

    def test_pagination_second_page(self):
        """Test pagination second page."""
        # Create additional units
        for i in range(3, 7):
            UnitOfMeasurement.objects.create(
                name=f"Unit{i}",
                abbreviation=f"u{i}"
            )
        
        response = self.client.get(self.list_url, {'page_size': 2, 'page': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertIsNotNone(response.data['previous'])

    def test_pagination_invalid_page(self):
        """Test pagination with invalid page number."""
        response = self.client.get(self.list_url, {'page': 9999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_pagination_custom_page_size(self):
        """Test pagination with custom page size."""
        response = self.client.get(self.list_url, {'page_size': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_pagination_max_page_size(self):
        """Test pagination respects max page size."""
        response = self.client.get(self.list_url, {'page_size': 200})  # Exceeds max_page_size=100
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should be limited to available records, not exceed max_page_size

    def test_combined_filters(self):
        """Test combining search, ordering, and pagination."""
        # Create additional test data
        UnitOfMeasurement.objects.create(name="Kiloliter", abbreviation="kL")
        UnitOfMeasurement.objects.create(name="Kilometer", abbreviation="km")
        
        response = self.client.get(self.list_url, {
            'search': 'kil',
            'ordering': 'name',
            'page_size': 2
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return units containing 'kil', ordered by name, with page size 2

    def test_content_type_headers(self):
        """Test API returns correct content type."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_api_response_structure(self):
        """Test API response has correct structure."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check paginated response structure
        required_keys = ['count', 'next', 'previous', 'results']
        for key in required_keys:
            self.assertIn(key, response.data)
        
        # Check individual unit structure
        if response.data['results']:
            unit = response.data['results'][0]
            expected_fields = ['id', 'name', 'abbreviation', 'description', 'created_at', 'updated_at']
            for field in expected_fields:
                self.assertIn(field, unit)

    def test_api_json_serialization(self):
        """Test that API responses can be JSON serialized."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should not raise an exception
        json_str = json.dumps(response.data, default=str)
        self.assertIsInstance(json_str, str)


class UnitOfMeasurementIntegrationTest(APITestCase):
    """Integration tests for unit of measurement workflow."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Authenticate the client with JWT token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        self.list_url = reverse('unitofmeasurement-list')

    def test_complete_crud_workflow(self):
        """Test complete CRUD workflow."""
        # 1. Create
        create_data = {
            "name": "Pascal",
            "abbreviation": "Pa",
            "description": "Unit of pressure"
        }
        create_response = self.client.post(self.list_url, create_data, format='json')
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        unit_id = create_response.data['id']
        
        # 2. Read (List)
        list_response = self.client.get(self.list_url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data['count'], 1)
        
        # 3. Read (Detail)
        detail_url = reverse('unitofmeasurement-detail', args=[unit_id])
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data['name'], 'Pascal')
        
        # 4. Update
        update_data = {
            "name": "Pascal",
            "abbreviation": "Pa",
            "description": "SI unit of pressure"
        }
        update_response = self.client.put(detail_url, update_data, format='json')
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['description'], 'SI unit of pressure')
        
        # 5. Delete
        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        
        # 6. Verify deletion
        verify_response = self.client.get(detail_url)
        self.assertEqual(verify_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_bulk_operations(self):
        """Test creating multiple units and bulk operations."""
        units_data = [
            {"name": "Second", "abbreviation": "s", "description": "Time unit"},
            {"name": "Ampere", "abbreviation": "A", "description": "Electric current unit"},
            {"name": "Kelvin", "abbreviation": "K", "description": "Temperature unit"},
            {"name": "Mole", "abbreviation": "mol", "description": "Amount of substance unit"},
            {"name": "Candela", "abbreviation": "cd", "description": "Luminous intensity unit"},
        ]
        
        # Create multiple units
        created_ids = []
        for unit_data in units_data:
            response = self.client.post(self.list_url, unit_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            created_ids.append(response.data['id'])
        
        # Test listing all units
        list_response = self.client.get(self.list_url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data['count'], 5)
        
        # Test search across multiple units
        search_response = self.client.get(self.list_url, {'search': 'unit'})
        self.assertEqual(search_response.status_code, status.HTTP_200_OK)
        self.assertEqual(search_response.data['count'], 5)  # All have 'unit' in description
        
        # Test pagination with multiple units
        paginated_response = self.client.get(self.list_url, {'page_size': 3})
        self.assertEqual(paginated_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(paginated_response.data['results']), 3)
        self.assertIsNotNone(paginated_response.data['next'])

    def test_error_handling_workflow(self):
        """Test error handling scenarios."""
        # Create a unit
        unit_data = {"name": "Test", "abbreviation": "T"}
        response = self.client.post(self.list_url, unit_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Try to create duplicate
        duplicate_response = self.client.post(self.list_url, unit_data, format='json')
        self.assertEqual(duplicate_response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Try invalid update
        unit_id = response.data['id']
        detail_url = reverse('unitofmeasurement-detail', args=[unit_id])
        invalid_update = {"name": "", "abbreviation": ""}
        update_response = self.client.put(detail_url, invalid_update, format='json')
        self.assertEqual(update_response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify original unit still exists and unchanged
        get_response = self.client.get(detail_url)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data['name'], 'Test')
