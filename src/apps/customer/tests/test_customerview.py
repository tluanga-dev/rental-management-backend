from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from customer.models import Customer  # ...adjust import as needed...

User = get_user_model()

class TestCustomerView(APITestCase):
    def setUp(self):
        # Create test user for authentication
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        
        # Get JWT token for the user
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        
        # Set authentication header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # ...existing setup code...
        self.customer1 = Customer.objects.create(
            name="John Doe",
            email="john.doe@example.com",
            # ...other required fields...
        )
        self.customer2 = Customer.objects.create(
            name="Jane Smith",
            email="jane.smith@example.com",
            # ...other required fields...
        )
        self.list_url = reverse("customer-list")  # adjust URL name if needed
        self.detail_url = reverse("customer-detail", kwargs={"pk": self.customer1.pk})

    def test_get_customer_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # ...assertions for list content, e.g. check returned count...

    def test_create_customer(self):
        data = {
            "name": "Alice Johnson",
            "email": "alice.johnson@example.com",
            # ...other required fields...
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # ...assertions for new customer content...

    def test_get_customer_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # ...assertions for detail fields (e.g. name, email)...

    def test_update_customer(self):
        data = {
            "name": "John Doe Updated",
            # ...other fields to update...
        }
        response = self.client.patch(self.detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # ...assertions to check updated fields...

    def test_delete_customer(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Customer.objects.filter(pk=self.customer1.pk).exists())
