from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.contenttypes.models import ContentType

from core.apps.contact_number.models import ContactNumber
from customer.models import Customer


class ContactNumberModelTest(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="Test Customer")
        self.content_type = ContentType.objects.get_for_model(Customer)

    def test_valid_phone_number_creation(self):
        # Test valid phone numbers
        valid_numbers = ["+1234567890", "1234567890", "+112345678901234"]
        for number in valid_numbers:
            with self.subTest(number=number):
                contact = ContactNumber(content_object=self.customer, number=number)
                contact.full_clean()  # Should not raise ValidationError
                contact.save()
                self.assertEqual(contact.number, number)

    def test_invalid_phone_number_raises_error(self):
        # Test invalid phone numbers
        invalid_numbers = ["invalid", "123-456-7890", "+1234abc567890"]
        for number in invalid_numbers:
            with self.subTest(number=number):
                contact = ContactNumber(content_object=self.customer, number=number)
                with self.assertRaises(ValidationError):
                    contact.full_clean()

    # Error occurs here, not during validation# Triggers field validation

    def test_same_number_allowed_for_different_customers(self):
        # Test same number can be added to different Customers
        customer2 = Customer.objects.create(name="Test Customer 2")
        ContactNumber.objects.create(content_object=self.customer, number="+1234567890")
        contact2 = ContactNumber(content_object=customer2, number="+1234567890")
        contact2.save()  # Should not raise an error
        self.assertEqual(ContactNumber.objects.count(), 2)

    def test_content_object_assignment(self):
        # Test ContactNumber correctly linked to Customer via GenericForeignKey
        contact = ContactNumber.objects.create(
            content_object=self.customer, number="+1234567890"
        )
        self.assertEqual(contact.content_object, self.customer)
        self.assertEqual(contact.content_type, self.content_type)
        self.assertEqual(
            contact.object_id, self.customer.id
        )  # Changed to compare UUID directly


class CustomerModelTest(TestCase):
    def test_customer_str_representation(self):
        customer = Customer.objects.create(name="Test Customer")
        self.assertEqual(str(customer), "Test Customer")

    def test_contact_numbers_generic_relation(self):
        customer = Customer.objects.create(name="Test Customer")
        contact = ContactNumber.objects.create(
            content_object=customer, number="+1234567890"
        )
        self.assertEqual(customer.contact_numbers.count(), 1)
        self.assertEqual(customer.contact_numbers.first().number, "+1234567890")

    def test_optional_fields_can_be_blank_or_null(self):
        # Test all optional fields can be omitted
        customer = Customer.objects.create(name="Test Customer")
        self.assertIsNone(customer.email)
        self.assertIsNone(customer.address)
        self.assertIsNone(customer.remarks)
        self.assertIsNone(customer.city)

    def test_optional_fields_can_be_populated(self):
        # Test optional fields can be set
        customer = Customer.objects.create(
            name="Test Customer",
            email="test@example.com",
            address="123 Main St",
            remarks="Regular client",
            city="Metropolis",
        )
        self.assertEqual(customer.email, "test@example.com")
        self.assertEqual(customer.address, "123 Main St")
        self.assertEqual(customer.remarks, "Regular client")
        self.assertEqual(customer.city, "Metropolis")

    def test_remarks_max_length_enforcement(self):
        # Test remarks field enforces max_length=255
        long_remarks = "A" * 256  # Exceeds 255 characters
        customer = Customer(name="Test Customer", remarks=long_remarks)
        with self.assertRaises(ValidationError):
            customer.full_clean()  # Now raises error with CharField

    def test_city_max_length_enforcement(self):
        # Test city field enforces max_length=255
        long_city = "A" * 256  # Exceeds 255 characters
        customer = Customer(name="Test Customer", city=long_city)
        with self.assertRaises(ValidationError):
            customer.full_clean()
