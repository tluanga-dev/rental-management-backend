from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ItemCategoryViewSet, ItemSubCategoryViewSet

router = DefaultRouter()
router.register(r'categories', ItemCategoryViewSet, basename='itemcategory')
router.register(r'subcategories', ItemSubCategoryViewSet, basename='itemsubcategory')

urlpatterns = [
    path('', include(router.urls)),
]
