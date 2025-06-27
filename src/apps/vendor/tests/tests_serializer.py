from django.test import TestCase
from rest_framework.exceptions import ValidationError
from vendor.models import Vendor
from vendor.serializers import VendorSerializer
from core.apps.contact_number.models import ContactNumber


class VendorSerializerTest(TestCase):
    def setUp(self):
        self.valid_data = {
            "name": "Test Vendor",
            "email": "valid@example.com",
            "address": "123 Test St",
            "remarks": "Test remarks",
            "contact_numbers": [{"number": "+1234567890"}, {"number": "+0987654321"}],
        }

    def test_valid_serializer(self):
        serializer = VendorSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

        vendor = serializer.save()
        self.assertEqual(vendor.name, "Test Vendor")
        self.assertEqual(vendor.contact_numbers.count(), 2)

    def test_missing_required_fields(self):
        invalid_data = {
            "email": "invalid-email",
            "contact_numbers": [{"number": "invalid"}],
        }
        serializer = VendorSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)
        self.assertIn("email", serializer.errors)
        self.assertIn("contact_numbers", serializer.errors)

    def test_invalid_contact_numbers(self):
        invalid_data = self.valid_data.copy()
        invalid_data["contact_numbers"] = [{"number": "invalid"}]

        serializer = VendorSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("contact_numbers", serializer.errors)

    def test_update_contact_numbers(self):
        # Create initial vendor
        vendor = Vendor.objects.create(name="Original Vendor")
        contact_number = ContactNumber.objects.create(
            content_object=vendor, number="+1111111111"
        )

        update_data = {
            "name": "Updated Vendor",
            "contact_numbers": [
                {"id": str(contact_number.id), "number": "+2222222222"},
                {"number": "+3333333333"},
            ],
        }

        serializer = VendorSerializer(vendor, data=update_data)
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()

        self.assertEqual(updated.name, "Updated Vendor")
        self.assertEqual(updated.contact_numbers.count(), 2)
        self.assertEqual(updated.contact_numbers.first().number, "+2222222222")

    def test_empty_contact_numbers(self):
        invalid_data = self.valid_data.copy()
        invalid_data["contact_numbers"] = []

        serializer = VendorSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("contact_numbers", serializer.errors)

    def test_remove_contact_numbers_on_update(self):
        vendor = Vendor.objects.create(name="Test Vendor")
        number = ContactNumber.objects.create(
            content_object=vendor, number="+1111111111"
        )

        update_data = {"name": "Updated Vendor", "contact_numbers": []}

        serializer = VendorSerializer(vendor, data=update_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("contact_numbers", serializer.errors)

    def test_serializer_output(self):
        vendor = Vendor.objects.create(name="Test Vendor")
        contact_number = ContactNumber.objects.create(
            content_object=vendor, number="+1234567890"
        )

        serializer = VendorSerializer(vendor)
        expected_data = {
            "id": str(vendor.id),
            "name": "Test Vendor",
            "email": None,
            "address": None,
            "remarks": None,
            "city": None,
            "is_active": True,
            "contact_numbers": [{"id": contact_number.id, "number": "+1234567890"}],
            "created_at": vendor.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "updated_at": vendor.updated_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }
        self.assertEqual(serializer.data, expected_data)
