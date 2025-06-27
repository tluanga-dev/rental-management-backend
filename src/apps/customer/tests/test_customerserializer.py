import unittest
from customer.serializers import (
    CustomerSerializer,
)  # ...adjust import as needed...


class TestCustomerSerializer(unittest.TestCase):
    def setUp(self):
        self.valid_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            # ...other required fields...
        }
        self.extra_data = {
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "extra_field": "unexpected",
            # ...other required fields...
        }

    def test_customer_serializer_valid_data(self):
        serializer = CustomerSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.data.get("name"), self.valid_data["name"])

    def test_customer_serializer_invalid_data(self):
        invalid_data = {
            "email": "invalid@example.com",
        }
        serializer = CustomerSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_customer_serializer_extra_fields(self):
        serializer = CustomerSerializer(data=self.extra_data)
        if serializer.is_valid():
            self.assertNotIn("extra_field", serializer.data)
        else:
            self.assertIn("extra_field", serializer.errors)

    def test_customer_serializer_error_messages(self):
        invalid_data = {
            "name": "",
            "email": "invalid-email-format",
        }
        serializer = CustomerSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)
        self.assertIn("email", serializer.errors)


if __name__ == "__main__":
    unittest.main()
