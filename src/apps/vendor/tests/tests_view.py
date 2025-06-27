from vendor.models import Vendor
from core.apps.contact_number.models import ContactNumber
from vendor.serializers import VendorSerializer
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse


class VendorViewSetTest(APITestCase):
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
        
        self.vendor1 = Vendor.objects.create(
            name="Vendor One",
            email="vendor1@example.com",
            address="123 Street",
            remarks="First vendor",
            is_active=True,
        )
        ContactNumber.objects.create(content_object=self.vendor1, number="1234567890")

        self.vendor2 = Vendor.objects.create(
            name="Vendor Two",
            email="vendor2@example.com",
            address="456 Avenue",
            remarks="Second vendor",
            is_active=False,
        )
        ContactNumber.objects.create(content_object=self.vendor2, number="0987654321")
        self.url = reverse("vendor-list")

    def test_list_vendors(self):
        response = self.client.get(self.url)
        vendors = Vendor.objects.all().order_by("-created_at")  # Updated ordering
        serializer = VendorSerializer(vendors, many=True)
        expected_results = [
            {
                "name": vendor["name"],
                "email": vendor["email"],
                "address": vendor["address"],
                "remarks": vendor["remarks"],
                "is_active": vendor["is_active"],
                "contact_numbers": vendor["contact_numbers"],
            }
            for vendor in serializer.data
        ]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], vendors.count())
        for actual, expected in zip(response.data["results"], expected_results):
            self.assertEqual(actual["name"], expected["name"])
            self.assertEqual(actual["email"], expected["email"])
            self.assertEqual(actual["address"], expected["address"])
            self.assertEqual(actual["remarks"], expected["remarks"])
            self.assertEqual(actual["is_active"], expected["is_active"])
            self.assertEqual(actual["contact_numbers"], expected["contact_numbers"])

    def test_filter_vendors_by_name(self):
        response = self.client.get(self.url, {"name": "Vendor One"})
        vendors = Vendor.objects.filter(name__icontains="Vendor One")
        serializer = VendorSerializer(vendors, many=True)
        expected_data = {
            "count": vendors.count(),
            "next": None,
            "previous": None,
            "results": serializer.data,
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)

    def test_pagination(self):
        # Create additional vendors to test pagination
        for i in range(10):
            Vendor.objects.create(
                name=f"Vendor {i+3}",
                email=f"vendor{i+3}@example.com",
                address=f"{i+3} Street",
                remarks=f"Vendor {i+3}",
                is_active=True,
            )
        response = self.client.get(self.url + "?page_size=2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)  # page_size is 2
        self.assertIsNotNone(response.data["next"])

    def test_filter_vendors_by_is_active(self):
        response = self.client.get(self.url, {"is_active": True})
        vendors = Vendor.objects.filter(is_active=True)
        serializer = VendorSerializer(vendors, many=True)
        expected_data = {
            "count": vendors.count(),
            "next": None,
            "previous": None,
            "results": serializer.data,
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)
