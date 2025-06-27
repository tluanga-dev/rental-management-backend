from django.test import TestCase
from core.apps.contact_number.models import ContactNumber
from vendor.models import Vendor
from django.contrib.contenttypes.models import ContentType


class VendorModelTest(TestCase):
    def setUp(self):
        # Create a Vendor instance
        self.vendor = Vendor.objects.create(
            name="Test Vendor",
            email="test@vendor.com",
            address="123 Test Street",
            remarks="Test remarks",
            city="Test City",
        )
        # Create a ContactNumber instance linked to the Vendor
        contact_number = ContactNumber.objects.create(
            number="+1234567890",
            content_type=ContentType.objects.get_for_model(Vendor),
            object_id=self.vendor.id,
        )
        # Use the set() method to associate the contact number
        self.vendor.contact_numbers.set([contact_number])

    def test_vendor_contact_number_association(self):
        """Test that the Vendor is correctly associated with the ContactNumber."""
        self.assertEqual(self.vendor.contact_numbers.count(), 1)
        self.assertEqual(self.vendor.contact_numbers.first().number, "+1234567890")

    def test_vendor_str_representation(self):
        """Test the string representation of the Vendor model."""
        self.assertEqual(str(self.vendor), "Test Vendor")

    def test_vendor_email_validation(self):
        """Test that the Vendor email is valid."""
        self.assertEqual(self.vendor.email, "test@vendor.com")
        self.assertIn("@", self.vendor.email)

    def test_vendor_address(self):
        """Test that the Vendor address is stored correctly."""
        self.assertEqual(self.vendor.address, "123 Test Street")

    def test_vendor_city(self):
        """Test that the Vendor city is stored correctly."""
        self.assertEqual(self.vendor.city, "Test City")

    def test_vendor_remarks(self):
        """Test that the Vendor remarks are stored correctly."""
        self.assertEqual(self.vendor.remarks, "Test remarks")

    def test_vendor_multiple_contact_numbers(self):
        """Test that a Vendor can have multiple contact numbers."""
        contact_number_2 = ContactNumber.objects.create(
            number="+9876543210",
            content_type=ContentType.objects.get_for_model(Vendor),
            object_id=self.vendor.id,
        )
        self.vendor.contact_numbers.add(contact_number_2)
        self.assertEqual(self.vendor.contact_numbers.count(), 2)
        self.assertIn(
            "+9876543210", [cn.number for cn in self.vendor.contact_numbers.all()]
        )
