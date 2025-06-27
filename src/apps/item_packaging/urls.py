from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ItemPackagingViewSet

router = DefaultRouter()
router.register(r'', ItemPackagingViewSet, basename='itempackaging')

urlpatterns = [
    path('packaging/', include(router.urls)),
]
