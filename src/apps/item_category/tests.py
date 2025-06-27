from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from item_category.models import ItemCategory, ItemSubCategory
from item_category.serializers import ItemCategorySerializer, ItemSubCategorySerializer

class ItemCategoryModelTest(TestCase):
    def setUp(self):
        self.category = ItemCategory.objects.create(
            name="Electronics", abbreviation="ELEC01", description="Electronic items"
        )

    def test_str(self):
        self.assertEqual(str(self.category), "Electronics")

    def test_unique_name(self):
        with self.assertRaises(Exception):
            ItemCategory.objects.create(
                name="Electronics", abbreviation="ELEC02", description="Duplicate name"
            )

    def test_unique_abbreviation(self):
        with self.assertRaises(Exception):
            ItemCategory.objects.create(
                name="Other", abbreviation="ELEC01", description="Duplicate abbreviation"
            )

class ItemSubCategoryModelTest(TestCase):
    def setUp(self):
        self.category = ItemCategory.objects.create(
            name="Electronics", abbreviation="ELEC01", description="Electronic items"
        )
        self.subcategory = ItemSubCategory.objects.create(
            name="Phones", abbreviation="PHONE1", description="Mobile phones", item_category=self.category
        )

    def test_str(self):
        self.assertEqual(str(self.subcategory), "Phones")

    def test_unique_name_per_category(self):
        with self.assertRaises(Exception):
            ItemSubCategory.objects.create(
                name="Phones", abbreviation="PHONE2", description="Duplicate", item_category=self.category
            )

    def test_same_name_different_category(self):
        other = ItemCategory.objects.create(
            name="Appliances", abbreviation="APPL01", description="Home appliances"
        )
        sub = ItemSubCategory.objects.create(
            name="Phones", abbreviation="PHONE3", description="Same name", item_category=other
        )
        self.assertEqual(sub.name, "Phones")
        self.assertEqual(sub.item_category, other)

class ItemCategorySerializerTest(TestCase):
    def setUp(self):
        self.category = ItemCategory.objects.create(
            name="Electronics", abbreviation="ELEC01", description="Electronic items"
        )

    def test_serializer_output(self):
        serializer = ItemCategorySerializer(self.category)
        self.assertEqual(serializer.data["name"], "Electronics")
        self.assertEqual(serializer.data["abbreviation"], "ELEC01")

    def test_serializer_validation(self):
        data = {"name": "NewCat", "abbreviation": "NEW001", "description": "desc"}
        serializer = ItemCategorySerializer(data=data)
        self.assertTrue(serializer.is_valid())

class ItemSubCategorySerializerTest(TestCase):
    def setUp(self):
        self.category = ItemCategory.objects.create(
            name="Electronics", abbreviation="ELEC01", description="Electronic items"
        )
        self.subcategory = ItemSubCategory.objects.create(
            name="Phones", abbreviation="PHONE1", description="Mobile phones", item_category=self.category
        )

    def test_serializer_output(self):
        serializer = ItemSubCategorySerializer(self.subcategory)
        self.assertEqual(serializer.data["name"], "Phones")
        self.assertEqual(serializer.data["abbreviation"], "PHONE1")
        self.assertEqual(serializer.data["item_category"], self.category.id)

    def test_serializer_validation(self):
        data = {
            "name": "Laptops",
            "abbreviation": "LAP001",
            "description": "desc",
            "item_category": self.category.id,
        }
        serializer = ItemSubCategorySerializer(data=data)
        self.assertTrue(serializer.is_valid())

class ItemCategoryViewSetTest(TestCase):
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
        
        self.category1 = ItemCategory.objects.create(
            name="Electronics", abbreviation="ELEC01", description="Electronic items"
        )
        self.category2 = ItemCategory.objects.create(
            name="Appliances", abbreviation="APPL01", description="Home appliances"
        )

    def test_list(self):
        url = reverse("itemcategory-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_filter_name(self):
        url = reverse("itemcategory-list")
        response = self.client.get(url, {"name": "Electronics"})
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Electronics")

    def test_pagination(self):
        url = reverse("itemcategory-list")
        response = self.client.get(url, {"page_size": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertTrue("count" in response.data)

    def test_create(self):
        url = reverse("itemcategory-list")
        data = {"name": "Furniture", "abbreviation": "FURN01", "description": "desc"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ItemCategory.objects.count(), 3)

    def test_retrieve(self):
        url = reverse("itemcategory-detail", args=[self.category1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Electronics")

    def test_update(self):
        url = reverse("itemcategory-detail", args=[self.category1.id])
        data = {"name": "Electronics Updated", "abbreviation": "ELEC01", "description": "desc"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category1.refresh_from_db()
        self.assertEqual(self.category1.name, "Electronics Updated")

    def test_delete(self):
        url = reverse("itemcategory-detail", args=[self.category1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ItemCategory.objects.count(), 1)

class ItemSubCategoryViewSetTest(TestCase):
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
        
        self.category = ItemCategory.objects.create(
            name="Electronics", abbreviation="ELEC01", description="Electronic items"
        )
        self.sub1 = ItemSubCategory.objects.create(
            name="Phones", abbreviation="PHONE1", description="Mobile phones", item_category=self.category
        )
        self.sub2 = ItemSubCategory.objects.create(
            name="Laptops", abbreviation="LAP001", description="Laptops", item_category=self.category
        )

    def test_list(self):
        url = reverse("itemsubcategory-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_filter_name(self):
        url = reverse("itemsubcategory-list")
        response = self.client.get(url, {"name": "Phones"})
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Phones")

    def test_filter_item_category(self):
        url = reverse("itemsubcategory-list")
        response = self.client.get(url, {"item_category": self.category.id})
        self.assertEqual(len(response.data["results"]), 2)

    def test_pagination(self):
        url = reverse("itemsubcategory-list")
        response = self.client.get(url, {"page_size": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertTrue("count" in response.data)

    def test_create(self):
        url = reverse("itemsubcategory-list")
        data = {
            "name": "Tablets",
            "abbreviation": "TAB001",
            "description": "desc",
            "item_category": self.category.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ItemSubCategory.objects.count(), 3)

    def test_retrieve(self):
        url = reverse("itemsubcategory-detail", args=[self.sub1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Phones")

    def test_update(self):
        url = reverse("itemsubcategory-detail", args=[self.sub1.id])
        data = {
            "name": "Phones Updated",
            "abbreviation": "PHONE1",
            "description": "desc",
            "item_category": self.category.id,
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.sub1.refresh_from_db()
        self.assertEqual(self.sub1.name, "Phones Updated")

    def test_delete(self):
        url = reverse("itemsubcategory-detail", args=[self.sub1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ItemSubCategory.objects.count(), 1)
