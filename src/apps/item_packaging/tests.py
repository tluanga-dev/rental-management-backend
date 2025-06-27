from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import ItemPackaging

class ItemPackagingAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Authenticate the client with JWT token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        self.url = reverse('itempackaging-list')
        self.item1 = ItemPackaging.objects.create(name="Box", label="BX", unit="pcs", remarks="Cardboard box")
        self.item2 = ItemPackaging.objects.create(name="Bag", label="BG", unit="pcs", remarks="Plastic bag")
        self.item3 = ItemPackaging.objects.create(name="Crate", label="CR", unit="pcs", remarks="Wooden crate")

    def test_list_item_packaging(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 2)

    def test_pagination(self):
        response = self.client.get(self.url + '?page_size=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertIn('count', response.data)

    def test_filter_by_name(self):
        response = self.client.get(self.url + '?name=Box')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Box')

    def test_retrieve_item_packaging(self):
        detail_url = reverse('itempackaging-detail', args=[self.item1.id])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Box')

    def test_create_item_packaging(self):
        data = {"name": "Pallet", "label": "PL", "unit": "pcs", "remarks": "Wooden pallet"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ItemPackaging.objects.count(), 4)

    def test_update_item_packaging(self):
        detail_url = reverse('itempackaging-detail', args=[self.item1.id])
        data = {"name": "Box Updated", "label": "BXU", "unit": "pcs", "remarks": "Updated"}
        response = self.client.put(detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item1.refresh_from_db()
        self.assertEqual(self.item1.name, "Box Updated")
        self.assertEqual(self.item1.label, "BXU")

    def test_delete_item_packaging(self):
        detail_url = reverse('itempackaging-detail', args=[self.item1.id])
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ItemPackaging.objects.filter(id=self.item1.id).exists())
